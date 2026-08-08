"""Shared fixtures for end-to-end critical path tests."""

import os
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

os.environ.setdefault("SALESOS_TESTING", "true")
os.environ.setdefault("SECRET_KEY", "e2e-test-secret-key-padded-to-32-chars!!")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("NEO4J_PASSWORD", "test")
os.environ.setdefault("JWT_SECRET_KEY", "e2e-test-jwt-secret-key-padded-to-32!!")
os.environ.setdefault("SALESOS_JWKS_ALLOW_REGENERATE", "1")

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.main import app
from app.modules.identity.router import get_register_db


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """FastAPI async test client with DB dependency override.

    Also overrides get_register_db: that dependency calls get_db() as a plain
    generator (not via Depends), so FastAPI's get_db override alone does not
    reach register — which caused FK failures (tenant in salesos_test, user
    insert via live get_db → app DB). Wire db_session_factory for SEC-01
    fail-closed middleware on tenant-scoped paths.
    """

    async def override_get_db():
        yield db_session

    async def override_get_register_db():
        yield db_session

    @asynccontextmanager
    async def _session_factory():
        yield db_session

    prev_factory = getattr(app.state, "db_session_factory", None)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_register_db] = override_get_register_db
    app.state.db_session_factory = _session_factory
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
    if prev_factory is None:
        if hasattr(app.state, "db_session_factory"):
            delattr(app.state, "db_session_factory")
    else:
        app.state.db_session_factory = prev_factory


@pytest_asyncio.fixture
async def test_tenant(db_session: AsyncSession) -> str:
    """Create a fresh tenant and return its ID."""
    from app.modules.identity.models import Tenant

    tenant = Tenant(
        name=f"E2E Tenant {uuid.uuid4().hex[:8]}",
        slug=f"e2e-{uuid.uuid4().hex[:8]}",
    )
    db_session.add(tenant)
    await db_session.flush()
    await db_session.commit()
    return str(tenant.id)


@pytest_asyncio.fixture
async def auth_headers(test_tenant: str, db_session: AsyncSession) -> dict:
    """Register a tenant admin via the API, login, and return auth headers."""
    from app.modules.identity.models import User
    from app.modules.identity.service import create_access_token

    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        email=f"admin-{user_id[:8]}@test.com",
        full_name="E2E Admin",
        tenant_id=test_tenant,
        role="admin",
        password_hash="$2b$12$LJ3m4ys3Lz9k7C5xp.JzUuQWBxGYNkYACRFwHB7RiG4D8xK2HMJXu",
    )
    db_session.add(user)
    await db_session.flush()

    token = create_access_token(user_id, test_tenant)
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-Id": test_tenant,
    }


@pytest_asyncio.fixture
async def registered_user(client: AsyncClient, test_tenant: str, db_session: AsyncSession) -> dict:
    """Register a real user via POST /api/v1/identity/register, then login.

    Returns dict with: access_token, refresh_token, tenant_id, user_email.
    """
    email = f"e2e-user-{uuid.uuid4().hex[:8]}@test.com"
    password = "TestPass123!"

    # Register
    resp = await client.post(
        "/api/v1/identity/register",
        json={
            "email": email,
            "password": password,
            "full_name": "E2E Test User",
            "tenant_id": test_tenant,
        },
    )
    assert resp.status_code in (200, 201), f"Register failed: {resp.text}"
    reg = resp.json()

    from sqlalchemy import select

    from app.modules.identity.models import User

    result = await db_session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user:
        user.role = "admin"
        await db_session.flush()

    return {
        "access_token": reg["access_token"],
        "refresh_token": reg["refresh_token"],
        "tenant_id": reg.get("tenant_id", test_tenant),
        "user_email": email,
        "password": password,
    }


@pytest_asyncio.fixture
def registered_user_headers(registered_user: dict) -> dict:
    """Auth headers from a real registered user."""
    return {
        "Authorization": f"Bearer {registered_user['access_token']}",
        "X-Tenant-Id": registered_user["tenant_id"],
    }
