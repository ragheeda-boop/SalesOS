"""Unit tests for signal_actions/priority.py — pure logic, no DB."""

from datetime import UTC, datetime, timedelta

import pytest

from app.modules.signal_actions.models import (
    ActionType,
    ActionUrgency,
    IntentLevel,
    SignalPriority,
    SignalQualification,
)
from app.modules.signal_actions.priority import _crm_boost, _recommend_action, _recency_weight, score_account


def _make_qual(
    signal_type: str = "funding",
    score: float = 80.0,
    priority: SignalPriority = SignalPriority.HIGH,
    days_ago: int = 0,
) -> SignalQualification:
    return SignalQualification(
        signal_id=f"sig-{signal_type}",
        company_name="TestCo",
        signal_type=signal_type,
        raw_confidence="high",
        priority=priority,
        priority_score=score,
        intent_contribution=score * 0.8,
        qualified_at=datetime.now(UTC) - timedelta(days=days_ago),
    )


# ── _recency_weight ──────────────────────────────────────────────

class TestRecencyWeight:
    def test_today(self):
        now = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
        assert _recency_weight(now, now) == 1.0

    def test_3_days(self):
        now = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
        assert _recency_weight(now - timedelta(days=3), now) == 0.9

    def test_14_days(self):
        now = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
        assert _recency_weight(now - timedelta(days=14), now) == 0.7

    def test_45_days(self):
        now = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
        assert _recency_weight(now - timedelta(days=45), now) == 0.5

    def test_90_days(self):
        now = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
        assert _recency_weight(now - timedelta(days=90), now) == 0.3


# ── _crm_boost ───────────────────────────────────────────────────

class TestCrmBoost:
    def test_empty_crm(self):
        assert _crm_boost({}) == 0.0

    def test_has_opportunity(self):
        assert _crm_boost({"has_opportunity": True}) == 10.0

    def test_recent_activity_7d(self):
        assert _crm_boost({"last_activity_days": 3}) == 8.0

    def test_recent_activity_30d(self):
        assert _crm_boost({"last_activity_days": 20}) == 5.0

    def test_recent_activity_90d(self):
        assert _crm_boost({"last_activity_days": 60}) == 2.0

    def test_old_activity(self):
        assert _crm_boost({"last_activity_days": 200}) == 0.0

    def test_enterprise_employees(self):
        assert _crm_boost({"employee_count": 1000}) == 5.0

    def test_midmarket_employees(self):
        assert _crm_boost({"employee_count": 100}) == 3.0

    def test_small_employees(self):
        assert _crm_boost({"employee_count": 10}) == 0.0

    def test_combined_boost_capped_at_20(self):
        crm = {
            "has_opportunity": True,
            "last_activity_days": 3,
            "employee_count": 1000,
        }
        assert _crm_boost(crm) == 20.0

    def test_opportunity_plus_activity(self):
        crm = {"has_opportunity": True, "last_activity_days": 30}
        assert _crm_boost(crm) == 15.0


# ── _recommend_action ────────────────────────────────────────────

