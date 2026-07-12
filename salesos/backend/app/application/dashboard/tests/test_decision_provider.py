"""Tests for DashboardDecisionProvider — scoring dashboard widget signals via Decision Platform."""

import pytest

from app.application.dashboard.services.decision_provider import DashboardDecisionProvider
from sdk.scoring.interfaces import DecisionContext, DecisionFactor, Recommendation, RecommendationEvidence


# ── Fakes for Decision Platform protocols ──


class FakeDecisionService:
    """In-memory DecisionServiceProtocol stub."""

    def __init__(self):
        self.contexts: list[DecisionContext] = []

    async def build_context(
        self,
        tenant_id: str,
        target_id: str,
        target_type: str,
        factors: list[DecisionFactor],
    ) -> DecisionContext:
        ctx = DecisionContext(
            id=f"ctx-{len(self.contexts)}",
            tenant_id=tenant_id,
            target_id=target_id,
            target_type=target_type,
            factors=factors,
        )
        self.contexts.append(ctx)
        return ctx

    async def get_latest_context(self, target_id: str, target_type: str):
        return None


class FakeRecommendationEngine:
    """In-memory RecommendationEngineProtocol stub that returns a recommendation when critical factors exist."""

    def __init__(self, return_recommendation: bool = True):
        self._return_recommendation = return_recommendation

    async def evaluate(self, context: DecisionContext):
        if not self._return_recommendation:
            return None
        critical = [f for f in context.factors if f.severity == "critical"]
        if not critical:
            return None
        return Recommendation(
            title="Critical dashboard issues detected",
            description=f"{len(critical)} critical factors require attention",
            confidence=0.9,
            evidence=[
                RecommendationEvidence(
                    source_layer=f.source_layer,
                    source_domain=f.source_domain,
                    key=f.key,
                    value=f.value,
                    narrative=f.label,
                )
                for f in critical
            ],
        )


class BrokenDecisionService:
    async def build_context(self, **kwargs):
        raise RuntimeError("Decision Service unavailable")

    async def get_latest_context(self, target_id, target_type):
        return None


# ── Tests ──


@pytest.mark.asyncio
async def test_score_dashboard_empty_signals():
    ds = FakeDecisionService()
    re = FakeRecommendationEngine()
    provider = DashboardDecisionProvider(ds, re)

    result = await provider.score_dashboard(tenant_id="t-1", widget_signals={})

    assert result["scored_decisions"] == []
    assert result["overall_health"] == 1.0


@pytest.mark.asyncio
async def test_score_dashboard_critical_decision_queue():
    ds = FakeDecisionService()
    re = FakeRecommendationEngine()
    provider = DashboardDecisionProvider(ds, re)

    decision_queue = {
        "items": [
            {"id": "d1", "priority": "high", "title": "Deal at risk"},
            {"id": "d2", "priority": "high", "title": "Stalled pipeline"},
            {"id": "d3", "priority": "medium", "title": "Review needed"},
        ],
        "total": 3,
    }

    result = await provider.score_dashboard(
        tenant_id="t-1",
        widget_signals={"decisionQueue": decision_queue},
    )

    assert len(result["scored_decisions"]) >= 1
    assert result["overall_health"] < 1.0
    critical_decisions = [d for d in result["scored_decisions"] if d["severity"] == "critical"]
    assert len(critical_decisions) >= 1
    assert critical_decisions[0]["factor_key"] == "critical_decisions"


@pytest.mark.asyncio
async def test_score_dashboard_critical_intelligence_signals():
    ds = FakeDecisionService()
    re = FakeRecommendationEngine()
    provider = DashboardDecisionProvider(ds, re)

    feed = {
        "items": [
            {"severity": "critical", "title": "Regulatory alert"},
            {"severity": "high", "title": "Competitor move"},
        ],
        "total": 2,
    }

    result = await provider.score_dashboard(
        tenant_id="t-1",
        widget_signals={"intelligenceFeed": feed},
    )

    critical_items = [d for d in result["scored_decisions"] if d["severity"] == "critical"]
    warning_items = [d for d in result["scored_decisions"] if d["severity"] == "warning"]
    assert len(critical_items) >= 1
    assert len(warning_items) >= 1
    assert critical_items[0]["factor_key"] == "critical_signals"
    assert warning_items[0]["factor_key"] == "warning_signals"


