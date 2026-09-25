"""Persistent HITL seller attribution and action lifecycle on salesos_test only.

This test intentionally does not use the shared ``db_session`` fixture: that
fixture drops the test schema at session teardown. It creates uniquely named
synthetic rows and deletes only those rows in a guarded finally block.
"""

from uuid import uuid4

import pytest
from sqlalchemy import text

from app.config import settings
from app.database import async_session, owner_engine
from app.modules.company.models import Company
from app.modules.identity.models import Tenant
from app.modules.signal_actions import hitl_router
from app.modules.signal_actions.actions import ActionExecutor
from app.modules.signal_actions.hitl_service import FeedbackService, OutcomeService
from app.modules.signal_actions.models import ActionType, ActionUrgency, NextBestAction


class _NoopEffectiveness:
    async def record_feedback_event(self, *_args, **_kwargs):
        return None

    async def record_outcome_event(self, *_args, **_kwargs):
        return None

    async def record_event(self, *_args, **_kwargs):
        return None


async def _assert_target(engine, expected_user: str) -> None:
    async with engine.connect() as conn:
        database, user = (
            await conn.execute(text("SELECT current_database(), current_user"))
        ).one()
    assert database == "salesos_test", f"refusing non-test database {database!r}"
    assert user == expected_user, f"unexpected database role {user!r}"


@pytest.mark.asyncio
async def test_authenticated_seller_rejection_completion_and_outcome_persist(monkeypatch):
    assert "salesos_test" in settings.app_database_url.rsplit("/", 1)[-1]
    tenant_id = uuid4()
    company_id = uuid4()
    seller_id = str(uuid4())
    company_name = f"Synthetic HITL QA {uuid4().hex[:10]}"
    rejected_nba_id = str(uuid4())
    completed_nba_id = str(uuid4())

    await _assert_target(owner_engine, "salesos")
    await _assert_target(async_session.kw["bind"], "salesos_app")

    try:
        async with async_session() as session:
            session.add(
                Tenant(
                    id=tenant_id,
                    name=company_name,
                    slug=f"hitl-qa-{tenant_id.hex}",
                )
            )
            await session.flush()
            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(tenant_id)},
            )
            session.add(
                Company(
                    id=company_id,
                    tenant_id=tenant_id,
                    name_ar=company_name,
                    name_en=company_name,
                )
            )
            await session.commit()

        executor = ActionExecutor(async_session)
        rejected = await executor.execute(
            NextBestAction(
                id=rejected_nba_id,
                company_name=company_name,
                tenant_id=str(tenant_id),
                action_type=ActionType.CALL,
                urgency=ActionUrgency.TODAY,
                title="Synthetic rejection-path call",
                rationale="Automated test fixture only",
            ),
            str(tenant_id),
            user_id=seller_id,
        )

        monkeypatch.setattr(hitl_router, "_fb_svc", FeedbackService(async_session))
        monkeypatch.setattr(hitl_router, "_eff_svc", _NoopEffectiveness())
        rejection = await hitl_router.record_feedback(
            hitl_router.FeedbackRequest(
                action_id=rejected.id,
                recommendation_id=rejected.nba_id,
                company_name=company_name,
                seller_id="spoofed-client-seller",
                decision="rejected",
                reason_code="not_relevant",
                original_action_type="call",
            ),
            tenant_id=str(tenant_id),
            current_user_id=seller_id,
            _rbac=None,
        )
        assert rejection["seller_id"] == seller_id

        async with async_session() as session:
            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(tenant_id)},
            )
            state = (
                await session.execute(
                    text("SELECT status, outcome FROM agent_sales_actions WHERE id = :id"),
                    {"id": rejected.id},
                )
            ).one()
            task_count = (
                await session.execute(
                    text("SELECT count(*) FROM tasks WHERE tenant_id = :tenant_id AND source = 'nba'"),
                    {"tenant_id": tenant_id},
                )
            ).scalar_one()
            feedback = (
                await session.execute(
                    text("SELECT seller_id, reason_code FROM nba_feedback WHERE action_id = :id"),
                    {"id": rejected.id},
                )
            ).one()
        assert state == ("skipped", "rejected")
        assert task_count == 0
        assert feedback == (seller_id, "not_relevant")

        completed = await executor.execute(
            NextBestAction(
                id=completed_nba_id,
                company_name=company_name,
                tenant_id=str(tenant_id),
                action_type=ActionType.MEETING,
                urgency=ActionUrgency.TODAY,
                title="Synthetic completion-path meeting",
                rationale="Automated test fixture only",
            ),
            str(tenant_id),
            user_id=seller_id,
        )
        assert await executor.complete(completed.id, str(tenant_id), outcome="positive")

        monkeypatch.setattr(hitl_router, "_out_svc", OutcomeService(async_session))
        monkeypatch.setattr(hitl_router, "_fu_svc", hitl_router.FollowupService(async_session))
        outcome_response = await hitl_router.record_outcome(
            hitl_router.OutcomeRequest(
                action_id=completed.id,
                company_name=company_name,
                seller_id="spoofed-client-seller",
                outcome_type="meeting_set",
                followup_required=True,
                idempotency_key="authenticated-seller-outcome",
            ),
            tenant_id=str(tenant_id),
            current_user_id=seller_id,
            _rbac=None,
        )
        assert outcome_response["outcome"]["seller_id"] == seller_id
        assert outcome_response["followup"] is not None

        async with async_session() as session:
            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(tenant_id)},
            )
            action_and_task = (
                await session.execute(
                    text("""
                        SELECT a.status, t.completed
                        FROM agent_sales_actions AS a
                        JOIN tasks AS t ON t.id::text = a.metadata->>'crm_task_id'
                        WHERE a.id = :action_id AND a.tenant_id = :tenant_id
                    """),
                    {"action_id": completed.id, "tenant_id": str(tenant_id)},
                )
            ).one()
            outcome = (
                await session.execute(
                    text("SELECT seller_id, outcome_type FROM action_outcomes WHERE action_id = :id"),
                    {"id": completed.id},
                )
            ).one()
            followup_count = (
                await session.execute(
                    text("SELECT count(*) FROM sales_followups WHERE parent_action_id = :id"),
                    {"id": completed.id},
                )
            ).scalar_one()
        assert action_and_task == ("completed", True)
        assert outcome == (seller_id, "meeting_set")
        assert followup_count == 1

        # Same synthetic records are invisible when RLS is pinned to another tenant.
        async with async_session() as session:
            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(uuid4())},
            )
            hidden = (
                await session.execute(
                    text("SELECT count(*) FROM action_outcomes WHERE action_id = :id"),
                    {"id": completed.id},
                )
            ).scalar_one()
        assert hidden == 0
    finally:
        await _assert_target(owner_engine, "salesos")
        async with owner_engine.begin() as conn:
            for table in (
                "sales_followups",
                "action_outcomes",
                "nba_feedback",
                "agent_sales_actions",
                "tasks",
            ):
                await conn.execute(
                    text(f"DELETE FROM {table} WHERE tenant_id::text = :tenant_id"),
                    {"tenant_id": str(tenant_id)},
                )
            await conn.execute(
                text("DELETE FROM companies WHERE tenant_id::text = :tenant_id"),
                {"tenant_id": str(tenant_id)},
            )
            await conn.execute(
                text("DELETE FROM tenants WHERE id::text = :tenant_id"),
                {"tenant_id": str(tenant_id)},
            )
