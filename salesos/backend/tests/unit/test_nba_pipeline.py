"""Tests for the NBA Decision Pipeline — normalize, rules, score, risk, confidence, recommend, recompute."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from runtime.nba_engine import (
    NBAEngine,
    NBAResult,
    NormalizedSignal,
    Evidence,
    Alternative,
    Impact,
    RiskFactor,
)


# ── Fake SQLAlchemy helpers ──────────────────────────────────────────────────

class FakeMapping:
    def __init__(self, data):
        self._data = data

    def __getitem__(self, key):
        return self._data[key]

    def get(self, key, default=None):
        return self._data.get(key, default)

    def keys(self):
        return self._data.keys()

    def __iter__(self):
        return iter(self._data)


class FakeMappings:
    def __init__(self, rows=None, one=None):
        self._rows = rows or []
        self._one = one

    def one(self):
        return FakeMapping(self._one) if self._one else None

    def one_or_none(self):
        return FakeMapping(self._one) if self._one else None

    def all(self):
        return [FakeMapping(r) for r in self._rows]


class FakeResult:
    def __init__(self, mappings_obj=None):
        self._mappings = mappings_obj or FakeMappings()

    def mappings(self):
        return self._mappings


# ── Fixtures ─────────────────────────────────────────────────────────────────

SAMPLE_OPP = {
    "id": "opp-1",
    "name": "ERP Implementation",
    "stage": "proposal",
    "value": 500000,
    "probability": 0.6,
    "company_id": "co-1",
    "tenant_id": "tenant-1",
    "owner_id": "user-1",
    "status": "open",
    "expected_close_date": datetime.now(timezone.utc) + timedelta(days=30),
    "company_name_ar": "شركة التقنية",
    "industry": "technology",
    "city": "Riyadh",
    "employees_count": 200,
    "annual_revenue": 10000000,
}

SAMPLE_ACTIVITIES = [
    {
        "id": "act-1",
        "action": "email_sent",
        "timestamp": datetime.now(timezone.utc) - timedelta(days=2),
        "description": "Sent proposal follow-up",
    },
    {
        "id": "act-2",
        "action": "call_made",
        "timestamp": datetime.now(timezone.utc) - timedelta(days=5),
        "description": "Discovery call completed",
    },
]


def _make_session_factory(opp=SAMPLE_OPP, activities=SAMPLE_ACTIVITIES):
    """Return a mock session_factory that responds to the two queries NBAEngine._normalize runs."""
    call_count = {"n": 0}

    async def execute(sql_str, params=None):
        text = str(sql_str)
        if "commercial_opportunities" in text and "activity_records" not in text:
            call_count["n"] += 1
            return FakeResult(FakeMappings(one=opp))
        elif "activity_records" in text:
            return FakeResult(FakeMappings(rows=activities))
        return FakeResult(FakeMappings())

    async def __aenter__(self):
        session = AsyncMock()
        session.execute = execute
        return session

    async def __aexit__(self, *a):
        pass

    factory = MagicMock()
    factory.return_value.__aenter__ = __aenter__
    factory.return_value.__aexit__ = __aexit__
    return factory


@pytest.fixture
def engine():
    factory = _make_session_factory()
    return NBAEngine(session_factory=factory)


@pytest.fixture
def engine_no_activities():
    factory = _make_session_factory(activities=[])
    return NBAEngine(session_factory=factory)


@pytest.fixture
def sample_signal():
    return NormalizedSignal(
        source="manual_refresh",
        entity_type="opportunity",
        entity_id="opp-1",
        opportunity_id="opp-1",
        tenant_id="tenant-1",
        timestamp=datetime.now(timezone.utc).isoformat(),
        data=SAMPLE_OPP.copy(),
        context={
            "opportunity": SAMPLE_OPP.copy(),
            "recent_activities": SAMPLE_ACTIVITIES.copy(),
        },
    )


@pytest.fixture
def signal_no_activities():
    return NormalizedSignal(
        source="manual_refresh",
        entity_type="opportunity",
        entity_id="opp-opp",
        opportunity_id="opp-opp",
        tenant_id="tenant-1",
        timestamp=datetime.now(timezone.utc).isoformat(),
        data=SAMPLE_OPP.copy(),
        context={
            "opportunity": SAMPLE_OPP.copy(),
            "recent_activities": [],
        },
    )


# ── Tests: _normalize ────────────────────────────────────────────────────────

class TestNormalize:
    async def test_returns_normalized_signal(self, engine):
        signal = await engine._normalize("opp-1", "tenant-1")
        assert isinstance(signal, NormalizedSignal)

    async def test_signal_has_opportunity_id(self, engine):
        signal = await engine._normalize("opp-1", "tenant-1")
        assert signal.opportunity_id == "opp-1"

    async def test_signal_has_tenant_id(self, engine):
        signal = await engine._normalize("opp-1", "tenant-1")
        assert signal.tenant_id == "tenant-1"

    async def test_signal_source(self, engine):
        signal = await engine._normalize("opp-1", "tenant-1")
        assert signal.source == "manual_refresh"

    async def test_signal_entity_type(self, engine):
        signal = await engine._normalize("opp-1", "tenant-1")
        assert signal.entity_type == "opportunity"

    async def test_signal_data_contains_opportunity(self, engine):
        signal = await engine._normalize("opp-1", "tenant-1")
        assert signal.data.get("name") == "ERP Implementation"

    async def test_signal_context_has_activities(self, engine):
        signal = await engine._normalize("opp-1", "tenant-1")
        assert len(signal.context["recent_activities"]) == 2

    async def test_returns_none_when_not_found(self, engine):
        factory = _make_session_factory(opp=None, activities=[])

        async def __aenter__(self):
            session = AsyncMock()

            async def execute(sql_str, params=None):
                return FakeResult(FakeMappings(one=None))

            session.execute = execute
            return session

        async def __aexit__(self, *a):
            pass

        factory = MagicMock()
        factory.return_value.__aenter__ = __aenter__
        factory.return_value.__aexit__ = __aexit__
        eng = NBAEngine(session_factory=factory)
        signal = await eng._normalize("nonexistent", "tenant-1")
        assert signal is None


# ── Tests: _apply_rules ──────────────────────────────────────────────────────

class TestApplyRules:
    async def test_returns_list(self, engine, sample_signal):
        candidates = await engine._apply_rules(sample_signal)
        assert isinstance(candidates, list)

    async def test_stage_based_candidate(self, engine, sample_signal):
        candidates = await engine._apply_rules(sample_signal)
        actions = [c["action"] for c in candidates]
        assert "send_proposal" in actions

    async def test_prospecting_stage(self, engine):
        opp = {**SAMPLE_OPP, "stage": "prospecting"}
        signal = NormalizedSignal(
            source="manual_refresh", entity_type="opportunity",
            entity_id="opp-1", opportunity_id="opp-1", tenant_id="t-1",
            timestamp="", data=opp,
            context={"opportunity": opp, "recent_activities": []},
        )
        candidates = await engine._apply_rules(signal)
        assert any(c["action"] == "send_introduction_email" for c in candidates)

    async def test_negotiation_stage(self, engine):
        opp = {**SAMPLE_OPP, "stage": "negotiation"}
        signal = NormalizedSignal(
            source="manual_refresh", entity_type="opportunity",
            entity_id="opp-1", opportunity_id="opp-1", tenant_id="t-1",
            timestamp="", data=opp,
            context={"opportunity": opp, "recent_activities": []},
        )
        candidates = await engine._apply_rules(signal)
        assert any(c["action"] == "review_contract_terms" for c in candidates)

    async def test_closed_won_stage(self, engine):
        opp = {**SAMPLE_OPP, "stage": "closed_won"}
        signal = NormalizedSignal(
            source="manual_refresh", entity_type="opportunity",
            entity_id="opp-1", opportunity_id="opp-1", tenant_id="t-1",
            timestamp="", data=opp,
            context={"opportunity": opp, "recent_activities": []},
        )
        candidates = await engine._apply_rules(signal)
        assert any(c["action"] == "schedule_onboarding" for c in candidates)

    async def test_candidate_has_score(self, engine, sample_signal):
        candidates = await engine._apply_rules(sample_signal)
        for c in candidates:
            assert "score" in c
            assert isinstance(c["score"], float)

    async def test_candidate_has_rule_name(self, engine, sample_signal):
        candidates = await engine._apply_rules(sample_signal)
        for c in candidates:
            assert "rule_name" in c

    async def test_candidate_has_metadata(self, engine, sample_signal):
        candidates = await engine._apply_rules(sample_signal)
        for c in candidates:
            assert "metadata" in c

    async def test_stagnation_rule_not_triggered_with_recent_activity(self, engine, sample_signal):
        candidates = await engine._apply_rules(sample_signal)
        rule_names = [c["rule_name"] for c in candidates]
        assert "stagnation_14d" not in rule_names

    async def test_candidate_has_reason_arabic(self, engine, sample_signal):
        candidates = await engine._apply_rules(sample_signal)
        for c in candidates:
            assert len(c["reason"]) > 0


# ── Tests: _score_candidates ─────────────────────────────────────────────────

class TestScoreCandidates:
    async def test_scored_candidates_have_opportunity_score(self, engine, sample_signal):
        candidates = [{"action": "test", "reason": "r", "score": 0.8, "rule_name": "test", "metadata": {}}]
        scored = await engine._score_candidates(sample_signal, candidates)
        for c in scored:
            assert "opportunity_score" in c

    async def test_scored_candidates_have_combined_score(self, engine, sample_signal):
        candidates = [{"action": "test", "reason": "r", "score": 0.8, "rule_name": "test", "metadata": {}}]
        scored = await engine._score_candidates(sample_signal, candidates)
        for c in scored:
            assert "combined_score" in c

    async def test_combined_score_formula(self, engine, sample_signal):
        """combined_score = rule_score * 0.6 + opportunity_score * 0.4"""
        candidates = [{"action": "test", "reason": "r", "score": 1.0, "rule_name": "test", "metadata": {}}]
        scored = await engine._score_candidates(sample_signal, candidates)
        c = scored[0]
        expected = c["score"] * 0.6 + c["opportunity_score"] * 0.4
        assert abs(c["combined_score"] - expected) < 0.001

    async def test_candidates_sorted_by_combined_score_desc(self, engine, sample_signal):
        candidates = [
            {"action": "a", "reason": "r", "score": 0.5, "rule_name": "r1", "metadata": {}},
            {"action": "b", "reason": "r", "score": 0.9, "rule_name": "r2", "metadata": {}},
        ]
        scored = await engine._score_candidates(sample_signal, candidates)
        assert scored[0]["combined_score"] >= scored[1]["combined_score"]

    async def test_opportunity_score_bounded(self, engine, sample_signal):
        candidates = [{"action": "test", "reason": "r", "score": 0.8, "rule_name": "test", "metadata": {}}]
        scored = await engine._score_candidates(sample_signal, candidates)
        for c in scored:
            assert 0 <= c["opportunity_score"] <= 1

    async def test_high_value_deal_increases_opportunity_score(self, engine):
        high_value_opp = {**SAMPLE_OPP, "value": 2000000, "stage": "negotiation"}
        signal = NormalizedSignal(
            source="manual_refresh", entity_type="opportunity",
            entity_id="opp-1", opportunity_id="opp-1", tenant_id="t-1",
            timestamp="", data=high_value_opp,
            context={"opportunity": high_value_opp, "recent_activities": []},
        )
        candidates = [{"action": "test", "reason": "r", "score": 0.8, "rule_name": "test", "metadata": {}}]
        scored = await engine._score_candidates(signal, candidates)
        assert scored[0]["opportunity_score"] > 0.2


# ── Tests: _assess_risk ─────────────────────────────────────────────────────

class TestAssessRisk:
    async def test_no_activities_means_high_risk(self, engine, signal_no_activities):
        risks = await engine._assess_risk(signal_no_activities)
        assert len(risks) >= 1
        assert any(r.type == "stagnation" and r.level == "high" for r in risks)

    async def test_has_activities_no_stagnation_risk(self, engine, sample_signal):
        risks = await engine._assess_risk(sample_signal)
        stagnation_risks = [r for r in risks if r.type == "stagnation"]
        assert len(stagnation_risks) == 0

    async def test_risk_factor_fields(self, engine, signal_no_activities):
        risks = await engine._assess_risk(signal_no_activities)
        for r in risks:
            assert isinstance(r, RiskFactor)
            assert r.type
            assert r.level in ("low", "medium", "high")
            assert r.description
            assert r.detected_at


# ── Tests: _build_recommendation ────────────────────────────────────────────

class TestBuildRecommendation:
    def test_returns_nba_result(self, engine, sample_signal):
        candidates = [
            {"action": "send_proposal", "reason": "أرسل عرض السعر", "score": 0.9,
             "rule_name": "stage_proposal", "metadata": {}, "combined_score": 0.85, "opportunity_score": 0.4},
        ]
        result = engine._build_recommendation(sample_signal, candidates, None, [], {})
        assert isinstance(result, NBAResult)

    def test_top_candidate_is_action(self, engine, sample_signal):
        candidates = [
            {"action": "send_proposal", "reason": "r1", "score": 0.9,
             "rule_name": "r", "metadata": {}, "combined_score": 0.85, "opportunity_score": 0.4},
            {"action": "schedule_call", "reason": "r2", "score": 0.7,
             "rule_name": "r", "metadata": {}, "combined_score": 0.6, "opportunity_score": 0.4},
        ]
        result = engine._build_recommendation(sample_signal, candidates, None, [], {})
        assert result.action == "send_proposal"

    def test_confidence_label_high(self, engine, sample_signal):
        candidates = [
            {"action": "x", "reason": "r", "score": 1.0,
             "rule_name": "r", "metadata": {}, "combined_score": 0.85, "opportunity_score": 0.4},
        ]
        result = engine._build_recommendation(sample_signal, candidates, None, [], {})
        assert result.confidence_label == "high"

    def test_confidence_label_medium(self, engine, sample_signal):
        candidates = [
            {"action": "x", "reason": "r", "score": 0.5,
             "rule_name": "r", "metadata": {}, "combined_score": 0.6, "opportunity_score": 0.4},
        ]
        result = engine._build_recommendation(sample_signal, candidates, None, [], {})
        assert result.confidence_label == "medium"

    def test_confidence_label_low(self, engine, sample_signal):
        candidates = [
            {"action": "x", "reason": "r", "score": 0.3,
             "rule_name": "r", "metadata": {}, "combined_score": 0.3, "opportunity_score": 0.1},
        ]
        result = engine._build_recommendation(sample_signal, candidates, None, [], {})
        assert result.confidence_label == "low"

    def test_no_candidates_returns_no_action(self, engine, sample_signal):
        result = engine._build_recommendation(sample_signal, [], None, [], {})
        assert result.action == "no_action_needed"
        assert result.confidence == 0.0

    def test_has_evidence(self, engine, sample_signal):
        candidates = [
            {"action": "x", "reason": "r", "score": 0.8,
             "rule_name": "r", "metadata": {}, "combined_score": 0.7, "opportunity_score": 0.4},
        ]
        result = engine._build_recommendation(sample_signal, candidates, None, [], {})
        assert len(result.evidence) >= 1
        assert isinstance(result.evidence[0], Evidence)

    def test_has_alternatives(self, engine, sample_signal):
        candidates = [
            {"action": "a", "reason": "r1", "score": 0.9,
             "rule_name": "r", "metadata": {}, "combined_score": 0.85, "opportunity_score": 0.4},
            {"action": "b", "reason": "r2", "score": 0.7,
             "rule_name": "r", "metadata": {}, "combined_score": 0.6, "opportunity_score": 0.4},
        ]
        result = engine._build_recommendation(sample_signal, candidates, None, [], {})
        assert len(result.alternatives) >= 1
        assert isinstance(result.alternatives[0], Alternative)

    def test_risks_included(self, engine, sample_signal):
        risks = [RiskFactor(type="stagnation", level="high", description="test", detected_at="now")]
        candidates = [
            {"action": "x", "reason": "r", "score": 0.8,
             "rule_name": "r", "metadata": {}, "combined_score": 0.7, "opportunity_score": 0.4},
        ]
        result = engine._build_recommendation(sample_signal, candidates, None, risks, {})
        assert len(result.potential_risks) == 1

    def test_revenue_category_for_proposal(self, engine, sample_signal):
        candidates = [
            {"action": "send_proposal", "reason": "r", "score": 0.9,
             "rule_name": "r", "metadata": {}, "combined_score": 0.85, "opportunity_score": 0.4},
        ]
        result = engine._build_recommendation(sample_signal, candidates, None, [], {})
        assert result.expected_impact.category == "revenue"

    def test_opportunity_id_set(self, engine, sample_signal):
        candidates = [
            {"action": "x", "reason": "r", "score": 0.8,
             "rule_name": "r", "metadata": {}, "combined_score": 0.7, "opportunity_score": 0.4},
        ]
        result = engine._build_recommendation(sample_signal, candidates, None, [], {})
        assert result.opportunity_id == "opp-1"


# ── Tests: recompute (full pipeline) ────────────────────────────────────────

class TestRecompute:
    async def test_returns_nba_result(self, engine):
        result = await engine.recompute("opp-1", "tenant-1")
        assert isinstance(result, NBAResult)

    async def test_result_has_all_fields(self, engine):
        result = await engine.recompute("opp-1", "tenant-1")
        assert result.id
        assert result.opportunity_id
        assert result.action
        assert result.reason
        assert isinstance(result.confidence, float)
        assert result.confidence_label in ("high", "medium", "low")
        assert result.source in ("rule", "ai", "hybrid")
        assert isinstance(result.evidence, list)
        assert isinstance(result.alternatives, list)
        assert isinstance(result.potential_risks, list)
        assert result.created_at
        assert result.updated_at

    async def test_pipeline_trace_recorded(self, engine):
        result = await engine.recompute("opp-1", "tenant-1")
        assert result.pipeline_trace is not None
        assert "total_ms" in result.pipeline_trace
        assert "normalization_ms" in result.pipeline_trace
        assert "rules_ms" in result.pipeline_trace
        assert "scoring_ms" in result.pipeline_trace

    async def test_confidence_bounded(self, engine):
        result = await engine.recompute("opp-1", "tenant-1")
        assert 0 <= result.confidence <= 1

    async def test_expected_impact_exists(self, engine):
        result = await engine.recompute("opp-1", "tenant-1")
        assert result.expected_impact is not None
        assert isinstance(result.expected_impact, Impact)


# ── Tests: dataclass types ──────────────────────────────────────────────────

class TestDataclasses:
    def test_normalized_signal_defaults(self):
        ns = NormalizedSignal(source="s", entity_type="t", entity_id="e")
        assert ns.opportunity_id is None
        assert ns.tenant_id == ""
        assert ns.data == {}
        assert ns.context == {}

    def test_risk_factor_dataclass(self):
        rf = RiskFactor(type="test", level="low", description="desc", detected_at="now")
        assert rf.type == "test"
        assert rf.level == "low"

    def test_impact_defaults(self):
        imp = Impact(description="test")
        assert imp.estimated_revenue is None
        assert imp.category == "information_gathering"

    def test_evidence_dataclass(self):
        ev = Evidence(id="1", type="signal", description="d", source="s", confidence=0.8, timestamp="now")
        assert ev.confidence == 0.8

    def test_alternative_dataclass(self):
        alt = Alternative(action="a", reason="r", confidence=0.9)
        assert alt.action == "a"
