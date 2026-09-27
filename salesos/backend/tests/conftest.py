"""Test fixtures for tests/ directory (health, architecture)."""

from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

# The disposable test database is selected in backend/conftest.py, which pytest
# loads first and which must set it before `load_dotenv()` and before `app` is
# imported (app.config builds its `settings` singleton at import time). It is
# deliberately NOT set here: by the time this file is imported, load_dotenv has
# already put `.env`'s POSTGRES_DB into os.environ, so a setdefault below would
# be a silent no-op.
#
# tests/integration/conftest.py then refuses the run outright if the resolved
# database is the persistent dev one.
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
