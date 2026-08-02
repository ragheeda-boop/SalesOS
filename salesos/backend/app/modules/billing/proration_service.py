"""STORY-05-05 — Quote / apply mid-cycle plan changes.

Uses admin_plans prices + subscription period. Env-only Stripe secrets unused.
Not Production GO.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.admin.db_models import PlanModel
from app.modules.billing.models import SubscriptionModel
from app.modules.billing.proration import PlanChangeTiming, quote_plan_change
from app.modules.billing.service import SubscriptionService
from app.modules.identity.models import Tenant


class ProrationError(ValueError):
    """Illegal plan change request."""


def _cycle_price(plan: PlanModel, billing_cycle: str) -> float:
    if billing_cycle == "yearly":
        return float(plan.price_yearly or 0)
    return float(plan.price_monthly or 0)


def _default_period_end(start: datetime | None, billing_cycle: str) -> datetime | None:
    if start is None:
        return None
    s = start if start.tzinfo else start.replace(tzinfo=UTC)
    if billing_cycle == "yearly":
        return s + timedelta(days=365)
    return s + timedelta(days=30)


class ProrationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.subs = SubscriptionService(session)

    async def _get_plan(self, plan_id: uuid.UUID | str) -> PlanModel:
        try:
            pid = uuid.UUID(str(plan_id))
        except ValueError as exc:
            raise ProrationError(f"invalid plan_id: {plan_id!r}") from exc
        plan = await self.session.get(PlanModel, pid)
        if plan is None:
            raise ProrationError(f"plan not found: {plan_id}")
        return plan

    async def _resolve_current_plan(self, sub: SubscriptionModel) -> PlanModel | None:
        if not sub.plan_id:
            return None
        try:
            return await self._get_plan(sub.plan_id)
        except ProrationError:
            # Opaque non-UUID plan_id — try tier match
            result = await self.session.execute(
                select(PlanModel).where(PlanModel.tier == sub.plan_id).limit(1)
            )
            return result.scalar_one_or_none()

    async def quote(
        self,
        *,
        tenant_id: uuid.UUID | str,
        target_plan_id: uuid.UUID | str,
        downgrade_immediate: bool = False,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        tid = uuid.UUID(str(tenant_id))
        sub = await self.subs.get_by_tenant(tid)
        if sub is None:
            raise ProrationError("no subscription for tenant")
        target = await self._get_plan(target_plan_id)
        current = await self._resolve_current_plan(sub)
        old_price = _cycle_price(current, sub.billing_cycle) if current else 0.0
        new_price = _cycle_price(target, sub.billing_cycle)
        period_end = sub.current_period_end or _default_period_end(
            sub.current_period_start, sub.billing_cycle
        )
        q = quote_plan_change(
            old_price=old_price,
            new_price=new_price,
            period_start=sub.current_period_start,
            period_end=period_end,
            downgrade_immediate=downgrade_immediate,
            now=now,
        )
        return {
            "tenant_id": str(tid),
            "subscription_id": str(sub.id),
            "from_plan_id": str(current.id) if current else sub.plan_id,
            "to_plan_id": str(target.id),
            "billing_cycle": sub.billing_cycle,
            "direction": q.direction.value,
            "timing": q.timing.value,
            "old_price": q.old_price,
            "new_price": q.new_price,
            "remaining_fraction": round(q.remaining_fraction, 6),
            "amount_due_now": q.amount_due_now,
            "period_start": sub.current_period_start.isoformat()
            if sub.current_period_start
            else None,
            "period_end": period_end.isoformat() if period_end else None,
            "pending_plan_id": sub.pending_plan_id,
            "pending_effective_at": sub.pending_effective_at.isoformat()
            if sub.pending_effective_at
            else None,
        }

    async def apply(
        self,
        *,
        tenant_id: uuid.UUID | str,
        target_plan_id: uuid.UUID | str,
        downgrade_immediate: bool = False,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        """Apply quote: upgrades immediate; downgrades deferred unless immediate."""
        tid = uuid.UUID(str(tenant_id))
        clock = now or datetime.now(UTC)
        if clock.tzinfo is None:
            clock = clock.replace(tzinfo=UTC)
        preview = await self.quote(
            tenant_id=tid,
            target_plan_id=target_plan_id,
            downgrade_immediate=downgrade_immediate,
            now=clock,
        )
        sub = await self.subs.get_by_tenant(tid)
        if sub is None:
            raise ProrationError("no subscription for tenant")
        target = await self._get_plan(target_plan_id)
        period_end = sub.current_period_end or _default_period_end(
            sub.current_period_start, sub.billing_cycle
        )

        if preview["timing"] == PlanChangeTiming.PERIOD_END.value:
            sub.pending_plan_id = str(target.id)
            sub.pending_effective_at = period_end
            await self.session.flush()
            preview["applied"] = "scheduled"
            preview["pending_plan_id"] = sub.pending_plan_id
            preview["pending_effective_at"] = (
                sub.pending_effective_at.isoformat() if sub.pending_effective_at else None
            )
            return preview

        # Immediate: swap plan_id, clear pending
        sub.plan_id = str(target.id)
        sub.pending_plan_id = None
        sub.pending_effective_at = None
        tenant = await self.session.get(Tenant, tid)
        if tenant is not None:
            tenant.plan_id = str(target.id)
        await self.session.flush()
        preview["applied"] = "immediate"
        preview["from_plan_id"] = preview["from_plan_id"]
        preview["to_plan_id"] = str(target.id)
        return preview

    async def apply_pending_due(self, *, now: datetime | None = None) -> dict[str, Any]:
        """Flip deferred downgrades whose pending_effective_at has elapsed."""
        clock = now or datetime.now(UTC)
        if clock.tzinfo is None:
            clock = clock.replace(tzinfo=UTC)
        result = await self.session.execute(
            select(SubscriptionModel).where(
                SubscriptionModel.pending_plan_id.is_not(None),
                SubscriptionModel.pending_effective_at.is_not(None),
                SubscriptionModel.pending_effective_at <= clock,
            )
        )
        rows = list(result.scalars().all())
        applied: list[str] = []
        for sub in rows:
            new_plan = sub.pending_plan_id
            if not new_plan:
                continue
            sub.plan_id = new_plan
            sub.pending_plan_id = None
            sub.pending_effective_at = None
            tenant = await self.session.get(Tenant, sub.tenant_id)
            if tenant is not None:
                tenant.plan_id = new_plan
            applied.append(str(sub.tenant_id))
        await self.session.flush()
        return {
            "evaluated_at": clock.isoformat(),
            "tenants_updated": applied,
            "count": len(applied),
        }
