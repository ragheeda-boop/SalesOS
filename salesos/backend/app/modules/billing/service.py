"""Subscription persistence helpers — STORY-05-01.

Owner-plane only. No Stripe (STORY-05-02). No Production GO.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.billing.models import SubscriptionModel
from app.modules.billing.state_machine import (
    SubscriptionEvent,
    SubscriptionStatus,
    SubscriptionTransitionError,
    apply_transition,
    can_transition,
)


def initial_status_for_provision(*, trial_ends_at: datetime | None) -> SubscriptionStatus:
    """OPS §11: trial if trial window set; else active (sales-assisted)."""
    return SubscriptionStatus.TRIAL if trial_ends_at is not None else SubscriptionStatus.ACTIVE


class SubscriptionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_tenant(self, tenant_id: uuid.UUID | str) -> SubscriptionModel | None:
        tid = uuid.UUID(str(tenant_id))
        result = await self.session.execute(
            select(SubscriptionModel).where(SubscriptionModel.tenant_id == tid)
        )
        return result.scalar_one_or_none()

    async def ensure_for_tenant(
        self,
        *,
        tenant_id: uuid.UUID | str,
        plan_id: str | None = None,
        trial_ends_at: datetime | None = None,
        billing_cycle: str = "monthly",
        seats: int = 1,
    ) -> tuple[SubscriptionModel, bool]:
        """Idempotent create — returns (row, created)."""
        tid = uuid.UUID(str(tenant_id))
        existing = await self.get_by_tenant(tid)
        if existing is not None:
            if plan_id is not None and existing.plan_id != plan_id:
                existing.plan_id = plan_id
            if trial_ends_at is not None and existing.trial_ends_at is None:
                existing.trial_ends_at = trial_ends_at
            await self.session.flush()
            return existing, False

        status = initial_status_for_provision(trial_ends_at=trial_ends_at)
        now = datetime.now(UTC)
        row = SubscriptionModel(
            id=uuid.uuid4(),
            tenant_id=tid,
            plan_id=plan_id,
            status=status.value,
            billing_cycle=billing_cycle if billing_cycle in ("monthly", "yearly") else "monthly",
            seats=max(1, int(seats)),
            trial_ends_at=trial_ends_at,
            current_period_start=now if status == SubscriptionStatus.ACTIVE else None,
            created_at=now,
            updated_at=now,
        )
        self.session.add(row)
        await self.session.flush()
        return row, True

    async def apply_event(
        self,
        *,
        tenant_id: uuid.UUID | str,
        event: str | SubscriptionEvent,
    ) -> SubscriptionModel:
        row = await self.get_by_tenant(tenant_id)
        if row is None:
            raise SubscriptionTransitionError(f"no subscription for tenant {tenant_id}")

        nxt = apply_transition(row.status, event)
        row.status = nxt.value
        now = datetime.now(UTC)
        row.updated_at = now
        if nxt == SubscriptionStatus.CHURNED:
            row.canceled_at = now
        elif nxt == SubscriptionStatus.ACTIVE:
            row.canceled_at = None
            if row.current_period_start is None:
                row.current_period_start = now
        await self.session.flush()
        return row

    async def sync_tenant_lifecycle(
        self,
        *,
        tenant_id: uuid.UUID | str,
        action: str,
    ) -> SubscriptionModel | None:
        """Best-effort SM sync for Owner tenant lifecycle (no raise if no row / illegal).

        action: suspend | activate | churn
        """
        row = await self.get_by_tenant(tenant_id)
        if row is None:
            return None
        if action == "suspend":
            event: SubscriptionEvent | None = SubscriptionEvent.SUSPEND
        elif action == "activate":
            # Suspended → reactivate; churned (post soft-delete) → resubscribe active.
            if can_transition(row.status, SubscriptionEvent.REACTIVATE):
                event = SubscriptionEvent.REACTIVATE
            elif can_transition(row.status, SubscriptionEvent.RESUBSCRIBE_ACTIVE):
                event = SubscriptionEvent.RESUBSCRIBE_ACTIVE
            else:
                return row
        elif action == "churn":
            event = SubscriptionEvent.CHURN
        else:
            return row
        if event is None or not can_transition(row.status, event):
            return row
        return await self.apply_event(tenant_id=tenant_id, event=event)

    def to_dict(self, row: SubscriptionModel) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "tenant_id": str(row.tenant_id),
            "plan_id": row.plan_id,
            "status": row.status,
            "billing_cycle": row.billing_cycle,
            "seats": row.seats,
            "trial_ends_at": row.trial_ends_at.isoformat() if row.trial_ends_at else None,
            "current_period_start": (
                row.current_period_start.isoformat() if row.current_period_start else None
            ),
            "current_period_end": (
                row.current_period_end.isoformat() if row.current_period_end else None
            ),
            "canceled_at": row.canceled_at.isoformat() if row.canceled_at else None,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        }
