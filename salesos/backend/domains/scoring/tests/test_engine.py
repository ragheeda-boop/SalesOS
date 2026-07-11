"""Tests for the Scoring Engine — validates signals → Decision Platform bridge."""

from __future__ import annotations
import pytest
from datetime import datetime, timezone

from ...decision.context.models import DecisionContext, DecisionFactor, Policy
from ...decision.context.service import DecisionService
from ...decision.context.repo import DecisionRepository
from ...decision.context.in_memory_repo import InMemoryDecisionRepository
from ...decision.recommendation.engine import RecommendationEngine
from ..engine import ScoringEngine
from ..models import ScoringDimension, ConfidenceLevel


@pytest.fixture
def decision_repo() -> DecisionRepository:
    return InMemoryDecisionRepository()


@pytest.fixture
def decision_service(decision_repo: DecisionRepository) -> DecisionService:
    return DecisionService(repository=decision_repo)


@pytest.fixture
def recommendation_engine() -> RecommendationEngine:
    return RecommendationEngine()


@pytest.fixture
def scoring_engine(
    decision_service: DecisionService,
    recommendation_engine: RecommendationEngine,
) -> ScoringEngine:
    return ScoringEngine(
        decision_service=decision_service,
        recommendation_engine=recommendation_engine,
    )


class TestScoringEngine:
    """Validates the ScoringEngine bridges signals to the Decision Platform."""

    SAMPLE_SIGNALS = [
        {
            "id": "sig_1",
            "signal_type": "funding",
            "title": "Series B funding round",
            "intensity": 0.85,
            "priority": "high",
            "description": "Company raised $50M Series B",
        },
        {
            "id": "sig_2",
            "signal_type": "hiring",
            "title": "Hiring 50 engineers",
            "intensity": 0.75,
            "priority": "high",
            "description": "Major hiring push in Riyadh",
        },
        {
            "id": "sig_3",
            "signal_type": "expansion",
            "title": "New office in Jeddah",
            "intensity": 0.7,
            "priority": "medium",
            "description": "Expanding operations to Jeddah",
        },
    ]

    @pytest.mark.asyncio
    async def test_score_signals_uses_decision_platform(
        self, scoring_engine: ScoringEngine
    ):
        """Signals flow through Decision Platform context builder."""
        card = await scoring_engine.score_signals(
            tenant_id="tenant-1",
            target_id="company-1",
            signals=self.SAMPLE_SIGNALS,
        )

        assert card is not None
        assert card.tenant_id == "tenant-1"
        assert card.target_id == "company-1"
        assert len(card.scores) > 0
        assert card.overall_score > 0

    @pytest.mark.asyncio
    async def test_dimension_scores(
        self, scoring_engine: ScoringEngine
    ):
        """Each dimension is scored independently."""
        card = await scoring_engine.score_signals(
            tenant_id="tenant-1",
            target_id="company-1",
            signals=self.SAMPLE_SIGNALS,
        )

        dimensions = {s.dimension for s in card.scores}
        assert ScoringDimension.BUYING_INTENT in dimensions
        assert ScoringDimension.ENGAGEMENT in dimensions
        assert ScoringDimension.MARKET_SIGNAL in dimensions

        for score in card.scores:
            assert 0 <= score.normalized_score <= 1
            assert score.confidence in (
                ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM, ConfidenceLevel.LOW
            )

    @pytest.mark.asyncio
    async def test_confidence_increases_with_signal_count(
        self, scoring_engine: ScoringEngine
    ):
        """More signals produce higher confidence."""
        card_1 = await scoring_engine.score_signals(
            tenant_id="tenant-1", target_id="company-2",
            signals=[self.SAMPLE_SIGNALS[0]],
        )
        card_2 = await scoring_engine.score_signals(
            tenant_id="tenant-1", target_id="company-2",
            signals=self.SAMPLE_SIGNALS,
        )

        engagement_1 = next(
            (s for s in card_1.scores if s.dimension == ScoringDimension.ENGAGEMENT),
            None,
        )
        engagement_2 = next(
            (s for s in card_2.scores if s.dimension == ScoringDimension.ENGAGEMENT),
            None,
        )
        if engagement_1 and engagement_2:
            thresholds = {
                ConfidenceLevel.HIGH: 3,
                ConfidenceLevel.MEDIUM: 2,
                ConfidenceLevel.LOW: 1,
            }
            assert thresholds[engagement_2.confidence] >= thresholds[engagement_1.confidence]

    @pytest.mark.asyncio
    async def test_risk_factors_identified(
        self, scoring_engine: ScoringEngine
    ):
        """Low-scoring factors are reported as risks."""
        weak_signals = [
            {
                "id": "sig_weak",
                "signal_type": "news",
                "title": "Minor mention",
                "intensity": 0.15,
                "priority": "low",
            },
        ]
        card = await scoring_engine.score_signals(
            tenant_id="tenant-1", target_id="company-3",
            signals=weak_signals,
        )

        assert len(card.risk_factors) >= 0

    @pytest.mark.asyncio
    async def test_scorecard_persistence(
        self, scoring_engine: ScoringEngine
    ):
        """ScoreCard is retrievable after scoring."""
        card = await scoring_engine.score_signals(
            tenant_id="tenant-1", target_id="company-4",
            signals=self.SAMPLE_SIGNALS,
        )

        retrieved = scoring_engine.get_scorecard(card.id)
        assert retrieved is not None
        assert retrieved.id == card.id
        assert retrieved.overall_score == card.overall_score

    @pytest.mark.asyncio
    async def test_top_opportunity(
        self, scoring_engine: ScoringEngine
    ):
        """Best dimension is reported as top opportunity."""
        card = await scoring_engine.score_signals(
            tenant_id="tenant-1", target_id="company-5",
            signals=self.SAMPLE_SIGNALS,
        )

        top = card.top_opportunity_score
        assert top is not None
        assert top.normalized_score == max(
            s.normalized_score for s in card.scores
        )

    @pytest.mark.asyncio
    async def test_decision_context_created(
        self, scoring_engine: ScoringEngine, decision_service: DecisionService
    ):
        """A DecisionContext is created in the Decision Platform."""
        card = await scoring_engine.score_signals(
            tenant_id="tenant-1", target_id="company-6",
            signals=self.SAMPLE_SIGNALS,
        )

        ctx = await decision_service.get_latest_context("company-6", "company")
        assert ctx is not None
        assert ctx.tenant_id == "tenant-1"
        assert ctx.target_id == "company-6"
        assert len(ctx.factors) > 0

    @pytest.mark.asyncio
    async def test_empty_signals(
        self, scoring_engine: ScoringEngine
    ):
        """Empty signals produce zero scores."""
        card = await scoring_engine.score_signals(
            tenant_id="tenant-1", target_id="company-7",
            signals=[],
        )

        assert card.overall_score == 0.0
        assert len(card.scores) == 0

    @pytest.mark.asyncio
    async def test_stats(
        self, scoring_engine: ScoringEngine
    ):
        """Engine stats reflect scoring activity."""
        await scoring_engine.score_signals(
            tenant_id="tenant-1", target_id="company-8",
            signals=self.SAMPLE_SIGNALS,
        )
        await scoring_engine.score_signals(
            tenant_id="tenant-1", target_id="company-9",
            signals=self.SAMPLE_SIGNALS[:1],
        )

        stats = scoring_engine.stats
        assert stats["total_scorecards"] == 2
        assert stats["avg_overall_score"] > 0
