"""Sales Action execution — tasks, opportunities, follow-ups, audit trail.

All actions are persisted with full provenance (signal_ids, nba_id, rationale).
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import date, timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .models import ActionType, NextBestAction, SalesAction

logger = logging.getLogger(__name__)


class ActionExecutor:
    """Create a tenant-scoped CRM follow-up task and its action audit record.

    External communications and opportunity creation remain human-controlled;
    this path turns every actionable NBA into a task a seller can review.
    """

    def __init__(self, session_factory: Any) -> None:
        self._session_factory = session_factory

    async def _pin_tenant(self, session: AsyncSession, tenant_id: str) -> None:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"),
            {"t": str(tenant_id)},
        )

    async def execute(
        self,
        nba: NextBestAction,
        tenant_id: str,
        user_id: str = "",
    ) -> SalesAction:
        """Create an idempotent CRM task for an actionable NBA."""
        action_id = str(
            uuid.uuid5(uuid.NAMESPACE_URL, f"salesos:nba-action:{tenant_id}:{nba.id}")
        )
        action = SalesAction(
            id=action_id,
            nba_id=nba.id,
            company_name=nba.company_name,
            tenant_id=tenant_id,
            user_id=user_id,
            action_type=nba.action_type,
            status="pending",
            notes=nba.rationale,
        )
        due_days = {
            "immediate": 0,
            "today": 0,
            "this_week": 7,
            "next_week": 14,
            "monitor": 30,
        }.get(nba.urgency.value, 7)
        task_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"salesos:nba-task:{action_id}"))
        priority = {
            "immediate": "critical",
            "today": "high",
            "this_week": "medium",
            "next_week": "low",
            "monitor": "low",
        }.get(nba.urgency.value, "medium")
        task_title = (
            nba.title
            or f"{nba.action_type.value.replace('_', ' ').title()}: {nba.company_name}"
        )[:500]
        task_created = nba.action_type != ActionType.NO_ACTION
        action.status = "pending" if task_created else "skipped"
        action.metadata = {
            "crm_task_id": task_id if task_created else None,
            "crm_task_created": task_created,
            "execution_mode": "crm_follow_up_task" if task_created else "no_action",
            "external_communication_sent": False,
            "opportunity_created": False,
        }

        async with self._session_factory() as session:
            await self._pin_tenant(session, tenant_id)
            try:
                if task_created:
                    # Link only on an exact tenant-local company-name match. If
                    # names are missing or ambiguous, preserve the task unlinked.
                    if nba.company_name.strip():
                        company_result = await session.execute(
                            text("""
                                SELECT id FROM companies
                                WHERE tenant_id::text = :tenant_id
                                  AND (
                                      lower(btrim(name_ar)) = lower(btrim(:company_name))
                                      OR lower(btrim(COALESCE(name_en, ''))) =
                                         lower(btrim(:company_name))
                                  )
                                LIMIT 2
                            """),
                            {"tenant_id": tenant_id, "company_name": nba.company_name},
                        )
                        company_matches = company_result.fetchall()
                    else:
                        company_matches = []
                    company_id = company_matches[0][0] if len(company_matches) == 1 else None
                    if company_id:
                        action.metadata["company_id"] = str(company_id)

                    await session.execute(
                        text("""
                            INSERT INTO tasks
                                (id, tenant_id, company_id, title, priority, source,
                                 due_date, completed, created_at)
                            VALUES
                                (:id, :tenant_id, :company_id, :title, :priority,
                                 'nba', :due_date, false, now())
                            ON CONFLICT (id) DO NOTHING
                        """),
                        {
                            "id": uuid.UUID(task_id),
                            "tenant_id": uuid.UUID(tenant_id),
                            "company_id": company_id,
                            "title": task_title,
                            "priority": priority,
                            # date.today() (local calendar date), matching every other
                            # date-only "today" computation in this codebase (contract/
                            # quote expiry, cost-tracker billing periods) — not
                            # datetime.now(UTC).date(), which drifts one calendar day
                            # behind local for any positive-UTC-offset deployment during
                            # the local-midnight-to-UTC-offset window, silently
                            # persisting a due_date of "yesterday" for a task meant to
                            # be due "today".
                            "due_date": date.today() + timedelta(days=due_days),
                        },
                    )

                await session.execute(
                    text("""
                        INSERT INTO agent_sales_actions
                            (id, nba_id, company_name, tenant_id, user_id,
                             action_type, status, outcome, notes,
                             created_at, metadata)
                        VALUES
                            (:id, :nba_id, :company_name, :tenant_id, :user_id,
                             :action_type, :status, :outcome, :notes,
                             :created_at, CAST(:metadata AS jsonb))
                        ON CONFLICT (id) DO NOTHING
                    """),
                    {
                        "id": uuid.UUID(action.id),
                        "nba_id": nba.id,
                        "company_name": nba.company_name,
                        "tenant_id": tenant_id,
                        "user_id": user_id,
                        "action_type": nba.action_type.value,
                        "status": action.status,
                        "outcome": "",
                        "notes": action.notes,
                        "created_at": action.created_at,
                        "metadata": json.dumps(action.metadata),
                    },
                )
                await session.commit()
                logger.info(
                    "sales_action_recorded: company=%s action=%s nba=%s task=%s",
                    nba.company_name,
                    nba.action_type.value,
                    nba.id,
                    task_id if task_created else "none",
                )
            except Exception:
                await session.rollback()
                logger.exception("execute_action failed for %s", nba.company_name)
                raise

        return action

    async def complete(
        self,
        action_id: str,
        tenant_id: str,
        outcome: str = "neutral",
        notes: str = "",
    ) -> bool:
        """Mark an action as completed. Raises ValueError if not found or unauthorized."""
        async with self._session_factory() as session:
            await self._pin_tenant(session, tenant_id)
            await session.execute(
                text("""
                    UPDATE tasks
                    SET completed = true
                    WHERE id::text = (
                        SELECT metadata->>'crm_task_id'
                        FROM agent_sales_actions
                        WHERE id = :id AND tenant_id = :tenant_id
                    )
                      AND tenant_id::text = :tenant_id
                """),
                {"id": action_id, "tenant_id": tenant_id},
            )
            result = await session.execute(
                text("""
                    UPDATE agent_sales_actions
                    SET status = 'completed',
                        outcome = :outcome,
                        notes = COALESCE(NULLIF(:notes, ''), notes),
                        completed_at = now()
                    WHERE id = :id AND tenant_id = :tenant_id
                """),
                {"id": action_id, "tenant_id": tenant_id, "outcome": outcome, "notes": notes},
            )
            await session.commit()
            if (result.rowcount or 0) == 0:
                raise ValueError(
                    f"Action {action_id} not found or not authorized "
                    f"for tenant {tenant_id}"
                )
            return True

    async def get_actions(
        self,
        tenant_id: str,
        company_name: str | None = None,
        status: str | None = None,
    ) -> list[SalesAction]:
        """Get sales actions for a tenant."""
        async with self._session_factory() as session:
            await self._pin_tenant(session, tenant_id)
            where_clauses = ["1=1"]
            params: dict[str, Any] = {}
            if company_name:
                where_clauses.append("company_name = :company")
                params["company"] = company_name
            if status:
                where_clauses.append("status = :status")
                params["status"] = status
            where = " AND ".join(where_clauses)
            rows = await session.execute(
                text(f"SELECT * FROM agent_sales_actions WHERE {where} ORDER BY created_at DESC"),
                params,
            )
            return [
                SalesAction(
                    id=str(r.id),
                    nba_id=str(r.nba_id) if r.nba_id else "",
                    company_name=r.company_name,
                    tenant_id=r.tenant_id,
                    user_id=r.user_id or "",
                    action_type=ActionType(r.action_type),
                    status=r.status,
                    outcome=r.outcome or "",
                    notes=r.notes or "",
                    created_at=r.created_at,
                    completed_at=r.completed_at,
                    metadata=getattr(r, "metadata", None) or {},
                )
                for r in rows
            ]

    async def get_pending_count(self, tenant_id: str) -> int:
        """Count pending actions."""
        async with self._session_factory() as session:
            await self._pin_tenant(session, tenant_id)
            rows = await session.execute(
                text(
                    "SELECT COUNT(*) FROM agent_sales_actions "
                    "WHERE status = 'pending' AND tenant_id = :t"
                ),
                {"t": tenant_id},
            )
            return rows.scalar() or 0

    async def get_completed_count(self, tenant_id: str) -> int:
        """Count completed actions."""
        async with self._session_factory() as session:
            await self._pin_tenant(session, tenant_id)
            rows = await session.execute(
                text(
                    "SELECT COUNT(*) FROM agent_sales_actions "
                    "WHERE status = 'completed' AND tenant_id = :t"
                ),
                {"t": tenant_id},
            )
            return rows.scalar() or 0
