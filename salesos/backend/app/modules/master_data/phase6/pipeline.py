"""Phase 6 — DB pipeline (idempotent, dry-run aware).

Reads Master Account source rows from `md_source_rows` (source_id =
muhide_master_accounts), computes the corrected OPTION-C classification plus
all Phase 6 derived outputs, and stages writes into the md_* Phase 6 tables.

DRY RUN: when dry_run=True the pipeline performs ZERO writes. Every intended
operation is recorded as a change row and all safety counters must be 0
(source rows modified, raw_payload modified, global IDs changed, existing
entities deleted, fuzzy auto-merges, government-ID vetoes bypassed, Apollo
calls, external API calls, production writes).

IDEMPOTENCY: every write uses deterministic unique keys / fingerprints so re-
running produces no duplicates (ON CONFLICT / deterministic PKs).
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from collections import Counter
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import asyncpg

from app.modules.master_data.phase6.classification import (
    IdentityState,
    classify_corrected,
    is_real_domain,
)
from app.modules.master_data.phase6.industry import normalize_industry
from app.modules.master_data.phase6.quality import score_quality
from app.modules.master_data.phase6.readiness import recompute_sales_readiness
from app.modules.master_data.phase6.relationships import infer_relationship

CLASSIFICATION_VERSION = "OPTION_C_1"
# The one version Phase 7 readers use. Change only with a report citing the
# run that produced it (history of every version stays in the tables).
ACTIVE_CLASSIFICATION_VERSION = "OPTION_C_1+EXCL_NCNP+DOMSH5"  # report 108

# Best_Match_Confidence values observed in MUHIDE data.
_CONFIDENCE_MATCHED = ("MATCHED", "LIKELY MATCH")
_CONFIDENCE_REVIEW = ("REVIEW REQUIRED", "REVIEW REQUIRED (fuzzy suggestion)")
MAX_CHANGE_SAMPLE = 20


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _b(s: Any) -> bool:
    if s is None:
        return False
    return str(s).strip().lower() in ("true", "1", "yes")


def _s(v: Any) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    if not s or s.lower() in ("none", "nan", "null", "n/a", ""):
        return None
    return s


def _digest(*parts: Any) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(str(p).encode("utf-8", errors="replace"))
    return h.hexdigest()


def _split_multi(v: str | None) -> list[str]:
    if not v:
        return []
    return [t.strip() for t in re.split(r"[;|،؛,]+", v) if t.strip()]


SHARED_DOMAIN_ALLOWLIST_PATH = Path(__file__).with_name("data") / "shared_domain_allowlist.csv"


def load_shared_domain_allowlist(path: Path = SHARED_DOMAIN_ALLOWLIST_PATH) -> frozenset[str]:
    """Group domains legitimately shared by one company's branches (report 108)."""
    import csv

    if not path.exists():
        return frozenset()
    with open(path, encoding="utf-8") as fh:
        return frozenset(r["domain"].strip().lower() for r in csv.DictReader(fh) if r["domain"].strip())


def _cr_digits(v: str) -> str:
    return re.sub(r"\D", "", v)


def filter_cr_by_source(
    cr_values: list[str],
    source_map: dict[str, dict[str, list[str]]],
    excluded_sources: frozenset[str],
) -> list[str]:
    """Drop CR tokens contributed only by excluded sources (PO decision G3-2, report 104).

    NCNP registers non-profits, which hold no commercial registration; its
    numbers must never act as a CR anchor. A token another source also reports
    is kept. Accounts with no source-map attribution are returned unchanged.
    """
    if not excluded_sources or not source_map:
        return list(cr_values)
    excluded = {
        _cr_digits(t) for s in excluded_sources for t in source_map.get(s, {}).get("cr", [])
    }
    vouched = {
        _cr_digits(t)
        for s, v in source_map.items()
        if s not in excluded_sources
        for t in v.get("cr", [])
    }
    return [t for t in cr_values if _cr_digits(t) not in excluded or _cr_digits(t) in vouched]


def _first_token_cr(v: str | None) -> dict[str, list[str]]:
    """Return per-source CR values from a single raw field (list of tokens)."""
    return {"_": list(_split_multi(v))}


