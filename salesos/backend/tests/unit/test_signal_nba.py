"""Unit tests for signal_actions/nba.py — pure logic, no DB."""

from datetime import UTC, datetime, timedelta

import pytest

from app.modules.signal_actions.models import (
    AccountPriority,
    ActionType,
    ActionUrgency,
    IntentLevel,
    SignalPriority,
    SignalQualification,
)
from app.modules.signal_actions.nba import _action_content, _expiry, generate_nba


def _make_qual(signal_type: str, score: float, priority: SignalPriority = SignalPriority.HIGH) -> SignalQualification:
    return SignalQualification(
        signal_id=f"sig-{signal_type}",
        company_name="TestCo",
        signal_type=signal_type,
        raw_confidence="high",
        priority=priority,
        priority_score=score,
        intent_contribution=score * 0.8,
        qualified_at=datetime.now(UTC),
    )


def _make_priority(
    action: ActionType = ActionType.EMAIL,
    urgency: ActionUrgency = ActionUrgency.THIS_WEEK,
    intent_level: IntentLevel = IntentLevel.HIGH,
    intent_score: float = 65.0,
    critical: int = 0,
    high: int = 1,
    signal_count: int = 3,
) -> AccountPriority:
    return AccountPriority(
        company_name="TestCo",
        tenant_id="t1",
        intent_level=intent_level,
        intent_score=intent_score,
        signal_count=signal_count,
        critical_signals=critical,
        high_signals=high,
        recommended_action=action,
        action_urgency=urgency,
    )


# ── _expiry ──────────────────────────────────────────────────────

class TestExpiry:
    def test_immediate(self):
        result = _expiry("immediate")
        now = datetime.now(UTC)
        delta = result - now
        assert timedelta(hours=3) <= delta <= timedelta(hours=5)

    def test_today(self):
        result = _expiry("today")
        now = datetime.now(UTC)
        delta = result - now
        assert timedelta(hours=23) <= delta <= timedelta(hours=25)

    def test_this_week(self):
        result = _expiry("this_week")
        now = datetime.now(UTC)
        delta = result - now
        assert timedelta(days=6) <= delta <= timedelta(days=8)

    def test_next_week(self):
        result = _expiry("next_week")
        now = datetime.now(UTC)
        delta = result - now
        assert timedelta(days=13) <= delta <= timedelta(days=15)

    def test_unknown_urgency(self):
        result = _expiry("bogus")
        now = datetime.now(UTC)
        delta = result - now
        assert timedelta(days=29) <= delta <= timedelta(days=31)


# ── _action_content ──────────────────────────────────────────────

class TestActionContent:
    def test_call(self):
        t, d, ch, m = _action_content(ActionType.CALL, "Acme", [_make_qual("funding", 90)], IntentLevel.HIGH)
        assert "Acme" in t
        assert "Call" in t
        assert ch == "phone"
        assert "Acme" in m

    def test_email(self):
        t, d, ch, m = _action_content(ActionType.EMAIL, "Bco", [_make_qual("hiring", 70)], IntentLevel.MEDIUM)
        assert "Bco" in t
        assert ch == "email"
        assert "Subject:" in m

    def test_whatsapp(self):
        t, d, ch, m = _action_content(ActionType.WHATSAPP, "Cco", [_make_qual("expansion", 60)], IntentLevel.HIGH)
        assert "Cco" in t
        assert ch == "whatsapp"

    def test_create_opportunity(self):
        t, d, ch, m = _action_content(ActionType.CREATE_OPPORTUNITY, "Dco", [_make_qual("funding", 90)], IntentLevel.VERY_HIGH)
        assert "Dco" in t
        assert ch == "internal"

    def test_proposal(self):
        t, d, ch, m = _action_content(ActionType.PROPOSAL, "Eco", [_make_qual("funding", 95)], IntentLevel.VERY_HIGH)
        assert "Eco" in t
        assert ch == "internal"

    def test_follow_up(self):
        t, d, ch, m = _action_content(ActionType.FOLLOW_UP, "Fco", [_make_qual("funding", 95)], IntentLevel.VERY_HIGH)
        assert "Fco" in t

    def test_meeting(self):
        t, d, ch, m = _action_content(ActionType.MEETING, "Gco", [_make_qual("hiring", 80)], IntentLevel.HIGH)
        assert "Gco" in t

    def test_research(self):
        t, d, ch, m = _action_content(ActionType.RESEARCH, "Hco", [_make_qual("product", 40)], IntentLevel.MEDIUM)
        assert "Hco" in t

    def test_create_task(self):
        t, d, ch, m = _action_content(ActionType.CREATE_TASK, "Ico", [_make_qual("hiring", 50)], IntentLevel.LOW)
        assert "Ico" in t

    def test_no_action_fallback(self):
        t, d, ch, m = _action_content(ActionType.NO_ACTION, "Jco", [], IntentLevel.UNKNOWN)
        assert "Monitor" in t
        assert ch == ""

    def test_empty_signals(self):
        t, d, ch, m = _action_content(ActionType.CALL, "Kco", [], IntentLevel.HIGH)
        assert "Kco" in t


# ── generate_nba ─────────────────────────────────────────────────

class TestGenerateNba:
    def test_basic_nba_structure(self):
        priority = _make_priority(intent_score=70.0)
        quals = [_make_qual("funding", 85.0, SignalPriority.CRITICAL)]
        nba = generate_nba(priority, quals)
        assert nba.company_name == "TestCo"
        assert nba.tenant_id == "t1"
        assert nba.action_type == ActionType.EMAIL
        assert nba.title
        assert nba.description
        assert nba.rationale

    def test_top_3_signals_in_rationale(self):
        priority = _make_priority()
        quals = [_make_qual(f"type{i}", 50 + i * 10) for i in range(5)]
        nba = generate_nba(priority, quals)
        assert "signals=[" in nba.rationale

    def test_signal_ids_extracted(self):
        priority = _make_priority()
        quals = [_make_qual("funding", 85.0), _make_qual("hiring", 70.0)]
        nba = generate_nba(priority, quals)
        assert len(nba.signal_ids) >= 1

    def test_confidence_capped_at_1(self):
        priority = _make_priority(intent_score=150.0)
        nba = generate_nba(priority, [_make_qual("funding", 90.0)])
        assert nba.confidence <= 1.0

    def test_metadata_populated(self):
        priority = _make_priority(signal_count=7)
        nba = generate_nba(priority, [_make_qual("funding", 90.0)])
        assert nba.metadata["signal_count"] == 7
        assert "intent_score" in nba.metadata

    def test_expires_at_set(self):
        priority = _make_priority(urgency=ActionUrgency.IMMEDIATE)
        nba = generate_nba(priority, [_make_qual("funding", 90.0)])
        assert nba.expires_at is not None
        assert nba.expires_at > datetime.now(UTC)

    def test_follow_up_action_for_critical_with_opportunity(self):
        priority = _make_priority(
            action=ActionType.FOLLOW_UP, urgency=ActionUrgency.IMMEDIATE,
            critical=2, signal_count=6,
        )
        nba = generate_nba(priority, [_make_qual("funding", 90.0, SignalPriority.CRITICAL)])
        assert nba.action_type == ActionType.FOLLOW_UP
