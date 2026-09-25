"""Entity Resolution Policy — Evidence-First Decision Engine.

Implements the approved architecture from Doc 05 (Entity Resolution).
This is the minimum policy component required for the Design Gate.
It does NOT depend on database, ORM, or external services.

Decision hierarchy (in strict order):
1. Government-ID VETO (CR/VAT/Unified conflict → FORBIDS merge)
2. Signal Independence (≥2 independent strong sources OR 1 government anchor)
3. Confidence Classification (HIGH/MEDIUM/LOW/VETOED)
4. Composite Score (supporting information ONLY)
5. Final Decision (AUTO_MERGE / REVIEW / SEPARATE)

Numeric score NEVER overrides: Government-ID veto, evidence class, signal independence, fuzzy-only prohibition.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ── Government-ID Normalization ──────────────────────────────────────────────

# List separators that indicate a multi-value CR field (NOT intra-number formatting).
# A single CR field that yields multiple distinct tokens is ambiguous and must never
# be concatenated into a plausible-looking anchor (Doc 05 §8.1, Data-Intelligence CR defect).
CR_VALUE_SEPARATORS = ";|,؛،/"

# RTL / Unicode format control characters that crop up in imported Saudi data and
# must be stripped before digit validation (e.g. "\u202d7054210393\u202c").
_CR_CONTROL_CHARS = re.compile(r"[\u200e\u200f\u202a-\u202e\u2066-\u2069\ufeff]")


def _normalize_cr_token(token: str) -> str | None:
    """Normalize a single CR token (whitespace/dash/dot-stripped) → 5-10 digits or None.

    Returns None if the token is not a plausible CR after leading-zero stripping.
    """
    s = _CR_CONTROL_CHARS.sub("", token)
    s = re.sub(r"[\s\-\.]+", "", s)
    s = s.lstrip("0")
    if not s.isdigit() or len(s) < 5 or len(s) > 10:
        return None
    return s


def normalize_cr(raw: str | None) -> str | None:
    """Normalize a Saudi CR number.

    Security rule (Data-Intelligence CR normalization defect):
      A CR field may carry multiple values separated by ``; | , / ؛ ،`` (e.g.
      "1005; 7066" or "2286; 1200727500").  Such multi-value fields MUST NOT be
      concatenated into a single plausible-looking CR — that fabricates a
      government anchor.  We normalize each separator-delimited token independently:
        - 0 distinct valid tokens  → None (invalid)
        - exactly 1 distinct valid token → that token (single unambiguous anchor)
        - 2+ distinct valid tokens → None (ambiguous; preserved, not promoted)

    Returns None for invalid/ambiguous/short input.
    """
    if not raw:
        return None
    s = _CR_CONTROL_CHARS.sub("", str(raw).strip())
    if not s:
        return None

    tokens = [t for t in re.split(r"[;|,؛،/]+", s) if t.strip()]
    if not tokens:
        return None
    # A separator-delimited field (multiple values) is NEVER a single trusted anchor,
    # regardless of whether one token happens to look valid.
    if len(tokens) > 1:
        return None

    norm = _normalize_cr_token(tokens[0])
    return norm


def classify_cr(raw: str | None) -> str:
    """Classify a raw CR value's anchor-trustworthiness.

    Data-Intelligence CR defect rule: a suspicious/short/multi-value CR must NEVER be
    treated as a verified government anchor.  Returns one of:

    - ``SAFE``            : a single unambiguous normalized CR (5-10 digits) → anchor OK
    - ``SUSPICIOUS_SHORT``: value is too short / zero-padded-suspect → NOT an anchor
    - ``SUSPICIOUS_MULTI``: multiple distinct plausible CRs (e.g. "1005; 7066") → NOT an anchor
    - ``AMBIGUOUS``       : malformed, non-digit, or unparseable → NOT an anchor
    """
    if not raw:
        return "AMBIGUOUS"
    s = _CR_CONTROL_CHARS.sub("", str(raw).strip())
    if not s:
        return "AMBIGUOUS"

    tokens = [t for t in re.split(r"[;|,؛،/]+", s) if t.strip()]
    if len(tokens) > 1:
        # Multiple separator-delimited values.
        valid = {n for t in tokens if (n := _normalize_cr_token(t))}
        if len(valid) == 1:
            # One real value among noise (e.g. "2286; 1200727500") BUT presence of a
            # short/ambiguous sibling makes the FIELD itself suspicious → not anchor.
            return "SUSPICIOUS_MULTI"
        return "SUSPICIOUS_MULTI"

    token = tokens[0] if tokens else s
    norm = _normalize_cr_token(token)
    if norm:
        return "SAFE"
    # Could not normalize: too short (<5) after zero-strip, or malformed.
    digits = re.sub(r"[^0-9]", "", token).lstrip("0")
    if digits and len(digits) < 5:
        return "SUSPICIOUS_SHORT"
    return "AMBIGUOUS"


def normalize_vat(raw: str | None) -> str | None:
    """Normalize Saudi VAT number.

    Canonical representation:
    1. Strip all whitespace (spaces, tabs, newlines)
    2. Strip hyphens, dots, slashes, backslashes
    3. Uppercase
    4. Allowed characters: digits + uppercase letters
    5. Validate: must be non-empty after normalization
    6. Structural validation: must be 15 digits (Saudi VAT = 3-digit prefix "3" + 9 digits + 3-digit suffix)
       OR 15 characters (12-digit TIN + 3-digit branch) — allows both formats

    Checksum: NOT USED — no authoritative checksum rule established for Saudi VAT.

    Matching: exact canonical match → Government-ID signal; conflict = HARD VETO.
    """
    if not raw:
        return None
    s = str(raw).strip()
    s = re.sub(r'[\s\-\.\/\\]+', '', s)
    s = s.upper()
    if not s:
        return None
    if not re.match(r'^[0-9A-Z]{15}$', s):
        return None
    return s


def normalize_unified_number(raw: str | None) -> str | None:
    """Normalize Saudi Unified National Number (الرقم الموحد).

    Canonical representation:
    1. Strip all whitespace
    2. Strip hyphens, dots, slashes, backslashes
    3. Uppercase
    4. Allowed characters: digits + uppercase letters
    5. Validate: must be non-empty after normalization
    6. Structural validation: must be exactly 10 digits (Saudi Unified National Number = 10 digits)

    Checksum: NOT USED — no authoritative checksum rule established.

    Matching: exact canonical match → Government-ID signal; conflict = HARD VETO.
    """
    if not raw:
        return None
    s = str(raw).strip()
    s = re.sub(r'[\s\-\.\/\\]+', '', s)
    s = s.upper()
    if not s:
        return None
    if not re.match(r'^[0-9]{10}$', s):
        return None
    return s


# ── Enums ────────────────────────────────────────────────────────────────────


class ConfidenceClass(Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    VETOED = "VETOED"


class Decision(Enum):
    AUTO_MERGE = "AUTO_MERGE"
    REVIEW = "REVIEW"
    SEPARATE = "SEPARATE"
    VETOED = "VETOED"


class EvidenceTier(Enum):
    GOVERNMENT_ANCHOR = "GOVERNMENT_ANCHOR"
    STRONG_DETERMINISTIC = "STRONG_DETERMINISTIC"
    WEAK_DETERMINISTIC = "WEAK_DETERMINISTIC"
    NORMALIZED_EXACT = "NORMALIZED_EXACT"
    FUZZY = "FUZZY"


# ── Signal Weights ───────────────────────────────────────────────────────────

SIGNAL_WEIGHTS: dict[str, tuple[int, EvidenceTier]] = {
    "cr_match": (100, EvidenceTier.GOVERNMENT_ANCHOR),
    "vat_match": (100, EvidenceTier.GOVERNMENT_ANCHOR),
    "unified_match": (100, EvidenceTier.GOVERNMENT_ANCHOR),
    "license_match": (95, EvidenceTier.STRONG_DETERMINISTIC),
    "membership_match": (90, EvidenceTier.STRONG_DETERMINISTIC),
    "domain_match": (85, EvidenceTier.STRONG_DETERMINISTIC),
    "website_match": (80, EvidenceTier.WEAK_DETERMINISTIC),
    "phone_match": (70, EvidenceTier.WEAK_DETERMINISTIC),
    "email_match": (70, EvidenceTier.WEAK_DETERMINISTIC),
    "canonical_name_exact": (65, EvidenceTier.NORMALIZED_EXACT),
    "canonical_name_fuzzy": (55, EvidenceTier.FUZZY),
    "canonical_name_contains": (55, EvidenceTier.FUZZY),
    "city": (20, EvidenceTier.WEAK_DETERMINISTIC),
    "region": (10, EvidenceTier.WEAK_DETERMINISTIC),
}

STRONG_DETERMINISTIC_SIGNALS = {
    name for name, (_, tier) in SIGNAL_WEIGHTS.items()
    if tier in (EvidenceTier.GOVERNMENT_ANCHOR, EvidenceTier.STRONG_DETERMINISTIC)
}

GOVERNMENT_ID_FIELDS = {"cr_number", "vat_number", "unified_national_number"}


# ── Domain Blacklist ─────────────────────────────────────────────────────────

DOMAIN_BLACKLIST = {
    'google.com', 'gmail.com', 'instagram.com', 'facebook.com',
    'twitter.com', 'linkedin.com', 'youtube.com', 'example.com',
    't.me', 'wa.me', 'apple.com', 'microsoft.com', 'amazon.com',
    'saudi.net', 'hotmail.com', 'yahoo.com', 'outlook.com'
}


# ── Data Classes ─────────────────────────────────────────────────────────────


@dataclass
class SourceRecord:
    """Minimal record for policy testing."""
    source_id: str
    cr_number: str | None = None
    vat_number: str | None = None
    unified_national_number: str | None = None
    canonical_name: str | None = None
    domain: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    license_number: str | None = None
    membership_number: str | None = None
    city: str | None = None
    region: str | None = None


@dataclass
class Signal:
    name: str
    matched: bool
    source_id: str
    weight: int = 0
    tier: EvidenceTier = EvidenceTier.FUZZY


@dataclass
class VetoDecision:
    vetoed: bool
    reason: str = ""
    field_name: str = ""
    value_a: str = ""
    value_b: str = ""


@dataclass
class IndependenceResult:
    independent: bool
    independent_sources: int = 0
    source_groups: dict = field(default_factory=dict)


@dataclass
class ResolutionResult:
    confidence: ConfidenceClass
    decision: Decision
    score: float
    veto: VetoDecision | None = None
    independence: IndependenceResult | None = None
    signals: list[Signal] = field(default_factory=list)
    has_fuzzy_only: bool = False
    has_government_anchor: bool = False
    has_strong_deterministic: bool = False


# ── Role Email Detection ─────────────────────────────────────────────────────

ROLE_EMAIL_PREFIXES = {
    'info', 'admin', 'sales', 'support', 'contact',
    'hr', 'accounting', 'office', 'general', 'help',
    'billing', 'legal', 'marketing', 'press', 'media',
    'team', 'hello', 'enquiries', 'customerservice',
}


def is_role_email(email: str | None) -> bool:
    """Check if email is role-based/shared."""
    if not email:
        return False
    local_part = email.split('@')[0].lower().strip()
    return any(local_part.startswith(p) for p in ROLE_EMAIL_PREFIXES)


# ── Government-ID Veto ───────────────────────────────────────────────────────


def check_government_veto(record_a: SourceRecord, record_b: SourceRecord) -> VetoDecision:
    """Check if government identifiers conflict between two records.

    If ANY government ID is present in both records and differs after normalization:
    → VETO the merge entirely.
    No score can override this.
    """
    checks = [
        ("cr_number", normalize_cr),
        ("vat_number", normalize_vat),
        ("unified_national_number", normalize_unified_number),
    ]
    for field_name, normalizer in checks:
        val_a = getattr(record_a, field_name, None)
        val_b = getattr(record_b, field_name, None)
        norm_a = normalizer(val_a)
        norm_b = normalizer(val_b)
        if norm_a and norm_b and norm_a != norm_b:
            return VetoDecision(
                vetoed=True,
                reason=f"Government ID conflict on {field_name}",
                field_name=field_name,
                value_a=norm_a,
                value_b=norm_b,
            )
    return VetoDecision(vetoed=False)


# ── Signal Independence ──────────────────────────────────────────────────────


def group_signals_by_source(signals: list[Signal]) -> dict[str, list[Signal]]:
    """Group matching signals by their source_id."""
    groups: dict[str, list[Signal]] = {}
    for sig in signals:
        if sig.matched:
            groups.setdefault(sig.source_id, []).append(sig)
    return groups


def check_signal_independence(source_groups: dict[str, list[Signal]]) -> IndependenceResult:
    """Require ≥2 independent source groups with strong signals for HIGH confidence."""
    strong_groups = 0
    for source_id, sigs in source_groups.items():
        if any(s.tier in (EvidenceTier.GOVERNMENT_ANCHOR, EvidenceTier.STRONG_DETERMINISTIC) for s in sigs):
            strong_groups += 1
    return IndependenceResult(
        independent=strong_groups >= 2,
        independent_sources=strong_groups,
        source_groups={k: [s.name for s in v] for k, v in source_groups.items()},
    )


# ── Confidence Classification ────────────────────────────────────────────────


def classify_confidence(
    veto: VetoDecision,
    has_government_anchor: bool,
    independence: IndependenceResult,
    has_strong_deterministic: bool,
    has_fuzzy_only: bool,
) -> ConfidenceClass:
    """Classify confidence based on evidence, not score.

    Decision hierarchy:
    1. Veto → VETOED
    2. Government anchor → HIGH
    3. Independence (≥2 strong groups) → HIGH
    4. Single strong → MEDIUM
    5. Fuzzy-only → LOW (NEVER auto-merge)
    """
    if veto.vetoed:
        return ConfidenceClass.VETOED
    if has_government_anchor:
        return ConfidenceClass.HIGH
    if independence.independent:
        return ConfidenceClass.HIGH
    if has_strong_deterministic:
        return ConfidenceClass.MEDIUM
    if has_fuzzy_only:
        return ConfidenceClass.LOW
    return ConfidenceClass.LOW


# ── Composite Score ──────────────────────────────────────────────────────────


def compute_composite_score(signals: dict[str, int], available: list[str]) -> float:
    """Compute composite score as SUPPORTING INFORMATION ONLY.

    Score NEVER overrides the confidence class.
    """
    matched_weight = sum(signals.get(s, 0) for s in available)
    max_possible = sum(SIGNAL_WEIGHTS[s][0] for s in available if s in SIGNAL_WEIGHTS)
    if max_possible == 0:
        return 0.0
    return (matched_weight / max_possible) * 100


# ── Final Decision ───────────────────────────────────────────────────────────


def make_decision(confidence: ConfidenceClass, score: float) -> Decision:
    """Make final decision based on confidence class and score.

    Decision rules:
    - VETOED → VETOED
    - HIGH + score ≥ 95 → AUTO_MERGE
    - HIGH + score < 95 → REVIEW (borderline)
    - MEDIUM → REVIEW
    - LOW → SEPARATE
    """
    if confidence == ConfidenceClass.VETOED:
        return Decision.VETOED
    if confidence == ConfidenceClass.HIGH and score >= 95:
        return Decision.AUTO_MERGE
    if confidence == ConfidenceClass.HIGH:
        return Decision.REVIEW
    if confidence == ConfidenceClass.MEDIUM:
        return Decision.REVIEW
    return Decision.SEPARATE


# ── Full Pipeline ────────────────────────────────────────────────────────────


def evaluate_pair(
    record_a: SourceRecord,
    record_b: SourceRecord,
    matched_signals: list[Signal],
    score: float,
) -> ResolutionResult:
    """Full evidence-first evaluation of a candidate pair.

    Implements the pipeline from Doc 05 §2 (Steps 3-8).
    """
    # Step 3: Evidence evaluation
    has_government_anchor = any(
        s.tier == EvidenceTier.GOVERNMENT_ANCHOR and s.matched for s in matched_signals
    )
    has_strong_deterministic = any(
        s.tier == EvidenceTier.STRONG_DETERMINISTIC and s.matched for s in matched_signals
    )
    fuzzy_only = any(s.tier == EvidenceTier.FUZZY and s.matched for s in matched_signals)
    non_fuzzy_matched = [s for s in matched_signals if s.matched and s.tier != EvidenceTier.FUZZY]
    has_fuzzy_only = fuzzy_only and not non_fuzzy_matched

    # Step 4: Government-ID veto
    veto = check_government_veto(record_a, record_b)

    # Step 5: Signal independence
    source_groups = group_signals_by_source(matched_signals)
    independence = check_signal_independence(source_groups)

    # Step 6: Confidence classification
    confidence = classify_confidence(
        veto, has_government_anchor, independence, has_strong_deterministic, has_fuzzy_only
    )

    # Step 7: Score is recorded but NEVER overrides confidence class

    # Step 8: Decision
    decision = make_decision(confidence, score)

    return ResolutionResult(
        confidence=confidence,
        decision=decision,
        score=score,
        veto=veto,
        independence=independence,
        signals=matched_signals,
        has_fuzzy_only=has_fuzzy_only,
        has_government_anchor=has_government_anchor,
        has_strong_deterministic=has_strong_deterministic,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# IDENTITY & SALES-READINESS CLASSIFICATION  (Data-Intelligence Phase 5 rules)
#
# Deterministic, evidence-first classification of a company record's identity
# strength and sales readiness.  NO LLM.  NO source mutation.  NO fabrication.
#
# Identity-state hierarchy (strict evidence definition — the handoff notes two
# historical "missing identity" definitions; we use the STRICT SalesOS blueprint
# definition: advisory fields like email/phone are contactability signals and do
# NOT count as government/strong identity evidence).
# ═══════════════════════════════════════════════════════════════════════════════


class IdentityState(str, Enum):
    NO_VERIFIABLE_IDENTITY = "NO_VERIFIABLE_IDENTITY"
    WEAK_IDENTITY = "WEAK_IDENTITY"
    DETERMINISTIC_SINGLE_SOURCE = "DETERMINISTIC_SINGLE_SOURCE"
    STRONG_MULTI_SOURCE = "STRONG_MULTI_SOURCE"
    GOVERNMENT_ANCHORED = "GOVERNMENT_ANCHORED"
    CONFLICTING_IDENTITY = "CONFLICTING_IDENTITY"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class SalesReadiness(str, Enum):
    SALES_READY = "SALES_READY"
    SALES_READY_WITH_REVIEW = "SALES_READY_WITH_REVIEW"
    ENRICHMENT_REQUIRED = "ENRICHMENT_REQUIRED"
    IDENTITY_REVIEW_REQUIRED = "IDENTITY_REVIEW_REQUIRED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


@dataclass
class IdentityAssessment:
    """Deterministic identity + sales assessment for a single company record."""
    identity_state: IdentityState
    sales_readiness: SalesReadiness
    cr_class: str  # SAFE / SUSPICIOUS_SHORT / SUSPICIOUS_MULTI / AMBIGUOUS
    has_cr: bool
    has_vat: bool
    has_unified: bool
    has_strong_domain: bool
    independent_source_count: int
    source_count: int
    review_priority: str  # P0 / P1 / P2 / P3 / P4
    conflicts: bool = False


def assess_identity(
    *,
    cr_number: str | None = None,
    vat_number: str | None = None,
    unified_national_number: str | None = None,
    domain: str | None = None,
    source_count: int = 1,
    independent_source_count: int = 1,
    conflicting_identity: bool = False,
    has_contactable_email: bool = False,
    has_phone: bool = False,
    has_size_data: bool = False,
    fuzzy_candidate: bool = False,
) -> IdentityAssessment:
    """Classify a company's identity strength and sales readiness.

    Priority order (strict, matches Data-Intelligence identity buckets):
      1. conflicting government IDs          → CONFLICTING_IDENTITY / P0
      2. SAFE government anchor              → GOVERNMENT_ANCHORED / P1-eligible
      3. ≥2 independent strong sources       → STRONG_MULTI_SOURCE / P1
      4. single strong deterministic source  → DETERMINISTIC_SINGLE_SOURCE
      5. fuzzy-only candidate                → REVIEW_REQUIRED / P3 (never auto-merge)
      6. weak advisory-only evidence         → WEAK_IDENTITY
      7. nothing verifiable                  → NO_VERIFIABLE_IDENTITY
    """
    cr_class = classify_cr(cr_number)
    cr_norm = normalize_cr(cr_number)
    has_cr = cr_norm is not None and cr_class == "SAFE"
    has_vat = normalize_vat(vat_number) is not None
    has_unified = normalize_unified_number(unified_national_number) is not None
    has_strong_domain = _is_strong_domain(domain)

    # P0: government-identity conflict → hard veto / review
    if conflicting_identity:
        return IdentityAssessment(
            IdentityState.CONFLICTING_IDENTITY, SalesReadiness.IDENTITY_REVIEW_REQUIRED,
            cr_class, has_cr, has_vat, has_unified, has_strong_domain,
            independent_source_count, source_count, "P0", conflicts=True,
        )

    # Government anchor present and SAFE
    if has_cr or has_vat or has_unified:
        if cr_class != "SAFE" and (has_cr is False):
            # suspicious CR present but no safe anchor → review, not anchor
            pass
        else:
            state = IdentityState.GOVERNMENT_ANCHORED
            readiness = (
                SalesReadiness.SALES_READY_WITH_REVIEW
                if source_count > 1 and independent_source_count > 1
                else SalesReadiness.SALES_READY
            )
            return IdentityAssessment(
                state, readiness, cr_class, has_cr, has_vat, has_unified,
                has_strong_domain, independent_source_count, source_count,
                "P1" if has_cr else "P1",
            )

    # Suspicious/short CR present but no safe anchor → do NOT trust as anchor
    if cr_class in ("SUSPICIOUS_SHORT", "SUSPICIOUS_MULTI", "AMBIGUOUS") and (
        cr_number is not None and str(cr_number).strip() not in ("", "None")
    ):
        # A malformed/suspicious CR exists → identity review required, NOT a trusted anchor.
        if fuzzy_candidate:
            return IdentityAssessment(
                IdentityState.REVIEW_REQUIRED, SalesReadiness.IDENTITY_REVIEW_REQUIRED,
                cr_class, False, has_vat, has_unified, has_strong_domain,
                independent_source_count, source_count, "P3",
            )
        return IdentityAssessment(
            IdentityState.REVIEW_REQUIRED, SalesReadiness.IDENTITY_REVIEW_REQUIRED,
            cr_class, False, has_vat, has_unified, has_strong_domain,
            independent_source_count, source_count, "P1",
        )

    # ≥2 independent strong sources
    if independent_source_count >= 2 and (has_strong_domain):
        return IdentityAssessment(
            IdentityState.STRONG_MULTI_SOURCE, SalesReadiness.SALES_READY_WITH_REVIEW,
            cr_class, False, has_vat, has_unified, has_strong_domain,
            independent_source_count, source_count, "P1",
        )

    # single strong deterministic source (corporate/strong domain is deterministic identity;
    # email-forwarded contactability alone is NOT deterministic identity evidence)
    if has_strong_domain:
        return IdentityAssessment(
            IdentityState.DETERMINISTIC_SINGLE_SOURCE, SalesReadiness.ENRICHMENT_REQUIRED,
            cr_class, False, has_vat, has_unified, has_strong_domain,
            independent_source_count, source_count, "P2",
        )

    # fuzzy-only → never auto-merge
    if fuzzy_candidate:
        return IdentityAssessment(
            IdentityState.REVIEW_REQUIRED, SalesReadiness.ENRICHMENT_REQUIRED,
            cr_class, False, has_vat, has_unified, has_strong_domain,
            independent_source_count, source_count, "P3",
        )

    # weak advisory-only (email/phone present but NO strong identity evidence)
    if has_contactable_email or has_phone:
        return IdentityAssessment(
            IdentityState.WEAK_IDENTITY, SalesReadiness.ENRICHMENT_REQUIRED,
            cr_class, False, has_vat, has_unified, has_strong_domain,
            independent_source_count, source_count, "P2",
        )

    # nothing verifiable → low-information account
    return IdentityAssessment(
        IdentityState.NO_VERIFIABLE_IDENTITY, SalesReadiness.INSUFFICIENT_DATA,
        cr_class, False, has_vat, has_unified, has_strong_domain,
        independent_source_count, source_count, "P4",
    )


def _is_strong_domain(domain: str | None) -> bool:
    """A strong-domain signal exists when the domain is normalized, non-blacklisted,
    and not a free-mail/consumer domain (advisory-only, not government identity)."""
    if not domain:
        return False
    d = domain.strip().lower()
    if not d or d in DOMAIN_BLACKLIST:
        return False
    # Free/consumer mail domains are contactability only, not strong identity.
    return d not in _FREE_MAIL_DOMAINS


_FREE_MAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
    "live.com", "icloud.com", "aol.com", "mail.com", "protonmail.com",
    "zoho.com", "yandex.com", "gmx.com", "tutamail.com",
}
