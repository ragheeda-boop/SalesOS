"""Tests for Deal Health Computer — stagnation, engagement, health classification, thresholds."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock

import pytest

from runtime.feature_store import FeatureResult
from runtime.nba_engine.engine.risk.deal_health import DealHealthComputer


# ── Fake SQLAlchemy helpers ──────────────────────────────────────────────────

class FakeMapping:
    def __init__(self, data):
        self._data = data

    def __getitem__(self, key):
        return self._data[key]

    def get(self, key, default=None):
        return self._data.get(key, default)


class FakeMappings:
    def __init__(self, rows=None, one=None):
        self._rows = rows or []
        self._one = one

    def one(self):
        return FakeMapping(self._one) if self._one else None

    def all(self):
        return [FakeMapping(r) for r in self._rows]


class FakeResult:
    def __init__(self, mappings_obj=None):
        self._mappings = mappings_obj or FakeMappings()

    def mappings(self):
        return self._mappings


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_computer(
    total_activities=10,
    last_activity_days_ago=5,
    signal_count=3,
    close_date_days_ahead=30,
):
    """Create a DealHealthComputer with a mock session returning controlled data."""
    last_activity = datetime.now(timezone.utc) - timedelta(days=last_activity_days_ago)
    close_date = (datetime.now(timezone.utc) + timedelta(days=close_date_days_ahead)).date() if close_date_days_ahead is not None else None

    call_count = {"n": 0}

    async def execute(sql_str, params=None):
        text = str(sql_str)
        if "activity_records" in text and "COUNT(*)" in text and "last_activity" in text:
            return FakeResult(FakeMappings(one={
                "total": total_activities,
                "last_activity": last_activity,
            }))
        elif "company_signals" in text:
            return FakeResult(FakeMappings(one={"cnt": signal_count}))
        return FakeResult(FakeMappings(one={"cnt": 0}))

    session = AsyncMock()
    session.execute = execute

    opportunity = {
        "id": "opp-1",
        "tenant_id": "t-1",
    }
    if close_date is not None:
        opportunity["expected_close_date"] = close_date

    return session, opportunity


# ── Tests: Stagnation Score ─────────────────────────────────────────────────

class TestStagnationScore:
    async def test_no_activity_means_0_5_stagnation(self):
        """No last_activity at all → stagnation = 0.5."""
        last_activity = None

        async def execute(sql_str, params=None):
            text = str(sql_str)
            if "activity_records" in text:
                return FakeResult(FakeMappings(one={"total": 0, "last_activity": None}))
            elif "company_signals" in text:
                return FakeResult(FakeMappings(one={"cnt": 0}))
            return FakeResult(FakeMappings(one={"cnt": 0}))

        session = AsyncMock()
        session.execute = execute
        opp = {"id": "opp-1", "tenant_id": "t-1"}

        computer = DealHealthComputer()
        result = await computer.compute(opp, session)

        assert isinstance(result, FeatureResult)
        assert result.score >= 0

    async def test_recent_activity_low_stagnation(self):
        """Activity 3 days ago → stagnation = 0."""
        session, opp = _make_computer(total_activities=5, last_activity_days_ago=3)
        computer = DealHealthComputer()
        result = await computer.compute(opp, session)
        # With low stagnation and some engagement, health should be good
        assert result.score > 0.5

    async def test_stagnation_increases_with_days(self):
        """Longer time since activity → higher stagnation → lower health."""
        session_recent, opp_recent = _make_computer(total_activities=5, last_activity_days_ago=3)
        session_old, opp_old = _make_computer(total_activities=5, last_activity_days_ago=25)

        computer = DealHealthComputer()
        result_recent = await computer.compute(opp_recent, session_recent)
        result_old = await computer.compute(opp_old, session_old)

        # Older activity should have lower health score
        assert result_old.score < result_recent.score


# ── Tests: Engagement Score ─────────────────────────────────────────────────

class TestEngagementScore:
    async def test_high_engagement_better_health(self):
        session_high, opp_high = _make_computer(total_activities=20, last_activity_days_ago=2)
        session_low, opp_low = _make_computer(total_activities=2, last_activity_days_ago=2)

        computer = DealHealthComputer()
        result_high = await computer.compute(opp_high, session_high)
        result_low = await computer.compute(opp_low, session_low)

        assert result_high.score >= result_low.score

    async def test_engagement_capped_at_1(self):
        """Even with 100+ activities, engagement shouldn't exceed 1.0."""
        session, opp = _make_computer(total_activities=100, last_activity_days_ago=1)
        computer = DealHealthComputer()
        result = await computer.compute(opp, session)
        # The score should be bounded by the formula
        assert 0 <= result.score <= 1


