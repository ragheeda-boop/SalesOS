"""Odoo Integration Foundation — Phase 1: External Identity + Real Client.

Provides:
  - OdooExternalId: maps Odoo record IDs to SalesOS canonical entities
  - OdooClient: real XML-RPC/HTTP client for Odoo 17+
  - OdooSyncService: persistence-layer sync orchestrator
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol
from uuid import uuid4

from celery import shared_task
from sqlalchemy import (
    Column, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from sdk.database import Base

logger = logging.getLogger(__name__)

# ── ORM Model ───────────────────────────────────────────────────────────────


class OdooExternalId(Base):
    """Maps Odoo record IDs to SalesOS canonical entities for idempotent sync."""
    __tablename__ = "odoo_external_ids"

    id: Mapped[str] = mapped_column(PGUUID(as_uuid=True), primary_key=True,
                                     default=lambda: str(uuid4()))
    tenant_id: Mapped[str] = mapped_column(PGUUID(as_uuid=True),
                                            ForeignKey("tenants.id", ondelete="CASCADE"),
                                            nullable=False)

    odoo_model: Mapped[str] = mapped_column(String(100), nullable=False)
    odoo_id: Mapped[int] = mapped_column(Integer, nullable=False)

    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)

    sync_status: Mapped[str] = mapped_column(String(20), nullable=False, default="synced")
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                      default=lambda: datetime.now(timezone.utc))
    odoo_write_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sync_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                  default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                  default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("tenant_id", "odoo_model", "odoo_id", name="uq_odoo_external"),
        Index("idx_oex_tenant", "tenant_id"),
        Index("idx_oex_entity", "entity_type", "entity_id"),
        Index("idx_oex_odoo", "odoo_model", "odoo_id"),
        Index("idx_oex_tenant_status", "tenant_id", "sync_status"),
    )


# ── Client Protocol ─────────────────────────────────────────────────────────


@dataclass
class OdooRecord:
    odoo_model: str
    odoo_id: int
    data: dict
    write_date: datetime | None = None


class OdooClientProtocol(Protocol):
    """Protocol defining Odoo client interface for dependency injection."""

    async def search_read(
        self, model: str, domain: list, fields: list | None = None,
        limit: int | None = None, offset: int = 0,
    ) -> list[dict]: ...

    async def count(self, model: str, domain: list) -> int: ...

    async def read(
        self, model: str, ids: list[int], fields: list | None = None,
    ) -> list[dict]: ...


@dataclass
class OdooConfig:
    url: str
    database: str
    username: str
    api_key: str = ""
    password: str = ""


# ── HTTP Client (Odoo 17+ JSON-RPC) ────────────────────────────────────────


class OdooJsonRpcClient:
    """Odoo 17+ JSON-RPC client using HTTP/JSON (not XML-RPC).

    Uses requests for synchronous calls; wrap in asyncio.to_thread for async.
    """

    def __init__(self, config: OdooConfig):
        self._url = config.url.rstrip("/")
        self._db = config.database
        self._user = config.username
        self._key = config.api_key or config.password
        self._uid: int | None = None
        self._jsonrpc_url = f"{self._url}/jsonrpc"

    def _call(self, service: str, method: str, *args) -> dict:
        import json
        import urllib.request

        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": service,
                "method": method,
                "args": list(args),
            },
            "id": 1,
        }
        req = urllib.request.Request(
            self._jsonrpc_url,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            if "error" in result:
                raise OdooError(result["error"].get("message", str(result["error"])))
            return result.get("result", {})

    def authenticate(self) -> int:
        if not self._uid:
            auth_args = [self._db, self._user, self._key]
            if not self._key:
                auth_args = [self._db, self._user, ""]
            result = self._call("common", "authenticate", *auth_args)
            self._uid = result if isinstance(result, int) else result.get("uid", 0)
        return self._uid or 0

    def search_read(
        self, model: str, domain: list, fields: list | None = None,
        limit: int | None = None, offset: int = 0,
    ) -> list[dict]:
        uid = self.authenticate()
        kwargs = {"domain": domain, "fields": fields or [], "offset": offset}
        if limit:
            kwargs["limit"] = limit
        return self._call("object", "execute_kw",
                          self._db, uid, self._key,
                          model, "search_read",
                          [domain], kwargs)

    def count(self, model: str, domain: list) -> int:
        uid = self.authenticate()
        return self._call("object", "execute_kw",
                          self._db, uid, self._key,
                          model, "search_count",
                          [domain], {})

    def read(
        self, model: str, ids: list[int], fields: list | None = None,
    ) -> list[dict]:
        uid = self.authenticate()
        return self._call("object", "execute_kw",
                          self._db, uid, self._key,
                          model, "read",
                          [ids], {"fields": fields or []})


class OdooError(Exception):
    pass


# ── Sync Service ────────────────────────────────────────────────────────────


@dataclass
class SyncResult:
    entity_type: str
    created: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)


class OdooSyncService:
    """Orchestrates Odoo → SalesOS sync with idempotent identity mapping."""

    ODOO_MODELS = {
        "res.partner": "company",
        "crm.lead": "opportunity",
    }

    def __init__(self, client: OdooClientProtocol, session_factory):
        self._client = client
        self._session_factory = session_factory
        self._algorithm_version = "odoo-sync-v1.0.0"

    async def resolve_entity_id(
        self, tenant_id: str, odoo_model: str, odoo_id: int,
    ) -> str | None:
        """Look up an existing entity mapping. Returns entity_id or None."""
        async with self._session_factory() as session:
            from sqlalchemy import select

            r = await session.execute(
                select(OdooExternalId).where(
                    OdooExternalId.tenant_id == tenant_id,
                    OdooExternalId.odoo_model == odoo_model,
                    OdooExternalId.odoo_id == odoo_id,
                )
            )
            mapping = r.scalar_one_or_none()
            return mapping.entity_id if mapping else None

    async def upsert_mapping(
        self, tenant_id: str, odoo_model: str, odoo_id: int,
        entity_type: str, entity_id: str, odoo_write_date: datetime | None = None,
    ) -> None:
        """Create or update an Odoo → SalesOS identity mapping."""
        async with self._session_factory() as session:
            from sqlalchemy import select, update

            r = await session.execute(
                select(OdooExternalId).where(
                    OdooExternalId.tenant_id == tenant_id,
                    OdooExternalId.odoo_model == odoo_model,
                    OdooExternalId.odoo_id == odoo_id,
                )
            )
            existing = r.scalar_one_or_none()

            if existing:
                await session.execute(
                    update(OdooExternalId)
                    .where(OdooExternalId.id == existing.id)
                    .values(
                        entity_id=entity_id,
                        sync_status="synced",
                        last_synced_at=datetime.now(timezone.utc),
                        odoo_write_date=odoo_write_date,
                        updated_at=datetime.now(timezone.utc),
                    )
                )
            else:
                session.add(OdooExternalId(
                    id=str(uuid4()),
                    tenant_id=tenant_id,
                    odoo_model=odoo_model,
                    odoo_id=odoo_id,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    sync_status="synced",
                    odoo_write_date=odoo_write_date,
                ))
            await session.commit()

    async def sync_partners(
        self, tenant_id: str, limit: int = 50,
    ) -> SyncResult:
        """Sync Odoo partners → SalesOS companies."""
        result = SyncResult(entity_type="company")
        try:
            partners = await self._client.search_read(
                "res.partner",
                [["is_company", "=", True], ["active", "=", True]],
                ["id", "name", "email", "phone", "x_studio_cr_number", "write_date"],
                limit=limit,
            )
        except OdooError as e:
            result.failed = 1
            result.errors.append(str(e))
            return result

        from uuid import uuid4
        from sqlalchemy import select

        for partner in partners:
            odoo_id = partner["id"]
            name = partner.get("name", "")
            cr = partner.get("x_studio_cr_number", "")
            write_date = partner.get("write_date")

            try:
                existing_entity = await self.resolve_entity_id(
                    tenant_id, "res.partner", odoo_id
                )

                async with self._session_factory() as session:
                    if existing_entity:
                        # Update existing company
                        from app.modules.company.models import Company
                        r = await session.execute(
                            select(Company).where(
                                Company.id == existing_entity,
                                Company.tenant_id == tenant_id,
                            )
                        )
                        company = r.scalar_one_or_none()
                        if company:
                            if name and not company.name_ar:
                                company.name_ar = name[:255]
                            company.updated_at = datetime.now(timezone.utc)
                            await session.commit()
                            result.updated += 1
                            await self.upsert_mapping(
                                tenant_id, "res.partner", odoo_id,
                                "company", str(company.id), write_date,
                            )
                            continue

                    # Check CR number dedup
                    if cr:
                        r = await session.execute(
                            select(Company).where(
                                Company.tenant_id == tenant_id,
                                Company.cr_number == cr,
                            )
                        )
                        dup = r.scalar_one_or_none()
                        if dup:
                            await self.upsert_mapping(
                                tenant_id, "res.partner", odoo_id,
                                "company", str(dup.id), write_date,
                            )
                            result.skipped += 1
                            continue

                    # Create new company
                    company_id = str(uuid4())
                    await session.execute(
                        Company.__table__.insert().values(
                            id=company_id, tenant_id=tenant_id,
                            name_ar=name[:255] if name else "Odoo Partner",
                            cr_number=cr or f"ODOO-{odoo_id}",
                            confidence_score=0.5,
                        )
                    )
                    await session.commit()
                    result.created += 1

                    await self.upsert_mapping(
                        tenant_id, "res.partner", odoo_id,
                        "company", company_id, write_date,
                    )
            except Exception as exc:
                result.failed += 1
                    result.errors.append(f"partner {odoo_id}: {exc}")

        return result

    async def sync_contacts(
        self, tenant_id: str, limit: int = 50,
    ) -> SyncResult:
        """Sync Odoo individual partners → SalesOS contacts."""
        result = SyncResult(entity_type="contact")
        try:
            contacts = await self._client.search_read(
                "res.partner",
                [["is_company", "=", False], ["active", "=", True]],
                ["id", "name", "email", "phone", "function", "parent_id", "write_date"],
                limit=limit,
            )
        except OdooError as e:
            result.failed = 1
            result.errors.append(str(e))
            return result

        from uuid import uuid4
        from sqlalchemy import select
        from app.modules.contact.models import Contact

        for contact_data in contacts:
            odoo_id = contact_data["id"]
            name = contact_data.get("name", "")
            email = (contact_data.get("email") or "").lower()
            phone = contact_data.get("phone", "")
            position = contact_data.get("function", "")
            parent_id = contact_data.get("parent_id")
            write_date = contact_data.get("write_date")

            if not name and not email:
                continue

            try:
                existing_entity = await self.resolve_entity_id(
                    tenant_id, "res.partner", odoo_id
                )
                async with self._session_factory() as session:
                    if existing_entity:
                        r = await session.execute(
                            select(Contact).where(
                                Contact.id == existing_entity,
                                Contact.tenant_id == tenant_id,
                            )
                        )
                        c = r.scalar_one_or_none()
                        if c:
                            if name and not c.name:
                                c.name = name[:255]
                            if position and not c.position:
                                c.position = position[:255]
                            c.updated_at = datetime.now(timezone.utc)
                            await session.commit()
                            result.updated += 1
                            await self.upsert_mapping(
                                tenant_id, "res.partner", odoo_id,
                                "contact", str(c.id), write_date,
                            )
                            continue

                    # Email dedup
                    if email:
                        r = await session.execute(
                            select(Contact).where(
                                Contact.tenant_id == tenant_id,
                                Contact.email == email,
                            )
                        )
                        dup = r.scalar_one_or_none()
                        if dup:
                            await self.upsert_mapping(
                                tenant_id, "res.partner", odoo_id,
                                "contact", str(dup.id), write_date,
                            )
                            result.skipped += 1
                            continue

                    # Resolve company mapping if parent_id
                    company_id = None
                    if parent_id:
                        existing_company = await self.resolve_entity_id(
                            tenant_id, "res.partner", parent_id[0] if isinstance(parent_id, list) else parent_id
                        )
                        company_id = existing_company

                    contact_id = str(uuid4())
                    await session.execute(
                        Contact.__table__.insert().values(
                            id=contact_id, tenant_id=tenant_id,
                            name=name[:255] if name else "Odoo Contact",
                            email=email or f"odoo-{odoo_id}@placeholder.local",
                            phone=phone[:50] if phone else None,
                            position=position[:255] if position else None,
                            company_id=company_id,
                            source="odoo_sync",
                        )
                    )
                    await session.commit()
                    result.created += 1
                    await self.upsert_mapping(
                        tenant_id, "res.partner", odoo_id,
                        "contact", contact_id, write_date,
                    )
            except Exception as exc:
                result.failed += 1
                result.errors.append(f"contact {odoo_id}: {exc}")

        return result

    async def sync_leads(
        self, tenant_id: str, limit: int = 50,
    ) -> SyncResult:
        """Sync Odoo CRM leads → SalesOS commercial opportunities."""
        result = SyncResult(entity_type="opportunity")
        try:
            leads = await self._client.search_read(
                "crm.lead",
                [["active", "=", True]],
                ["id", "name", "type", "stage_id", "expected_revenue",
                 "partner_id", "description", "write_date"],
                limit=limit,
            )
        except OdooError as e:
            result.failed = 1
            result.errors.append(str(e))
            return result

        from uuid import uuid4
        from sqlalchemy import select
        from domains.commercial.infrastructure.models import OpportunityModel

        STAGE_MAP = {
            "new": "prospecting", "qualified": "qualification",
            "proposition": "proposal", "won": "closed_won",
        }

        for lead in leads:
            odoo_id = lead["id"]
            name = lead.get("name", "")
            stage = STAGE_MAP.get(lead.get("type", ""), "prospecting")
            value = float(lead.get("expected_revenue", 0))
            partner_id = lead.get("partner_id")
            write_date = lead.get("write_date")

            if not name:
                continue

            try:
                existing_entity = await self.resolve_entity_id(
                    tenant_id, "crm.lead", odoo_id
                )
                async with self._session_factory() as session:
                    if existing_entity:
                        r = await session.execute(
                            select(OpportunityModel).where(
                                OpportunityModel.id == existing_entity,
                                OpportunityModel.tenant_id == tenant_id,
                            )
                        )
                        opp = r.scalar_one_or_none()
                        if opp:
                            if value and opp.value == 0.0:
                                opp.value = value
                            opp.updated_at = datetime.now(timezone.utc)
                            await session.commit()
                            result.updated += 1
                            await self.upsert_mapping(
                                tenant_id, "crm.lead", odoo_id,
                                "opportunity", opp.id, write_date,
                            )
                            continue

                    # Resolve company from partner_id
                    company_id = ""
                    if partner_id:
                        if isinstance(partner_id, list):
                            partner_id = partner_id[0]
                        company_entity = await self.resolve_entity_id(
                            tenant_id, "res.partner", partner_id
                        )
                        if company_entity:
                            company_id = company_entity

                    opp_id = str(uuid4())
                    await session.execute(
                        OpportunityModel.__table__.insert().values(
                            id=opp_id, tenant_id=tenant_id,
                            name=name[:500],
                            company_id=company_id or "",
                            stage=stage,
                            value=value,
                            status="open",
                            probability=0.10,
                            description=lead.get("description", ""),
                        )
                    )
                    await session.commit()
                    result.created += 1
                    await self.upsert_mapping(
                        tenant_id, "crm.lead", odoo_id,
                        "opportunity", opp_id, write_date,
                    )
            except Exception as exc:
                result.failed += 1
                result.errors.append(f"lead {odoo_id}: {exc}")

        return result

    async def run_full_sync(self, tenant_id: str, limit: int = 100) -> dict:
        """Run complete Odoo→SalesOS reconciliation sync."""
        partners = await self.sync_partners(tenant_id, limit)
        contacts = await self.sync_contacts(tenant_id, limit)
        leads = await self.sync_leads(tenant_id, limit)

        return {
            "companies": {"created": partners.created, "updated": partners.updated,
                          "skipped": partners.skipped, "failed": partners.failed},
            "contacts": {"created": contacts.created, "updated": contacts.updated,
                         "skipped": contacts.skipped, "failed": contacts.failed},
            "opportunities": {"created": leads.created, "updated": leads.updated,
                              "skipped": leads.skipped, "failed": leads.failed},
            "errors": partners.errors + contacts.errors + leads.errors,
            "algorithm_version": self._algorithm_version,
        }


# ── Celery Task ────────────────────────────────────────────────────────────


def _run_odoo_sync(tenant_id: str, limit: int = 100) -> dict:
    import asyncio

    async def _sync():
        from app.database import async_session

        config = OdooConfig(
            url=settings.odoo_url,
            database=settings.odoo_database,
            username=settings.odoo_username,
            api_key=settings.odoo_api_key,
        )
        client = OdooJsonRpcClient(config)
        service = OdooSyncService(client, async_session)
        return await service.run_full_sync(tenant_id, limit)

    return asyncio.run(_sync())


@shared_task(name="odoo_sync_all")
def odoo_sync_all() -> dict:
    """Celery task: sync Odoo partners, contacts, and leads for all tenants."""
    logger.info("Odoo sync task started")
    if not settings.odoo_url:
        logger.warning("Odoo sync skipped: ODOO_URL not configured")
        return {"status": "skipped", "reason": "odoo_not_configured"}

    from sqlalchemy import select, text
    from app.database import owner_engine

    result = {}
    async def _run():
        async with owner_engine.connect() as conn:
            tenants = await conn.execute(select(text("id")).select_from(text("tenants")).limit(10))
            for row in tenants.fetchall():
                tid = str(row[0])
                try:
                    result[tid] = _run_odoo_sync(tid, limit=50)
                except Exception as e:
                    result[tid] = {"error": str(e)}
        return result

    return asyncio.run(_run())
