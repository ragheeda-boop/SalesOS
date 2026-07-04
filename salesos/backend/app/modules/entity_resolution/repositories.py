"""PostgreSQL repositories for Entity Resolution module."""

import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from sdk.database import SqlAlchemyRepository

from .models import EntityResolutionConflict, EntityResolutionLog, GoldenRecord


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
