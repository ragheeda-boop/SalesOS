"""PostgreSQL proof for immutable, tenant-isolated quota snapshots."""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import async_session, engine
from domains.commercial.infrastructure.postgres_repositories import PostgresQuotaRepository
from domains.revenue.quota.service import QuotaService
from domains.revenue.router import list_quota_snapshots


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
async def test_quota_snapshots_are_durable_immutable_and_tenant_scoped():
    """A later attainment update cannot rewrite a historical snapshot."""
    tenant_a, tenant_b = str(uuid.uuid4()), str(uuid.uuid4())
    async with async_session() as session:
        for tenant_id, suffix in ((tenant_a, "a"), (tenant_b, "b")):
            await session.execute(
                text("INSERT INTO tenants (id, name, slug) VALUES (:id, :name, :slug)"),
                {
                    "id": tenant_id,
                    "name": f"Quota Snapshot {suffix.upper()}",
                    "slug": f"quota-snapshot-{suffix}-{tenant_id[:8]}",
                },
            )

        await _set_tenant(session, tenant_a)
        service = QuotaService(PostgresQuotaRepository(session))
        first = await service.create_quota(tenant_a, "rep-a", 100_000, rep_name="A")
        second = await service.create_quota(tenant_a, "rep-b", 50_000, rep_name="B")
        await service.update_attainment(first.id, 25_000)

        snapshot = await service.take_snapshot(tenant_a, "2026-Q3")
        assert snapshot.total_target == 150_000
        assert snapshot.total_attained == 25_000
        assert snapshot.team is not None
        assert snapshot.team.rep_count == 2

        await service.update_attainment(first.id, 80_000)
        assert (await service.get_quota(first.id)).attained_amount == 80_000

        saved = await service.list_snapshots(tenant_a)
        assert len(saved) == 1
        assert saved[0].id == snapshot.id
        assert saved[0].total_target == 150_000
        assert saved[0].total_attained == 25_000
        assert {quota.id for quota in saved[0].quotas} == {first.id, second.id}

        response = await list_quota_snapshots(tenant_a, service, 10)
        assert len(response) == 1
        assert response[0]["id"] == snapshot.id
        assert response[0]["period_label"] == "2026-Q3"
        assert response[0]["quota_count"] == 2
        assert response[0]["total_target"] == 150_000
        assert response[0]["total_attained"] == 25_000
        assert response[0]["overall_attainment"] == 16.67
        assert response[0]["team"]["rep_count"] == 2

        await _set_tenant(session, tenant_b)
        assert await service.list_snapshots(tenant_b) == []
        assert await service.list_snapshots(tenant_a) == []

        await _set_tenant(session, None)
        assert await service.list_snapshots(tenant_a) == []
        await session.rollback()
