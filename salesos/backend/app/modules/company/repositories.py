"""PostgreSQL repositories for Company module."""

import uuid
from typing import Any

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from sdk.database import SqlAlchemyRepository

from .models import Branch, Company, Contact, License, Source


class CompanyRepository(SqlAlchemyRepository[Company, uuid.UUID]):
    model_class = Company

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_with_relations(self, company_id: uuid.UUID) -> Company:
        result = await self._session.execute(
            select(Company)
            .options(
                selectinload(Company.branches),
                selectinload(Company.licenses),
                selectinload(Company.contacts),
            )
            .where(Company.id == company_id)
        )
        company = result.scalar_one_or_none()
        if company is None:
            from sdk.exceptions import ObjectNotFoundError
            raise ObjectNotFoundError("Company", str(company_id))
        return company

    async def get_by_cr_number(self, tenant_id: str, cr_number: str) -> Company | None:
        result = await self._session.execute(
            select(Company).where(
                Company.tenant_id == uuid.UUID(tenant_id),
                Company.cr_number == cr_number,
            )
        )
        return result.scalar_one_or_none()

    async def exists_by_cr_number(self, tenant_id: str, cr_number: str) -> bool:
        result = await self._session.execute(
            select(Company.id).where(
                Company.tenant_id == uuid.UUID(tenant_id),
                Company.cr_number == cr_number,
            ).limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def search(
        self,
        tenant_id: str,
        query: str | None = None,
        filters: dict | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> tuple[list[Company], int]:
        base = select(Company).where(Company.tenant_id == uuid.UUID(tenant_id))
        count_base = select(func.count()).select_from(Company).where(
            Company.tenant_id == uuid.UUID(tenant_id)
        )

        if query:
            like = f"%{query}%"
            condition = or_(
                Company.name_ar.ilike(like),
                Company.name_en.ilike(like),
                Company.cr_number.ilike(like),
                Company.city.ilike(like),
                Company.activity_description.ilike(like),
            )
            base = base.where(condition)
            count_base = count_base.where(condition)

        if filters:
            for field, value in filters.items():
                if hasattr(Company, field):
                    if isinstance(value, dict) and "contains" in value:
                        cond = getattr(Company, field).ilike(f"%{value['contains']}%")
                        base = base.where(cond)
                        count_base = count_base.where(cond)
                    else:
                        cond = getattr(Company, field) == value
                        base = base.where(cond)
                        count_base = count_base.where(cond)

        total = await self._session.scalar(count_base) or 0

        order_col = getattr(Company, sort_by, Company.created_at)
        base = base.order_by(order_col.desc() if sort_desc else order_col.asc())
        base = base.offset((page - 1) * page_size).limit(page_size)

        result = await self._session.execute(base)
        return list(result.scalars().all()), total

    async def find_by_status(self, tenant_id: str, status: str) -> list[Company]:
        result = await self._session.execute(
            select(Company).where(
                Company.tenant_id == uuid.UUID(tenant_id),
                Company.status == status,
            )
        )
        return list(result.scalars().all())

    async def find_by_city(self, tenant_id: str, city: str) -> list[Company]:
        result = await self._session.execute(
            select(Company).where(
                Company.tenant_id == uuid.UUID(tenant_id),
                Company.city == city,
            )
        )
        return list(result.scalars().all())

    async def get_cr_numbers_for_tenant(self, tenant_id: str) -> list[str]:
        result = await self._session.execute(
            select(Company.cr_number).where(
                Company.tenant_id == uuid.UUID(tenant_id)
            )
        )
        return [row[0] for row in result.fetchall()]

    async def count_by_status(self, tenant_id: str) -> dict[str, int]:
        from sqlalchemy import func

        result = await self._session.execute(
            select(Company.status, func.count())
            .where(Company.tenant_id == uuid.UUID(tenant_id))
            .group_by(Company.status)
        )
        return dict(result.fetchall())

    async def bulk_upsert(
        self, tenant_id: str, records: list[dict]
    ) -> tuple[list[Company], list[Company]]:
        created = []
        updated = []

        cr_numbers = []
        cr_map: dict[str, dict] = {}
        for record in records:
            cr_number = record.get("cr_number") or record.get("CR_number")
            if not cr_number:
                continue
            cr_numbers.append(cr_number)
            cr_map.setdefault(cr_number, record)

        if not cr_numbers:
            return created, updated

        tid = uuid.UUID(tenant_id)
        existing_result = await self._session.execute(
            select(Company).where(
                Company.tenant_id == tid,
                Company.cr_number.in_(cr_numbers),
            )
        )
        existing_by_cr: dict[str, Company] = {
            c.cr_number: c for c in existing_result.scalars().all()
        }

        for cr_number, record in cr_map.items():
            existing = existing_by_cr.get(cr_number)
            if existing:
                for key, value in record.items():
                    if value is not None and hasattr(existing, key):
                        setattr(existing, key, value)
                updated.append(existing)
            else:
                company = Company(
                    tenant_id=tid,
                    **{k: v for k, v in record.items()
                       if hasattr(Company, k) and v is not None},
                )
                self._session.add(company)
                created.append(company)

        if created or updated:
            await self._session.flush()

        return created, updated


class BranchRepository(SqlAlchemyRepository[Branch, uuid.UUID]):
    model_class = Branch

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def find_by_company(self, company_id: uuid.UUID) -> list[Branch]:
        result = await self._session.execute(
            select(Branch).where(Branch.company_id == company_id)
        )
        return list(result.scalars().all())

    async def find_by_city(self, city: str) -> list[Branch]:
        result = await self._session.execute(
            select(Branch).where(Branch.city == city)
        )
        return list(result.scalars().all())


class LicenseRepository(SqlAlchemyRepository[License, uuid.UUID]):
    model_class = License

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def find_by_company(self, company_id: uuid.UUID) -> list[License]:
        result = await self._session.execute(
            select(License).where(License.company_id == company_id)
        )
        return list(result.scalars().all())

    async def find_expiring(self, within_days: int = 30) -> list[License]:
        from datetime import datetime, timedelta, timezone

        threshold = datetime.now(timezone.utc).date() + timedelta(days=within_days)
        result = await self._session.execute(
            select(License).where(
                License.expiry_date.isnot(None),
                License.expiry_date <= threshold,
                License.expiry_date >= datetime.now(timezone.utc).date(),
            )
        )
        return list(result.scalars().all())

    async def find_by_license_number(self, license_number: str) -> License | None:
        result = await self._session.execute(
            select(License).where(License.license_number == license_number)
        )
        return result.scalar_one_or_none()

    async def find_by_authority(self, authority: str) -> list[License]:
        result = await self._session.execute(
            select(License).where(License.issuing_authority == authority)
        )
        return list(result.scalars().all())


class ContactRepository(SqlAlchemyRepository[Contact, uuid.UUID]):
    model_class = Contact

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def find_by_company(self, company_id: uuid.UUID) -> list[Contact]:
        result = await self._session.execute(
            select(Contact).where(Contact.company_id == company_id)
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

    async def find_by_email(self, email: str) -> list[Contact]:
        result = await self._session.execute(
            select(Contact).where(Contact.email == email)
        )
        return list(result.scalars().all())


class SourceRepository(SqlAlchemyRepository[Source, uuid.UUID]):
    model_class = Source

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_slug(self, slug: str) -> Source | None:
        result = await self._session.execute(
            select(Source).where(Source.slug == slug)
        )
        return result.scalar_one_or_none()

    async def find_active(self) -> list[Source]:
        result = await self._session.execute(
            select(Source).where(Source.is_active.is_(True))
        )
        return list(result.scalars().all())

    async def exists_by_slug(self, slug: str) -> bool:
        result = await self._session.execute(
            select(Source.id).where(Source.slug == slug).limit(1)
        )
        return result.scalar_one_or_none() is not None
