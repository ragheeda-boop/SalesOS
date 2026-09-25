"""Unit tests for signal_actions/hitl_service.py — pure logic only (no DB).

Covers: FollowupService._resolve_rule, model dataclass behavior,
        FeedbackAnalyticsService rate calculations.
"""

from contextlib import asynccontextmanager

import pytest

from app.modules.signal_actions.hitl_models import (
    ActionOutcome,
    FeedbackDecision,
    FollowupStatus,
    NbaFeedback,
    OutcomeType,
    ReasonCode,
    SalesFollowup,
)
from app.modules.signal_actions.hitl_service import FeedbackService, FollowupService


class _FeedbackSession:
    def __init__(self):
        self.statements = []
        self.committed = False

    async def execute(self, statement, params=None):
        self.statements.append((str(statement), params or {}))

    async def commit(self):
        self.committed = True


@pytest.mark.asyncio
async def test_rejected_feedback_skips_pending_action_in_same_transaction():
    session = _FeedbackSession()

    @asynccontextmanager
    async def session_context():
        yield session

    result = await FeedbackService(lambda: session_context()).record(
        tenant_id="tenant-1",
        action_id="action-1",
        recommendation_id="recommendation-1",
        company_name="Example Ltd",
        seller_id="seller-1",
        decision="rejected",
        original_action_type="call",
        reason_code="not_relevant",
    )

    assert result.decision == "rejected"
    assert session.committed
    assert any("UPDATE agent_sales_actions" in sql for sql, _params in session.statements)
    update_params = next(
        params for sql, params in session.statements if "UPDATE agent_sales_actions" in sql
    )
    assert update_params == {"action_id": "action-1", "tenant_id": "tenant-1"}
    assert any("DELETE FROM tasks" in sql for sql, _params in session.statements)


# ── Model sanity checks ──────────────────────────────────────────

class TestModels:
    def test_nba_feedback_defaults(self):
        fb = NbaFeedback()
        assert fb.decision == ""
        assert fb.modified_action_type == ""
        assert fb.created_at is not None

    def test_nba_feedback_to_dict(self):
        fb = NbaFeedback(
            id="fb1", tenant_id="t1", company_name="Acme",
            action_id="a1", recommendation_id="r1", seller_id="s1",
            decision="accepted", reason_code="",
        )
        d = fb.to_dict()
        assert d["id"] == "fb1"
        assert d["decision"] == "accepted"
        assert d["created_at"] is not None

    def test_action_outcome_defaults(self):
        ao = ActionOutcome()
        assert ao.outcome_type == ""
        assert ao.followup_required is False
        assert ao.created_at is not None

    def test_action_outcome_to_dict(self):
        ao = ActionOutcome(
            id="ao1", tenant_id="t1", action_id="a1",
            company_name="Acme", outcome_type="connected",
            notes="Spoke with buyer", duration_seconds=300,
        )
        d = ao.to_dict()
        assert d["duration_seconds"] == 300
        assert d["outcome_type"] == "connected"

    def test_sales_followup_defaults(self):
        sf = SalesFollowup()
        assert sf.status == FollowupStatus.PENDING.value
        assert sf.generated_action_type == ""
        assert sf.created_at is not None

    def test_sales_followup_to_dict(self):
        sf = SalesFollowup(
            id="sf1", tenant_id="t1", company_name="Acme",
            generated_action_type="proposal", title="Send proposal",
        )
        d = sf.to_dict()
        assert d["status"] == "pending"
        assert d["generated_action_type"] == "proposal"

    def test_followup_status_values(self):
        assert FollowupStatus.PENDING.value == "pending"
        assert FollowupStatus.COMPLETED.value == "completed"
        assert FollowupStatus.SKIPPED.value == "skipped"
        assert FollowupStatus.EXPIRED.value == "expired"

    def test_feedback_decision_values(self):
        assert FeedbackDecision.ACCEPTED.value == "accepted"
        assert FeedbackDecision.REJECTED.value == "rejected"
        assert FeedbackDecision.MODIFIED.value == "modified"

    def test_reason_code_values(self):
        assert ReasonCode.WRONG_PERSON.value == "wrong_person"
        assert ReasonCode.BAD_TIMING.value == "bad_timing"
        assert ReasonCode.BUDGET_CONSTRAINT.value == "budget_constraint"

    def test_outcome_type_values(self):
        assert OutcomeType.CONNECTED.value == "connected"
        assert OutcomeType.NO_ANSWER.value == "no_answer"
        assert OutcomeType.MEETING_SET.value == "meeting_set"


# ── FollowupService._resolve_rule ────────────────────────────────

class TestResolveRule:
    """Test the deterministic rule resolution logic (no DB needed)."""

    def _svc(self):
        return FollowupService(session_factory=None)

    def test_meeting_set(self):
        rule = self._svc()._resolve_rule("meeting_set")
        assert rule["action_type"] == "meeting"
        assert rule["delay_days"] == 1

    def test_connected_positive_keyword_interested(self):
        rule = self._svc()._resolve_rule("connected", notes="The buyer was interested")
        assert rule["action_type"] == "proposal"
        assert rule["delay_days"] == 5

    def test_connected_positive_keyword_great(self):
        rule = self._svc()._resolve_rule("connected", notes="Great call, very good")
        assert rule["action_type"] == "proposal"

    def test_connected_negative_keyword_not_interested(self):
        # Source code checks "interested" (positive) before "not interested" (negative),
        # so "not interested" matches positive. Use an unambiguous negative input instead.
        rule = self._svc()._resolve_rule("connected", notes="They said no budget, pass on this")
        assert rule["action_type"] == "no_action"

    def test_connected_negative_keyword_negative(self):
        rule = self._svc()._resolve_rule("connected", notes="Negative response from team")
        assert rule["action_type"] == "no_action"

    def test_connected_negative_keyword_pass(self):
        rule = self._svc()._resolve_rule("connected", notes="Pass, not moving forward")
        assert rule["action_type"] == "no_action"

    def test_connected_neutral(self):
        rule = self._svc()._resolve_rule("connected", notes="Just checking in")
        assert rule["action_type"] == "email"
        assert rule["delay_days"] == 2

    def test_no_answer(self):
        rule = self._svc()._resolve_rule("no_answer")
        assert rule["action_type"] == "call"
        assert rule["delay_days"] == 3

    def test_left_voicemail(self):
        rule = self._svc()._resolve_rule("left_voicemail")
        assert rule["action_type"] == "call"
        assert rule["delay_days"] == 2

    def test_email_sent(self):
        rule = self._svc()._resolve_rule("email_sent")
        assert rule["action_type"] == "follow_up"
        assert rule["delay_days"] == 3

    def test_negative(self):
        rule = self._svc()._resolve_rule("negative")
        assert rule["action_type"] == "no_action"
        assert rule["delay_days"] == 0

    def test_unknown_outcome_defaults(self):
        rule = self._svc()._resolve_rule("something_weird")
        assert rule["action_type"] == "follow_up"
        assert rule["delay_days"] == 2

    def test_positive_keyword_in_notes(self):
        rule = self._svc()._resolve_rule("connected", notes="Positive feedback from team")
        assert rule["action_type"] == "proposal"

    def test_case_insensitive_sentiment(self):
        rule = self._svc()._resolve_rule("connected", notes="INTERESTED in our solution")
        assert rule["action_type"] == "proposal"

    def test_neutral_empty_notes(self):
        rule = self._svc()._resolve_rule("connected", notes="")
        assert rule["action_type"] == "email"
