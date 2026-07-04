import uuid
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import NotFoundError

from .models import Contact


class ContactService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, tenant_id: str, data: dict) -> Contact:
        contact = Contact(
            tenant_id=uuid.UUID(tenant_id),
            company_id=uuid.UUID(data["company_id"]) if data.get("company_id") else None,
            name=data["name"],
            name_ar=data.get("name_ar"),
            email=data.get("email"),
            phone=data.get("phone"),
            mobile=data.get("mobile"),
            position=data.get("position"),
            position_ar=data.get("position_ar"),
            department=data.get("department"),
            is_primary=data.get("is_primary", False),
            source=data.get("source"),
            tags=data.get("tags", []),
        )
        self.db.add(contact)
        await self.db.flush()
        return contact

    async def get(self, contact_id: str) -> Contact:
        result = await self.db.execute(
            select(Contact).where(Contact.id == contact_id)
        )
        contact = result.scalar_one_or_none()
        if not contact:
            raise NotFoundError("Contact", contact_id)
        return contact

    async def update(self, contact_id: str, updates: dict) -> Contact:
        contact = await self.get(contact_id)
        for key, value in updates.items():
            if value is not None and hasattr(contact, key):
                setattr(contact, key, value)
        await self.db.flush()
        return contact

    async def delete(self, contact_id: str) -> None:
        contact = await self.get(contact_id)
        await self.db.delete(contact)
        await self.db.flush()

    async def search(
        self,
        tenant_id: str,
        query: str | None = None,
        filters: dict | None = None,
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

        total = await self.db.scalar(count_base) or 0

        order_col = getattr(Contact, sort_by, Contact.created_at)
        base = base.order_by(order_col.desc() if sort_desc else order_col.asc())
        base = base.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(base)
        return list(result.scalars().all()), total

    async def find_by_company(self, tenant_id: str, company_id: str) -> list[Contact]:
        result = await self.db.execute(
            select(Contact).where(
                Contact.tenant_id == uuid.UUID(tenant_id),
                Contact.company_id == uuid.UUID(company_id),
            )
        )
        return list(result.scalars().all())

    async def find_by_email(self, tenant_id: str, email: str) -> list[Contact]:
        result = await self.db.execute(
            select(Contact).where(
                Contact.tenant_id == uuid.UUID(tenant_id),
                Contact.email == email,
            )
        )
        return list(result.scalars().all())

    async def bulk_upsert(
        self, tenant_id: str, records: list[dict]
    ) -> tuple[list[Contact], list[Contact]]:
        created = []
        updated = []

        for record in records:
            email = record.get("email")
            if not email:
                continue

            existing = await self.db.execute(
                select(Contact).where(
                    Contact.tenant_id == uuid.UUID(tenant_id),
                    Contact.email == email,
                )
            )
            existing_contact = existing.scalar_one_or_none()

            if existing_contact:
                for key, value in record.items():
                    if value is not None and hasattr(existing_contact, key):
                        setattr(existing_contact, key, value)
                updated.append(existing_contact)
            else:
                contact = Contact(
                    tenant_id=uuid.UUID(tenant_id),
                    **{k: v for k, v in record.items()
                       if hasattr(Contact, k) and v is not None},
                )
                self.db.add(contact)
                created.append(contact)

        if created or updated:
            await self.db.flush()

        return created, updated
