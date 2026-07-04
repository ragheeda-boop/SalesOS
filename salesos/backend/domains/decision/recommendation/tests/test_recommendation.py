"""Tests for Recommendation Engine Domain."""

import pytest

from domains.decision.recommendation.models import (
    Alternative, Recommendation, RecommendationEvidence, RecommendationStatus,
)
from domains.decision.recommendation.engine import RecommendationEngine
from domains.decision.recommendation.in_memory_repo import InMemoryRecommendationRepository
from domains.decision.context.models import DecisionContext, DecisionFactor


def test_recommendation_evidence():
    r = Recommendation(id="r1", tenant_id="t1", context_id="c1", title="Test",
                       evidence=[RecommendationEvidence(source_layer="fact", source_domain="pipeline",
                                                          key="stage_aging", value=14,
                                                          narrative="14 days in stage")])
    assert len(r.evidence_summary) == 1
    assert "14 days in stage" in r.evidence_summary[0]


def test_recommendation_has_alternatives():
    r = Recommendation(id="r1", tenant_id="t1", context_id="c1", title="Test",
                       alternatives=[Alternative(title="Option A", description="Do X"),
                                      Alternative(title="Option B", description="Do Y")])
    assert len(r.alternatives) == 2


def test_recommendation_no_action():
    """Recommendation must never execute actions."""
    r = Recommendation(id="r1", tenant_id="t1", context_id="c1", title="Test")
    assert not hasattr(r, "action")
    assert not hasattr(r, "execute")


@pytest.mark.asyncio
async def test_engine_critical_stage_aging():
    engine = RecommendationEngine()
    ctx = DecisionContext(id="c1", tenant_id="t1", target_id="opp-1", target_type="opportunity", factors=[
        DecisionFactor(source_layer="fact", source_domain="pipeline", key="stage_aging",
                       value=14, severity="critical", label="14 days in stage with no activity"),
    ])

    rec = await engine.evaluate(ctx)
    assert rec is not None
    assert rec.confidence == 0.87
    assert "Schedule" in rec.title
    assert len(rec.alternatives) >= 2
    assert len(rec.evidence) >= 1


@pytest.mark.asyncio
async def test_engine_forecast_warning():
    engine = RecommendationEngine()
    ctx = DecisionContext(id="c1", tenant_id="t1", target_id="opp-1", target_type="opportunity", factors=[
        DecisionFactor(source_layer="knowledge", source_domain="forecast", key="forecast_drop",
                       value=0.22, severity="warning", label="Forecast dropped 22%"),
    ])

    rec = await engine.evaluate(ctx)
    assert rec is not None
    assert rec.confidence == 0.75
    assert "Review" in rec.title


@pytest.mark.asyncio
async def test_engine_no_recommendation_for_healthy_deal():
    """Healthy opportunities should produce no recommendation."""
    engine = RecommendationEngine()
    ctx = DecisionContext(id="c1", tenant_id="t1", target_id="opp-1", target_type="opportunity",
                          factors=[DecisionFactor(source_layer="fact", source_domain="activity",
                                                    key="recent_activity", severity="info",
                                                    value=3, label="Activity within 3 days")])
    rec = await engine.evaluate(ctx)
    assert rec is None


@pytest.mark.asyncio
async def test_engine_explainable():
    engine = RecommendationEngine()
    ctx = DecisionContext(id="c1", tenant_id="t1", target_id="opp-1", target_type="opportunity", factors=[
        DecisionFactor(source_layer="fact", source_domain="pipeline", key="stage_aging",
                       value=14, severity="critical", label="No activity for 14 days"),
    ])

    rec = await engine.evaluate(ctx)
    assert rec is not None
    assert rec.reasoning
    assert rec.expected_impact
    assert rec.risk


@pytest.mark.asyncio
async def test_recommendation_persistence():
    repo = InMemoryRecommendationRepository()
    rec = Recommendation(id="r1", tenant_id="t1", context_id="c1", title="Test")
    await repo.save(rec)

    loaded = await repo.get("r1")
    assert loaded is not None
    assert loaded.title == "Test"


@pytest.mark.asyncio
async def test_accept_recommendation():
    rec = Recommendation(id="r1", tenant_id="t1", context_id="c1", title="Test",
                         status=RecommendationStatus.ACCEPTED)
    assert rec.is_accepted
