"""Test fixtures for tests/ directory (health, architecture)."""

from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.main import app


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncClient:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_tenant(db_session: AsyncSession) -> str:
    from app.modules.identity.models import Tenant

    tenant = Tenant(name="Test Tenant", slug=f"test-tenant-{uuid4()}")
    db_session.add(tenant)
    await db_session.flush()
    return str(tenant.id)


@pytest.fixture
def test_user_id() -> str:
    return str(uuid4())