class TestRecommendAction:
    def test_critical_with_opportunity(self):
        action, urgency = _recommend_action(
            IntentLevel.HIGH, critical=2, high=1, signal_count=6,
            crm={"has_opportunity": True},
        )
        assert action == ActionType.FOLLOW_UP
        assert urgency == ActionUrgency.IMMEDIATE

    def test_critical_without_opportunity(self):
        action, urgency = _recommend_action(
            IntentLevel.HIGH, critical=2, high=1, signal_count=6,
            crm={},
        )
        assert action == ActionType.CALL
        assert urgency == ActionUrgency.IMMEDIATE

    def test_single_critical_many_signals(self):
        action, urgency = _recommend_action(
            IntentLevel.HIGH, critical=1, high=2, signal_count=6,
            crm={},
        )
        assert action == ActionType.MEETING
        assert urgency == ActionUrgency.TODAY

    def test_single_critical_few_signals(self):
        action, urgency = _recommend_action(
            IntentLevel.MEDIUM, critical=1, high=0, signal_count=3,
            crm={},
        )
        assert action == ActionType.EMAIL
        assert urgency == ActionUrgency.TODAY

    def test_high_intent_no_opportunity(self):
        action, urgency = _recommend_action(
            IntentLevel.HIGH, critical=0, high=1, signal_count=3,
            crm={"has_opportunity": False},
        )
        assert action == ActionType.CREATE_OPPORTUNITY
        assert urgency == ActionUrgency.THIS_WEEK

    def test_high_intent_with_opportunity(self):
        action, urgency = _recommend_action(
            IntentLevel.HIGH, critical=0, high=1, signal_count=3,
            crm={"has_opportunity": True},
        )
        assert action == ActionType.PROPOSAL
        assert urgency == ActionUrgency.THIS_WEEK

    def test_medium_intent_many_signals(self):
        action, urgency = _recommend_action(
            IntentLevel.MEDIUM, critical=0, high=0, signal_count=5,
            crm={},
        )
        assert action == ActionType.RESEARCH
        assert urgency == ActionUrgency.THIS_WEEK

    def test_medium_intent_few_signals(self):
        action, urgency = _recommend_action(
            IntentLevel.MEDIUM, critical=0, high=0, signal_count=2,
            crm={},
        )
        assert action == ActionType.EMAIL
        assert urgency == ActionUrgency.NEXT_WEEK

    def test_low_intent(self):
        action, urgency = _recommend_action(
            IntentLevel.LOW, critical=0, high=0, signal_count=1,
            crm={},
        )
        assert action == ActionType.RESEARCH
        assert urgency == ActionUrgency.MONITOR

    def test_unknown_intent(self):
        action, urgency = _recommend_action(
            IntentLevel.UNKNOWN, critical=0, high=0, signal_count=0,
            crm={},
        )
        assert action == ActionType.NO_ACTION
        assert urgency == ActionUrgency.MONITOR

    def test_very_high_no_opportunity(self):
        action, urgency = _recommend_action(
            IntentLevel.VERY_HIGH, critical=0, high=3, signal_count=5,
            crm={"has_opportunity": False},
        )
        assert action == ActionType.CREATE_OPPORTUNITY
        assert urgency == ActionUrgency.THIS_WEEK

    def test_very_high_with_opportunity(self):
        action, urgency = _recommend_action(
            IntentLevel.VERY_HIGH, critical=0, high=3, signal_count=5,
            crm={"has_opportunity": True},
        )
        assert action == ActionType.PROPOSAL
        assert urgency == ActionUrgency.THIS_WEEK


# ── score_account ────────────────────────────────────────────────

class TestScoreAccount:
    def test_no_signals(self):
        result = score_account("EmptyCo", "t1", [])
        assert result.intent_level == IntentLevel.UNKNOWN
        assert result.signal_count == 0
        assert result.recommended_action == ActionType.NO_ACTION

    def test_single_critical_signal(self):
        quals = [_make_qual("funding", 90.0, SignalPriority.CRITICAL)]
        result = score_account("Acme", "t1", quals)
        assert result.signal_count == 1
        assert result.critical_signals == 1
        assert result.recommended_action in (ActionType.CALL, ActionType.EMAIL, ActionType.MEETING)

    def test_diversity_score(self):
        quals = [
            _make_qual("funding", 80.0, SignalPriority.HIGH),
            _make_qual("hiring", 70.0, SignalPriority.HIGH),
            _make_qual("expansion", 60.0, SignalPriority.MEDIUM),
        ]
        result = score_account("MultiCo", "t1", quals)
        assert result.diversity_score > 0
        assert len(result.top_signal_types) >= 1

    def test_crm_boosts_score(self):
        quals = [_make_qual("funding", 70.0, SignalPriority.HIGH)]
        base = score_account("X", "t1", quals)
        boosted = score_account("X", "t1", quals, crm_data={"has_opportunity": True})
        assert boosted.intent_score >= base.intent_score

    def test_score_never_exceeds_100(self):
        quals = [_make_qual("funding", 100.0, SignalPriority.CRITICAL) for _ in range(10)]
        result = score_account("MaxCo", "t1", quals)
        assert result.intent_score <= 100.0

    def test_metadata_contains_crm_boost(self):
        result = score_account("X", "t1", [_make_qual()], crm_data={"has_opportunity": True})
        assert result.metadata["crm_boost"] > 0

    def test_tenant_id_populated(self):
        result = score_account("X", "my-tenant", [_make_qual()])
        assert result.tenant_id == "my-tenant"
