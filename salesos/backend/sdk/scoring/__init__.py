"""Scoring SDK — interfaces bridging scoring domain to decision platform."""

from sdk.scoring.interfaces import (
    DecisionContext,
    DecisionFactor,
    DecisionServiceProtocol,
    Recommendation,
    RecommendationEngineProtocol,
    RecommendationEvidence,
    ScoreCardRepository,
)

__all__ = [
    "DecisionContext",
    "DecisionFactor",
    "DecisionServiceProtocol",
    "Recommendation",
    "RecommendationEngineProtocol",
    "RecommendationEvidence",
    "ScoreCardRepository",
]
