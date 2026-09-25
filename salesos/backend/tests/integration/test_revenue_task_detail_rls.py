"""Database proof for the tenant-scoped Revenue Execution task detail path."""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import async_session, engine
from app.modules.revenue_execution.service import RevenueService


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
async def test_task_detail_is_direct_and_tenant_scoped():
    tenant_a, tenant_b, task_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    async with async_session() as session:
        for tenant_id, suffix in ((tenant_a, "a"), (tenant_b, "b")):
            await session.execute(
                text("INSERT INTO tenants (id, name, slug) VALUES (:id, :name, :slug)"),
                {
                    "id": tenant_id,
                    "name": f"Task Detail {suffix.upper()}",
                    "slug": f"task-detail-{suffix}-{str(tenant_id)[:8]}",
                },
            )
        await _set_tenant(session, str(tenant_a))
        await session.execute(
            text(
                "INSERT INTO tasks (id, tenant_id, title, priority, source, completed) "
                "VALUES (:id, :tenant_id, :title, :priority, :source, false)"
            ),
            {
                "id": task_id,
                "tenant_id": tenant_a,
                "title": "Call decision maker",
                "priority": "high",
                "source": "manual",
            },
        )

        service = RevenueService(session)
        own = await service.get_task(str(task_id), str(tenant_a))
        assert own is not None
        assert own["id"] == task_id
        assert own["title"] == "Call decision maker"

        await _set_tenant(session, str(tenant_b))
        assert await service.get_task(str(task_id), str(tenant_b)) is None

        await _set_tenant(session, None)
        assert await service.get_task(str(task_id), str(tenant_a)) is None
        await session.rollback()
