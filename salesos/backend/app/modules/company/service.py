import uuid
from datetime import date

import sqlalchemy as sa
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.common.exceptions import DuplicateError, NotFoundError
from sdk.audit import AuditTrail
from sdk.events import EventBus
from sdk.events.domain_events import (
    BranchCreated,
    CompanyCreated,
    CompanyIngested,
    CompanyUpdated,
    ContactCreated,
    LicenseCreated,
)
from sdk.telemetry import StructuredLogger

from .models import Branch, Company, Contact, License, Source


class CompanyService:
    def __init__(
        self,
        db: AsyncSession,
        event_bus: EventBus | None = None,
        logger: StructuredLogger | None = None,
    ):
        self.db = db
        self.event_bus = event_bus
        self.logger = logger

    async def create_company(
        self,
        tenant_id: str,
        name_ar: str,
        cr_number: str,
        name_en: str | None = None,
        status: str = "active",
        city: str | None = None,
        region: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        website: str | None = None,
        address: str | None = None,
        activity_description: str | None = None,
        activity_code: str | None = None,
        legal_form: str | None = None,
    ) -> Company:
        existing = await self.db.execute(
            select(Company).where(
                Company.tenant_id == tenant_id,
                Company.cr_number == cr_number,
            )
        )
        if existing.scalar_one_or_none():
            raise DuplicateError("Company", "cr_number", cr_number)

        company = Company(
            tenant_id=uuid.UUID(tenant_id),
            name_ar=name_ar,
            name_en=name_en,
            cr_number=cr_number,
            status=status,
            city=city,
            region=region,
            phone=phone,
            email=email,
            website=website,
            address=address,
            activity_description=activity_description,
            activity_code=activity_code,
            legal_form=legal_form,
        )
        self.db.add(company)
        await self.db.flush()

        audit = AuditTrail(self.db)
        await audit.record(
            tenant_id=tenant_id,
            entity_type="company",
            entity_id=str(company.id),
            action="created",
        )
        if self.event_bus:
            await self.event_bus.publish(
                CompanyCreated(
                    tenant_id=tenant_id,
                    aggregate_id=str(company.id),
                    aggregate_type="company",
                    data={"cr_number": cr_number, "name_ar": name_ar},
                )
            )

        return company

    async def get_company(self, company_id: str) -> Company:
        result = await self.db.execute(
            select(Company)
            .options(selectinload(Company.branches), selectinload(Company.licenses))
            .where(Company.id == company_id)
        )
        company = result.scalar_one_or_none()
        if not company:
            raise NotFoundError("Company", company_id)
        return company

    async def update_company(self, company_id: str, updates: dict) -> Company:
        company = await self.get_company(company_id)
        for key, value in updates.items():
            if value is not None and hasattr(company, key):
                setattr(company, key, value)
        await self.db.flush()

        audit = AuditTrail(self.db)
        await audit.record(
            tenant_id=str(company.tenant_id),
            entity_type="company",
            entity_id=company_id,
            action="updated",
            changes=updates,
        )
        if self.event_bus:
            await self.event_bus.publish(
                CompanyUpdated(
                    tenant_id=str(company.tenant_id),
                    aggregate_id=company_id,
                    aggregate_type="company",
                    data={"updates": updates},
                )
            )

        return company

    async def add_branch(self, company_id: str, data: dict) -> Branch:
        company = await self.get_company(company_id)
        branch = Branch(company_id=company.id, **data)
        self.db.add(branch)
        await self.db.flush()

        audit = AuditTrail(self.db)
        await audit.record(
            tenant_id=str(company.tenant_id),
            entity_type="branch",
            entity_id=str(branch.id),
            action="created",
        )
        if self.event_bus:
            await self.event_bus.publish(
                BranchCreated(
                    tenant_id=str(company.tenant_id),
                    aggregate_id=str(branch.id),
                    aggregate_type="branch",
                    data={"company_id": company_id, **data},
                )
            )

        return branch

    async def add_license(self, company_id: str, data: dict) -> License:
        company = await self.get_company(company_id)
        license = License(company_id=company.id, **data)
        self.db.add(license)
        await self.db.flush()

        audit = AuditTrail(self.db)
        await audit.record(
            tenant_id=str(company.tenant_id),
            entity_type="license",
            entity_id=str(license.id),
            action="created",
        )
        if self.event_bus:
            await self.event_bus.publish(
                LicenseCreated(
                    tenant_id=str(company.tenant_id),
                    aggregate_id=str(license.id),
                    aggregate_type="license",
                    data={"company_id": company_id, **data},
                )
            )

        return license

    async def add_contact(self, company_id: str, data: dict) -> Contact:
        company = await self.get_company(company_id)
        contact = Contact(company_id=company.id, **data)
        self.db.add(contact)
        await self.db.flush()

        audit = AuditTrail(self.db)
        await audit.record(
            tenant_id=str(company.tenant_id),
            entity_type="contact",
            entity_id=str(contact.id),
            action="created",
        )
        if self.event_bus:
            await self.event_bus.publish(
                ContactCreated(
                    tenant_id=str(company.tenant_id),
                    aggregate_id=str(contact.id),
                    aggregate_type="contact",
                    data={"company_id": company_id, **data},
                )
            )

        return contact

    async def delete_company(self, company_id: str) -> None:
        company = await self.get_company(company_id)
        await self.db.delete(company)
        await self.db.flush()

        audit = AuditTrail(self.db)
        await audit.record(
            tenant_id=str(company.tenant_id),
            entity_type="company",
            entity_id=company_id,
            action="deleted",
        )
        if self.event_bus:
            from sdk.events.domain_events import CompanyUpdated
            await self.event_bus.publish(
                CompanyUpdated(
                    tenant_id=str(company.tenant_id),
                    aggregate_id=company_id,
                    aggregate_type="company",
                    data={"status": "deleted"},
                )
            )

    async def search_companies(
        self, tenant_id: str, query: str | None = None,
        page: int = 1, page_size: int = 20,
    ) -> tuple[list[Company], int]:
        base = select(Company).where(Company.tenant_id == uuid.UUID(tenant_id))
        count_base = select(sa.func.count()).select_from(Company).where(
            Company.tenant_id == uuid.UUID(tenant_id)
        )

        if query:
            like = f"%{query}%"
            condition = or_(
                Company.name_ar.ilike(like),
                Company.name_en.ilike(like),
                Company.cr_number.ilike(like),
                Company.city.ilike(like),
            )
            base = base.where(condition)
            count_base = count_base.where(condition)

        total = await self.db.scalar(count_base) or 0
        base = base.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(base)
        return list(result.scalars().all()), total

    async def ingest_from_source(
        self, tenant_id: str, source_slug: str, records: list[dict]
    ) -> dict:
        result = await self.db.execute(select(Source).where(Source.slug == source_slug))
        source = result.scalar_one_or_none()
        if not source:
            raise NotFoundError("Source", source_slug)

        created = 0
        updated = 0
        errors = []

        for record in records:
            try:
                cr_number = record.get("cr_number") or record.get("CR_number")
                if not cr_number:
                    errors.append({"record": record, "error": "Missing cr_number"})
                    continue

                existing = await self.db.execute(
                    select(Company).where(
                        Company.tenant_id == uuid.UUID(tenant_id),
                        Company.cr_number == cr_number,
                    )
                )
                existing_company = existing.scalar_one_or_none()

                if existing_company:
                    for key, value in record.items():
                        if hasattr(existing_company, key) and value is not None:
                            setattr(existing_company, key, value)
                    if existing_company.source_ids:
                        if source_slug not in existing_company.source_ids:
                            existing_company.source_ids.append(source_slug)
                    else:
                        existing_company.source_ids = [source_slug]
                    updated += 1
                else:
                    company_data = {
                        "tenant_id": uuid.UUID(tenant_id),
                        "source_ids": [source_slug],
                        **{k: v for k, v in record.items() if hasattr(Company, k) and v is not None},
                    }
                    company = Company(**company_data)
                    self.db.add(company)
                    created += 1

            except Exception as e:
                errors.append({"record": record, "error": str(e)})

        await self.db.flush()

        if self.event_bus:
            await self.event_bus.publish(
                CompanyIngested(
                    tenant_id=tenant_id,
                    aggregate_id="",
                    aggregate_type="company",
                    data={
                        "source": source_slug,
                        "created": created,
                        "updated": updated,
                        "total_processed": len(records),
                    },
                )
            )

        return {
            "source": source_slug,
            "created": created,
            "updated": updated,
            "errors": errors,
            "total_processed": len(records),
        }
