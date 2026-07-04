"""PostgreSQL repositories for Identity module (Tenant, User)."""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sdk.database import SqlAlchemyRepository

from .models import Tenant, User


class TenantRepository(SqlAlchemyRepository[Tenant, uuid.UUID]):
    model_class = Tenant

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_slug(self, slug: str) -> Tenant | None:
        result = await self._session.execute(
            select(Tenant).where(Tenant.slug == slug)
        )
        return result.scalar_one_or_none()

    async def get_by_domain(self, domain: str) -> Tenant | None:
        result = await self._session.execute(
            select(Tenant).where(Tenant.domain == domain)
        )
        return result.scalar_one_or_none()

    async def find_all_active(self, page: int = 1, page_size: int = 20) -> tuple[list[Tenant], int]:
        return await self.find_all(page=page, page_size=page_size)

    async def exists_by_slug(self, slug: str) -> bool:
        result = await self._session.execute(
            select(Tenant.id).where(Tenant.slug == slug).limit(1)
        )
        return result.scalar_one_or_none() is not None


class UserRepository(SqlAlchemyRepository[User, uuid.UUID]):
    model_class = User

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def find_by_tenant(
        self, tenant_id: str, page: int = 1, page_size: int = 20
    ) -> tuple[list[User], int]:
        from sqlalchemy import func

        base = select(User).where(User.tenant_id == tenant_id).order_by(User.created_at)
        count_q = select(func.count()).select_from(User).where(User.tenant_id == tenant_id)
        total = await self._session.scalar(count_q) or 0

        stmt = base.offset((page - 1) * page_size).limit(page_size)
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total

    async def find_by_role(self, tenant_id: str, role: str) -> list[User]:
        result = await self._session.execute(
            select(User).where(User.tenant_id == tenant_id, User.role == role)
        )
        return list(result.scalars().all())

    async def exists_by_email(self, email: str) -> bool:
        result = await self._session.execute(
            select(User.id).where(User.email == email).limit(1)
        )
        return result.scalar_one_or_none() is not None
