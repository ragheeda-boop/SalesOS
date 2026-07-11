"""ScoringEngine — bridges signals to Decision Platform.

Consumes signals from SignalEngine, transforms them into DecisionContext factors,
and produces explainable ScoreCards via the Decision Platform's RecommendationEngine.

Flow: Signals → DecisionContext → RecommendationEngine → ScoreCard
"""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any

from ..decision.context.models import DecisionContext, DecisionFactor
from ..decision.context.service import DecisionService
from ..decision.recommendation.engine import RecommendationEngine
from ..decision.recommendation.models import RecommendationEvidence
from .models import (
    ConfidenceLevel, Score, ScoreCard, ScoringDimension,
    ScoringFactor, SignalEvidence,
)


class ScoringEngine:
    """Evaluates signals against the Decision Platform to produce scored intelligence.

    This is the canonical scoring entry point. All scoring goes through this engine,
    which delegates to the Decision Platform's context builder + recommendation engine.
    """

    def __init__(
        self,
        decision_service: DecisionService,
        recommendation_engine: RecommendationEngine,
        event_bus: Any = None,
    ):
        self._decision_service = decision_service
        self._recommendation_engine = recommendation_engine
        self._event_bus = event_bus
        self._scorecards: dict[str, ScoreCard] = {}

    async def score_signals(
        self,
        tenant_id: str,
        target_id: str,
        signals: list[dict[str, Any]],
        target_type: str = "company",
    ) -> ScoreCard:
        """Score a set of signals for a target entity through the Decision Platform."""
        factors = self._signals_to_factors(signals)
        context = await self._decision_service.build_context(
            tenant_id=tenant_id,
            target_id=target_id,
            target_type=target_type,
            factors=factors,
        )

        recommendation = await self._recommendation_engine.evaluate(context)

        scores = self._compute_dimension_scores(signals)
        overall = self._compute_overall(scores)

        evidence_list = []
        if recommendation:
            for e in recommendation.evidence:
                evidence_list.append(
                    self._evidence_from_recommendation(e, target_id)
                )

        card = ScoreCard(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            target_id=target_id,
            target_type=target_type,
            scores=scores,
            overall_score=overall,
            overall_confidence=self._resolve_confidence(overall),
        )
        self._scorecards[card.id] = card
        return card

    def _signals_to_factors(self, signals: list[dict[str, Any]]) -> list[DecisionFactor]:
        """Transform raw signals into DecisionContext factors."""
        factors: list[DecisionFactor] = []
        severity_map = {"high": "warning", "critical": "critical"}
        for sig in signals:
            factors.append(DecisionFactor(
                source_layer="measurement",
                source_domain="signals",
                key=sig.get("signal_type", "unknown"),
                value=sig.get("intensity", 0.5),
                label=sig.get("title", ""),
                severity=severity_map.get(sig.get("priority", "medium"), "info"),
            ))
        return factors

    def _compute_dimension_scores(
        self, signals: list[dict[str, Any]]
    ) -> list[Score]:
        """Compute per-dimension scores from signals."""
        dimension_signals: dict[ScoringDimension, list[dict]] = {
            d: [] for d in ScoringDimension
        }

        signal_routing = {
            "hiring": ScoringDimension.ENGAGEMENT,
            "funding": ScoringDimension.BUYING_INTENT,
            "expansion": ScoringDimension.BUYING_INTENT,
            "contract": ScoringDimension.ENGAGEMENT,
            "project": ScoringDimension.URGENCY,
            "partnership": ScoringDimension.RELATIONSHIP,
            "merger": ScoringDimension.MARKET_SIGNAL,
            "leadership": ScoringDimension.RELATIONSHIP,
            "tender": ScoringDimension.BUYING_INTENT,
            "competitor_move": ScoringDimension.MARKET_SIGNAL,
            "regulatory": ScoringDimension.FIT,
            "news": ScoringDimension.MARKET_SIGNAL,
        }

        for sig in signals:
            st = sig.get("signal_type", "").lower()
            dimension = signal_routing.get(st, ScoringDimension.MARKET_SIGNAL)
            dimension_signals[dimension].append(sig)

        scores = []
        for dimension, dim_signals in dimension_signals.items():
            if not dim_signals:
                continue

            weighted_sum = sum(
                s.get("intensity", 0.5) * self._get_weight(s, dimension)
                for s in dim_signals
            )
            count = len(dim_signals)
            raw = weighted_sum / max(count, 1)
            normalized = min(raw, 1.0)

            factors = []
            for s in dim_signals:
                factors.append(ScoringFactor(
                    dimension=dimension,
                    key=s.get("signal_type", "unknown"),
                    value=s.get("intensity", 0.5),
                    weight=self._get_weight(s, dimension),
                    label=s.get("title", ""),
                    evidence=[
                        SignalEvidence(
                            source_layer="measurement",
                            source_domain="signals",
                            signal_id=s.get("id", ""),
                            signal_type=s.get("signal_type", ""),
                            intensity=s.get("intensity", 0.5),
                            narrative=s.get("description", s.get("title", "")),
                            detected_at=datetime.now(timezone.utc),
                        )
                    ],
                ))

            scores.append(Score(
                dimension=dimension,
                raw_score=round(raw, 4),
                normalized_score=round(normalized, 4),
                confidence=self._compute_confidence(dim_signals),
                factors=factors,
                narrative=self._dimension_narrative(dimension, normalized, count),
            ))

        return scores

    def _get_weight(self, signal: dict, dimension: ScoringDimension) -> float:
        base = signal.get("intensity", 0.5)
        if dimension == ScoringDimension.BUYING_INTENT:
            return base * 1.2
        if dimension == ScoringDimension.URGENCY:
            return base * 1.1
        return base

    def _compute_confidence(self, signals: list[dict]) -> ConfidenceLevel:
        if len(signals) >= 5:
            return ConfidenceLevel.HIGH
        if len(signals) >= 2:
            return ConfidenceLevel.MEDIUM
        return ConfidenceLevel.LOW

    def _compute_overall(self, scores: list[Score]) -> float:
        if not scores:
            return 0.0
        weights = {
            ScoringDimension.BUYING_INTENT: 0.30,
            ScoringDimension.ENGAGEMENT: 0.20,
            ScoringDimension.FIT: 0.15,
            ScoringDimension.URGENCY: 0.15,
            ScoringDimension.RELATIONSHIP: 0.10,
            ScoringDimension.MARKET_SIGNAL: 0.10,
        }
        total_weight = sum(weights.get(s.dimension, 0.15) for s in scores)
        if total_weight == 0:
            return 0.0
        weighted = sum(
            s.normalized_score * weights.get(s.dimension, 0.15)
            for s in scores
        )
        return round(min(weighted / total_weight, 1.0), 4)

    def _resolve_confidence(self, score: float) -> ConfidenceLevel:
        if score >= 0.7:
            return ConfidenceLevel.HIGH
        if score >= 0.4:
            return ConfidenceLevel.MEDIUM
        return ConfidenceLevel.LOW

    def _dimension_narrative(self, dimension: ScoringDimension, score: float, count: int) -> str:
        narratives = {
            ScoringDimension.BUYING_INTENT:
                f"نية شراء {self._describe_score(score)} — {count} إشارة",
            ScoringDimension.ENGAGEMENT:
                f"مستوى تفاعل {self._describe_score(score)} — {count} إشارة",
            ScoringDimension.FIT:
                f"ملاءمة {self._describe_score(score)} — {count} إشارة",
            ScoringDimension.URGENCY:
                f"إلحاح {self._describe_score(score)} — {count} إشارة",
            ScoringDimension.RELATIONSHIP:
                f"علاقة {self._describe_score(score)} — {count} إشارة",
            ScoringDimension.MARKET_SIGNAL:
                f"إشارة سوق {self._describe_score(score)} — {count} إشارة",
        }
        return narratives.get(dimension, f"تقييم {dimension.value}: {score:.0%}")

    def _describe_score(self, score: float) -> str:
        if score >= 0.8:
            return "عالٍ جداً"
        if score >= 0.6:
            return "عالٍ"
        if score >= 0.4:
            return "متوسط"
        return "منخفض"

    def _evidence_from_recommendation(
        self, evidence: RecommendationEvidence, target_id: str
    ) -> SignalEvidence:
        return SignalEvidence(
            source_layer=evidence.source_layer,
            source_domain=evidence.source_domain,
            signal_id=target_id,
            signal_type=evidence.key,
            intensity=float(evidence.value) if evidence.value else 0.5,
            narrative=evidence.narrative,
            detected_at=datetime.now(timezone.utc),
        )

    def get_scorecard(self, card_id: str) -> ScoreCard | None:
        return self._scorecards.get(card_id)

    async def get_scorecard_for_target(
        self, tenant_id: str, target_id: str, target_type: str = "company"
    ) -> ScoreCard | None:
        ctx = await self._decision_service.get_latest_context(target_id, target_type)
        if not ctx:
            return None
        for card in self._scorecards.values():
            if card.target_id == target_id and card.target_type == target_type:
                return card
        return None

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "total_scorecards": len(self._scorecards),
            "avg_overall_score": round(
                sum(c.overall_score for c in self._scorecards.values())
                / max(len(self._scorecards), 1), 4
            ),
        }
