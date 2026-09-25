"""Database proof that commercial deal reviews are tenant-isolated."""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import async_session, engine


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
async def test_commercial_reviews_are_isolated_and_fail_closed():
    tenant_a, tenant_b = str(uuid.uuid4()), str(uuid.uuid4())
    async with async_session() as session:
        for tenant_id, suffix in ((tenant_a, "a"), (tenant_b, "b")):
            await session.execute(
                text("INSERT INTO tenants (id, name, slug) VALUES (:id, :name, :slug)"),
                {
                    "id": tenant_id,
                    "name": f"Commercial Review {suffix.upper()}",
                    "slug": f"commercial-review-{suffix}-{tenant_id[:8]}",
                },
            )
        await _set_tenant(session, str(tenant_a))
        await session.execute(
            text(
                "INSERT INTO commercial_reviews "
                "(id, tenant_id, review_type, target_id, target_type, status, decisions, metadata) "
                "VALUES (:id, :tenant_id, 'deal', 'opportunity-a', 'opportunity', 'pending', '[]', '{}')"
            ),
            {"id": str(uuid.uuid4()), "tenant_id": str(tenant_a)},
        )
        assert (await session.execute(text("SELECT count(*) FROM commercial_reviews"))).scalar() == 1

        await _set_tenant(session, str(tenant_b))
        assert (await session.execute(text("SELECT count(*) FROM commercial_reviews"))).scalar() == 0

        await _set_tenant(session, None)
        assert (await session.execute(text("SELECT count(*) FROM commercial_reviews"))).scalar() == 0
        await session.rollback()
