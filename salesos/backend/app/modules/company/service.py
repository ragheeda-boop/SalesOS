import uuid

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

    # ── Health Scoring ───────────────────────────────────────────────

    @staticmethod
    def _heuristic_health_score(
        contacts: list[dict],
        opportunities: list[dict],
        signals: list[dict],
    ) -> float:
        """Compute a 0–1 health score for a company from contacts, opportunities, and signals.

        Baseline 0.5 (neutral). Positive factors raise, negative factors lower.
        """
        score = 0.5

        if contacts:
            score += 0.1
        if opportunities:
            score += 0.15

        for sig in signals:
            sev = sig.get("severity", "")
            if sev == "critical":
                score -= 0.10
            elif sev == "high":
                score -= 0.05
            elif sev == "positive":
                score += 0.05
            elif sev == "info":
                score -= 0.05

        return round(max(0.0, min(1.0, score)), 4)

    # ── User helpers ─────────────────────────────────────────────────

    async def _get_users(self, db: AsyncSession, owner_ids: list[str]) -> list[dict]:
        """Fetch users by IDs, returning empty list on failure or empty input."""
        if not owner_ids:
            return []
        try:
            from app.modules.identity.models import User
            result = await db.execute(select(User).where(User.id.in_(owner_ids)))
            return [
                {"id": str(u.id), "full_name": u.full_name, "email": u.email, "role": u.role}
                for u in result.scalars().all()
            ]
        except Exception as e:
            if self.logger:
                self.logger.warn("company.get_users_failed", error=str(e))
            return []

    # ── Intelligence endpoint ────────────────────────────────────────

    async def get_company_intelligence(
        self, company: Company, company_id: str, tenant_id: str, db: AsyncSession,
    ) -> dict:
        """Return intelligence-layer data: golden record, enrichment, confidence."""
        golden_record_id = None
        golden_record_data = None
        try:
            from app.modules.entity_resolution.models import GoldenRecord
            uid = uuid.UUID(company_id) if isinstance(company_id, str) else company_id
            gr_result = await db.execute(
                select(GoldenRecord).where(GoldenRecord.company_id == uid, GoldenRecord.is_active == True)
            )
            golden_record = gr_result.scalar_one_or_none()
            if golden_record:
                golden_record_id = str(golden_record.id)
                golden_record_data = golden_record.data
        except Exception as e:
            if self.logger:
                self.logger.warn("company_360.golden_record_failed", company_id=company_id, error=str(e))

        enrichment = {
            "sources": company.source_ids or [],
            "is_golden_record": company.is_golden_record or False,
            "confidence_score": company.confidence_score or 0.0,
            "last_enriched_at": company.updated_at.isoformat() if company.updated_at else None,
        }

        return {
            "enrichment": enrichment,
            "golden_record_id": golden_record_id,
            "golden_record_data": golden_record_data,
        }

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
            try:
                await self.event_bus.publish(
                    CompanyCreated(
                        tenant_id=tenant_id,
                        aggregate_id=str(company.id),
                        aggregate_type="company",
                        data={"cr_number": cr_number, "name_ar": name_ar},
                    )
                )
            except Exception:
                if self.logger:
                    self.logger.warn("event.publish_failed", entity_type="company", aggregate_id=str(company.id))

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
        await self.db.refresh(company)

        audit = AuditTrail(self.db)
        await audit.record(
            tenant_id=str(company.tenant_id),
            entity_type="company",
            entity_id=company_id,
            action="updated",
            changes=updates,
        )
        if self.event_bus:
            try:
                await self.event_bus.publish(
                    CompanyUpdated(
                        tenant_id=str(company.tenant_id),
                        aggregate_id=company_id,
                        aggregate_type="company",
                        data={"updates": updates},
                    )
                )
            except Exception:
                if self.logger:
                    self.logger.warn("event.publish_failed", entity_type="company", entity_id=company_id)

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
            try:
                await self.event_bus.publish(
                    BranchCreated(
                        tenant_id=str(company.tenant_id),
                        aggregate_id=str(branch.id),
                        aggregate_type="branch",
                        data={"company_id": company_id, **data},
                    )
                )
            except Exception:
                if self.logger:
                    self.logger.warn("event.publish_failed", entity_type="branch", aggregate_id=str(branch.id))

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
            try:
                await self.event_bus.publish(
                    LicenseCreated(
                        tenant_id=str(company.tenant_id),
                        aggregate_id=str(license.id),
                        aggregate_type="license",
                        data={"company_id": company_id, **data},
                    )
                )
            except Exception:
                if self.logger:
                    self.logger.warn("event.publish_failed", entity_type="license", aggregate_id=str(license.id))

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
            try:
                await self.event_bus.publish(
                    ContactCreated(
                        tenant_id=str(company.tenant_id),
                        aggregate_id=str(contact.id),
                        aggregate_type="contact",
                        data={"company_id": company_id, **data},
                    )
                )
            except Exception:
                if self.logger:
                    self.logger.warn("event.publish_failed", entity_type="contact", aggregate_id=str(contact.id))

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
            try:
                await self.event_bus.publish(
                    CompanyUpdated(
                        tenant_id=str(company.tenant_id),
                        aggregate_id=company_id,
                        aggregate_type="company",
                        data={"status": "deleted"},
                    )
                )
            except Exception:
                if self.logger:
                    self.logger.warn("event.publish_failed", entity_type="company", aggregate_id=company_id)

    async def get_company_360(
        self, company_id: str, tenant_id: str, activity_runtime=None, db: AsyncSession | None = None,
        kg_engine=None,
        page: int = 1, page_size: int = 50,
    ) -> dict:
        company = await self.get_company(company_id)
        session = db or self.db
        uid = uuid.UUID(company_id) if isinstance(company_id, str) else company_id

        contacts = []
        opportunities = []
        assigned_employees = []
        timeline = []
        contracts = []
        invoices = []
        documents = []
        meetings = []
        tasks = []
        emails = []
        branches = []
        licenses = []

        try:
            from .models import Contact as CompanyContact
            contacts_total_q = select(sa.func.count()).select_from(CompanyContact).where(
                CompanyContact.company_id == company_id,
            )
            contacts_total = await session.scalar(contacts_total_q) or 0
            result = await session.execute(
                select(CompanyContact).where(
                    CompanyContact.company_id == company_id,
                ).order_by(CompanyContact.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
            )
            contacts = [
                {"id": str(c.id), "name": c.name, "email": c.email, "phone": c.phone,
                 "position": c.position, "is_primary": c.is_primary}
                for c in result.scalars().all()
            ]
        except Exception as e:
            contacts_total = 0
            if self.logger:
                self.logger.warn("company_360.contacts_failed", company_id=company_id, error=str(e))

        try:
            from domains.commercial.opportunity.contracts.repository import OpportunityQuery
            from domains.commercial.infrastructure.postgres_repositories import PostgresOpportunityRepository
            opp_repo = PostgresOpportunityRepository(session)
            opp_result = await opp_repo.query(OpportunityQuery(
                tenant_id=tenant_id, company_id=company_id,
                page=page, page_size=page_size,
            ))
            opportunities = [
                {"id": str(o.id), "name": o.name, "value": o.value, "stage": o.stage,
                 "status": o.status.value if hasattr(o.status, 'value') else str(o.status),
                 "probability": o.probability, "owner_id": o.owner_id}
                for o in opp_result.items
            ]
            opportunities_total = opp_result.total
            owner_ids = list(set(o["owner_id"] for o in opportunities if o.get("owner_id")))
            if owner_ids:
                from app.modules.identity.models import User
                user_result = await session.execute(
                    select(User).where(User.id.in_(owner_ids))
                )
                assigned_employees = [
                    {"id": str(u.id), "full_name": u.full_name, "email": u.email, "role": u.role}
                    for u in user_result.scalars().all()
                ]
        except Exception as e:
            opportunities_total = 0
            if self.logger:
                self.logger.warn("company_360.opportunities_failed", company_id=company_id, error=str(e))

        timeline_total = 0
        try:
            if activity_runtime:
                items, total = await activity_runtime.get_by_entity(
                    "company", company_id, tenant_id=tenant_id, limit=page_size
                )
                timeline = items
                timeline_total = total
                for a in items:
                    action = a.get("action", "")
                    if action.startswith("meeting"):
                        meetings.append(a)
                    elif action.startswith("email"):
                        emails.append(a)
                    elif action.startswith("task"):
                        tasks.append(a)
                    elif action.startswith("document"):
                        documents.append(a)
                    elif action.startswith("invoice"):
                        invoices.append(a)
                    elif action.startswith("contract"):
                        contracts.append(a)
        except Exception as e:
            if self.logger:
                self.logger.warn("company_360.timeline_failed", company_id=company_id, error=str(e))

        try:
            from .models import Branch as BranchModel, License as LicenseModel
            branch_result = await session.execute(
                select(BranchModel).where(BranchModel.company_id == uid)
            )
            from .schemas import BranchResponse, LicenseResponse
            branches = [BranchResponse.model_validate(b) for b in branch_result.scalars().all()]
            license_result = await session.execute(
                select(LicenseModel).where(LicenseModel.company_id == uid)
            )
            licenses = [LicenseResponse.model_validate(l) for l in license_result.scalars().all()]
        except Exception as e:
            if self.logger:
                self.logger.warn("company_360.branches_failed", company_id=company_id, error=str(e))

        total_revenue = sum(o.get("value", 0) or 0 for o in opportunities)
        active_contracts = sum(1 for c in contracts if c.get("metadata", {}).get("status") in ("active", "signed"))
        pending_tasks = sum(1 for t in tasks if t.get("metadata", {}).get("status") != "completed")
        upcoming_meetings = sum(1 for m in meetings if m.get("metadata", {}).get("status") == "scheduled")
        last_activity = timeline[0].get("timestamp") if timeline else None

        signals = self._detect_signals(company, contacts, opportunities, contracts, branches, tenant_id)

        enrichment = {
            "sources": company.source_ids or [],
            "is_golden_record": company.is_golden_record or False,
            "confidence_score": company.confidence_score or 0.0,
            "last_enriched_at": company.updated_at.isoformat() if company.updated_at else None,
        }

        golden_record_id = None
        golden_record_data = None
        try:
            from app.modules.entity_resolution.models import GoldenRecord
            gr_result = await session.execute(
                select(GoldenRecord).where(GoldenRecord.company_id == uid, GoldenRecord.is_active == True)
            )
            golden_record = gr_result.scalar_one_or_none()
            if golden_record:
                golden_record_id = str(golden_record.id)
                golden_record_data = golden_record.data
        except Exception as e:
            if self.logger:
                self.logger.warn("company_360.golden_record_failed", company_id=company_id, error=str(e))

        related_entities = []
        decision_makers = []
        if kg_engine:
            try:
                related_entities = await kg_engine.get_ego_network(company_id=company_id, depth=1)
            except Exception as e:
                if self.logger:
                    self.logger.warn("company_360.related_entities_failed", company_id=company_id, error=str(e))
            try:
                dm_nodes = await kg_engine.get_decision_makers(company_id=company_id)
                decision_makers = [n.to_dict() for n in dm_nodes]
            except Exception as e:
                if self.logger:
                    self.logger.warn("company_360.decision_makers_failed", company_id=company_id, error=str(e))

        health_score = self._heuristic_health_score(contacts, opportunities, signals["items"])

        return {
            "company": company,
            "related_entities": related_entities,
            "decision_makers": decision_makers,
            "health_score": health_score,
            "overview": {
                "total_contacts": len(contacts),
                "total_opportunities": len(opportunities),
                "total_revenue": total_revenue,
                "active_contracts": active_contracts,
                "pending_tasks": pending_tasks,
                "upcoming_meetings": upcoming_meetings,
                "last_activity": last_activity,
                "signal_count": signals["total"],
                "contacts_page": page,
                "contacts_total": contacts_total,
                "opportunities_page": page,
                "opportunities_total": opportunities_total,
                "timeline_page": page,
                "timeline_total": timeline_total,
            },
            "organization": {
                "branches": branches,
                "departments": [],
                "employees_count": company.employees_count or 0,
                "legal_form": company.legal_form,
                "incorporation_date": str(company.incorporation_date) if company.incorporation_date else None,
            },
            "contacts": contacts,
            "assigned_employees": assigned_employees,
            "emails": emails,
            "meetings": meetings,
            "tasks": tasks,
            "opportunities": opportunities,
            "contracts": contracts,
            "invoices": invoices,
            "timeline": timeline,
            "documents": documents,
            "signals": {"items": signals["items"], "total": signals["total"]},
            "branches": branches,
            "licenses": licenses,
            "contact_count": len(contacts),
            "opportunity_count": len(opportunities),
            "total_revenue": total_revenue,
            "contacts_page": page,
            "contacts_total": contacts_total,
            "opportunities_page": page,
            "opportunities_total": opportunities_total,
            "timeline_page": page,
            "timeline_total": timeline_total,
            "enrichment": enrichment,
            "golden_record_id": golden_record_id,
            "golden_record_data": golden_record_data,
        }

    def _detect_signals(self, company, contacts: list, opportunities: list, contracts: list, branches: list, tenant_id: str) -> dict:
        items = []
        from datetime import datetime
        now = datetime.now()

        if hasattr(company, "expiry_date") and company.expiry_date:
            days_left = (company.expiry_date - now.date()).days if company.expiry_date else 365
            if days_left < 0:
                items.append({"type": "expired", "severity": "critical",
                              "title": "License expired", "days": abs(days_left)})
            elif days_left < 30:
                items.append({"type": "expiring_soon", "severity": "high",
                              "title": "License expiring soon", "days": days_left})
            elif days_left < 90:
                items.append({"type": "expiring", "severity": "medium",
                              "title": "License expiring", "days": days_left})

        if opportunities:
            stalled = [o for o in opportunities if o.get("stage") == "prospecting" and o.get("status") == "open"]
            if len(stalled) > 3:
                items.append({"type": "stalled_pipeline", "severity": "medium",
                              "title": f"{len(stalled)} deals stuck in prospecting"})
            won = sum(1 for o in opportunities if o.get("status") in ("won", "closed_won"))
            if won > 0:
                items.append({"type": "won_deals", "severity": "positive",
                              "title": f"{won} deals won", "value": won})

        if not contacts:
            items.append({"type": "no_contacts", "severity": "info",
                          "title": "No contacts saved yet"})

        if not branches:
            items.append({"type": "no_branches", "severity": "info",
                          "title": "No branches registered"})

        if company.confidence_score is not None and company.confidence_score < 0.5:
            items.append({"type": "low_confidence", "severity": "info",
                          "title": "Low data confidence", "score": company.confidence_score})

        completeness_fields = [
            (5.0, "name_ar"), (5.0, "cr_number"), (5.0, "status"),
            (5.0, "name_en"), (5.0, "city"), (5.0, "region"),
            (5.0, "phone"), (5.0, "email"), (5.0, "website"), (5.0, "address"),
            (5.0, "activity_description"), (5.0, "activity_code"),
            (5.0, "industry"), (5.0, "legal_form"),
            (20.0 / 3, "employees_count"), (20.0 / 3, "capital"),
            (20.0 / 3, "incorporation_date"),
        ]
        filled = sum(
            weight for weight, field in completeness_fields
            if getattr(company, field, None) is not None
        )
        if filled < 50.0:
            items.append({"type": "low_data_quality", "severity": "info",
                          "title": "Low data completeness",
                          "score": round(filled, 1)})

        return {"items": items, "total": len(items)}

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
                            existing_company.source_ids = existing_company.source_ids + [source_slug]
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
            try:
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
            except Exception:
                if self.logger:
                    self.logger.warn("event.publish_failed", entity_type="company", aggregate_id="")

        return {
            "source": source_slug,
            "created": created,
            "updated": updated,
            "errors": errors,
            "total_processed": len(records),
        }
