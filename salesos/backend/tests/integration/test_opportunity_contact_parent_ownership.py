"""Database proof for opportunity stakeholder parent ownership.

The canonical opportunity/contact junction uses a text opportunity key, so a
foreign-key error alone cannot prove tenant ownership.  This test exercises
the explicit router guard against a temporary PostgreSQL database.
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy import text

from app.database import async_session, engine, owner_engine
from app.routers.opportunity_contacts import _require_tenant_relationship_parents


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    yield
    await engine.dispose()
    await owner_engine.dispose()


async def _set_tenant(session, tenant_id: str) -> None:
    await session.execute(
        text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
        {"tenant_id": tenant_id},
    )


async def _insert_fixture_rows(session, tenant_id: str, suffix: str) -> tuple[str, str]:
    company_id, contact_id, opportunity_id = (str(uuid.uuid4()) for _ in range(3))
    await _set_tenant(session, tenant_id)
    await session.execute(
        text(
            "INSERT INTO companies (id, tenant_id, name_ar) "
            "VALUES (:id, :tenant_id, :name_ar)"
        ),
        {"id": company_id, "tenant_id": tenant_id, "name_ar": f"شركة العلاقة {suffix}"},
    )
    await session.execute(
        text(
            "INSERT INTO contacts (id, tenant_id, company_id, name) "
            "VALUES (:id, :tenant_id, :company_id, :name)"
        ),
        {
            "id": contact_id,
            "tenant_id": tenant_id,
            "company_id": company_id,
            "name": f"Stakeholder {suffix}",
        },
    )
    await session.execute(
        text(
            "INSERT INTO commercial_opportunities (id, tenant_id, company_id, name) "
            "VALUES (:id, :tenant_id, :company_id, :name)"
        ),
        {
            "id": opportunity_id,
            "tenant_id": tenant_id,
            "company_id": company_id,
            "name": f"Stakeholder deal {suffix}",
        },
    )
    return contact_id, opportunity_id


@pytest.mark.asyncio
async def test_stakeholder_parent_guard_rejects_cross_tenant_edges():
    tenant_a, tenant_b = str(uuid.uuid4()), str(uuid.uuid4())
    # Fixture creation uses the owner connection; assertions below use the
    # restricted application connection so RLS is actually exercised.
    async with owner_engine.begin() as conn:
        for tenant_id, suffix in ((tenant_a, "a"), (tenant_b, "b")):
            await conn.execute(
                text("INSERT INTO tenants (id, name, slug) VALUES (:id, :name, :slug)"),
                {
                    "id": tenant_id,
                    "name": f"Stakeholder QA {suffix}",
                    "slug": f"stakeholder-qa-{suffix}-{tenant_id[:8]}",
                },
            )
        contact_a, opportunity_a = await _insert_fixture_rows(conn, tenant_a, "a")
        contact_b, opportunity_b = await _insert_fixture_rows(conn, tenant_b, "b")

    async with async_session() as session:
        await _set_tenant(session, tenant_a)
        await _require_tenant_relationship_parents(
            session,
            tenant_id=tenant_a,
            opportunity_id=opportunity_a,
            contact_id=uuid.UUID(contact_a),
        )
        with pytest.raises(HTTPException) as cross_contact:
            await _require_tenant_relationship_parents(
                session,
                tenant_id=tenant_a,
                opportunity_id=opportunity_a,
                contact_id=uuid.UUID(contact_b),
            )
        assert cross_contact.value.status_code == 404
        with pytest.raises(HTTPException) as cross_opportunity:
            await _require_tenant_relationship_parents(
                session,
                tenant_id=tenant_a,
                opportunity_id=opportunity_b,
                contact_id=uuid.UUID(contact_a),
            )
        assert cross_opportunity.value.status_code == 404
        await session.rollback()
