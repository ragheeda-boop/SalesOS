"""Entity Resolution Matching Pipeline — Evidence-First.

Implements the full ER pipeline:
  Source rows → Blocking → Signal extraction → Pair evaluation → Persist

This is the core intelligence module that connects resolution_policy.py
(decision engine) to the database (md_source_rows → md_global_companies).

Design principles:
- Evidence-first: every match decision traces to concrete signals
- Government-ID veto: CR/VAT/Unified conflict = hard FORBIDS merge
- Source independence: ≥2 independent strong sources OR 1 government anchor
- No LLM in the resolution path: deterministic, auditable, reproducible
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.entity_resolution.resolution_policy import (
    SourceRecord,
    ConfidenceClass,
    Decision,
    EvidenceTier,
    Signal,
    SIGNAL_WEIGHTS,
    STRONG_DETERMINISTIC_SIGNALS,
    DOMAIN_BLACKLIST,
    evaluate_pair,
    normalize_cr,
    normalize_vat,
    normalize_unified_number,
    is_role_email,
)


# ── Constants ────────────────────────────────────────────────────────────────

# Fields extracted from raw_payload to SourceRecord
SOURCE_RECORD_FIELDS = [
    "cr_number", "vat_number", "unified_national_number",
    "canonical_name", "domain", "phone", "email", "website",
    "license_number", "membership_number", "city", "region",
]

# Common key aliases in raw payloads (MUHIDE v2 + others)
FIELD_ALIASES: dict[str, list[str]] = {
    "cr_number": ["cr_number", "CR_number", "cr", "CR", "سجل_تجاري", "رقم_سجل"],
    "vat_number": ["vat_number", "VAT_number", "vat", "VAT", "الرقم_الضريبي", "رقم_ضريبي"],
    "unified_national_number": [
        "unified_national_number", "unified_number", "national_number",
        "الرقم_الموحد", "رقم_موحد",
    ],
    "canonical_name": [
        "canonical_name", "company_name", "name", "اسم_الشركة",
        "الاسم", "اسم", "company",
    ],
    "domain": ["domain", "website_domain", "النطاق"],
    "phone": ["phone", "telephone", "tel", "mobile", "الهاتف", "جوال"],
    "email": ["email", "mail", "البريد"],
    "website": ["website", "url", "الموقع"],
    "city": ["city", "المدينة", "المنطقة"],
    "region": ["region", "المنطقة", "state", "المحافظة"],
}


# ── Helpers ──────────────────────────────────────────────────────────────────


def extract_field_value(raw_payload: dict[str, Any], field_name: str) -> str | None:
    """Extract a field value from raw_payload using aliases."""
    aliases = FIELD_ALIASES.get(field_name, [field_name])
    for alias in aliases:
        val = raw_payload.get(alias)
        if val is not None:
            s = str(val).strip()
            if s and s.lower() not in ("none", "null", "n/a", "—", "-"):
                return s
    return None


def extract_source_record(
    source_id: str,
    source_record_id: str,
    raw_payload: dict[str, Any],
) -> SourceRecord:
    """Convert raw payload dict → SourceRecord for policy evaluation."""
    fields = {}
    for field_name in SOURCE_RECORD_FIELDS:
        fields[field_name] = extract_field_value(raw_payload, field_name)
    return SourceRecord(source_id=source_id, **fields)


def normalize_domain(raw: str | None) -> str | None:
    """Normalize domain: lowercase, strip protocol/path."""
    if not raw:
        return None
    s = raw.strip().lower()
    s = re.sub(r'^https?://', '', s)
    s = re.sub(r'/.*$', '', s)
    s = s.strip('.')
    if not s or s in DOMAIN_BLACKLIST:
        return None
    return s


def normalize_phone(raw: str | None) -> str | None:
    """Normalize phone: strip spaces/dashes/dots, remove leading +."""
    if not raw:
        return None
    s = str(raw).strip()
    s = re.sub(r'[\s\-\.]+', '', s)
    s = s.lstrip('+')
    if not s.isdigit() or len(s) < 7:
        return None
    return s


def normalize_name(raw: str | None) -> str | None:
    """Normalize company name: lowercase, strip extra whitespace."""
    if not raw:
        return None
    s = raw.strip().lower()
    s = re.sub(r'\s+', ' ', s)
    return s if s else None


# ── Signal Extraction ────────────────────────────────────────────────────────


def extract_signals(
    record_a: SourceRecord,
    record_b: SourceRecord,
) -> list[Signal]:
    """Extract all matching signals between two SourceRecords.

    Returns a list of Signal objects indicating which signals matched,
    their weight, and evidence tier.
    """
    signals: list[Signal] = []
    source_ids = {record_a.source_id, record_b.source_id}

    # Government ID signals
    cr_a = normalize_cr(record_a.cr_number)
    cr_b = normalize_cr(record_b.cr_number)
    if cr_a and cr_b and cr_a == cr_b:
        signals.append(Signal(
            name="cr_match", matched=True, source_id=record_a.source_id,
            weight=100, tier=EvidenceTier.GOVERNMENT_ANCHOR,
        ))

    vat_a = normalize_vat(record_a.vat_number)
    vat_b = normalize_vat(record_b.vat_number)
    if vat_a and vat_b and vat_a == vat_b:
        signals.append(Signal(
            name="vat_match", matched=True, source_id=record_a.source_id,
            weight=100, tier=EvidenceTier.GOVERNMENT_ANCHOR,
        ))

    uni_a = normalize_unified_number(record_a.unified_national_number)
    uni_b = normalize_unified_number(record_b.unified_national_number)
    if uni_a and uni_b and uni_a == uni_b:
        signals.append(Signal(
            name="unified_match", matched=True, source_id=record_a.source_id,
            weight=100, tier=EvidenceTier.GOVERNMENT_ANCHOR,
        ))

    # Domain match
    dom_a = normalize_domain(record_a.domain) or normalize_domain(record_a.website)
    dom_b = normalize_domain(record_b.domain) or normalize_domain(record_b.website)
    if dom_a and dom_b and dom_a == dom_b:
        signals.append(Signal(
            name="domain_match", matched=True, source_id=record_a.source_id,
            weight=85, tier=EvidenceTier.STRONG_DETERMINISTIC,
        ))

    # Phone match
    ph_a = normalize_phone(record_a.phone)
    ph_b = normalize_phone(record_b.phone)
    if ph_a and ph_b and ph_a == ph_b:
        signals.append(Signal(
            name="phone_match", matched=True, source_id=record_a.source_id,
            weight=70, tier=EvidenceTier.WEAK_DETERMINISTIC,
        ))

    # Email match
    em_a = (record_a.email or "").strip().lower()
    em_b = (record_b.email or "").strip().lower()
    if em_a and em_b and em_a == em_b and not is_role_email(em_a):
        signals.append(Signal(
            name="email_match", matched=True, source_id=record_a.source_id,
            weight=70, tier=EvidenceTier.WEAK_DETERMINISTIC,
        ))

    # Canonical name exact match
    name_a = normalize_name(record_a.canonical_name)
    name_b = normalize_name(record_b.canonical_name)
    if name_a and name_b and name_a == name_b:
        signals.append(Signal(
            name="canonical_name_exact", matched=True, source_id=record_a.source_id,
            weight=65, tier=EvidenceTier.NORMALIZED_EXACT,
        ))
    elif name_a and name_b and len(name_a) > 3 and len(name_b) > 3:
        # Fuzzy: one contains the other
        if name_a in name_b or name_b in name_a:
            signals.append(Signal(
                name="canonical_name_contains", matched=True, source_id=record_a.source_id,
                weight=55, tier=EvidenceTier.FUZZY,
            ))

    # City match
    city_a = (record_a.city or "").strip().lower()
    city_b = (record_b.city or "").strip().lower()
    if city_a and city_b and city_a == city_b:
        signals.append(Signal(
            name="city", matched=True, source_id=record_a.source_id,
            weight=20, tier=EvidenceTier.WEAK_DETERMINISTIC,
        ))

    # Region match
    region_a = (record_a.region or "").strip().lower()
    region_b = (record_b.region or "").strip().lower()
    if region_a and region_b and region_a == region_b:
        signals.append(Signal(
            name="region", matched=True, source_id=record_a.source_id,
            weight=10, tier=EvidenceTier.WEAK_DETERMINISTIC,
        ))

    return signals


def compute_score(signals: list[Signal]) -> float:
    """Compute composite score from matched signals."""
    if not signals:
        return 0.0
    matched_weight = sum(s.weight for s in signals if s.matched)
    max_possible = sum(
        SIGNAL_WEIGHTS[s.name][0]
        for s in signals
        if s.name in SIGNAL_WEIGHTS
    )
    if max_possible == 0:
        return 0.0
    return (matched_weight / max_possible) * 100


# ── Blocking Strategy ────────────────────────────────────────────────────────


@dataclass
class BlockingCandidate:
    """A candidate match pair."""
    source_row_id_a: str
    source_row_id_b: str
    source_id_a: str
    source_id_b: str
    raw_payload_a: dict[str, Any]
    raw_payload_b: dict[str, Any]
    blocking_key: str  # Which blocking key matched


async def find_candidates(
    session: AsyncSession,
    tenant_id: str | None = None,
    source_file_id: str | None = None,
    max_candidates: int = 10000,
) -> list[BlockingCandidate]:
    """Find candidate pairs for matching using deterministic blocking.

    Blocking strategies (in priority order):
    1. Exact CR number
    2. Exact VAT number
    3. Exact Unified National Number
    4. Normalized name + city

    Returns list of BlockingCandidate pairs to evaluate.
    """
    candidates: list[BlockingCandidate] = []
    seen_pairs: set[tuple[str, str]] = set()

    async def _add_candidates(
        query: str, params: dict, blocking_key: str
    ):
        result = await session.execute(text(query), params)
        rows = [dict(r) for r in result.mappings().all()]

        # Group by blocking key value
        groups: dict[str, list[dict]] = {}
        for row in rows:
            key_val = str(row.get("blocking_value", "")).strip()
            if key_val:
                groups.setdefault(key_val, []).append(row)

        # Generate pairs within each group
        for key_val, group_rows in groups.items():
            for i in range(len(group_rows)):
                for j in range(i + 1, len(group_rows)):
                    a = group_rows[i]
                    b = group_rows[j]
                    pair = tuple(sorted([a["id"], b["id"]]))
                    if pair not in seen_pairs:
                        seen_pairs.add(pair)
                        candidates.append(BlockingCandidate(
                            source_row_id_a=a["id"],
                            source_row_id_b=b["id"],
                            source_id_a=a["source_id"],
                            source_id_b=b["source_id"],
                            raw_payload_a=a["raw_payload"],
                            raw_payload_b=b["raw_payload"],
                            blocking_key=blocking_key,
                        ))

    # Build tenant filter
    tenant_filter = ""
    file_filter = ""
    bind_params: dict[str, Any] = {}
    if tenant_id:
        tenant_filter = "AND sr.tenant_id = :tenant_id"
        bind_params["tenant_id"] = tenant_id
    if source_file_id:
        file_filter = "AND sr.source_file_id = :file_id"
        bind_params["file_id"] = source_file_id

    base_filter = f"{tenant_filter} {file_filter}"

    # Block 1: CR number (normalized: strip non-digits + control chars, min 5 digits).
    # Split on multi-value separators so a CR_Numbers list ('1005; 7066') does NOT get
    # concatenated into a fabricated anchor.  Take the FIRST separator-delimited token.
    await _add_candidates(
        f"""
        SELECT sr.id, sr.source_id, sr.raw_payload,
               REGEXP_REPLACE(
                   (REGEXP_REPLACE(REGEXP_REPLACE(
                       COALESCE(sr.raw_payload->>'cr_number', sr.raw_payload->>'CR_number', ''),
                       '[\\u200e\\u200f\\u202a-\\u202e\\u2066-\\u2069\\ufeff]', '', 'g'
                   ), '[;|,؛،/]+.*$', '', 'g')), '^0+', '') AS blocking_value
        FROM md_source_rows sr
        WHERE (
            sr.raw_payload->>'cr_number' IS NOT NULL AND sr.raw_payload->>'cr_number' != ''
            OR sr.raw_payload->>'CR_number' IS NOT NULL AND sr.raw_payload->>'CR_number' != ''
        )
          AND LENGTH(REGEXP_REPLACE(
              (REGEXP_REPLACE(REGEXP_REPLACE(
                  COALESCE(sr.raw_payload->>'cr_number', sr.raw_payload->>'CR_number', ''),
                  '[\\u200e\\u200f\\u202a-\\u202e\\u2066-\\u2069\\ufeff]', '', 'g'
              ), '[;|,؛،/]+.*$', '', 'g')), '^0+', '')) >= 5
          AND sr.global_entity_id IS NULL
          {base_filter}
        """,
        bind_params,
        "cr_number",
    )

    # Block 2: VAT number
    await _add_candidates(
        f"""
        SELECT sr.id, sr.source_id, sr.raw_payload,
               raw_payload->>'vat_number' AS blocking_value
        FROM md_source_rows sr
        WHERE sr.raw_payload->>'vat_number' IS NOT NULL
          AND sr.raw_payload->>'vat_number' != ''
          AND sr.global_entity_id IS NULL
          {base_filter}
        """,
        bind_params,
        "vat_number",
    )

    # Block 3: Unified number
    await _add_candidates(
        f"""
        SELECT sr.id, sr.source_id, sr.raw_payload,
               raw_payload->>'unified_national_number' AS blocking_value
        FROM md_source_rows sr
        WHERE sr.raw_payload->>'unified_national_number' IS NOT NULL
          AND sr.raw_payload->>'unified_national_number' != ''
          AND sr.global_entity_id IS NULL
          {base_filter}
        """,
        bind_params,
        "unified_national_number",
    )

    # Block 4: Normalized name + city (only for remaining candidates)
    # Check multiple name aliases: company_name, name, canonical_name, اسم_الشركة, etc.
    if len(candidates) < max_candidates:
        await _add_candidates(
            f"""
            SELECT sr.id, sr.source_id, sr.raw_payload,
                   LOWER(TRIM(COALESCE(
                       sr.raw_payload->>'company_name',
                       sr.raw_payload->>'name',
                       sr.raw_payload->>'canonical_name',
                       sr.raw_payload->>'اسم_الشركة',
                       sr.raw_payload->>'اسم',
                       sr.raw_payload->>'company',
                       ''
                   ))) || '|' ||
                   LOWER(TRIM(COALESCE(sr.raw_payload->>'city', sr.raw_payload->>'المدينة', ''))) AS blocking_value
            FROM md_source_rows sr
            WHERE COALESCE(
                      sr.raw_payload->>'company_name',
                      sr.raw_payload->>'name',
                      sr.raw_payload->>'canonical_name',
                      sr.raw_payload->>'اسم_الشركة',
                      sr.raw_payload->>'اسم',
                      sr.raw_payload->>'company',
                      ''
                  ) != ''
              AND sr.global_entity_id IS NULL
              {base_filter}
            """,
            bind_params,
            "name_city",
        )

    return candidates[:max_candidates]


# ── Match Result ─────────────────────────────────────────────────────────────


@dataclass
class MatchResult:
    """Result of evaluating a candidate pair."""
    source_row_id_a: str
    source_row_id_b: str
    source_id_a: str
    source_id_b: str
    confidence: ConfidenceClass
    decision: Decision
    score: float
    signals: list[Signal]
    veto_reason: str | None = None


@dataclass
class PipelineResult:
    """Summary of a full matching pipeline run."""
    total_candidates: int = 0
    matches_found: int = 0
    auto_merge: int = 0
    review: int = 0
    separate: int = 0
    vetoed: int = 0
    errors: int = 0
    duration_seconds: float = 0.0


# ── Persistence ──────────────────────────────────────────────────────────────


async def persist_match(
    session: AsyncSession,
    global_entity_id: str,
    source_row_id_a: str,
    source_row_id_b: str,
    result: MatchResult,
    match_status: str = "pending_review",
) -> str:
    """Persist a match result to md_entity_matches.

    Returns the match ID.
    """
    match_id = str(uuid.uuid4())
    now = datetime.now(UTC)

    signals_json = [
        {"name": s.name, "matched": s.matched, "source_id": s.source_id, "weight": s.weight}
        for s in result.signals if s.matched
    ]

    await session.execute(
        text(
            "INSERT INTO md_entity_matches "
            "(id, global_entity_id, source_a_id, source_b_id, match_score, match_method, "
            "match_signals, match_status, created_at) "
            "VALUES (:id, :entity_id, :src_a, :src_b, :score, :method, :signals, :status, :now) "
            "ON CONFLICT (source_a_id, source_b_id) DO NOTHING"
        ),
        {
            "id": match_id,
            "entity_id": global_entity_id,
            "src_a": source_row_id_a,
            "src_b": source_row_id_b,
            "score": result.score,
            "method": result.signals[0].name if result.signals else "unknown",
            "signals": signals_json,
            "status": match_status,
            "now": now,
        },
    )

    return match_id


async def persist_conflict(
    session: AsyncSession,
    global_entity_id: str,
    field_name: str,
    value_a: str,
    source_a_id: str,
    value_b: str,
    source_b_id: str,
    is_government_id: bool = False,
) -> str:
    """Persist a field-level conflict to md_entity_conflicts.

    Returns the conflict ID.
    """
    conflict_id = str(uuid.uuid4())
    now = datetime.now(UTC)

    await session.execute(
        text(
            "INSERT INTO md_entity_conflicts "
            "(id, global_entity_id, field_name, value_a, source_a_id, source_a_priority, "
            "value_b, source_b_id, source_b_priority, is_government_id, veto_enabled, "
            "resolution, created_at) "
            "VALUES (:id, :entity_id, :field, :val_a, :src_a, :pri_a, :val_b, :src_b, :pri_b, "
            ":is_gov, :veto, 'open', :now)"
        ),
        {
            "id": conflict_id,
            "entity_id": global_entity_id,
            "field": field_name,
            "val_a": value_a,
            "src_a": source_a_id,
            "pri_a": 0,
            "val_b": value_b,
            "src_b": source_b_id,
            "pri_b": 0,
            "is_gov": is_government_id,
            "veto": is_government_id,
            "now": now,
        },
    )

    return conflict_id


# ── Full Pipeline ────────────────────────────────────────────────────────────


async def run_matching_pipeline(
    session: AsyncSession,
    tenant_id: str | None = None,
    source_file_id: str | None = None,
    max_candidates: int = 100000,
) -> PipelineResult:
    """Run the full entity resolution matching pipeline.

    Steps:
    1. Blocking: find candidate pairs by shared blocking keys
    2. Signal extraction: convert raw payloads → SourceRecord pairs
    3. Pair evaluation: resolution_policy.evaluate_pair()
    4. Persist matches and conflicts
    5. Update source row resolution status

    Returns PipelineResult with summary counts.
    """
    import time
    start = time.monotonic()

    result = PipelineResult()

    # Step 1: Blocking
    candidates = await find_candidates(session, tenant_id, source_file_id, max_candidates)
    result.total_candidates = len(candidates)

    # Batch size for persistence
    BATCH_SIZE = 5000
    match_batch: list[dict] = []

    # Step 2-4: Evaluate each candidate pair
    for cand in candidates:
        try:
            record_a = extract_source_record(
                cand.source_id_a, cand.source_row_id_a, cand.raw_payload_a
            )
            record_b = extract_source_record(
                cand.source_id_b, cand.source_row_id_b, cand.raw_payload_b
            )

            signals = extract_signals(record_a, record_b)
            score = compute_score(signals)
            er_result = evaluate_pair(record_a, record_b, signals, score)

            match_result = MatchResult(
                source_row_id_a=cand.source_row_id_a,
                source_row_id_b=cand.source_row_id_b,
                source_id_a=cand.source_id_a,
                source_id_b=cand.source_id_b,
                confidence=er_result.confidence,
                decision=er_result.decision,
                score=er_result.score,
                signals=er_result.signals,
                veto_reason=er_result.veto.reason if er_result.veto else None,
            )

            if er_result.decision == Decision.AUTO_MERGE:
                result.auto_merge += 1
                match_status = "auto_matched"
            elif er_result.decision == Decision.REVIEW:
                result.review += 1
                match_status = "pending_review"
            elif er_result.decision == Decision.VETOED:
                result.vetoed += 1
                match_status = "vetoed"
            else:
                result.separate += 1
                match_status = "separate"

            if er_result.decision != Decision.SEPARATE:
                signals_json = [
                    {"name": s.name, "matched": s.matched, "source_id": s.source_id, "weight": s.weight}
                    for s in er_result.signals if s.matched
                ]
                match_batch.append({
                    "id": str(uuid.uuid4()),
                    "entity_id": "",
                    "src_a": cand.source_row_id_a,
                    "src_b": cand.source_row_id_b,
                    "score": er_result.score,
                    "method": er_result.signals[0].name if er_result.signals else "unknown",
                    "signals": signals_json,
                    "status": match_status,
                    "now": datetime.now(UTC),
                })
                result.matches_found += 1

                # Persist batch when full
                if len(match_batch) >= BATCH_SIZE:
                    await _flush_match_batch(session, match_batch)
                    match_batch.clear()

                # Persist field-level conflicts
                if er_result.veto and er_result.veto.vetoed:
                    await persist_conflict(
                        session,
                        global_entity_id="",
                        field_name=er_result.veto.field_name,
                        value_a=er_result.veto.value_a,
                        source_a_id=cand.source_id_a,
                        value_b=er_result.veto.value_b,
                        source_b_id=cand.source_id_b,
                        is_government_id=True,
                    )

        except Exception:
            result.errors += 1

    # Flush remaining batch
    if match_batch:
        await _flush_match_batch(session, match_batch)

    result.duration_seconds = time.monotonic() - start
    return result


async def _flush_match_batch(session: AsyncSession, batch: list[dict]) -> None:
    """Flush a batch of match records using executemany."""
    if not batch:
        return
    from sqlalchemy import insert as sa_insert
    # Use raw executemany for performance
    await session.execute(
        text(
            "INSERT INTO md_entity_matches "
            "(id, global_entity_id, source_a_id, source_b_id, match_score, match_method, "
            "match_signals, match_status, created_at) "
            "VALUES (:id, :entity_id, :src_a, :src_b, :score, :method, :signals, :status, :now) "
            "ON CONFLICT (source_a_id, source_b_id) DO NOTHING"
        ),
        batch,
    )
