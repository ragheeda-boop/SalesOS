"""Database proof for seller outcome links and retry safety.

The test runs only against the temporary test database supplied by the
execution harness. It never calls a provider or a production database.
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import async_session, engine, owner_engine
from app.modules.signal_actions.hitl_service import OutcomeOpportunityNotFound, OutcomeService


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    yield
    await engine.dispose()
    await owner_engine.dispose()


async def _set_tenant(session, tenant_id: str | None) -> None:
    if tenant_id:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": tenant_id},
        )
    else:
        await session.execute(text("RESET app.tenant_id"))


async def _insert_opportunity(session, tenant_id: str, suffix: str) -> str:
    opportunity_id = str(uuid.uuid4())
    await _set_tenant(session, tenant_id)
    await session.execute(
        text(
            "INSERT INTO commercial_opportunities (id, tenant_id, company_id, name) "
            "VALUES (:id, :tenant_id, :company_id, :name)"
        ),
        {
            "id": opportunity_id,
            "tenant_id": tenant_id,
            "company_id": f"company-{suffix}",
            "name": f"Outcome link {suffix}",
        },
    )
    return opportunity_id


@pytest.mark.asyncio
async def test_action_outcome_link_is_tenant_scoped_and_idempotent():
    tenant_a, tenant_b = str(uuid.uuid4()), str(uuid.uuid4())
    action_id = str(uuid.uuid4())
    # Seed as the migration owner; the service itself uses the restricted
    # runtime connection and therefore proves the RLS boundary.
    async with owner_engine.begin() as conn:
        for tenant_id, suffix in ((tenant_a, "a"), (tenant_b, "b")):
            await conn.execute(
                text("INSERT INTO tenants (id, name, slug) VALUES (:id, :name, :slug)"),
                {
                    "id": tenant_id,
                    "name": f"Outcome Link {suffix}",
                    "slug": f"outcome-link-{suffix}-{tenant_id[:8]}",
                },
            )
        opportunity_a = await _insert_opportunity(conn, tenant_a, "a")
        opportunity_b = await _insert_opportunity(conn, tenant_b, "b")

    service = OutcomeService(async_session)
    first = await service.record(
        tenant_id=tenant_a,
        action_id=action_id,
        company_name="Linked Company",
        seller_id="seller-a",
        outcome_type="meeting_set",
        opportunity_id=opportunity_a,
        idempotency_key="network-retry-1",
    )
    replay = await service.record(
        tenant_id=tenant_a,
        action_id=action_id,
        company_name="Linked Company",
        seller_id="seller-a",
        outcome_type="meeting_set",
        opportunity_id=opportunity_a,
        idempotency_key="network-retry-1",
    )

    assert first.opportunity_id == opportunity_a
    assert replay.id == first.id
    assert replay.is_replay is True

    async with async_session() as session:
        await _set_tenant(session, tenant_a)
        count = (
            await session.execute(
                text("SELECT count(*) FROM action_outcomes WHERE action_id = :action_id"),
                {"action_id": action_id},
            )
        ).scalar_one()
        assert count == 1

    with pytest.raises(OutcomeOpportunityNotFound):
        await service.record(
            tenant_id=tenant_a,
            action_id=str(uuid.uuid4()),
            company_name="Wrong tenant",
            seller_id="seller-a",
            outcome_type="connected",
            opportunity_id=opportunity_b,
            idempotency_key="cross-tenant-link",
        )

    async with async_session() as session:
        await _set_tenant(session, tenant_b)
        assert (
            await session.execute(
                text("SELECT count(*) FROM action_outcomes WHERE action_id = :action_id"),
                {"action_id": action_id},
            )
        ).scalar_one() == 0
        await session.rollback()
