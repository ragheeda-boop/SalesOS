"""Phase 6 — Corrected identity classification (Data Intelligence OPTION C).

Implements the authoritative corrected methodology from
`PHASE6_RECALCULATION_SPEC.md` and `PHASE6_METHODOLOGY_DECISION.md`:

  1. Email and phone are CONTACTABILITY_ONLY — never identity evidence.
  2. A generic/personal-email-pattern domain is NON_IDENTITY (excluded before
     counting domain as identity evidence).
  3. The no-identity-signal check runs BEFORE the confidence-tier checks
     (fixes the DI step-5-before-step-6 ordering defect).
  4. Multi-source corroboration requires FIELD-LEVEL AGREEMENT, not mere
     co-occurrence on Distinct_Source_System_Count (767+16 conflicting
     accounts route to review/conflict, not STRONG_MULTI_SOURCE).
  5. P1/P2 use the validated interim rules — NOT hard-coded to 23,306/37,719.

Pure, deterministic, no DB, no LLM, no network. Testable in isolation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.modules.entity_resolution.resolution_policy import (
    classify_cr,
    normalize_cr,
    normalize_unified_number,
    normalize_vat,
)

# ═══════════════════════════════════════════════════════════════════════════
# Corrected Domain Filter (RECALCULATION_SPEC §Corrected Domain Filter)
# ═══════════════════════════════════════════════════════════════════════════

# DI-derived generic/personal-email-pattern substrings (case-insensitive).
GENERIC_DOMAIN_SUBSTRINGS = (
    "gmai", "gmil", "hotmai", "hotmil", "yaho", "outlook", "windowslive",
    "live.com", "icloud", "msn.com", "yopmail", "mail.com", "me.com",
    "boxomail", "drmail",
)

# Full-match free-mail domains (superset used by Phase 5 strict classifier).
_FREE_MAIL_FULL = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "live.com",
    "icloud.com", "aol.com", "mail.com", "protonmail.com", "zoho.com",
    "yandex.com", "gmx.com", "tutamail.com", "msn.com", "me.com", "yopmail.com",
}


def is_generic_domain(domain: str | None) -> bool:
    """True if the domain is a generic/personal-email-pattern value (NON_IDENTITY).

    A generic domain must NEVER count as company identity evidence
    (RECALCULATION_SPEC §Corrected Domain Filter).
    """
    if not domain:
        return False
    d = domain.strip().lower().rstrip(".")
    if not d:
        return False
    if d in _FREE_MAIL_FULL:
        return True
    return any(sub in d for sub in GENERIC_DOMAIN_SUBSTRINGS)


def is_real_domain(domain: str | None) -> bool:
    """True iff a domain is present AND not a generic/personal-email pattern."""
    if not domain:
        return False
    d = domain.strip().lower()
    if not d or d in ("none", "nan", "null", "n/a"):
        return False
    if is_generic_domain(d):
        return False
    # A bare TLD or obviously not a domain is not real company identity.
    if "." not in d:
        return False
    return True


# ═══════════════════════════════════════════════════════════════════════════
# Identity states / readiness (mirrors Phase 5 enums, used unchanged).
# ═══════════════════════════════════════════════════════════════════════════

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
class IdentityResult:
    """Deterministic corrected classification for a single company record."""
    identity_state: IdentityState
    sales_readiness: SalesReadiness
    review_priority: str          # P0/P1/P2/P3/P4
    cr_class: str                 # SAFE / SUSPICIOUS_SHORT / SUSPICIOUS_MULTI / AMBIGUOUS
    has_cr: bool
    has_vat: bool
    has_unified: bool
    has_real_domain: bool
    has_contactability: bool      # email OR phone present (CONTACTABILITY_ONLY, not identity)
    independent_source_count: int
    source_count: int
    genuinely_corroborated: bool  # field-agreement across ≥2 independent systems
    field_conflict: bool          # a corroborating field CONFLICTS across systems
    conflict_fields: list[str] = field(default_factory=list)
    signals: dict[str, Any] = field(default_factory=dict)
    source_ids: list[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════
# Corrected source-independence (field-agreement) — RECALCULATION_SPEC §4
# ═══════════════════════════════════════════════════════════════════════════

FIELD_AGREEMENT_EPSILON = 0


def evaluate_source_field_agreement(
    *,
    cr_values_by_source: dict[str, list[str]] | None = None,
    domain_values_by_source: dict[str, list[str]] | None = None,
    phone_values_by_source: dict[str, list[str]] | None = None,
    name_values_by_source: dict[str, list[str]] | None = None,
) -> tuple[bool, bool, list[str]]:
    """Evaluate whether multi-source evidence is genuinely corroborated.

    Args:
        cr_values_by_source: {source_id: [normalized CR values]}.
        domain_values_by_source: {source_id: [normalized domain values]}.
        phone_values_by_source: {source_id: [normalized phone values]}.
        name_values_by_source: {source_id: [normalized canonical-name values]}.

    Returns:
        (genuinely_corroborated, field_conflict, conflict_fields)

    Rule (RECALCULATION_SPEC §4): genuinely corroborated when ≥2 independent
    source systems share an AGREEING value on CR, OR on domain, OR on
    (phone + name jointly). A field that appears in ≥2 systems but CONFLICTS
    is NOT corroboration and marks the account for review/conflict.
    """
    cr_values_by_source = cr_values_by_source or {}
    domain_values_by_source = domain_values_by_source or {}
    phone_values_by_source = phone_values_by_source or {}
    name_values_by_source = name_values_by_source or {}

    conflict_fields: list[str] = []

    def _agrees_or_conflicts(mapping: dict[str, list[str]]) -> tuple[bool, bool]:
        present = {src: {v for v in vals if v} for src, vals in mapping.items()}
        present = {src: vs for src, vs in present.items() if vs}
        if len(present) < 2:
            return False, False
        all_vals = set()
        for vs in present.values():
            all_vals |= vs
        # All contributing sources share at least one common value AND no
        # source carries a conflicting different value.
        common = set.intersection(*present.values()) if present else set()
        has_conflict = any(len(present[src] - common) > 0 for src in present)
        agreed = bool(common) and not has_conflict
        return agreed, (not agreed)  # if ≥2 sources present but no agreement → conflict
        return agreed, has_conflict

    cr_ok, cr_conflict = _agrees_or_conflicts(cr_values_by_source)
    if cr_conflict:
        conflict_fields.append("cr_number")

    domain_ok, domain_conflict = _agrees_or_conflicts(domain_values_by_source)
    if domain_conflict:
        conflict_fields.append("domain")

    # Phone + name jointly agree across ≥2 systems.
    phone_by_src = {s: set(v) for s, v in phone_values_by_source.items() if any(v)}
    name_by_src = {s: set(v) for s, v in name_values_by_source.items() if any(v)}
    joint_sources = set(phone_by_src) & set(name_by_src)
    joint_ok = False
    if len(joint_sources) >= 2:
        common_phone = set.intersection(*[phone_by_src[s] for s in joint_sources])
        common_name = set.intersection(*[name_by_src[s] for s in joint_sources])
        joint_ok = bool(common_phone) and bool(common_name)

    genuinely = cr_ok or domain_ok or joint_ok
    field_conflict = bool(conflict_fields) or (cr_conflict or domain_conflict)
    return genuinely, field_conflict, conflict_fields


# ═══════════════════════════════════════════════════════════════════════════
# Corrected bucket priority — RECALCULATION_SPEC §Corrected Bucket Priority
# ═══════════════════════════════════════════════════════════════════════════

def check_conflicting_cr(cr: str | None) -> tuple[bool, list[str]]:
    """Detect a CONFLICTING/ambiguous CR (multi-value or separator-listed).

    Returns (is_conflicting, raw_tokens). Per DI P0: an account whose CR field
    yields multiple distinct normalized anchors, or is shared with another
    account, is CONFLICTING_IDENTITY. Here we detect the multi-anchor form;
    cross-account sharing is detected at the pipeline level.
    """
    if not cr:
        return False, []
    s = str(cr).strip()
    tokens = [t for t in re.split(r"[;|,،؛/]+", s) if t.strip()]
    if len(tokens) > 1:
        valid = {n for t in tokens if (n := normalize_cr(t))}
        if len(valid) > 1:
            return True, sorted(valid)
    return False, []


def classify_corrected(
    *,
    cr_number: str | None = None,
    vat_number: str | None = None,
    unified_national_number: str | None = None,
    domain: str | None = None,
    apollo_account_id: str | None = None,
    confidence: str | None = None,
    source_count: int = 1,
    independent_source_count: int = 1,
    has_contactable_email: bool = False,
    has_phone: bool = False,
    fuzzy_candidate: bool = False,
    shared_cr_conflict: bool = False,
    cr_values_by_source: dict[str, list[str]] | None = None,
    domain_values_by_source: dict[str, list[str]] | None = None,
    phone_values_by_source: dict[str, list[str]] | None = None,
    name_values_by_source: dict[str, list[str]] | None = None,
    source_ids: list[str] | None = None,
) -> IdentityResult:
    """Classify a company record under the corrected (OPTION C) methodology.

    Priority order (corrected, RECALCULATION_SPEC §Corrected Bucket Priority,
    with OPTION-C domain filter + field-agreement source independence):
      1. conflicting CR            → CONFLICTING_IDENTITY / P0
      2. NOT identity_signal_present ... → NO_VERIFIABLE_IDENTITY  [MOVED UP]
      3. valid CR AND conf==MATCHED → GOVERNMENT_ANCHORED
      4. genuinely multi-source     → STRONG_MULTI_SOURCE  (field-agreement)
      5. single-source strong       → DETERMINISTIC_SINGLE_SOURCE
      6. confidence REVIEW          → REVIEW_REQUIRED
      7. else                       → WEAK_IDENTITY

    `confidence` is the DI `Best_Match_Confidence` (MATCHED / LIKELY MATCH /
    REVIEW REQUIRED / UNMATCHED / etc.). It gates the deterministic tiers per the
    spec, but a valid CR is always the strongest anchor regardless of a single
    field's confidence label.
    """
    cr_class = classify_cr(cr_number)
    cr_norm = normalize_cr(cr_number)
    has_cr = cr_norm is not None and cr_class == "SAFE"
    has_vat = normalize_vat(vat_number) is not None
    has_unified = normalize_unified_number(unified_national_number) is not None
    has_real_domain = is_real_domain(domain)
    has_contactability = bool(has_contactable_email or has_phone)

    source_ids = source_ids or []
    conf_norm = (confidence or "").strip().lower()
    conf_matched = conf_norm == "matched"
    conf_strong = conf_norm in ("matched", "likely match")
    conf_review = "review" in conf_norm or "fuzzy" in conf_norm

    # Signal-agreement evaluation for multi-source accounts.
    genuinely, field_conflict, conflict_fields = evaluate_source_field_agreement(
        cr_values_by_source=cr_values_by_source,
        domain_values_by_source=domain_values_by_source,
        phone_values_by_source=phone_values_by_source,
        name_values_by_source=name_values_by_source,
    )

    # Corrected identity-signal set: CR OR apollo OR real-domain.
    identity_present = has_cr or bool(apollo_account_id) or has_real_domain

    # Signals for provenance.
    signals = {
        "cr_present": has_cr,
        "cr_class": cr_class,
        "vat_present": has_vat,
        "unified_present": has_unified,
        "apollo_account_present": bool(apollo_account_id),
        "real_domain_present": has_real_domain,
        "raw_domain_present": bool(domain and str(domain).strip()),
        "contactability": has_contactability,
        "email_contactability_only": bool(has_contactable_email),
        "phone_contactability_only": bool(has_phone),
        "best_match_confidence": confidence,
        "field_conflict": field_conflict,
        "conflict_fields": conflict_fields,
    }

    # 1. Conflicting CR → P0. Cross-account CR sharing is a P0 conflict too.
    multi_cr, multi_cr_tokens = check_conflicting_cr(cr_number)
    if multi_cr or shared_cr_conflict:
        return IdentityResult(
            IdentityState.CONFLICTING_IDENTITY, SalesReadiness.IDENTITY_REVIEW_REQUIRED,
            "P0", cr_class, has_cr, has_vat, has_unified, has_real_domain,
            has_contactability, independent_source_count, source_count,
            genuinely, field_conflict, conflict_fields, signals, source_ids,
        )

    # 2. [MOVED UP] No identity signal at all → NO_VERIFIABLE_IDENTITY.
    if not identity_present:
        return IdentityResult(
            IdentityState.NO_VERIFIABLE_IDENTITY, SalesReadiness.INSUFFICIENT_DATA,
            "P4", cr_class, has_cr, has_vat, has_unified, has_real_domain,
            has_contactability, independent_source_count, source_count,
            genuinely, field_conflict, conflict_fields, signals, source_ids,
        )

    # Multi-source with field conflict → not corroborated; route to review/conflict.
    if field_conflict:
        # A genuine field conflict inside "multi-source" is routed to review,
        # never STRONG_MULTI_SOURCE (783-account defect). Not a government P0
        # unless CR itself conflicts (handled above); otherwise review/P1.
        return IdentityResult(
            IdentityState.REVIEW_REQUIRED, SalesReadiness.IDENTITY_REVIEW_REQUIRED,
            "P1", cr_class, has_cr, has_vat, has_unified, has_real_domain,
            has_contactability, independent_source_count, source_count,
            genuinely, field_conflict, conflict_fields, signals, source_ids,
        )

    # 3. Government anchor (valid CR) → GOVERNMENT_ANCHORED (step 3 of spec;
    #    a valid CR is the strongest anchor, gated to MATCHED for the tier).
    if has_cr:
        if conf_matched:
            state, readiness, prio = (
                IdentityState.GOVERNMENT_ANCHORED, SalesReadiness.SALES_READY, "P1"
            )
        else:
            # Valid CR but confidence not MATCHED → still deterministic single.
            state, readiness, prio = (
                IdentityState.DETERMINISTIC_SINGLE_SOURCE, SalesReadiness.ENRICHMENT_REQUIRED, "P2"
            )
        return IdentityResult(
            state, readiness, prio, cr_class, has_cr, has_vat, has_unified,
            has_real_domain, has_contactability, independent_source_count,
            source_count, genuinely, field_conflict, conflict_fields, signals, source_ids,
        )

    # 4. Genuinely corroborated multi-source + strong confidence → STRONG_MULTI_SOURCE.
    #    DI corrected rule: distinct_sources >= 2 AND confidence in (MATCHED,
    #    LIKELY MATCH) AND the field-agreement check passes (no conflicts).
    if genuinely and independent_source_count >= 2 and conf_strong:
        return IdentityResult(
            IdentityState.STRONG_MULTI_SOURCE, SalesReadiness.SALES_READY,
            "P1", cr_class, has_cr, has_vat, has_unified, has_real_domain,
            has_contactability, independent_source_count, source_count,
            genuinely, field_conflict, conflict_fields, signals, source_ids,
        )

    # 5. Single-source / deterministic (real domain or Apollo account).
    if has_real_domain or bool(apollo_account_id):
        if independent_source_count <= 1:
            if conf_review and fuzzy_candidate:
                return IdentityResult(
                    IdentityState.REVIEW_REQUIRED, SalesReadiness.ENRICHMENT_REQUIRED,
                    "P3", cr_class, has_cr, has_vat, has_unified, has_real_domain,
                    has_contactability, independent_source_count, source_count,
                    genuinely, field_conflict, conflict_fields, signals, source_ids,
                )
            return IdentityResult(
                IdentityState.DETERMINISTIC_SINGLE_SOURCE, SalesReadiness.ENRICHMENT_REQUIRED,
                "P2", cr_class, has_cr, has_vat, has_unified, has_real_domain,
                has_contactability, independent_source_count, source_count,
                genuinely, field_conflict, conflict_fields, signals, source_ids,
            )

    # 6. Review-required confidence (broad P1 interim rule: single-source weak/
    #    strong evidence + REVIEW REQUIRED) / fuzzy candidate (P3).
    if conf_review or fuzzy_candidate:
        if fuzzy_candidate:
            return IdentityResult(
                IdentityState.REVIEW_REQUIRED, SalesReadiness.ENRICHMENT_REQUIRED,
                "P3", cr_class, has_cr, has_vat, has_unified, has_real_domain,
                has_contactability, independent_source_count, source_count,
                genuinely, field_conflict, conflict_fields, signals, source_ids,
            )
        return IdentityResult(
            IdentityState.REVIEW_REQUIRED, SalesReadiness.ENRICHMENT_REQUIRED,
            "P1", cr_class, has_cr, has_vat, has_unified, has_real_domain,
            has_contactability, independent_source_count, source_count,
            genuinely, field_conflict, conflict_fields, signals, source_ids,
        )

    # 7. Weak identity (some contactability but no determinism).
    return IdentityResult(
        IdentityState.WEAK_IDENTITY, SalesReadiness.ENRICHMENT_REQUIRED,
        "P2", cr_class, has_cr, has_vat, has_unified, has_real_domain,
        has_contactability, independent_source_count, source_count,
        genuinely, field_conflict, conflict_fields, signals, source_ids,
    )
