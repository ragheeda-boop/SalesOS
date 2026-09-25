"""Phase 6 — Canonical field authority (survivorship).

Contract: canonical field values are selected by AUTHORITY-BASED SURVIVORSHIP
ONLY. Frequency must NEVER determine canonical identity. For each entity+field
we persist: value, source, evidence tier, authority, selection_reason,
observed_at, is_current. The system can answer "why is this value currently
canonical?"

Authority ranking (highest wins) mirrors the evidence-tier hierarchy:
  GOVERNMENT_ANCHOR > STRONG_DETERMINISTIC > WEAK_DETERMINISTIC >
  NORMALIZED_EXACT > FUZZY.
Within the same tier, a single observed value wins; ties across genuinely
independent sources keep the most recent. Frequency is not consulted.
"""

from __future__ import annotations

from dataclasses import dataclass

TIER_ORDER = [
    "GOVERNMENT_ANCHOR",      # 0 highest
    "STRONG_DETERMINISTIC",   # 1
    "WEAK_DETERMINISTIC",     # 2
    "NORMALIZED_EXACT",       # 3
    "FUZZY",                  # 4
]
TIER_RANK = {name: i for i, name in enumerate(TIER_ORDER)}


@dataclass
class CanonicalCandidate:
    value: str
    source_row_id: str | None
    evidence_tier: str
    authority_score: float
    selection_reason: str
    observed_at: str  # ISO timestamp


def select_canonical(candidates: list[CanonicalCandidate]) -> CanonicalCandidate | None:
    """Select the canonical value from candidates by authority ONLY.

    Returns None if no candidates.
    Tie-break within the winning tier: most recent observed at. Frequency is
    never used.
    """
    if not candidates:
        return None
    valid = [c for c in candidates if c.value]
    if not valid:
        return None
    # Highest authority tier (lowest rank) wins.
    best_tier = min(valid, key=lambda c: TIER_RANK.get(c.evidence_tier, 99))
    top_tier_rank = TIER_RANK.get(best_tier.evidence_tier, 99)
    tier_candidates = [c for c in valid if TIER_RANK.get(c.evidence_tier, 99) == top_tier_rank]
    # Within tier: most recent observed_at wins (tie only on authority).
    tier_candidates.sort(key=lambda c: (c.observed_at or ""), reverse=True)
    winner = tier_candidates[0]
    return winner


def selection_reason_for(winner: CanonicalCandidate | None) -> str:
    if winner is None:
        return "no_canonical_evidence"
    return f"highest_authority_tier:{winner.evidence_tier}"
