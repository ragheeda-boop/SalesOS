import uuid
from datetime import UTC, datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.common.exceptions import DuplicateError, NotFoundError, is_tenant_isolation_failure
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
from sdk.pagination import CursorPage
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
        """Compute a 0–1 health score from evidence only.

        No contacts/opportunities/signals → 0.0 (honest empty), not a fake 0.5.
        With evidence, start from a neutral 0.5 and adjust.
        """
        if not contacts and not opportunities and not signals:
            return 0.0

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
        self,
        company: Company,
        company_id: str,
        tenant_id: str,
        db: AsyncSession,
    ) -> dict:
        """Return intelligence-layer data: golden record, enrichment, confidence."""
        golden_record_id = None
        golden_record_data = None
        try:
            from app.modules.entity_resolution.models import GoldenRecord

            uid = uuid.UUID(company_id) if isinstance(company_id, str) else company_id
            gr_result = await db.execute(
                select(GoldenRecord).where(
                    GoldenRecord.company_id == uid, GoldenRecord.is_active.is_(True)
                )
            )
            golden_record = gr_result.scalar_one_or_none()
            if golden_record:
                golden_record_id = str(golden_record.id)
                golden_record_data = golden_record.data
        except Exception as e:
            if self.logger:
                self.logger.warn(
                    "company_360.golden_record_failed", company_id=company_id, error=str(e)
                )

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
                    self.logger.warn(
                        "event.publish_failed", entity_type="company", aggregate_id=str(company.id)
                    )

        return company

    async def get_company(self, company_id: str, tenant_id: str) -> Company:
        try:
            cid = uuid.UUID(str(company_id))
            tid = uuid.UUID(str(tenant_id))
        except (ValueError, TypeError, AttributeError):
            # Invalid UUID must be 404 (not asyncpg DataError → 500).
            raise NotFoundError("Company", company_id) from None

        # App-layer tenant filter (defense-in-depth; RLS is not enough alone).
        result = await self.db.execute(
            select(Company)
            .options(selectinload(Company.branches), selectinload(Company.licenses))
            .where(Company.id == cid, Company.tenant_id == tid)
        )
        company = result.scalar_one_or_none()
        if not company:
            raise NotFoundError("Company", company_id)
        return company

    async def update_company(self, company_id: str, updates: dict, *, tenant_id: str) -> Company:
        company = await self.get_company(company_id, tenant_id)
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
                    self.logger.warn(
                        "event.publish_failed", entity_type="company", entity_id=company_id
                    )

        return company

    async def add_branch(self, company_id: str, data: dict, *, tenant_id: str) -> Branch:
        company = await self.get_company(company_id, tenant_id)
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
                    self.logger.warn(
                        "event.publish_failed", entity_type="branch", aggregate_id=str(branch.id)
                    )

        return branch

    async def add_license(self, company_id: str, data: dict, *, tenant_id: str) -> License:
        company = await self.get_company(company_id, tenant_id)
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
                    self.logger.warn(
                        "event.publish_failed", entity_type="license", aggregate_id=str(license.id)
                    )

        return license

    async def add_contact(self, company_id: str, data: dict, *, tenant_id: str) -> Contact:
        company = await self.get_company(company_id, tenant_id)
        payload = dict(data)
        payload.setdefault("tenant_id", company.tenant_id)
        contact = Contact(company_id=company.id, **payload)
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
                    self.logger.warn(
                        "event.publish_failed", entity_type="contact", aggregate_id=str(contact.id)
                    )

        return contact

    async def delete_company(self, company_id: str, *, tenant_id: str) -> None:
        company = await self.get_company(company_id, tenant_id)
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
                    self.logger.warn(
                        "event.publish_failed", entity_type="company", aggregate_id=company_id
                    )

    async def get_company_360(
        self,
        company_id: str,
        tenant_id: str,
        activity_runtime=None,
        db: AsyncSession | None = None,
        kg_engine=None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        company = await self.get_company(company_id, tenant_id)
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

            contacts_total_q = (
                select(sa.func.count())
                .select_from(CompanyContact)
                .where(
                    CompanyContact.company_id == company_id,
                )
            )
            contacts_total = await session.scalar(contacts_total_q) or 0
            result = await session.execute(
                select(CompanyContact)
                .where(
                    CompanyContact.company_id == company_id,
                )
                .order_by(CompanyContact.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            contacts = [
                {
                    "id": str(c.id),
                    "name": c.name,
                    "email": c.email,
                    "phone": c.phone,
                    "position": c.position,
                    "is_primary": c.is_primary,
                }
                for c in result.scalars().all()
            ]
        except Exception as e:
            contacts_total = 0
            if self.logger:
                self.logger.warn("company_360.contacts_failed", company_id=company_id, error=str(e))

        try:
            from domains.commercial.infrastructure.postgres_repositories import (
                PostgresOpportunityRepository,
            )
            from domains.commercial.opportunity.contracts.repository import OpportunityQuery

            opp_repo = PostgresOpportunityRepository(session)
            opp_result = await opp_repo.query(
                OpportunityQuery(
                    tenant_id=tenant_id,
                    company_id=company_id,
                    page=page,
                    page_size=page_size,
                )
            )
            opportunities = [
                {
                    "id": str(o.id),
                    "name": o.name,
                    "value": o.value,
                    "stage": o.stage,
                    "status": o.status.value if hasattr(o.status, "value") else str(o.status),
                    "probability": o.probability,
                    "owner_id": o.owner_id,
                }
                for o in opp_result.items
            ]
            opportunities_total = opp_result.total
            owner_ids = list({o["owner_id"] for o in opportunities if o.get("owner_id")})
            if owner_ids:
                from app.modules.identity.models import User

                user_result = await session.execute(select(User).where(User.id.in_(owner_ids)))
                assigned_employees = [
                    {"id": str(u.id), "full_name": u.full_name, "email": u.email, "role": u.role}
                    for u in user_result.scalars().all()
                ]
        except Exception as e:
            opportunities_total = 0
            if self.logger:
                self.logger.warn(
                    "company_360.opportunities_failed", company_id=company_id, error=str(e)
                )

        timeline_total = 0
        timeline_error: str | None = None
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
            if is_tenant_isolation_failure(e):
                if self.logger:
                    self.logger.error(
                        "company_360.timeline_rls_failed",
                        company_id=company_id,
                        error=str(e),
                    )
                raise
            timeline_error = "unavailable"
            if self.logger:
                self.logger.warn("company_360.timeline_failed", company_id=company_id, error=str(e))

        try:
            from .models import Branch as BranchModel
            from .models import License as LicenseModel

            branch_result = await session.execute(
                select(BranchModel).where(BranchModel.company_id == uid)
            )
            from .schemas import BranchResponse, LicenseResponse

            branches = [BranchResponse.model_validate(b) for b in branch_result.scalars().all()]
            license_result = await session.execute(
                select(LicenseModel).where(LicenseModel.company_id == uid)
            )
            licenses = [
                LicenseResponse.model_validate(lic) for lic in license_result.scalars().all()
            ]  # noqa: E501
        except Exception as e:
            if self.logger:
                self.logger.warn("company_360.branches_failed", company_id=company_id, error=str(e))

        total_revenue = sum(o.get("value", 0) or 0 for o in opportunities)
        active_contracts = sum(
            1 for c in contracts if c.get("metadata", {}).get("status") in ("active", "signed")
        )
        pending_tasks = sum(1 for t in tasks if t.get("metadata", {}).get("status") != "completed")
        upcoming_meetings = sum(
            1 for m in meetings if m.get("metadata", {}).get("status") == "scheduled"
        )
        last_activity_raw = timeline[0].get("timestamp") if timeline else None
        if last_activity_raw is None:
            last_activity = None
        elif hasattr(last_activity_raw, "isoformat"):
            last_activity = last_activity_raw.isoformat()
        else:
            last_activity = str(last_activity_raw)

        # ── Signals: compute → persist → read from DB (fail-graceful) ──
        signals = self._detect_signals(
            company, contacts, opportunities, contracts, branches, tenant_id
        )

        try:
            from app.modules.company.signal_persistence import (
                upsert_signals, read_signals, signals_to_response,
            )
            # Persist computed signals (idempotent upsert)
            await upsert_signals(
                session, tenant_id=tenant_id,
                company_id=uid, signals=signals.get("items", []),
            )
            # Read back from DB for lifecycle-enriched view
            persisted = await read_signals(
                session, tenant_id=tenant_id, company_id=uid,
            )
            if persisted:
                signals = signals_to_response(persisted)
        except Exception as sig_exc:
            # Persistence failure must not break Company 360
            if self.logger:
                self.logger.warning(
                    "company_360.signal_persistence_skipped",
                    company_id=company_id, error=str(sig_exc),
                )

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
                select(GoldenRecord).where(
                    GoldenRecord.company_id == uid, GoldenRecord.is_active.is_(True)
                )
            )
            golden_record = gr_result.scalar_one_or_none()
            if golden_record:
                golden_record_id = str(golden_record.id)
                golden_record_data = golden_record.data
        except Exception as e:
            if self.logger:
                self.logger.warn(
                    "company_360.golden_record_failed", company_id=company_id, error=str(e)
                )

        related_entities = []
        decision_makers = []
        if kg_engine:
            try:
                related_entities = await kg_engine.get_ego_network(company_id=company_id, depth=1)
            except Exception as e:
                if self.logger:
                    self.logger.warn(
                        "company_360.related_entities_failed", company_id=company_id, error=str(e)
                    )
            try:
                dm_nodes = await kg_engine.get_decision_makers(company_id=company_id)
                decision_makers = [n.to_dict() for n in dm_nodes]
            except Exception as e:
                if self.logger:
                    self.logger.warn(
                        "company_360.decision_makers_failed", company_id=company_id, error=str(e)
                    )

        health_score = self._heuristic_health_score(contacts, opportunities, signals["items"])

        # ── ADR-012 Activity Intelligence Integration ──
        engagement_data = None
        try:
            from intelligence.activity_intelligence.readers.postgres_readers import (
                build_company_engines,
            )

            _email_eng, _calendar_eng, engagement_eng, followup_eng = build_company_engines(session)

            followup_status = await followup_eng.get_status(company_id, tenant_id)
            health = await engagement_eng.get_relationship_health(company_id, tenant_id)

            engagement_data = {
                "relationship_health": health.get("relationship_health", 0.0),
                "metrics": health.get("metrics", {}),
                "followup_status": {
                    "assigned": followup_status.assigned,
                    "need_followup": followup_status.need_followup,
                    "waiting_customer": followup_status.waiting_customer,
                    "waiting_you": followup_status.waiting_you,
                    "overdue": followup_status.overdue,
                    "last_outbound_days": followup_status.last_outbound_days,
                    "priority": followup_status.priority,
                },
            }
            if health.get("relationship_health", 0.0) > 0:
                health_score = round(max(0.0, min(1.0, health["relationship_health"])), 4)
        except Exception as e:
            if self.logger:
                self.logger.warn("company_360.adr012_failed", company_id=company_id, error=str(e))

        # ── Entity Resolution section ──
        entity_resolution = {
            "is_golden_record": company.is_golden_record or False,
            "golden_record_id": golden_record_id,
            "confidence_score": company.confidence_score or 0.0,
            "source_count": len(company.source_ids) if company.source_ids else 0,
            "duplicates_detected": 0,
            "conflicts_pending": 0,
        }
        try:
            from app.modules.entity_resolution.models import GoldenRecord

            gr_result = await session.execute(
                select(GoldenRecord).where(
                    GoldenRecord.company_id == uid, GoldenRecord.is_active.is_(True)
                )
            )
            gr = gr_result.scalar_one_or_none()
            if gr:
                entity_resolution["duplicates_detected"] = (
                    len(gr.source_ids) - 1 if gr.source_ids else 0
                )
        except Exception as e:
            if self.logger:
                self.logger.warn(
                    "company_360.entity_resolution_failed", company_id=company_id, error=str(e)
                )

        try:
            from app.modules.entity_resolution.models import EntityResolutionConflict

            conflict_count = await session.scalar(
                select(sa.func.count())
                .select_from(EntityResolutionConflict)
                .where(
                    EntityResolutionConflict.golden_record_id == uid,
                    EntityResolutionConflict.status == "pending",
                )
            )
            entity_resolution["conflicts_pending"] = conflict_count or 0
        except Exception as e:
            if self.logger:
                self.logger.warn(
                    "company_360.conflicts_failed", company_id=company_id, error=str(e)
                )

        # ── CRM section ──
        crm = {
            "deals": opportunities,
            "deals_total": len(opportunities),
            "deals_value": total_revenue,
            "contacts": contacts,
            "contacts_total": contacts_total,
            "opportunities": opportunities,
            "opportunities_total": opportunities_total,
        }

        # ── Timeline section ──
        timeline_section = {
            "events": timeline,
            "count": timeline_total,
            "page": page,
            "total": timeline_total,
            "error": timeline_error,
        }

        # ── Enrichment section ──
        enrichment_section = {
            "firmographics": {
                "industry": company.industry,
                "isic_code": company.isic_code,
                "isic_description": company.isic_description,
                "legal_form": company.legal_form,
                "employees_count": company.employees_count,
                "capital": company.capital,
                "incorporation_date": str(company.incorporation_date)
                if company.incorporation_date
                else None,
                "city": company.city,
                "region": company.region,
                "activity_description": company.activity_description,
                "activity_code": company.activity_code,
            },
            "financials": {
                "total_revenue": total_revenue,
                "total_opportunity_value": total_revenue,
                "active_contracts": active_contracts,
                "pending_invoices": len(invoices),
            },
            "sources": company.source_ids or [],
            "is_golden_record": company.is_golden_record or False,
            "confidence_score": company.confidence_score or 0.0,
            "last_enriched_at": company.updated_at.isoformat() if company.updated_at else None,
        }

        # ── Knowledge Graph section ──
        kg_section: dict[str, Any] = {
            "relationships": [],
            "hierarchy": {
                "parent_company": None,
                "subsidiaries": [],
                "level": 0,
            },
            "competitors": [],
            "partners": [],
            "decision_makers": decision_makers,
        }
        if kg_engine:
            try:
                for item in related_entities:
                    node = item.get("node", {})
                    rel_type = item.get("relationship", "")
                    kg_section["relationships"].append(
                        {
                            "entity_id": node.get("id", ""),
                            "entity_name": node.get("properties", {}).get("name_en")
                            or node.get("properties", {}).get("name_ar"),
                            "relationship_type": rel_type,
                            "strength": 1.0,
                            "properties": node.get("properties", {}),
                        }
                    )
                    if rel_type == "COMPETITOR_OF":
                        kg_section["competitors"].append(node)
                    elif rel_type == "PARTNER_WITH":
                        kg_section["partners"].append(node)
            except Exception as e:
                if self.logger:
                    self.logger.warn("company_360.kg_failed", company_id=company_id, error=str(e))
            try:
                from sqlalchemy import text as sa_text

                row = await session.execute(
                    sa_text(
                        "SELECT id, name_ar, name_en FROM companies WHERE id = :cid AND parent_company_id IS NOT NULL"  # noqa: E501
                    ),
                    {"cid": company_id},
                )
                _ = row.mappings().one_or_none()
            except Exception:
                pass

        return {
            "company": company,
            "crm": crm,
            "timeline": timeline_section,
            "enrichment": enrichment_section,
            "entity_resolution": entity_resolution,
            "knowledge_graph": kg_section,
            "related_entities": related_entities,
            "decision_makers": decision_makers,
            "health_score": health_score,
            "engagement": engagement_data,
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
                "incorporation_date": str(company.incorporation_date)
                if company.incorporation_date
                else None,
            },
            "contacts": contacts,
            "assigned_employees": assigned_employees,
            "emails": emails,
            "meetings": meetings,
            "tasks": tasks,
            "opportunities": opportunities,
            "contracts": contracts,
            "invoices": invoices,
            "timeline_legacy": timeline,
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
            "enrichment_legacy": enrichment,
            "golden_record_id": golden_record_id,
            "golden_record_data": golden_record_data,
        }

    def _detect_signals(
        self,
        company,
        contacts: list,
        opportunities: list,
        contracts: list,
        branches: list,
        tenant_id: str,
    ) -> dict:
        items = []
        now = datetime.now(UTC)

        if hasattr(company, "expiry_date") and company.expiry_date:
            days_left = (company.expiry_date - now.date()).days if company.expiry_date else 365
            if days_left < 0:
                items.append(
                    {
                        "type": "expired",
                        "severity": "critical",
                        "title": "License expired",
                        "days": abs(days_left),
                    }
                )
            elif days_left < 30:
                items.append(
                    {
                        "type": "expiring_soon",
                        "severity": "high",
                        "title": "License expiring soon",
                        "days": days_left,
                    }
                )
            elif days_left < 90:
                items.append(
                    {
                        "type": "expiring",
                        "severity": "medium",
                        "title": "License expiring",
                        "days": days_left,
                    }
                )

        if opportunities:
            stalled = [
                o
                for o in opportunities
                if o.get("stage") == "prospecting" and o.get("status") == "open"
            ]
            if len(stalled) > 3:
                items.append(
                    {
                        "type": "stalled_pipeline",
                        "severity": "medium",
                        "title": f"{len(stalled)} deals stuck in prospecting",
                    }
                )
            won = sum(1 for o in opportunities if o.get("status") in ("won", "closed_won"))
            if won > 0:
                items.append(
                    {
                        "type": "won_deals",
                        "severity": "positive",
                        "title": f"{won} deals won",
                        "value": won,
                    }
                )

        if not contacts:
            items.append(
                {"type": "no_contacts", "severity": "info", "title": "No contacts saved yet"}
            )

        if not branches:
            items.append(
                {"type": "no_branches", "severity": "info", "title": "No branches registered"}
            )

        if company.confidence_score is not None and company.confidence_score < 0.5:
            items.append(
                {
                    "type": "low_confidence",
                    "severity": "info",
                    "title": "Low data confidence",
                    "score": company.confidence_score,
                }
            )

        completeness_fields = [
            (5.0, "name_ar"),
            (5.0, "cr_number"),
            (5.0, "status"),
            (5.0, "name_en"),
            (5.0, "city"),
            (5.0, "region"),
            (5.0, "phone"),
            (5.0, "email"),
            (5.0, "website"),
            (5.0, "address"),
            (5.0, "activity_description"),
            (5.0, "activity_code"),
            (5.0, "industry"),
            (5.0, "legal_form"),
            (20.0 / 3, "employees_count"),
            (20.0 / 3, "capital"),
            (20.0 / 3, "incorporation_date"),
        ]
        filled = sum(
            weight
            for weight, field in completeness_fields
            if getattr(company, field, None) is not None
        )
        if filled < 50.0:
            items.append(
                {
                    "type": "low_data_quality",
                    "severity": "info",
                    "title": "Low data completeness",
                    "score": round(filled, 1),
                }
            )

        return {"items": items, "total": len(items)}

    async def search_companies(
        self,
        tenant_id: str,
        query: str | None = None,
        page: int = 1,
        page_size: int = 20,
        cursor: str | None = None,
    ) -> tuple[list[Company], int]:
        base = select(Company).where(Company.tenant_id == uuid.UUID(tenant_id))
        count_base = (
            select(sa.func.count())
            .select_from(Company)
            .where(Company.tenant_id == uuid.UUID(tenant_id))
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
        # Stable keyset order: created_at + id (matches build_keyset_condition).
        base = base.order_by(Company.created_at.desc(), Company.id.desc())

        if cursor:
            from sdk.pagination import build_keyset_condition, decode_cursor

            cursor_id, cursor_sort = decode_cursor(cursor)
            condition = build_keyset_condition(
                Company,
                cursor_id,
                cursor_sort,
                sort_by="created_at",
                sort_dir="desc",
            )
            base = base.where(condition)

        # Fetch one extra row for has-more detection, then trim to page_size.
        base = base.limit(page_size + 1)
        result = await self.db.execute(base)
        rows = list(result.scalars().all())
        if len(rows) > page_size:
            rows = rows[:page_size]
        return rows, total

    async def search_companies_cursored(
        self,
        tenant_id: str,
        query: str | None = None,
        filters: dict | None = None,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_desc: bool = True,
        cursor: str | None = None,
    ) -> CursorPage[Company]:
        from .repositories import CompanyRepository

        repo = CompanyRepository(self.db)
        return await repo.search_cursored(
            tenant_id=tenant_id,
            query=query,
            filters=filters,
            page_size=page_size,
            sort_by=sort_by,
            sort_desc=sort_desc,
            cursor=cursor,
        )

    async def bulk_update_companies(
        self, company_ids: list[str], updates: dict, *, tenant_id: str
    ) -> dict:
        allowed_fields = {"industry", "size", "status", "tags"}
        field_map = {"size": "employees_count"}
        field_updates = {k: v for k, v in updates.items() if k in allowed_fields}

        updated = 0
        failed = 0
        errors = []

        for cid in company_ids:
            try:
                company = await self.get_company(cid, tenant_id)
                for key, value in field_updates.items():
                    model_key = field_map.get(key, key)
                    if key == "size":
                        try:
                            value = int(value)
                        except (ValueError, TypeError):
                            failed += 1
                            errors.append(
                                {"company_id": cid, "error": f"Invalid size value: {value}"}
                            )
                            continue
                    if hasattr(company, model_key) and value is not None:
                        setattr(company, model_key, value)
                await self.db.flush()
                await self.db.refresh(company)

                audit = AuditTrail(self.db)
                await audit.record(
                    tenant_id=str(company.tenant_id),
                    entity_type="company",
                    entity_id=cid,
                    action="bulk_updated",
                    changes=field_updates,
                )
                if self.event_bus:
                    try:
                        await self.event_bus.publish(
                            CompanyUpdated(
                                tenant_id=str(company.tenant_id),
                                aggregate_id=cid,
                                aggregate_type="company",
                                data={"updates": field_updates, "bulk": True},
                            )
                        )
                    except Exception:
                        if self.logger:
                            self.logger.warn(
                                "event.publish_failed", entity_type="company", aggregate_id=cid
                            )
                updated += 1
            except Exception as e:
                failed += 1
                errors.append({"company_id": cid, "error": str(e)})

        return {"updated": updated, "failed": failed, "errors": errors}

    async def bulk_delete_companies(self, company_ids: list[str], *, tenant_id: str) -> dict:
        deleted = 0

        for cid in company_ids:
            try:
                company = await self.get_company(cid, tenant_id)
                company.is_active = False
                company.status = "deleted"
                await self.db.flush()

                audit = AuditTrail(self.db)
                await audit.record(
                    tenant_id=str(company.tenant_id),
                    entity_type="company",
                    entity_id=cid,
                    action="deleted",
                    changes={"bulk": True},
                )
                deleted += 1
            except Exception:
                pass

        return {"deleted": deleted}

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

        # BATCH: load all existing companies by cr_number in one query instead of N+1
        cr_numbers = []
        for record in records:
            cr = record.get("cr_number") or record.get("CR_number")
            if cr:
                cr_numbers.append(cr)
        if cr_numbers:
            existing_result = await self.db.execute(
                select(Company).where(
                    Company.tenant_id == uuid.UUID(tenant_id),
                    Company.cr_number.in_(cr_numbers),
                )
            )
            existing_companies = {c.cr_number: c for c in existing_result.scalars().all()}
        else:
            existing_companies = {}

        for record in records:
            try:
                cr_number = record.get("cr_number") or record.get("CR_number")
                if not cr_number:
                    errors.append({"record": record, "error": "Missing cr_number"})
                    continue

                existing_company = existing_companies.get(cr_number)

                if existing_company:
                    for key, value in record.items():
                        if hasattr(existing_company, key) and value is not None:
                            setattr(existing_company, key, value)
                    if existing_company.source_ids:
                        if source_slug not in existing_company.source_ids:
                            existing_company.source_ids = existing_company.source_ids + [
                                source_slug
                            ]
                    else:
                        existing_company.source_ids = [source_slug]
                    updated += 1
                else:
                    company_data = {
                        "tenant_id": uuid.UUID(tenant_id),
                        "source_ids": [source_slug],
                        **{
                            k: v for k, v in record.items() if hasattr(Company, k) and v is not None
                        },
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
