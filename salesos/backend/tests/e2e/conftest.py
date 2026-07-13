"""Shared fixtures for end-to-end critical path tests."""

import os
import uuid
from typing import AsyncGenerator

os.environ.setdefault("SALESOS_TESTING", "true")
os.environ.setdefault("SECRET_KEY", "e2e-test-secret")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("NEO4J_PASSWORD", "test")
os.environ.setdefault("JWT_SECRET_KEY", "e2e-test-jwt-key")

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.main import app


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """FastAPI async test client with DB dependency override."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


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
    return str(tenant.id)


@pytest_asyncio.fixture
async def auth_headers(test_tenant: str, db_session: AsyncSession) -> dict:
    """Register a tenant admin via the API, login, and return auth headers."""
    import jwt as pyjwt
    from app.config import settings

    token = pyjwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "tenant_id": test_tenant,
            "role": "admin",
            "type": "access",
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-Id": test_tenant,
    }


@pytest_asyncio.fixture
async def registered_user(
    client: AsyncClient, test_tenant: str, db_session: AsyncSession
) -> dict:
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
