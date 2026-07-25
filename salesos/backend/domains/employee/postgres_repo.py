from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from sdk.pagination import build_keyset_condition, decode_cursor, encode_cursor

from .db_models import EmployeeSignalModel, EmployeeScoreModel
from .models import EmployeeSignal, EmployeeScore
from .repository import EmployeeSignalRepository


class PostgresEmployeeSignalRepository(EmployeeSignalRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save(self, signal: EmployeeSignal) -> EmployeeSignal:
        model = EmployeeSignalModel(
            id=uuid.UUID(signal.id),
            employee_id=uuid.UUID(signal.employee_id),
            tenant_id=uuid.UUID(signal.tenant_id),
            signal_type=signal.signal_type,
            source=signal.source,
            metadata=signal.metadata,
            timestamp=signal.timestamp,
        )
        self.db.add(model)
        await self.db.flush()
        return signal

    async def save_many(self, signals: list[EmployeeSignal]) -> list[EmployeeSignal]:
        models = [
            EmployeeSignalModel(
                id=uuid.UUID(s.id),
                employee_id=uuid.UUID(s.employee_id),
                tenant_id=uuid.UUID(s.tenant_id),
                signal_type=s.signal_type,
                source=s.source,
                metadata=s.metadata,
                timestamp=s.timestamp,
            )
            for s in signals
        ]
        self.db.add_all(models)
        await self.db.flush()
        return signals

    async def get_by_employee(
        self, employee_id: str, tenant_id: str,
        since: datetime | None = None,
        until: datetime | None = None,
        source: str | None = None,
        signal_type: str | None = None,
        limit: int = 50,
        cursor: str | None = None,
    ) -> tuple[list[EmployeeSignal], int, str | None]:
        query = select(EmployeeSignalModel).where(
            EmployeeSignalModel.employee_id == uuid.UUID(employee_id),
            EmployeeSignalModel.tenant_id == uuid.UUID(tenant_id),
        )
        count_query = select(func.count()).select_from(EmployeeSignalModel).where(
            EmployeeSignalModel.employee_id == uuid.UUID(employee_id),
            EmployeeSignalModel.tenant_id == uuid.UUID(tenant_id),
        )

        if since:
            query = query.where(EmployeeSignalModel.timestamp >= since)
            count_query = count_query.where(EmployeeSignalModel.timestamp >= since)
        if until:
            query = query.where(EmployeeSignalModel.timestamp <= until)
            count_query = count_query.where(EmployeeSignalModel.timestamp <= until)
        if source:
            query = query.where(EmployeeSignalModel.source == source)
            count_query = count_query.where(EmployeeSignalModel.source == source)
        if signal_type:
            query = query.where(EmployeeSignalModel.signal_type == signal_type)
            count_query = count_query.where(EmployeeSignalModel.signal_type == signal_type)

        total = await self.db.scalar(count_query) or 0

        if cursor:
            cursor_id, cursor_sort = decode_cursor(cursor)
            condition = build_keyset_condition(
                EmployeeSignalModel, cursor_id, cursor_sort,
                sort_by="timestamp", sort_dir="desc",
            )
            query = query.where(condition)

        query = query.order_by(desc(EmployeeSignalModel.timestamp)).limit(limit + 1)
        rows = (await self.db.execute(query)).scalars().all()

        next_cursor: str | None = None
        if len(rows) > limit:
            rows = rows[:limit]
            last = rows[-1]
            next_cursor = encode_cursor(str(last.id), last.timestamp)

        signals = [
            EmployeeSignal(
                id=str(r.id), employee_id=str(r.employee_id),
                tenant_id=str(r.tenant_id), signal_type=r.signal_type,
                source=r.source, metadata=r.metadata or {},
                timestamp=r.timestamp, created_at=r.created_at,
            )
            for r in rows
        ]
        return signals, total, next_cursor

    async def get_summary(
        self, employee_id: str, tenant_id: str,
        since: datetime | None = None,
    ) -> dict[str, Any]:
        # Count total with SQL instead of loading all rows
        base = select(
            EmployeeSignalModel.signal_type,
            EmployeeSignalModel.source,
        ).where(
            EmployeeSignalModel.employee_id == uuid.UUID(employee_id),
            EmployeeSignalModel.tenant_id == uuid.UUID(tenant_id),
        )
        if since:
            base = base.where(EmployeeSignalModel.timestamp >= since)

        rows = (await self.db.execute(base)).fetchall()

        by_source: dict[str, int] = {}
        by_type: dict[str, int] = {}
        for signal_type, source in rows:
            by_source[source] = by_source.get(source, 0) + 1
            by_type[signal_type] = by_type.get(signal_type, 0) + 1

        total_count = len(rows)

        # Load recent signals separately (only 20 rows)
        recent_query = select(EmployeeSignalModel).where(
            EmployeeSignalModel.employee_id == uuid.UUID(employee_id),
            EmployeeSignalModel.tenant_id == uuid.UUID(tenant_id),
        )
        if since:
            recent_query = recent_query.where(EmployeeSignalModel.timestamp >= since)
        recent_query = recent_query.order_by(desc(EmployeeSignalModel.timestamp)).limit(20)
        recent_rows = (await self.db.execute(recent_query)).scalars().all()

        return {
            "total_signals": total_count,
            "by_source": by_source,
            "by_type": by_type,
            "recent_signals": [
                EmployeeSignal(
                    id=str(r.id), employee_id=str(r.employee_id),
                    tenant_id=str(r.tenant_id), signal_type=r.signal_type,
                    source=r.source, metadata=r.metadata or {},
                    timestamp=r.timestamp, created_at=r.created_at,
                )
                for r in recent_rows
            ],
        }

    async def save_score(self, score: EmployeeScore) -> EmployeeScore:
        model = EmployeeScoreModel(
            id=uuid.UUID(score.id),
            employee_id=uuid.UUID(score.employee_id),
            tenant_id=uuid.UUID(score.tenant_id),
            overall_score=score.overall_score,
            signal_volume_score=score.signal_volume_score,
            recency_score=score.recency_score,
            diversity_score=score.diversity_score,
            completion_rate=score.completion_rate,
            confidence_interval_low=score.confidence_interval_low,
            confidence_interval_high=score.confidence_interval_high,
            signal_count=score.signal_count,
        )
        self.db.add(model)
        await self.db.flush()
        return score

    async def get_latest_score(
        self, employee_id: str, tenant_id: str,
    ) -> EmployeeScore | None:
        query = select(EmployeeScoreModel).where(
            EmployeeScoreModel.employee_id == uuid.UUID(employee_id),
            EmployeeScoreModel.tenant_id == uuid.UUID(tenant_id),
        ).order_by(desc(EmployeeScoreModel.generated_at)).limit(1)
        row = (await self.db.execute(query)).scalar_one_or_none()
        if not row:
            return None
        return EmployeeScore(
            id=str(row.id), employee_id=str(row.employee_id),
            tenant_id=str(row.tenant_id), overall_score=row.overall_score,
            signal_volume_score=row.signal_volume_score,
            recency_score=row.recency_score,
            diversity_score=row.diversity_score,
            completion_rate=row.completion_rate,
            confidence_interval_low=row.confidence_interval_low,
            confidence_interval_high=row.confidence_interval_high,
            signal_count=row.signal_count,
            generated_at=row.generated_at,
        )

    async def delete_by_employee(
        self, employee_id: str, tenant_id: str,
    ) -> int:
        from sqlalchemy import delete as sa_delete
        stmt = sa_delete(EmployeeSignalModel).where(
            EmployeeSignalModel.employee_id == uuid.UUID(employee_id),
            EmployeeSignalModel.tenant_id == uuid.UUID(tenant_id),
        )
        result = await self.db.execute(stmt)
        return result.rowcount
