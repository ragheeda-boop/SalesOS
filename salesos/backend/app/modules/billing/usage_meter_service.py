"""STORY-05-03 — UsageMeter record + hourly rollup service.

Append events (avoid hot-path amplification); rollup into ``usage_meters``.
Owner-plane only. No RLS. No Stripe secrets. Not Production GO.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.billing.models import UsageMeterEventModel, UsageMeterModel
from app.modules.billing.usage_metrics import (
    combine_quantities,
    hour_bucket,
    normalize_metric_key,
    normalize_op,
)


class UsageMeterService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record_event(
        self,
        *,
        tenant_id: uuid.UUID | str,
        metric_key: str,
        quantity: float,
        op: str | None = None,
        recorded_at: datetime | None = None,
        source: str | None = None,
    ) -> UsageMeterEventModel:
        tid = uuid.UUID(str(tenant_id))
        key = normalize_metric_key(metric_key)
        operation = normalize_op(op, metric_key=key)
        qty = float(quantity)
        if qty < 0:
            raise ValueError("quantity must be >= 0")
        at = recorded_at or datetime.now(UTC)
        if at.tzinfo is None:
            at = at.replace(tzinfo=UTC)
        row = UsageMeterEventModel(
            id=uuid.uuid4(),
            tenant_id=tid,
            metric_key=key,
            quantity=qty,
            op=operation,
            recorded_at=at,
            source=(source or "")[:64] or None,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def rollup_pending(
        self,
        *,
        through: datetime | None = None,
        limit: int = 5000,
    ) -> dict[str, Any]:
        """Roll up pending events with recorded_at < through (default: start of current hour)."""
        now = datetime.now(UTC)
        current_hour, _ = hour_bucket(now)
        cutoff = through or current_hour
        if cutoff.tzinfo is None:
            cutoff = cutoff.replace(tzinfo=UTC)

        result = await self.session.execute(
            select(UsageMeterEventModel)
            .where(
                UsageMeterEventModel.rolled_up_at.is_(None),
                UsageMeterEventModel.recorded_at < cutoff,
            )
            .order_by(UsageMeterEventModel.recorded_at.asc())
            .limit(max(1, min(int(limit), 50_000)))
        )
        events = list(result.scalars().all())
        if not events:
            return {"events_rolled": 0, "buckets_touched": 0, "through": cutoff.isoformat()}

        # Aggregate in memory by (tenant, metric, period_start, op family)
        buckets: dict[tuple[uuid.UUID, str, datetime], dict[str, float]] = {}
        # For mixed ops in same hour: apply add sum and set max separately then combine.
        for ev in events:
            start, end = hour_bucket(ev.recorded_at)
            key = (ev.tenant_id, ev.metric_key, start)
            slot = buckets.setdefault(
                key, {"add": 0.0, "set": 0.0, "has_set": 0.0, "end": end.timestamp()}
            )
            if ev.op == "set":
                slot["set"] = max(slot["set"], float(ev.quantity))
                slot["has_set"] = 1.0
            else:
                slot["add"] += float(ev.quantity)

        touched = 0
        for (tenant_id, metric_key, period_start), agg in buckets.items():
            period_end = datetime.fromtimestamp(agg["end"], tz=UTC)
            existing = (
                await self.session.execute(
                    select(UsageMeterModel).where(
                        UsageMeterModel.tenant_id == tenant_id,
                        UsageMeterModel.metric_key == metric_key,
                        UsageMeterModel.period_start == period_start,
                    )
                )
            ).scalar_one_or_none()
            quantity = 0.0
            if existing is not None:
                quantity = float(existing.quantity)
            if agg["has_set"]:
                quantity = combine_quantities("set", quantity, agg["set"])
            if agg["add"]:
                quantity = combine_quantities("add", quantity, agg["add"])

            if existing is None:
                self.session.add(
                    UsageMeterModel(
                        id=uuid.uuid4(),
                        tenant_id=tenant_id,
                        metric_key=metric_key,
                        period_start=period_start,
                        period_end=period_end,
                        quantity=quantity,
                    )
                )
            else:
                existing.quantity = quantity
                existing.period_end = period_end
            touched += 1

        stamp = datetime.now(UTC)
        for ev in events:
            ev.rolled_up_at = stamp
        await self.session.flush()
        return {
            "events_rolled": len(events),
            "buckets_touched": touched,
            "through": cutoff.isoformat(),
        }

    async def list_meters(
        self,
        *,
        tenant_id: uuid.UUID | str | None = None,
        metric_key: str | None = None,
        period_from: datetime | None = None,
        period_to: datetime | None = None,
        limit: int = 200,
    ) -> list[UsageMeterModel]:
        q = select(UsageMeterModel).order_by(UsageMeterModel.period_start.desc())
        if tenant_id is not None:
            q = q.where(UsageMeterModel.tenant_id == uuid.UUID(str(tenant_id)))
        if metric_key is not None:
            q = q.where(UsageMeterModel.metric_key == normalize_metric_key(metric_key))
        if period_from is not None:
            q = q.where(UsageMeterModel.period_start >= period_from)
        if period_to is not None:
            q = q.where(UsageMeterModel.period_start < period_to)
        q = q.limit(max(1, min(int(limit), 1000)))
        return list((await self.session.execute(q)).scalars().all())
