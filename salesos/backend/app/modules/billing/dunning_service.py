"""STORY-05-04 — Dunning open / clear / evaluate → auto-suspend.

Uses Subscription SM + Tenant.provisioning_status. No Stripe secret invent.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.modules.billing.dunning import DunningCaseStatus, grace_elapsed, grace_ends_at
from app.modules.billing.models import DunningCaseModel
from app.modules.billing.service import SubscriptionService
from app.modules.billing.state_machine import SubscriptionEvent, can_transition
from app.modules.identity.models import Tenant


class DunningService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.subs = SubscriptionService(session)

    @property
    def grace_days(self) -> int:
        return max(0, int(getattr(settings, "dunning_grace_days", 7)))

    async def get_open_case(self, tenant_id: uuid.UUID) -> DunningCaseModel | None:
        result = await self.session.execute(
            select(DunningCaseModel)
            .where(
                DunningCaseModel.tenant_id == tenant_id,
                DunningCaseModel.status == DunningCaseStatus.OPEN.value,
            )
            .order_by(DunningCaseModel.failed_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def open_or_bump(
        self,
        *,
        tenant_id: uuid.UUID | str,
        stripe_invoice_id: str | None = None,
        failed_at: datetime | None = None,
    ) -> DunningCaseModel:
        tid = uuid.UUID(str(tenant_id))
        clock = failed_at or datetime.now(UTC)
        if clock.tzinfo is None:
            clock = clock.replace(tzinfo=UTC)
        sub = await self.subs.get_by_tenant(tid)
        if sub is not None and can_transition(sub.status, SubscriptionEvent.MARK_PAST_DUE):
            await self.subs.apply_event(tenant_id=tid, event=SubscriptionEvent.MARK_PAST_DUE)
            sub = await self.subs.get_by_tenant(tid)

        existing = await self.get_open_case(tid)
        if existing is not None:
            existing.failure_count = int(existing.failure_count or 0) + 1
            if stripe_invoice_id:
                existing.last_stripe_invoice_id = stripe_invoice_id[:128]
            await self.session.flush()
            return existing

        case = DunningCaseModel(
            id=uuid.uuid4(),
            tenant_id=tid,
            subscription_id=sub.id if sub else None,
            status=DunningCaseStatus.OPEN.value,
            failed_at=clock,
            grace_ends_at=grace_ends_at(clock, grace_days=self.grace_days),
            failure_count=1,
            last_stripe_invoice_id=(stripe_invoice_id[:128] if stripe_invoice_id else None),
        )
        self.session.add(case)
        await self.session.flush()
        return case

    async def clear_for_tenant(self, tenant_id: uuid.UUID | str) -> int:
        tid = uuid.UUID(str(tenant_id))
        result = await self.session.execute(
            select(DunningCaseModel).where(
                DunningCaseModel.tenant_id == tid,
                DunningCaseModel.status == DunningCaseStatus.OPEN.value,
            )
        )
        rows = list(result.scalars().all())
        now = datetime.now(UTC)
        for row in rows:
            row.status = DunningCaseStatus.CLEARED.value
            row.cleared_at = now
        await self.session.flush()
        return len(rows)

    async def evaluate_due(self, *, now: datetime | None = None) -> dict[str, Any]:
        """Auto-suspend open cases whose grace window elapsed."""
        clock = now or datetime.now(UTC)
        if clock.tzinfo is None:
            clock = clock.replace(tzinfo=UTC)
        result = await self.session.execute(
            select(DunningCaseModel).where(
                DunningCaseModel.status == DunningCaseStatus.OPEN.value,
                DunningCaseModel.grace_ends_at <= clock,
            )
        )
        cases = list(result.scalars().all())
        suspended: list[str] = []
        for case in cases:
            if not grace_elapsed(case.grace_ends_at, now=clock):
                continue
            sub = await self.subs.get_by_tenant(case.tenant_id)
            if sub is not None and can_transition(sub.status, SubscriptionEvent.SUSPEND):
                await self.subs.apply_event(
                    tenant_id=case.tenant_id, event=SubscriptionEvent.SUSPEND
                )
            tenant = await self.session.get(Tenant, case.tenant_id)
            if tenant is not None:
                tenant.provisioning_status = "suspended"
                tenant.is_active = False
            case.status = DunningCaseStatus.SUSPENDED.value
            case.suspended_at = clock
            suspended.append(str(case.tenant_id))
        await self.session.flush()
        return {
            "evaluated_at": clock.isoformat(),
            "cases_due": len(cases),
            "tenants_suspended": suspended,
            "grace_days": self.grace_days,
        }

    async def list_cases(
        self,
        *,
        status: str | None = None,
        tenant_id: uuid.UUID | str | None = None,
        limit: int = 100,
    ) -> list[DunningCaseModel]:
        q = select(DunningCaseModel).order_by(DunningCaseModel.failed_at.desc())
        if status:
            q = q.where(DunningCaseModel.status == status)
        if tenant_id is not None:
            q = q.where(DunningCaseModel.tenant_id == uuid.UUID(str(tenant_id)))
        q = q.limit(max(1, min(int(limit), 500)))
        return list((await self.session.execute(q)).scalars().all())
