"""CompanyService cross-tenant read harness — automated isolation proof (app layer).

Not live Railway multi-tenant proof (prod still single shared tenant topology).
Does not weaken auth/RLS; uses existing get_company tenant filter.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import NotFoundError
from app.modules.company.models import Company
from app.modules.company.service import CompanyService
from app.modules.contact.models import Contact
from app.modules.identity.models import Tenant
from tests.support.schema import ensure_tables_created
from tests.support.tenant_isolation import assert_cross_tenant_read_blocked

pytestmark = pytest.mark.asyncio


async def _ensure_tenant(db: AsyncSession, name: str) -> str:
    tenant = Tenant(name=name, slug=f"{name}-{uuid.uuid4().hex[:8]}")
    db.add(tenant)
    await db.flush()
    return str(tenant.id)


class TestCompanyServiceCrossTenant:
    async def test_cross_tenant_company_read_blocked_via_harness(self, db_session: AsyncSession):
        await ensure_tables_created(db_session)
        svc = CompanyService(db_session)

        tenant_a = await _ensure_tenant(db_session, "iso-a")
        tenant_b = await _ensure_tenant(db_session, "iso-b")

        async def create_as(tenant_id: str) -> str:
            company = Company(
                tenant_id=uuid.UUID(tenant_id),
                name_ar="شركة عزل",
                name_en="Isolation Co",
                cr_number=f"CR-{uuid.uuid4().hex[:8].upper()}",
                status="active",
            )
            db_session.add(company)
            await db_session.flush()
            return str(company.id)

        async def read_as(key: str, tenant_id: str):
            try:
                return await svc.get_company(key, tenant_id)
            except NotFoundError:
                return None

        await assert_cross_tenant_read_blocked(
            create_as=create_as,
            read_as=read_as,
            tenant_a=tenant_a,
            tenant_b=tenant_b,
        )

    async def test_company_360_contacts_exclude_foreign_tenant_rows(self, db_session: AsyncSession):
        """Defense-in-depth: 360 contact list filters tenant_id, not company_id alone."""
        await ensure_tables_created(db_session)
        svc = CompanyService(db_session)

        tenant_a = await _ensure_tenant(db_session, "360-a")
        tenant_b = await _ensure_tenant(db_session, "360-b")

        company = Company(
            tenant_id=uuid.UUID(tenant_a),
            name_ar="شركة ثلاثمائة وستون",
            name_en="360 Isolation Co",
            cr_number=f"CR-{uuid.uuid4().hex[:8].upper()}",
            status="active",
        )
        db_session.add(company)
        await db_session.flush()

        own = Contact(
            tenant_id=uuid.UUID(tenant_a),
            company_id=company.id,
            name="Own Contact",
            email="own@example.com",
        )
        leaked = Contact(
            tenant_id=uuid.UUID(tenant_b),
            company_id=company.id,
            name="Foreign Contact",
            email="foreign@example.com",
        )
        db_session.add_all([own, leaked])
        await db_session.flush()

        result = await svc.get_company_360(str(company.id), tenant_a, db=db_session)
        names = {c.get("name") for c in result["contacts"]}
        assert "Own Contact" in names
        assert "Foreign Contact" not in names
        assert result["overview"]["total_contacts"] == 1