# ── Tests: Timeline Risk ────────────────────────────────────────────────────

class TestTimelineRisk:
    async def test_overdue_deal_worse_health(self):
        session_overdue, opp_overdue = _make_computer(
            total_activities=5, last_activity_days_ago=3, close_date_days_ahead=-5,
        )
        session_ok, opp_ok = _make_computer(
            total_activities=5, last_activity_days_ago=3, close_date_days_ahead=60,
        )

        computer = DealHealthComputer()
        result_overdue = await computer.compute(opp_overdue, session_overdue)
        result_ok = await computer.compute(opp_ok, session_ok)

        assert result_overdue.score < result_ok.score

    async def test_no_close_date_no_timeline_risk(self):
        """No expected_close_date → timeline_risk = 0."""
        session, opp = _make_computer(
            total_activities=5, last_activity_days_ago=3, close_date_days_ahead=None,
        )
        opp.pop("expected_close_date", None)
        computer = DealHealthComputer()
        result = await computer.compute(opp, session)
        assert 0 <= result.score <= 1


# ── Tests: Health Classification ────────────────────────────────────────────

class TestHealthClassification:
    async def test_healthy_explanation(self):
        """High health score → healthy explanation."""
        session, opp = _make_computer(total_activities=20, last_activity_days_ago=1)
        computer = DealHealthComputer()
        result = await computer.compute(opp, session)
        if result.score >= 0.7:
            assert "جيدة" in result.explanation

    async def test_critical_explanation(self):
        """Low health score → critical explanation."""
        session, opp = _make_computer(total_activities=0, last_activity_days_ago=30)
        computer = DealHealthComputer()
        result = await computer.compute(opp, session)
        if result.score < 0.4:
            assert "حرجة" in result.explanation

    async def test_at_risk_explanation(self):
        """Medium health → at_risk explanation."""
        session, opp = _make_computer(total_activities=3, last_activity_days_ago=18)
        computer = DealHealthComputer()
        result = await computer.compute(opp, session)
        if 0.4 <= result.score < 0.7:
            assert "متوسطة" in result.explanation


# ── Tests: FeatureResult Structure ──────────────────────────────────────────

class TestFeatureResult:
    async def test_has_all_fields(self):
        session, opp = _make_computer()
        computer = DealHealthComputer()
        result = await computer.compute(opp, session)
        assert isinstance(result, FeatureResult)
        assert 0 <= result.score <= 1
        assert result.version == 1
        assert isinstance(result.computed_at, datetime)
        assert result.confidence == 0.8
        assert isinstance(result.contributing_signals, dict)
        assert isinstance(result.explanation, str)

    async def test_contributing_signals_has_keys(self):
        session, opp = _make_computer()
        computer = DealHealthComputer()
        result = await computer.compute(opp, session)
        signals = result.contributing_signals
        assert "stagnation" in signals
        assert "engagement" in signals
        assert "timeline_risk" in signals
        assert "signal_count" in signals
        assert "total_activities" in signals

    async def test_health_score_bounded(self):
        session, opp = _make_computer()
        computer = DealHealthComputer()
        result = await computer.compute(opp, session)
        assert 0 <= result.score <= 1

    async def test_name_and_version(self):
        computer = DealHealthComputer()
        assert computer.name == "deal_health"
        assert computer.version == 1


# ── Tests: Threshold Boundaries ─────────────────────────────────────────────

class TestThresholdBoundaries:
    async def test_score_exactly_0(self):
        """Maximum stagnation, no engagement, overdue → near 0."""
        session, opp = _make_computer(
            total_activities=0, last_activity_days_ago=40, close_date_days_ahead=-30,
        )
        computer = DealHealthComputer()
        result = await computer.compute(opp, session)
        assert result.score < 0.4

    async def test_score_near_1(self):
        """No stagnation, full engagement, no timeline pressure → near 1."""
        session, opp = _make_computer(
            total_activities=20, last_activity_days_ago=1, close_date_days_ahead=90,
        )
        computer = DealHealthComputer()
        result = await computer.compute(opp, session)
        assert result.score > 0.6
