"""PostgreSQL repository for Revenue Analytics snapshots."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import JSON, DateTime, Float, String, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from sdk.database import Base
from domains.revenue.analytics.models import AnalyticsSnapshot, KPIValue
from domains.revenue.analytics.repo import AnalyticsRepository


class RevenueAnalyticsSnapshotModel(Base):
    __tablename__ = "revenue_analytics_snapshots"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    values: Mapped[list] = mapped_column(JSON, default=list)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    version: Mapped[int] = mapped_column(default=1)


class PostgresRevenueAnalyticsRepository(AnalyticsRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, snapshot: AnalyticsSnapshot) -> AnalyticsSnapshot:
        values_data = [
            {
                "kpi_id": v.kpi_id,
                "value": v.value,
                "previous_value": v.previous_value,
                "change": v.change,
                "change_percent": v.change_percent,
                "dimension": v.dimension,
                "note": v.note,
            }
            for v in snapshot.values
        ]
        stmt = select(RevenueAnalyticsSnapshotModel).where(RevenueAnalyticsSnapshotModel.id == snapshot.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            model.values = values_data
            model.period_start = snapshot.period_start
            model.period_end = snapshot.period_end
            model.version = snapshot.version
        else:
            model = RevenueAnalyticsSnapshotModel(
                id=snapshot.id,
                tenant_id=snapshot.tenant_id,
                period_start=snapshot.period_start,
                period_end=snapshot.period_end,
                values=values_data,
                generated_at=snapshot.generated_at,
                version=snapshot.version,
            )
            self.session.add(model)
        await self.session.flush()
        return snapshot

    async def get(self, snapshot_id: str) -> Optional[AnalyticsSnapshot]:
        stmt = select(RevenueAnalyticsSnapshotModel).where(RevenueAnalyticsSnapshotModel.id == snapshot_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_by_tenant(self, tenant_id: str, limit: int = 20) -> list[AnalyticsSnapshot]:
        stmt = (
            select(RevenueAnalyticsSnapshotModel)
            .where(RevenueAnalyticsSnapshotModel.tenant_id == tenant_id)
            .order_by(RevenueAnalyticsSnapshotModel.generated_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [self._to_domain(r) for r in result.scalars().all()]

    async def get_latest(self, tenant_id: str) -> Optional[AnalyticsSnapshot]:
        stmt = (
            select(RevenueAnalyticsSnapshotModel)
            .where(RevenueAnalyticsSnapshotModel.tenant_id == tenant_id)
            .order_by(RevenueAnalyticsSnapshotModel.generated_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    def _to_domain(self, model: RevenueAnalyticsSnapshotModel) -> AnalyticsSnapshot:
        values = [
            KPIValue(
                kpi_id=v.get("kpi_id", ""),
                value=v.get("value", 0.0),
                previous_value=v.get("previous_value", 0.0),
                change=v.get("change", 0.0),
                change_percent=v.get("change_percent", 0.0),
                dimension=v.get("dimension", ""),
                note=v.get("note", ""),
            )
            for v in (model.values or [])
        ]
        return AnalyticsSnapshot(
            id=model.id,
            tenant_id=model.tenant_id,
            period_start=model.period_start,
            period_end=model.period_end,
            values=values,
            generated_at=model.generated_at,
            version=model.version,
        )
