"""PostgreSQL proof for territory account lookup and tenant isolation."""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import async_session, engine
from domains.commercial.infrastructure.postgres_repositories import PostgresTerritoryRepository
from domains.revenue.territory.service import TerritoryService


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    yield
    await engine.dispose()


async def _set_tenant(session, tenant_id: str | None) -> None:
    if tenant_id:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": tenant_id},
        )
    else:
        await session.execute(text("RESET app.tenant_id"))


@pytest.mark.asyncio
async def test_territory_lookup_uses_json_membership_and_forced_rls():
    tenant_a, tenant_b = str(uuid.uuid4()), str(uuid.uuid4())
    async with async_session() as session:
        for tenant_id, suffix in ((tenant_a, "a"), (tenant_b, "b")):
            await session.execute(
                text("INSERT INTO tenants (id, name, slug) VALUES (:id, :name, :slug)"),
                {
                    "id": tenant_id,
                    "name": f"Territory {suffix.upper()}",
                    "slug": f"territory-{suffix}-{tenant_id[:8]}",
                },
            )

        await _set_tenant(session, tenant_a)
        service = TerritoryService(PostgresTerritoryRepository(session))
        territory_a = await service.create_territory(
            tenant_a, "Riyadh", account_ids=["account-a", "shared-account"]
        )
        found_a = await service._repository.find_territory_for_account(
            tenant_a, "shared-account"
        )
        assert found_a is not None
        assert found_a.id == territory_a.id

        await _set_tenant(session, tenant_b)
        territory_b = await service.create_territory(
            tenant_b, "Jeddah", account_ids=["account-b", "shared-account"]
        )
        found_b = await service._repository.find_territory_for_account(
            tenant_b, "shared-account"
        )
        assert found_b is not None
        assert found_b.id == territory_b.id
        assert await service._repository.find_territory_for_account(tenant_a, "account-a") is None

        await _set_tenant(session, None)
        assert await service.list_territories(tenant_a) == []
        await session.rollback()
