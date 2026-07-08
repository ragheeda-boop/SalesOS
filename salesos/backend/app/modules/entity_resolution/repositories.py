"""PostgreSQL repositories for Entity Resolution module."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from sdk.database import SqlAlchemyRepository

from .models import DeadLetterRecord, EntityResolutionConflict, EntityResolutionLog, GoldenRecord


class GoldenRecordRepository(SqlAlchemyRepository[GoldenRecord, uuid.UUID]):
    model_class = GoldenRecord

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_cr_number(self, tenant_id: uuid.UUID, cr_number: str) -> GoldenRecord | None:
        result = await self._session.execute(
            select(GoldenRecord).where(
                GoldenRecord.tenant_id == tenant_id,
                GoldenRecord.cr_number == cr_number,
            )
        )
        return result.scalar_one_or_none()

    async def find_by_tenant(
        self, tenant_id: uuid.UUID, page: int = 1, page_size: int = 20
    ) -> tuple[list[GoldenRecord], int]:
        base = select(GoldenRecord).where(
            GoldenRecord.tenant_id == tenant_id
        ).order_by(GoldenRecord.updated_at.desc())

        count = await self._session.scalar(
            select(func.count()).select_from(GoldenRecord).where(
                GoldenRecord.tenant_id == tenant_id
            )
        ) or 0

        stmt = base.offset((page - 1) * page_size).limit(page_size)
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), count

    async def find_by_confidence_range(
        self, tenant_id: uuid.UUID, min_conf: float, max_conf: float = 1.0
    ) -> list[GoldenRecord]:
        result = await self._session.execute(
            select(GoldenRecord).where(
                GoldenRecord.tenant_id == tenant_id,
                GoldenRecord.confidence_score >= min_conf,
                GoldenRecord.confidence_score <= max_conf,
            )
        )
        return list(result.scalars().all())

    async def count_by_tenant(self, tenant_id: uuid.UUID) -> int:
        return await self._session.scalar(
            select(func.count()).select_from(GoldenRecord).where(
                GoldenRecord.tenant_id == tenant_id
            )
        ) or 0


class ConflictRepository(SqlAlchemyRepository[EntityResolutionConflict, uuid.UUID]):
    model_class = EntityResolutionConflict

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def find_open_by_golden_record(
        self, golden_record_id: uuid.UUID
    ) -> list[EntityResolutionConflict]:
        result = await self._session.execute(
            select(EntityResolutionConflict).where(
                EntityResolutionConflict.golden_record_id == golden_record_id,
                EntityResolutionConflict.status == "open",
            )
        )
        return list(result.scalars().all())

    async def find_by_tenant(
        self, tenant_id: uuid.UUID, status: str | None = None, page: int = 1, page_size: int = 20
    ) -> tuple[list[EntityResolutionConflict], int]:
        base = select(EntityResolutionConflict).where(
            EntityResolutionConflict.tenant_id == tenant_id
        )
        count_base = select(func.count()).select_from(EntityResolutionConflict).where(
            EntityResolutionConflict.tenant_id == tenant_id
        )

        if status:
            base = base.where(EntityResolutionConflict.status == status)
            count_base = count_base.where(EntityResolutionConflict.status == status)

        total = await self._session.scalar(count_base) or 0
        stmt = base.order_by(EntityResolutionConflict.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size)
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total

    async def count_open(self, tenant_id: uuid.UUID) -> int:
        return await self._session.scalar(
            select(func.count()).select_from(EntityResolutionConflict).where(
                EntityResolutionConflict.tenant_id == tenant_id,
                EntityResolutionConflict.status == "open",
            )
        ) or 0


class DeadLetterRepository:
    """Persistence layer for the dead letter queue."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(
        self,
        tenant_id: str | uuid.UUID,
        source_slug: str,
        stage: str,
        record_data: dict,
        error_message: str,
        error_type: str | None = None,
        cr_number: str | None = None,
    ) -> DeadLetterRecord:
        entry = DeadLetterRecord(
            tenant_id=uuid.UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id,
            source_slug=source_slug,
            cr_number=cr_number,
            stage=stage,
            record_data=record_data,
            error_message=error_message,
            error_type=error_type or type(error_message).__name__,
            retry_count=0,
            max_retries=3,
            status="failed",
        )
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def list(
        self,
        tenant_id: str | uuid.UUID,
        status: str | None = None,
        stage: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[DeadLetterRecord], int]:
        tid = uuid.UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id
        query = select(DeadLetterRecord).where(DeadLetterRecord.tenant_id == tid)
        count_query = select(func.count()).select_from(DeadLetterRecord).where(DeadLetterRecord.tenant_id == tid)

        if status:
            query = query.where(DeadLetterRecord.status == status)
            count_query = count_query.where(DeadLetterRecord.status == status)
        if stage:
            query = query.where(DeadLetterRecord.stage == stage)
            count_query = count_query.where(DeadLetterRecord.stage == stage)

        total_result = await self._session.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(DeadLetterRecord.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self._session.execute(query)
        records = list(result.scalars().all())

        return records, total

    async def get_pending_retries(
        self,
        tenant_id: str | uuid.UUID,
        limit: int = 50,
    ) -> list[DeadLetterRecord]:
        tid = uuid.UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id
        query = (
            select(DeadLetterRecord)
            .where(
                DeadLetterRecord.tenant_id == tid,
                DeadLetterRecord.status == "failed",
                DeadLetterRecord.retry_count < DeadLetterRecord.max_retries,
            )
            .order_by(DeadLetterRecord.created_at.asc())
            .limit(limit)
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def mark_retried(self, entry_id: int) -> None:
        stmt = (
            update(DeadLetterRecord)
            .where(DeadLetterRecord.id == entry_id)
            .values(
                retry_count=DeadLetterRecord.retry_count + 1,
                last_retry_at=datetime.now(timezone.utc),
            )
        )
        await self._session.execute(stmt)

    async def mark_resolved(self, entry_id: int) -> None:
        stmt = (
            update(DeadLetterRecord)
            .where(DeadLetterRecord.id == entry_id)
            .values(status="resolved")
        )
        await self._session.execute(stmt)

    async def mark_failed(self, entry_id: int, error_message: str) -> None:
        stmt = (
            update(DeadLetterRecord)
            .where(DeadLetterRecord.id == entry_id)
            .values(
                status="failed",
                error_message=error_message,
                retry_count=DeadLetterRecord.retry_count + 1,
                last_retry_at=datetime.now(timezone.utc),
            )
        )
        await self._session.execute(stmt)

    async def purge(
        self,
        tenant_id: str | uuid.UUID,
        status: str | None = None,
    ) -> int:
        tid = uuid.UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id
        stmt = delete(DeadLetterRecord).where(DeadLetterRecord.tenant_id == tid)
        if status:
            stmt = stmt.where(DeadLetterRecord.status == status)
        result = await self._session.execute(stmt)
        return result.rowcount

    async def count_by_stage(self, tenant_id: str | uuid.UUID) -> dict[str, int]:
        tid = uuid.UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id
        query = (
            select(DeadLetterRecord.stage, func.count())
            .where(DeadLetterRecord.tenant_id == tid, DeadLetterRecord.status == "failed")
            .group_by(DeadLetterRecord.stage)
        )
        result = await self._session.execute(query)
        return dict(result.all())
