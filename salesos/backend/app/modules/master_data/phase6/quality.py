"""Phase 6 — Quality score recalculation.

Deterministic, versioned. Preserves previous scores in history (the pipeline
writes to md_quality_score_history; it never silently overwrites an earlier
assessment — it inserts a NEW versioned row each run).

Dimensions (0..100):
  completeness — how many core fields are populated (weighted).
  accuracy     — agreement of corroborating sources on identity fields.
  consistency  — internal consistency (e.g. domain vs website, no field conflict).
  freshness    — data age vs a reference (observed_at recency).
  provenance   — evidence-tier strength of sourced fields.
  overall      — weighted composite.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Core fields that contribute to completeness (each wanders 0..1 weight).
CORE_FIELDS = {
    "cr_number": 3,
    "vat_number": 2,
    "unified_national_number": 2,
    "canonical_name": 2,
    "domain": 2,
    "phone": 1,
    "email": 1,
    "city": 1,
    "industry": 1,
}

PROVENANCE_TIER_RANK = {
    "GOVERNMENT_ANCHOR": 1.0,
    "STRONG_DETERMINISTIC": 0.85,
    "WEAK_DETERMINISTIC": 0.6,
    "NORMALIZED_EXACT": 0.5,
    "FUZZY": 0.3,
}


@dataclass
class QualityResult:
    completeness_score: float
    accuracy_score: float
    consistency_score: float
    freshness_score: float
    provenance_score: float
    overall_score: float
    evidence_basis: dict = field(default_factory=dict)


def _weighted_avg(values: list[tuple[float, float]]) -> float:
    """Weighted average; fall back to 0 if no weighted weight."""
    num = sum(v * w for v, w in values)
    den = sum(w for _, w in values)
    return round(num / den, 2) if den else 0.0


def score_quality(
    *,
    fields: dict[str, bool | None],
    provenance_tiers: dict[str, str] | None = None,
    field_conflict: bool = False,
    conflict_fields: list[str] | None = None,
    independent_source_count: int = 1,
    source_count: int = 1,
    observed_recency_days: float | None = None,
    freshness_window_days: float = 365.0,
) -> QualityResult:
    """Compute a versioned quality score for one entity.

    Args:
        fields: {field_name: truthy/populated}.
        provenance_tiers: {field_name: evidence-tier label}; used for provenance.
        field_conflict: whether corroboration fields conflict.
        conflict_fields: which fields conflict.
        independent_source_count / source_count: corroboration for accuracy.
        observed_recency_days: age of newest data; None → assume fresh (0).
        freshness_window_days: full-freshness horizon.
    """
    conflict_fields = conflict_fields or []

    # completeness
    present = {f for f, p in (fields or {}).items() if p}
    comp_num = sum(CORE_FIELDS.get(f, 1) for f in present if f in CORE_FIELDS)
    comp_den = sum(CORE_FIELDS.values())
    completeness = round((comp_num / comp_den) * 100, 2) if comp_den else 0.0

    # accuracy: agree across sources, penalized by conflicts.
    base_accuracy = 100.0
    if field_conflict:
        base_accuracy -= 30.0 * min(len(conflict_fields), 3)
    if independent_source_count <= 1:
        base_accuracy -= 10.0  # single-source → cannot corroborate
    accuracy = max(0.0, round(base_accuracy, 2))

    # consistency: penalize conflicts; reward multi-field coherence.
    consistency = 100.0
    if field_conflict:
        consistency -= 25.0 * min(len(conflict_fields), 3)
    consistency = max(0.0, round(consistency, 2))

    # freshness: linear decay from 100 → 0 at window.
    if observed_recency_days is None or observed_recency_days <= 0:
        freshness = 100.0
    else:
        freshness = max(
            0.0, round(100.0 * (1.0 - observed_recency_days / freshness_window_days), 2)
        )

    # provenance: average tier rank over present fields.
    prov_tiers = provenance_tiers or {}
    ranks = [
        PROVENANCE_TIER_RANK.get(t, 0.5)
        for f in present
        for t in (prov_tiers.get(f),)
        if t
    ]
    provenance = round((sum(ranks) / len(ranks)) * 100, 2) if ranks else 0.0

    overall = _weighted_avg([
        (completeness, 0.30),
        (accuracy, 0.25),
        (consistency, 0.15),
        (freshness, 0.15),
        (provenance, 0.15),
    ])

    evidence_basis = {
        "fields_present": sorted(present),
        "field_conflict": field_conflict,
        "conflict_fields": conflict_fields,
        "independent_source_count": independent_source_count,
        "source_count": source_count,
        "observed_recency_days": observed_recency_days,
    }
    return QualityResult(
        completeness, accuracy, consistency, freshness, provenance, overall,
        evidence_basis,
    )
