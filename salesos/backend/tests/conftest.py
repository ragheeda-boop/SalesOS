"""Test fixtures for tests/ directory (health, architecture)."""

import os
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

# Point the test session at a disposable database BEFORE `app` is imported.
#
# `app/config.py` builds its `settings` singleton at import time, and this file
# imports `app.database`/`app.main` below, so this must be set first or it has no
# effect. `POSTGRES_DB` is used rather than a literal URL so no credential is
# embedded in the test suite, and it feeds both the app engine and the
# `owner_engine` DDL path (both are built from `postgres_db`).
#
# Why: `postgres_db` defaults to "salesos", and the checked-out `backend/.env`
# points `DATABASE_URL` at that same persistent dev database as the `salesos`
# superuser role. Without this default a bare `pytest` seeds, migrates, and
# mutates real dev data — observed as an integration run that did not complete
# within 10 minutes.
#
# `setdefault` keeps it overridable; tests/integration/conftest.py then refuses
# the run outright if the resolved database is the persistent dev one.
os.environ.setdefault("POSTGRES_DB", "salesos_test")

from app.database import get_db  # noqa: E402
from app.main import app  # noqa: E402


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
