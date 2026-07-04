"""Recommendation Engine Domain — consumes Decision Context, produces explainable recommendations.

Every recommendation must be contextual, explainable, and optional.
Never executes actions. Never replaces human decisions.
"""

from .models import Alternative, Recommendation, RecommendationEvidence
from .repo import RecommendationRepository
from .engine import RecommendationEngine

__all__ = ["Recommendation", "Alternative", "RecommendationEvidence", "RecommendationRepository", "RecommendationEngine"]