@pytest.mark.asyncio
async def test_score_dashboard_mission_center_no_deals():
    ds = FakeDecisionService()
    re = FakeRecommendationEngine()
    provider = DashboardDecisionProvider(ds, re)

    mc = {"activeDeals": 0, "pipelineValue": 0, "signalsToday": 0}

    result = await provider.score_dashboard(
        tenant_id="t-1",
        widget_signals={"missionCenter": mc},
    )

    warning_items = [d for d in result["scored_decisions"] if d["severity"] == "warning"]
    assert len(warning_items) >= 1
    assert warning_items[0]["factor_key"] == "no_active_deals"


@pytest.mark.asyncio
async def test_score_dashboard_overall_health_degrades_with_critical():
    ds = FakeDecisionService()
    re = FakeRecommendationEngine()
    provider = DashboardDecisionProvider(ds, re)

    feed = {"items": [{"severity": "critical", "title": "Alert"}], "total": 1}
    mc = {"activeDeals": 0, "pipelineValue": 0, "signalsToday": 0}

    result = await provider.score_dashboard(
        tenant_id="t-1",
        widget_signals={"intelligenceFeed": feed, "missionCenter": mc},
    )

    assert result["overall_health"] < 1.0


@pytest.mark.asyncio
async def test_score_dashboard_recommendation_included():
    ds = FakeDecisionService()
    re = FakeRecommendationEngine(return_recommendation=True)
    provider = DashboardDecisionProvider(ds, re)

    feed = {"items": [{"severity": "critical", "title": "Urgent"}], "total": 1}

    result = await provider.score_dashboard(
        tenant_id="t-1",
        widget_signals={"intelligenceFeed": feed},
    )

    rec_items = [d for d in result["scored_decisions"] if d["factor_key"] == "recommendation"]
    assert len(rec_items) == 1
    assert rec_items[0]["source_domain"] == "recommendation_engine"
    assert rec_items[0]["score"] == 0.9


@pytest.mark.asyncio
async def test_score_dashboard_decision_service_failure_is_non_blocking():
    ds = BrokenDecisionService()
    re = FakeRecommendationEngine()
    provider = DashboardDecisionProvider(ds, re)

    feed = {"items": [{"severity": "high", "title": "Test"}], "total": 1}

    result = await provider.score_dashboard(
        tenant_id="t-1",
        widget_signals={"intelligenceFeed": feed},
    )

    assert result["scored_decisions"] == []
    assert result["overall_health"] == 0.0


@pytest.mark.asyncio
async def test_score_dashboard_no_recommendation_when_no_critical():
    ds = FakeDecisionService()
    re = FakeRecommendationEngine(return_recommendation=True)
    provider = DashboardDecisionProvider(ds, re)

    mc = {"activeDeals": 5, "pipelineValue": 100000, "signalsToday": 3}

    result = await provider.score_dashboard(
        tenant_id="t-1",
        widget_signals={"missionCenter": mc},
    )

    rec_items = [d for d in result["scored_decisions"] if d["factor_key"] == "recommendation"]
    assert len(rec_items) == 0


@pytest.mark.asyncio
async def test_score_dashboard_recent_activity_empty():
    ds = FakeDecisionService()
    re = FakeRecommendationEngine(return_recommendation=False)
    provider = DashboardDecisionProvider(ds, re)

    activity = {"items": [], "total": 0}

    result = await provider.score_dashboard(
        tenant_id="t-1",
        widget_signals={"recentActivity": activity},
    )

    info_items = [d for d in result["scored_decisions"] if d["severity"] == "info"]
    assert len(info_items) >= 1
    assert info_items[0]["factor_key"] == "no_recent_activity"
