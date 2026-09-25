"""HITL records must use the authenticated seller identity, not body fields."""

import pytest

from app.modules.signal_actions import hitl_router
from app.modules.signal_actions.hitl_models import ActionOutcome, NbaFeedback


class _NoopEffectiveness:
    async def record_feedback_event(self, *_args, **_kwargs):
        return None

    async def record_outcome_event(self, *_args, **_kwargs):
        return None

    async def record_event(self, *_args, **_kwargs):
        return None


@pytest.mark.asyncio
async def test_feedback_seller_comes_from_authenticated_identity(monkeypatch):
    captured = {}

    class FeedbackStub:
        async def record(self, **kwargs):
            captured.update(kwargs)
            return NbaFeedback(**kwargs)

    monkeypatch.setattr(hitl_router, "_fb_svc", FeedbackStub())
    monkeypatch.setattr(hitl_router, "_eff_svc", _NoopEffectiveness())
    body = hitl_router.FeedbackRequest(
        action_id="action-1",
        recommendation_id="recommendation-1",
        company_name="Synthetic Test Company",
        seller_id="spoofed-user",
        decision="rejected",
        reason_code="not_relevant",
        original_action_type="call",
    )

    result = await hitl_router.record_feedback(
        body,
        tenant_id="tenant-1",
        current_user_id="authenticated-user",
        _rbac=None,
    )

    assert captured["seller_id"] == "authenticated-user"
    assert result["seller_id"] == "authenticated-user"


@pytest.mark.asyncio
async def test_outcome_seller_comes_from_authenticated_identity(monkeypatch):
    captured = {}

    class OutcomeStub:
        async def record(self, **kwargs):
            captured.update(kwargs)
            return ActionOutcome(**kwargs)

    class FollowupStub:
        async def generate(self, *_args, **_kwargs):
            return None

    monkeypatch.setattr(hitl_router, "_out_svc", OutcomeStub())
    monkeypatch.setattr(hitl_router, "_fu_svc", FollowupStub())
    monkeypatch.setattr(hitl_router, "_eff_svc", _NoopEffectiveness())
    body = hitl_router.OutcomeRequest(
        action_id="action-1",
        company_name="Synthetic Test Company",
        seller_id="spoofed-user",
        outcome_type="connected",
        idempotency_key="retry-key-1",
    )

    result = await hitl_router.record_outcome(
        body,
        tenant_id="tenant-1",
        current_user_id="authenticated-user",
        _rbac=None,
    )

    assert captured["seller_id"] == "authenticated-user"
    assert result["outcome"]["seller_id"] == "authenticated-user"


@pytest.mark.asyncio
async def test_current_seller_queue_uses_token_identity(monkeypatch):
    captured = {}

    class WorkQueueStub:
        async def get_my_day(self, tenant_id, seller_id):
            captured.update(tenant_id=tenant_id, seller_id=seller_id)
            return {"pending_actions": []}

    monkeypatch.setattr(hitl_router, "_wq_svc", WorkQueueStub())

    result = await hitl_router.get_my_day_for_current_user(
        tenant_id="tenant-1",
        current_user_id="authenticated-user",
        _rbac=None,
    )

    assert captured == {"tenant_id": "tenant-1", "seller_id": "authenticated-user"}
    assert result == {"pending_actions": []}


def test_outcome_without_idempotency_key_is_rejected():
    # PO decision B7 (report 99): a NULL key defeated outcome dedup (report 87).
    import pydantic

    with pytest.raises(pydantic.ValidationError):
        hitl_router.OutcomeRequest(action_id="a", company_name="c", outcome_type="connected")


@pytest.mark.asyncio
async def test_analytics_leaderboard_only_for_managers(monkeypatch):
    # PO decision B6 (report 99).
    calls = []

    class AnalyticsStub:
        async def get_dashboard(self, tenant_id, seller_id=None, *, leaderboard=True):
            calls.append((seller_id, leaderboard))
            return {}

    monkeypatch.setattr(hitl_router, "_analytics_svc", AnalyticsStub())
    for role in ("admin", "manager"):
        await hitl_router.get_analytics(seller_id="someone-else", tenant_id="t", current_user_id="me",
                                        role=role, _rbac=None)
    for role in ("user", "auditor", "api"):
        await hitl_router.get_analytics(seller_id="someone-else", tenant_id="t", current_user_id="me",
                                        role=role, _rbac=None)
    assert calls[:2] == [("someone-else", True), ("someone-else", True)]
    assert calls[2:] == [("me", False)] * 3
