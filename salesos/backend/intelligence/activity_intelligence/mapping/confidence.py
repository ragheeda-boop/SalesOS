"""Confidence Scorer — Stage 4 of the Mapping Pipeline (ADR-012 §6).

Scores each candidate match:
- confidence = f(method_weight, data_quality, historical_accuracy)
- Method weights: explicit=1.0, opportunity=0.9, contact=0.8, domain=0.6, ai=0.4
- Rejects candidates below threshold (default: 0.5)
"""

from __future__ import annotations

from intelligence.activity_intelligence.contracts.models import (
    CandidateMatch,
    ScoredCandidate,
)

METHOD_WEIGHTS = {
    "explicit_ref": 1.0,
    "opportunity_lookup": 0.9,
    "contact_lookup": 0.8,
    "domain_match": 0.6,
    "ai_match": 0.4,
}


class ConfidenceScorer:
    """Score candidate matches and reject below threshold."""

    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold

    def score(
        self, candidates: list[CandidateMatch]
    ) -> ScoredCandidate | None:
        """Score candidates and return the best one above threshold.

        Returns None if no candidate meets the threshold.
        """
        if not candidates:
            return None

        best: ScoredCandidate | None = None

        for candidate in candidates:
            score = self._compute_score(candidate)
            if score >= self.threshold and (best is None or score > best.score):
                best = ScoredCandidate(
                    candidate=candidate,
                    score=score,
                    reason=candidate.reason,
                    threshold=self.threshold,
                )

        return best

    def score_all(
        self, candidates: list[CandidateMatch]
    ) -> list[ScoredCandidate]:
        """Score all candidates, sorted by score descending.

        Filters out those below threshold.
        """
        scored = []
        for candidate in candidates:
            score = self._compute_score(candidate)
            if score >= self.threshold:
                scored.append(
                    ScoredCandidate(
                        candidate=candidate,
                        score=score,
                        reason=candidate.reason,
                        threshold=self.threshold,
                    )
                )
        return sorted(scored, key=lambda s: s.score, reverse=True)

    def _compute_score(self, candidate: CandidateMatch) -> float:
        """Compute confidence score using method weight and data quality."""
        base_weight = METHOD_WEIGHTS.get(candidate.method, 0.3)
        quality_factor = 1.0

        # Penalize if no entity_id
        if not candidate.entity_id:
            quality_factor = 0.5

        # Use candidate's own confidence if set
        if candidate.confidence > 0:
            base_weight = candidate.confidence

        return round(base_weight * quality_factor, 4)
