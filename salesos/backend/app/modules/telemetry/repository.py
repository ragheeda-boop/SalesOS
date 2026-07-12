"""PostgresTelemetryRepository — SQLAlchemy-backed telemetry persistence."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func as sa_func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import TelemetryEvent
from .service import TelemetryRepository


class PostgresTelemetryRepository(TelemetryRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, event: TelemetryEvent) -> TelemetryEvent:
        self._session.add(event)
        await self._session.flush()
        return event

    async def query(
        self,
        tenant_id: str,
        event_type: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> tuple[list[TelemetryEvent], int]:
        stmt = select(TelemetryEvent).where(TelemetryEvent.tenant_id == tenant_id)
        if event_type:
            stmt = stmt.where(TelemetryEvent.event_type == event_type)
        if from_date:
            stmt = stmt.where(TelemetryEvent.timestamp >= from_date)
        if to_date:
            stmt = stmt.where(TelemetryEvent.timestamp <= to_date)

        count_stmt = select(sa_func.count()).select_from(stmt.subquery())
        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar() or 0

        stmt = stmt.order_by(TelemetryEvent.timestamp.desc())
        stmt = stmt.offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total

    async def aggregate(
        self,
        tenant_id: str,
        event_type: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        granularity: str = "day",
    ) -> list[dict[str, Any]]:
        stmt = select(TelemetryEvent).where(TelemetryEvent.tenant_id == tenant_id)
        if event_type:
            stmt = stmt.where(TelemetryEvent.event_type == event_type)
        if from_date:
            stmt = stmt.where(TelemetryEvent.timestamp >= from_date)
        if to_date:
            stmt = stmt.where(TelemetryEvent.timestamp <= to_date)

        result = await self._session.execute(stmt)
        events = result.scalars().all()

        buckets: dict[str, int] = {}
        for e in events:
            ts = e.timestamp
            if not ts:
                continue
            if granularity == "hour":
                key = ts.strftime("%Y-%m-%dT%H:00:00")
            elif granularity == "day":
                key = ts.strftime("%Y-%m-%d")
            elif granularity == "week":
                iso = ts.isocalendar()
                key = f"{iso[0]}-W{iso[1]:02d}"
            elif granularity == "month":
                key = ts.strftime("%Y-%m")
            else:
                key = ts.strftime("%Y-%m-%d")
            buckets[key] = buckets.get(key, 0) + 1

        return [{"period": k, "count": v} for k, v in sorted(buckets.items())]

    async def get_all_events(self, tenant_id: str) -> list[TelemetryEvent]:
        stmt = select(TelemetryEvent).where(TelemetryEvent.tenant_id == tenant_id).order_by(TelemetryEvent.timestamp)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_all_events_in_range(
        self,
        tenant_id: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> list[TelemetryEvent]:
        stmt = select(TelemetryEvent)
        if tenant_id is not None:
            stmt = stmt.where(TelemetryEvent.tenant_id == tenant_id)
        if from_date:
            stmt = stmt.where(TelemetryEvent.timestamp >= from_date)
        if to_date:
            stmt = stmt.where(TelemetryEvent.timestamp <= to_date)
        stmt = stmt.order_by(TelemetryEvent.timestamp)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