class Phase6Pipeline:
    """Compute + optionally write Phase 6 outputs for all Master Accounts."""

    def __init__(
        self,
        conn: asyncpg.Connection,
        *,
        dry_run: bool = True,
        change_sink: Callable[[dict[str, Any]], None] | None = None,
        cr_excluded_sources: frozenset[str] = frozenset(),
        shared_domain_threshold: int | None = None,
    ):
        self.conn = conn
        self.cr_excluded_sources = frozenset(cr_excluded_sources)
        # A domain used by >= this many distinct Master Accounts is a platform,
        # agent, typo free-mail or placeholder, not an entity's own domain (report 107).
        self.shared_domain_threshold = shared_domain_threshold
        self._shared_domains: set[str] = set()
        self.dry_run = dry_run
        self.change_sink = change_sink
        self.safety = Counter()
        self.changes: list[dict[str, Any]] = []
        self.change_count = 0
        self._staged_counts = Counter()
        self._identity_sample_rows: list[tuple[Any, ...]] = []
        self._processed_accounts = 0
        self.summary = Counter()
        self._identity_rows: list[tuple[Any, ...]] = []
        self._candidate_rows: list[dict[str, Any]] = []
        self._industry_rows: list[tuple[Any, ...]] = []
        self._rel_rows: list[dict[str, Any]] = []
        self._quality_rows: list[tuple[Any, ...]] = []
        self._readiness_rows: list[tuple[Any, ...]] = []
        # A different CR rule is a different classification; never reuse the key.
        self.version = (
            CLASSIFICATION_VERSION + "+EXCL_" + "_".join(sorted(self.cr_excluded_sources))
            if self.cr_excluded_sources
            else CLASSIFICATION_VERSION
        )
        if shared_domain_threshold:
            self.version += f"+DOMSH{shared_domain_threshold}"

    # ── helpers ─────────────────────────────────────────────────────────────

    async def _load_ma_source_maps(
        self, master_account_ids: set[str] | None = None
    ) -> dict[str, dict[str, dict[str, list[str]]]]:
        """Load per-MA per-source-system field values from the source map.

        Returns {master_account_id: {source_system: {
            "cr":   [normalized CR strings],
            "domain": [domain strings],
            "phone": [phone strings],
            "name": [company-name strings],
        }}}. Signals are grouped by their ACTUAL source system so that
        corroboration is evaluated across genuinely independent sources and
        same-source duplicates are never treated as independent (D1 fix).
        """
        rows = await self._fetch_scoped_rows(
            """SELECT raw_payload FROM md_source_rows
               WHERE source_id = 'muhide_source_map'""",
            """SELECT raw_payload FROM md_source_rows
               WHERE source_id = 'muhide_source_map'
                 AND raw_payload->>'Master Account ID' = ANY($1::text[])""",
            master_account_ids,
        )
        out: dict[str, dict[str, dict[str, list[str]]]] = {}
        for r in rows:
            p = self._parse_payload(r["raw_payload"])
            ma = _s(p.get("Master Account ID"))
            sysname = _s(p.get("Source System"))
            if not ma or not sysname:
                continue
            entry = out.setdefault(ma, {}).setdefault(sysname, {
                "cr": [], "domain": [], "phone": [], "name": [],
            })
            cr = _s(p.get("Source CR Number"))
            if cr:
                entry["cr"].extend(t for t in _split_multi(cr) if t)
            dom = _s(p.get("Source Domain"))
            if dom:
                entry["domain"].append(dom)
            phone = _s(p.get("Source Phone"))
            if phone:
                entry["phone"].append(phone)
            name = _s(p.get("Source Company Name"))
            if name:
                entry["name"].append(name)
        return out

    def _record(self, *, op: str, entity_id: str | None, table: str,
                payload: dict[str, Any], safety: str | None = None,
                key: str | None = None) -> None:
        change = {
            "op": op, "entity_id": entity_id, "table": table,
            "key": key or "", "payload": json.dumps(payload, ensure_ascii=False, default=str),
        }
        self.change_count += 1
        if self.change_sink is not None:
            self.change_sink(change)
        if len(self.changes) < MAX_CHANGE_SAMPLE:
            self.changes.append(change)
        if safety:
            self.safety[safety] += 1

    async def _fetch_scoped_rows(
        self,
        unscoped_query: str,
        scoped_query: str,
        identifiers: set[str] | None,
    ) -> list[Any]:
        """Fetch all rows, or a deterministic subset; an empty set returns none."""
        if identifiers is None:
            return await self.conn.fetch(unscoped_query)
        if not identifiers:
            return []
        return await self.conn.fetch(scoped_query, sorted(identifiers))

    @staticmethod
    def _parse_payload(p: dict[str, Any] | str) -> dict[str, Any]:
        if isinstance(p, str):
            import json as _json
            try:
                return _json.loads(p)
            except _json.JSONDecodeError:
                return {}
        return p

    # ── source field extraction ─────────────────────────────────────────────

    def _extract(self, p: dict[str, Any] | str) -> dict[str, Any]:
        p = self._parse_payload(p)
        cr_values = _split_multi(_s(p.get("CR_Numbers")))
        cr_raw = _s(p.get("CR_Numbers"))
        primary_domain = _s(p.get("Primary_Domain"))
        all_domains = _s(p.get("All_Domains")) or primary_domain
        apollo = _s(p.get("Apollo_Account_IDs")) or _s(p.get("Apollo_Account_ID"))
        src_count_raw = _s(p.get("Source_Count")) or _s(p.get("Distinct_Source_System_Count"))
        try:
            src_count = int(src_count_raw) if src_count_raw else 1
        except ValueError:
            src_count = 1
        # Independent source systems: parse Source_Systems (; separated).
        indep = len(
            {s.split("(")[0].strip() for s in _split_multi(_s(p.get("Source_Systems")))}
        )
        if indep == 0:
            indep = src_count
        return {
            "cr_values": cr_values,
            "cr_raw": cr_raw,
            "master_account_id": _s(p.get("Master Account ID")),
            "primary_domain": primary_domain,
            "all_domains": all_domains,
            "apollo": apollo,
            "src_count": src_count,
            "indep": indep,
            "has_email": _b(p.get("has_email")),
            "has_phone": _b(p.get("has_phone")),
            "email": _s(p.get("Primary_Email")),
            "phone": _s(p.get("Primary_Phone")),
            "industry_raw": _s(p.get("Industry_Raw_Values")),
            "confidence": _s(p.get("Best_Match_Confidence")),
            "sales_priority": _s(p.get("Sales_Priority")),
            "icp": _s(p.get("ICP_Classification")),
            "canonical_name": _s(p.get("Canonical_Company_Name")),
            "city": _s(p.get("City")),
            "all_phones": _s(p.get("All_Phones")),
            "is_fuzzy": "fuzzy" in (_s(p.get("Best_Match_Confidence")) or "").lower()
                        or (_s(p.get("Under_Entity_Review")) or "").strip().lower() == "true",
        }

    async def _load_shared_domains(self) -> None:
        if not self.shared_domain_threshold:
            return
        rows = await self.conn.fetch(
            """SELECT lower(trim(raw_payload->>'Source Domain')) AS d
                 FROM md_source_rows
                WHERE source_id = 'muhide_source_map'
                  AND coalesce(trim(raw_payload->>'Source Domain'), '') <> ''
                GROUP BY 1
               HAVING count(DISTINCT raw_payload->>'Master Account ID') >= $1""",
            self.shared_domain_threshold,
        )
        allow = load_shared_domain_allowlist()
        self._shared_domains = {r["d"] for r in rows} - allow
        self.summary["shared_domains_allowlisted"] = len({r["d"] for r in rows} & allow)
        self.summary["shared_domains_excluded"] = len(self._shared_domains)

    def _is_entity_domain(self, d: str | None) -> bool:
        return is_real_domain(d) and (d or "").strip().lower() not in self._shared_domains

    def _process_account(
        self,
        row: Any,
        ma_source_maps: dict[str, dict[str, dict[str, list[str]]]],
        identity_states: Counter,
        cr_classes: Counter,
        priorities: Counter,
    ) -> None:
        sr_id = str(row["source_row_id"])
        payload = row["raw_payload"]
        ex = self._extract(payload)
        domain = ex["primary_domain"] or ex["all_domains"]
        if self._shared_domains:
            candidates = [ex["primary_domain"], *_split_multi(ex["all_domains"])]
            entity = next((d for d in candidates if self._is_entity_domain(d)), None)
            if entity != domain and is_real_domain(domain):
                self.summary["domain_changed_by_shared_rule"] += 1
            domain = entity
        ma_id = ex.get("master_account_id") or sr_id

        source_map = ma_source_maps.get(ma_id, {})
        cr_values = ex["cr_values"]
        cr_raw = _s(ex.get("cr_raw"))
        if self.cr_excluded_sources:
            kept = filter_cr_by_source(cr_values, source_map, self.cr_excluded_sources)
            if len(kept) != len(cr_values):
                self.summary["cr_accounts_changed_by_source_rule"] += 1
                self.summary["cr_tokens_excluded_by_source_rule"] += len(cr_values) - len(kept)
                cr_values, cr_raw = kept, ("; ".join(kept) or None)
        cr_by_src = {
            system: values["cr"]
            for system, values in source_map.items()
            if values["cr"] and system not in self.cr_excluded_sources
        }
        domain_by_src = {
            system: [value for value in values["domain"] if self._is_entity_domain(value)]
            for system, values in source_map.items()
            if any(self._is_entity_domain(value) for value in values["domain"])
        }
        phone_by_src = {
            system: values["phone"] for system, values in source_map.items() if values["phone"]
        }
        name_by_src = {
            system: values["name"] for system, values in source_map.items() if values["name"]
        }

        if not cr_by_src and cr_values:
            cr_by_src = {"_": cr_values}
        if not domain_by_src and self._is_entity_domain(domain):
            domain_by_src = {"_": [domain]}
        if not phone_by_src and ex.get("all_phones"):
            phone_by_src = {"_": _split_multi(_s(ex.get("all_phones", "")))}
        if not name_by_src and ex["canonical_name"]:
            name_by_src = {"_": [ex["canonical_name"]]}

        result = classify_corrected(
            cr_number=cr_raw,
            domain=domain,
            apollo_account_id=ex["apollo"],
            confidence=ex["confidence"],
            source_count=ex["src_count"],
            independent_source_count=ex["indep"],
            has_contactable_email=ex["has_email"],
            has_phone=ex["has_phone"],
            fuzzy_candidate=ex["is_fuzzy"],
            cr_values_by_source=cr_by_src,
            domain_values_by_source=domain_by_src,
            phone_values_by_source=phone_by_src,
            name_values_by_source=name_by_src,
            source_ids=sorted(source_map.keys()) if source_map else ["muhide_master_accounts"],
        )
        identity_states[result.identity_state.value] += 1
        cr_classes[result.cr_class] += 1
        priorities[result.review_priority] += 1

        entity_key = self._real_company_id(ma_id)
        if entity_key is None:
            self.summary["unmapped_master_accounts"] += 1
            self.safety["unmapped_master_account_without_global_company_id"] += 1
            return

        readiness = recompute_sales_readiness(
            identity_state=result.identity_state,
            has_contactable_email=ex["has_email"],
            has_phone=ex["has_phone"],
            has_real_domain=result.has_real_domain,
        )
        identity_row = (
            entity_key, result.identity_state.value, readiness.sales_readiness.value,
            result.review_priority, result.cr_class, result.has_cr, result.has_vat,
            result.has_unified, result.has_real_domain, result.independent_source_count,
            result.source_count, result.field_conflict,
            json.dumps(result.signals, ensure_ascii=False, default=str),
            json.dumps(result.source_ids, ensure_ascii=False),
        )
        self._identity_rows.append(identity_row)
        if self._processed_accounts % 500 == 0:
            self._identity_sample_rows.append(identity_row)

        if result.review_priority in ("P0", "P1", "P2", "P3"):
            self._candidate_rows.append({
                "entity_key": entity_key,
                "candidate_type": result.review_priority,
                "priority_score": self._priority_score(result, ex),
                "reason": self._candidate_reason(result, ex),
                "evidence": result.signals,
                "source_ids": result.source_ids,
            })

        if ex["industry_raw"]:
            industry = normalize_industry(ex["industry_raw"])
            normalized_industry = (industry.normalized_industry or "")[:255]
            self._industry_rows.append((
                entity_key, industry.raw_industry, normalized_industry,
                industry.industry_code or "", industry.normalization_method, sr_id, True,
            ))

        quality = score_quality(
            fields={
                "cr_number": result.has_cr, "vat_number": result.has_vat,
                "unified_national_number": result.has_unified,
                "domain": result.has_real_domain, "phone": ex["has_phone"],
                "email": ex["has_email"], "city": bool(ex["city"]),
                "industry": bool(ex["industry_raw"]),
            },
            provenance_tiers=self._provenance_tiers(result),
            field_conflict=result.field_conflict,
            conflict_fields=result.signals.get("conflict_fields", []),
            independent_source_count=result.independent_source_count,
            source_count=result.source_count,
        )
        self._quality_rows.append((
            entity_key, quality.completeness_score, quality.accuracy_score,
            quality.consistency_score, quality.freshness_score, quality.provenance_score,
            quality.overall_score, json.dumps(quality.evidence_basis, ensure_ascii=False),
            None, None,
        ))
        self._readiness_rows.append((
            entity_key, readiness.sales_readiness.value, result.identity_state.value,
            json.dumps(readiness.basis, ensure_ascii=False), None, None,
        ))
        self._processed_accounts += 1

    # ── main compute + stage ────────────────────────────────────────────────

    async def run(self, *, max_accounts: int | None = None) -> dict[str, Any]:
        if max_accounts is not None:
            if max_accounts < 1:
                raise ValueError("max_accounts must be a positive integer")
            if not self.dry_run:
                raise ValueError("Bounded account runs are permitted only in dry-run mode")

        if self.dry_run:
            return await self._run_streamed_dry_run(max_accounts)
        if max_accounts is not None:
            raise ValueError("Bounded account runs are permitted only in dry-run mode")
        return await self._run_buffered()

    def _reset_run_state(self) -> None:
        for rows in (
            self._identity_rows, self._candidate_rows, self._industry_rows,
            self._rel_rows, self._quality_rows, self._readiness_rows,
            self.changes, self._identity_sample_rows,
        ):
            rows.clear()
        self.summary.clear()
        self.safety.clear()
        self.change_count = 0
        self._staged_counts.clear()
        self._processed_accounts = 0

    def _flush_dry_run_batch(self) -> None:
        batch_counts = {
            "identity_classifications": len(self._identity_rows),
            "review_candidates": len(self._candidate_rows),
            "industry_normalizations": len(self._industry_rows),
            "quality_history": len(self._quality_rows),
            "sales_readiness_history": len(self._readiness_rows),
        }
        for table, count in batch_counts.items():
            self._staged_counts[table] += count
        self._stage_as_changes()
        self._identity_rows.clear()
        self._candidate_rows.clear()
        self._industry_rows.clear()
        self._quality_rows.clear()
        self._readiness_rows.clear()

    async def _load_company_mapping(self, master_account_ids: set[str] | None = None) -> None:
        rows = await self._fetch_scoped_rows(
            "SELECT legacy_id, global_entity_id FROM md_legacy_id_mappings "
            "WHERE legacy_id_type='LEGACY_MUHIDE_MA_ID'",
            "SELECT legacy_id, global_entity_id FROM md_legacy_id_mappings "
            "WHERE legacy_id_type='LEGACY_MUHIDE_MA_ID' "
            "AND legacy_id = ANY($1::text[])",
            master_account_ids,
        )
        self.ma_to_company = {
            str(row["legacy_id"]): str(row["global_entity_id"])
            for row in rows
        }

    async def _run_streamed_dry_run(self, max_accounts: int | None) -> dict[str, Any]:
        """Process dry-run account rows in bounded batches and stream change details."""
        self._reset_run_state()
        await self._load_shared_domains()
        self.summary["sampled_run"] = max_accounts is not None
        self.summary["sample_limit"] = max_accounts or 0
        identity_states = Counter()
        cr_classes = Counter()
        priorities = Counter()
        account_query = """SELECT id AS source_row_id, raw_payload
                           FROM md_source_rows
                           WHERE source_id = 'muhide_master_accounts'
                           ORDER BY id"""
        batch_size = 10_000

        if max_accounts is not None:
            rows = await self.conn.fetch(account_query + " LIMIT $1", max_accounts)
            ma_ids = {
                value
                for row in rows
                if (value := _s(self._parse_payload(row["raw_payload"]).get("Master Account ID")))
            }
            await self._load_company_mapping(ma_ids)
            source_maps = await self._load_ma_source_maps(ma_ids)
            for row in rows:
                self._process_account(row, source_maps, identity_states, cr_classes, priorities)
            self.summary["master_accounts_loaded"] = len(rows)
            self._flush_dry_run_batch()
            relationship_scope = ma_ids
        else:
            last_id = None
            processed = 0
            while True:
                if last_id is None:
                    rows = await self.conn.fetch(account_query + " LIMIT $1", batch_size)
                else:
                    rows = await self.conn.fetch(
                        """SELECT id AS source_row_id, raw_payload
                           FROM md_source_rows
                           WHERE source_id = 'muhide_master_accounts' AND id > $1::uuid
                           ORDER BY id LIMIT $2""",
                        last_id,
                        batch_size,
                    )
                if not rows:
                    break
                ma_ids = {
                    value
                    for row in rows
                    if (value := _s(self._parse_payload(row["raw_payload"]).get("Master Account ID")))
                }
                await self._load_company_mapping(ma_ids)
                source_maps = await self._load_ma_source_maps(ma_ids)
                for row in rows:
                    self._process_account(row, source_maps, identity_states, cr_classes, priorities)
                processed += len(rows)
                self.summary["master_accounts_loaded"] = processed
                self._flush_dry_run_batch()
                last_id = str(rows[-1]["source_row_id"])
            relationship_scope = None

        self.summary["identity_states"] = dict(identity_states)
        self.summary["cr_classes"] = dict(cr_classes)
        self.summary["priorities"] = dict(priorities)
        await self._stage_contact_relationships(relationship_scope)
        self.summary["contact_relationships_staged"] = len(self._rel_rows)
        self._staged_counts["contact_relationships"] += len(self._rel_rows)
        self._stage_relationship_changes()
        self._rel_rows.clear()
        return self._result()

    async def _run_buffered(self) -> dict[str, Any]:
        """Non-dry-run implementation; restricted callers should use dry-run first."""
        self._reset_run_state()

        account_query = """SELECT id AS source_row_id, raw_payload
                            FROM md_source_rows
                            WHERE source_id = 'muhide_master_accounts'
                            ORDER BY id"""
        rows = await self.conn.fetch(account_query)
        self.summary["master_accounts_loaded"] = len(rows)
        self.summary["sampled_run"] = False
        self.summary["sample_limit"] = 0
        id_state = Counter()
        cr_class_ct = Counter()
        priority = Counter()

        # Real Global Company IDs (D2): md_legacy_id_mappings resolves each
        # Master Account to the authoritative md_global_companies.id.
        await self._load_company_mapping()
        await self._load_shared_domains()

        # Per-source field values (D1): build genuine field-agreement maps.
        ma_source_maps = await self._load_ma_source_maps()

        for r in rows:
            self._process_account(r, ma_source_maps, id_state, cr_class_ct, priority)

        self.summary["identity_states"] = dict(id_state)
        self.summary["cr_classes"] = dict(cr_class_ct)
        self.summary["priorities"] = dict(priority)

        # Contact ↔ company relationship evidence (person layer).
        await self._stage_contact_relationships()

        # Persist staged rows (or record as changes in dry-run).
        if not self.dry_run:
            if self.safety:
                raise RuntimeError(
                    "Phase 6 refused database writes because one or more safety gates failed: "
                    f"{dict(self.safety)}"
                )
            await self._write_all()
            await self._write_relationships()
        else:
            self._stage_as_changes()
            self._stage_relationship_changes()

        self._staged_counts.update({
            "identity_classifications": len(self._identity_rows),
            "review_candidates": len(self._candidate_rows),
            "industry_normalizations": len(self._industry_rows),
            "quality_history": len(self._quality_rows),
            "sales_readiness_history": len(self._readiness_rows),
            "contact_relationships": len(self._rel_rows),
        })

        return self._result()

    # ── contact relationship evidence ───────────────────────────────────────

    async def _stage_contact_relationships(
        self, master_account_ids: set[str] | None = None
    ) -> None:
        conn = self.conn
        contacts = await self._fetch_scoped_rows(
            "SELECT raw_payload FROM md_source_rows WHERE source_id='muhide_contacts'",
            """SELECT raw_payload FROM md_source_rows
               WHERE source_id='muhide_contacts'
                 AND raw_payload->>'Master Account ID' = ANY($1::text[])""",
            master_account_ids,
        )
        contact_rows = [
            self._parse_payload(row["raw_payload"])
            for row in contacts
        ]
        contact_ids = {
            value for row in contact_rows if (value := _s(row.get("Contact ID")))
        }
        contact_ma_ids = {
            value for row in contact_rows if (value := _s(row.get("Master Account ID")))
        }

        person_by_contact = {}
        person_mappings = await self._fetch_scoped_rows(
            "SELECT legacy_id, global_entity_id FROM md_legacy_id_mappings "
            "WHERE legacy_id_type='LEGACY_MUHIDE_CONTACT_ID'",
            "SELECT legacy_id, global_entity_id FROM md_legacy_id_mappings "
            "WHERE legacy_id_type='LEGACY_MUHIDE_CONTACT_ID' "
            "AND legacy_id = ANY($1::text[])",
            contact_ids,
        )
        for mapping in person_mappings:
            person_by_contact[str(mapping["legacy_id"])] = str(mapping["global_entity_id"])

        company_by_ma = {}
        company_mappings = await self._fetch_scoped_rows(
            "SELECT legacy_id, global_entity_id FROM md_legacy_id_mappings "
            "WHERE legacy_id_type='LEGACY_MUHIDE_MA_ID'",
            "SELECT legacy_id, global_entity_id FROM md_legacy_id_mappings "
            "WHERE legacy_id_type='LEGACY_MUHIDE_MA_ID' "
            "AND legacy_id = ANY($1::text[])",
            contact_ma_ids,
        )
        for mapping in company_mappings:
            company_by_ma[str(mapping["legacy_id"])] = str(mapping["global_entity_id"])

        person_ids = set(person_by_contact.values())
        people = (
            await conn.fetch(
                "SELECT id, company_global_id, email FROM md_global_people "
                "WHERE id = ANY($1::uuid[])",
                list(person_ids),
            )
            if person_ids
            else []
        )
        person_company = {}
        person_domain = {}
        for person in people:
            person_id = str(person["id"])
            if person["company_global_id"]:
                person_company[person_id] = str(person["company_global_id"])
            email = str(person["email"] or "").strip()
            if "@" in email:
                domain = email.rsplit("@", 1)[1].lower()
                if "." in domain:
                    person_domain[person_id] = domain

        company_ids = set(company_by_ma.values())
        companies = (
            await conn.fetch(
                "SELECT id, domain FROM md_global_companies "
                "WHERE domain IS NOT NULL AND id = ANY($1::uuid[])",
                list(company_ids),
            )
            if company_ids
            else []
        )
        company_domain = {
            str(company["id"]): str(company["domain"]).strip().lower()
            for company in companies
        }

        for p in contact_rows:
            cid = _s(p.get("Contact ID"))
            ma = _s(p.get("Master Account ID"))
            person_id = person_by_contact.get(str(cid)) if cid else None
            company_id = company_by_ma.get(str(ma)) if ma else None
            if not person_id or not company_id:
                continue
            rel = infer_relationship(
                person_global_id=person_id,
                company_global_id=company_id,
                relationship_type="contact",
                person_company_global_id=person_company.get(person_id),
                source_ma_assignment=bool(ma),
                email_domain_match=bool(
                    person_domain.get(person_id)
                    and company_domain.get(company_id)
                    and person_domain[person_id] == company_domain[company_id]
                ),
                person_email_domain=person_domain.get(person_id),
                company_domain=company_domain.get(company_id),
                source_id="muhide_contacts",
                observed_at=_now(),
            )
            from datetime import datetime as _dt
            obs_at = rel.observed_at
            if isinstance(obs_at, str):
                obs_at = _dt.fromisoformat(obs_at.replace('Z', '+00:00'))
            self._rel_rows.append({
                "person_id": person_id, "company_id": company_id,
                "relationship_type": rel.relationship_type, "status": rel.status,
                "linking_basis": rel.linking_basis, "confidence": rel.confidence,
                "evidence": rel.evidence, "source_id": rel.source_id,
                "observed_at": obs_at,
            })
        self.summary["contact_relationships_staged"] = len(self._rel_rows)

    async def _write_relationships(self) -> None:
        conn = self.conn
        await conn.executemany(
            """INSERT INTO md_contact_relationships
               (id, person_global_id, company_global_id, relationship_type,
                status, linking_basis, confidence, evidence, source_id, observed_at, created_at)
               VALUES ($1::uuid, $2::uuid, $3::uuid, $4, $5, $6, $7,
                       CAST($8 AS JSONB), $9, $10, now())
               ON CONFLICT (person_global_id, company_global_id, linking_basis) DO NOTHING""",
            [
                (str(uuid.uuid5(uuid.NAMESPACE_DNS,
                                f"rel:{rel['person_id']}:{rel['company_id']}:{rel['linking_basis']}")),
                 rel["person_id"], rel["company_id"], rel["relationship_type"],
                 rel["status"], rel["linking_basis"], rel["confidence"],
                 json.dumps(rel["evidence"], ensure_ascii=False, default=str),
                 rel["source_id"], rel["observed_at"])
                for rel in self._rel_rows
            ],
        )

    def _stage_relationship_changes(self) -> None:
        for rel in self._rel_rows:
            self._record(op="INSERT", entity_id=rel["person_id"],
                         table="md_contact_relationships",
                         payload={"company_id": rel["company_id"], "status": rel["status"],
                                  "basis": rel["linking_basis"], "confidence": rel["confidence"]})

    # ── deterministic keys (idempotency) ───────────────────────────────────

    def _real_company_id(self, ma_id: str | None) -> str | None:
        """Resolve a Master Account ID to the real md_global_companies.id.

        D2 fix: never generate a synthetic company UUID. Return the actual
        Global Company ID from the authoritative md_legacy_id_mappings.
        Returns None if the MA is not mapped; callers must fail closed.
        """
        if not ma_id:
            return None
        return self.ma_to_company.get(str(ma_id))

    def _to_uuid(self, key: str) -> str:
        """Validate and return the authoritative internal Global Company UUID."""
        try:
            return str(uuid.UUID(str(key)))
        except (ValueError, AttributeError) as exc:
            raise ValueError(
                f"Phase 6 requires an authoritative Global Company UUID, got {key!r}"
            ) from exc

    def _candidate_reason(self, res, _ex) -> str:
        if res.review_priority == "P0":
            return "CONFLICTING_CR"
        if res.review_priority == "P3":
            return "FUZZY_CANDIDATE_REVIEW"
        if res.identity_state == IdentityState.REVIEW_REQUIRED:
            return "FIELD_CONFLICT_REVIEW" if res.field_conflict else "WEAK_IDENTITY_REVIEW"
        if res.review_priority == "P1":
            return "SINGLE_SOURCE_STRONG_REVIEW" if res.identity_state == IdentityState.DETERMINISTIC_SINGLE_SOURCE else "CORROBORATION_REVIEW"
        return "PRIORITIZATION_P" + res.review_priority

    def _priority_score(self, res, ex) -> int:
        # Prioritization ONLY. Higher = higher review priority.
        base = {"P0": 100, "P1": 80, "P2": 60, "P3": 40}.get(res.review_priority, 0)
        icp_boost = 15 if ex["icp"] and "A -" in (ex["icp"] or "") else (8 if ex["icp"] and "B -" in (ex["icp"] or "") else 0)
        return base + icp_boost

    def _provenance_tiers(self, res) -> dict[str, str]:
        tiers = {}
        if res.has_cr:
            tiers["cr_number"] = "GOVERNMENT_ANCHOR"
        if res.has_vat:
            tiers["vat_number"] = "GOVERNMENT_ANCHOR"
        if res.has_unified:
            tiers["unified_national_number"] = "GOVERNMENT_ANCHOR"
        if res.has_real_domain:
            tiers["domain"] = "STRONG_DETERMINISTIC"
        if res.signals.get("contactability"):
            tiers["email"] = "WEAK_DETERMINISTIC"
            tiers["phone"] = "WEAK_DETERMINISTIC"
        tiers["city"] = "WEAK_DETERMINISTIC"
        tiers["industry"] = "NORMALIZED_EXACT"
        return tiers

    # ── writes (idempotent) ────────────────────────────────────────────────

    async def _write_all(self) -> None:
        conn = self.conn
        # md_identity_classifications
        await conn.executemany(
            """INSERT INTO md_identity_classifications
               (id, global_entity_id, classification_version, identity_state,
                sales_readiness, review_priority, cr_class, has_cr, has_vat,
                has_unified, has_real_domain, independent_source_count,
                source_count, conflicts, signals, source_ids, computed_at)
               VALUES ($1::uuid, $2::uuid, $3, $4, $5, $6, $7, $8, $9, $10,
                       $11, $12, $13, $14, CAST($15 AS JSONB), CAST($16 AS JSONB), now())
               ON CONFLICT (global_entity_id, classification_version) DO NOTHING""",
            [
                (str(uuid.uuid5(uuid.NAMESPACE_DNS, f"idc:{s[0]}:{self.version}")),
                 self._to_uuid(s[0]), self.version, s[1], s[2], s[3], s[4],
                 s[5], s[6], s[7], s[8], s[9], s[10], s[11], s[12], s[13])
                for s in self._identity_rows
            ],
        )

        # md_review_candidates
        await conn.executemany(
            """INSERT INTO md_review_candidates
               (id, global_entity_id, candidate_type, priority_score, reason,
                evidence, source_ids, status, created_at)
               VALUES ($1::uuid, $2::uuid, $3, $4, $5, CAST($6 AS JSONB),
                       CAST($7 AS JSONB), 'pending', now())
               ON CONFLICT (global_entity_id, candidate_type, reason) DO NOTHING""",
            [
                (str(uuid.uuid5(uuid.NAMESPACE_DNS, f"rc:{c['entity_key']}:{c['candidate_type']}:{c['reason']}")),
                 self._to_uuid(c["entity_key"]), c["candidate_type"],
                 c["priority_score"], c["reason"],
                 json.dumps(c["evidence"], ensure_ascii=False, default=str),
                 json.dumps(c["source_ids"], ensure_ascii=False))
                for c in self._candidate_rows
            ],
        )

        # md_industry_normalization
        await conn.executemany(
            """INSERT INTO md_industry_normalization
               (id, global_entity_id, raw_industry, normalized_industry,
                industry_code, normalization_method, source_row_id, is_current, created_at)
               VALUES ($1::uuid, $2::uuid, $3, $4, $5, $6, $7::uuid, $8, now())
               ON CONFLICT (global_entity_id, raw_industry, normalization_method) DO NOTHING""",
            [
                (str(uuid.uuid5(uuid.NAMESPACE_DNS, f"ind:{r[0]}:{r[1]}:{r[4]}")),
                 self._to_uuid(r[0]), r[1], r[2], r[3], r[4], r[5], r[6])
                for r in self._industry_rows
            ],
        )

        # md_quality_score_history (with previous_version, previous_overall for history)
        await conn.executemany(
            """INSERT INTO md_quality_score_history
               (id, global_entity_id, calc_version, completeness_score,
                accuracy_score, consistency_score, freshness_score,
                provenance_score, overall_score, evidence_basis,
                previous_version, previous_overall, computed_at)
               VALUES ($1::uuid, $2::uuid, $3, $4, $5, $6, $7, $8, $9,
                       CAST($10 AS JSONB), NULL, NULL, now())
               ON CONFLICT (global_entity_id, calc_version) DO NOTHING""",
            [
                (str(uuid.uuid5(uuid.NAMESPACE_DNS, f"q:{r[0]}:{self.version}")),
                 self._to_uuid(r[0]), self.version, r[1], r[2], r[3], r[4], r[5],
                 r[6], r[7])
                for r in self._quality_rows
            ],
        )

        # md_sales_readiness_history (with previous_version, previous_readiness)
        await conn.executemany(
            """INSERT INTO md_sales_readiness_history
               (id, global_entity_id, calc_version, sales_readiness,
                identity_state, basis, previous_version, previous_readiness, computed_at)
               VALUES ($1::uuid, $2::uuid, $3, $4, $5, CAST($6 AS JSONB), $7, $8, now())
               ON CONFLICT (global_entity_id, calc_version) DO NOTHING""",
            [
                (str(uuid.uuid5(uuid.NAMESPACE_DNS, f"sr:{r[0]}:{self.version}")),
                 self._to_uuid(r[0]), self.version, r[1], r[2], r[3], r[4], r[5])
                for r in self._readiness_rows
            ],
        )

    def _stage_as_changes(self) -> None:
        for s in self._identity_rows:
            self._record(op="INSERT", entity_id=self._to_uuid(s[0]),
                         table="md_identity_classifications",
                         payload={"identity_state": s[1], "sales_readiness": s[2],
                                  "review_priority": s[3], "cr_class": s[4]})
        for c in self._candidate_rows:
            self._record(op="INSERT", entity_id=self._to_uuid(c["entity_key"]),
                         table="md_review_candidates",
                         payload={"candidate_type": c["candidate_type"],
                                  "priority_score": c["priority_score"], "reason": c["reason"]})
        for r in self._industry_rows:
            self._record(op="INSERT", entity_id=self._to_uuid(r[0]),
                         table="md_industry_normalization",
                         payload={"raw": r[1], "normalized": r[2], "method": r[4]})
        for r in self._quality_rows:
            self._record(op="INSERT", entity_id=self._to_uuid(r[0]),
                         table="md_quality_score_history",
                         payload={"overall": r[6], "version": self.version})
        for r in self._readiness_rows:
            self._record(op="INSERT", entity_id=self._to_uuid(r[0]),
                         table="md_sales_readiness_history",
                         payload={"sales_readiness": r[1], "identity_state": r[2],
                                  "version": self.version})

    # ── results ────────────────────────────────────────────────────────────

    async def _load_contact_relationships(self) -> int:
        # Count existing person→company relationships (from md_global_people).
        return await self.conn.fetchval(
            "SELECT COUNT(*) FROM md_global_people WHERE company_global_id IS NOT NULL"
        )

    def _result(self) -> dict[str, Any]:
        return {
            "dry_run": self.dry_run,
            "version": self.version,
            "summary": dict(self.summary),
            "staged": dict(self._staged_counts),
            "safety": dict(sorted(self.safety.items())),
            "change_count": self.change_count,
        }
