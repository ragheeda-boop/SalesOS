"""PostgreSQL repositories for standalone Contact module.

Implements the Repository Pattern (Constitution Art. 3.3) for the
contacts_standalone table. Follows the same SqlAlchemyRepository base
used by CompanyRepository.
"""

import logging
import uuid
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from sdk.database import SqlAlchemyRepository

from .models import Contact

logger = logging.getLogger(__name__)


class ContactRepository(SqlAlchemyRepository[Contact, uuid.UUID]):
    """PostgreSQL repository for standalone contacts (contacts_standalone table)."""

    model_class = Contact

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def find_by_company(self, company_id: uuid.UUID) -> list[Contact]:
        result = await self._session.execute(
            select(Contact).where(Contact.company_id == company_id)
        )
        return list(result.scalars().all())

    async def find_by_email(self, email: str) -> list[Contact]:
        result = await self._session.execute(
            select(Contact).where(Contact.email == email)
        )
        return list(result.scalars().all())

    async def find_primary_by_company(self, company_id: uuid.UUID) -> Contact | None:
        result = await self._session.execute(
            select(Contact).where(
                Contact.company_id == company_id,
                Contact.is_primary.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def search(
        self,
        tenant_id: str,
        query: str | None = None,
        filters: dict[str, Any] | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> tuple[list[Contact], int]:
        base = select(Contact).where(Contact.tenant_id == uuid.UUID(tenant_id))
        count_base = select(func.count()).select_from(Contact).where(
            Contact.tenant_id == uuid.UUID(tenant_id)
        )

        if query:
            like = f"%{query}%"
            condition = or_(
                Contact.name.ilike(like),
                Contact.name_ar.ilike(like),
                Contact.email.ilike(like),
                Contact.phone.ilike(like),
                Contact.position.ilike(like),
                Contact.department.ilike(like),
            )
            base = base.where(condition)
            count_base = count_base.where(condition)

        if filters:
            for field, value in filters.items():
                if hasattr(Contact, field) and value is not None:
                    base = base.where(getattr(Contact, field) == value)
                    count_base = count_base.where(getattr(Contact, field) == value)

        total = await self._session.scalar(count_base) or 0

        order_col = getattr(Contact, sort_by, Contact.created_at)
        base = base.order_by(order_col.desc() if sort_desc else order_col.asc())
        base = base.offset((page - 1) * page_size).limit(page_size)

        result = await self._session.execute(base)
        return list(result.scalars().all()), total

    async def find_by_tenant(
        self, tenant_id: str, page: int = 1, page_size: int = 20
    ) -> tuple[list[Contact], int]:
        base = select(Contact).where(Contact.tenant_id == uuid.UUID(tenant_id))
        count_base = select(func.count()).select_from(Contact).where(
            Contact.tenant_id == uuid.UUID(tenant_id)
        )

        total = await self._session.scalar(count_base) or 0
        base = base.order_by(Contact.created_at.desc())
        base = base.offset((page - 1) * page_size).limit(page_size)

        result = await self._session.execute(base)
        return list(result.scalars().all()), total

    async def find_by_tenant_and_company(
        self, tenant_id: str, company_id: uuid.UUID
    ) -> list[Contact]:
        result = await self._session.execute(
            select(Contact).where(
                Contact.tenant_id == uuid.UUID(tenant_id),
                Contact.company_id == company_id,
            )
        )
        return list(result.scalars().all())

    async def find_by_tenant_and_email(
        self, tenant_id: str, email: str
    ) -> list[Contact]:
        result = await self._session.execute(
            select(Contact).where(
                Contact.tenant_id == uuid.UUID(tenant_id),
                Contact.email == email,
            )
        )
        return list(result.scalars().all())

    async def bulk_upsert(
        self, tenant_id: str, records: list[dict]
    ) -> tuple[list[Contact], list[Contact]]:
        created: list[Contact] = []
        updated: list[Contact] = []

        for record in records:
            email = record.get("email")
            if not email:
                continue

            existing = await self.find_by_tenant_and_email(tenant_id, email)
            if existing:
                contact = existing[0]
                for key, value in record.items():
                    if value is not None and hasattr(contact, key):
                        setattr(contact, key, value)
                updated.append(contact)
            else:
                contact = Contact(
                    tenant_id=uuid.UUID(tenant_id),
                    **{
                        k: v
                        for k, v in record.items()
                        if hasattr(Contact, k) and v is not None
                    },
                )
                self._session.add(contact)
                created.append(contact)

        if created or updated:
            await self._session.flush()

        return created, updated
