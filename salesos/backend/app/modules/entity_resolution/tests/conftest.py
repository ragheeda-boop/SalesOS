"""Fixtures for Entity Resolution tests."""

import uuid
from typing import AsyncGenerator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.models import Tenant


@pytest_asyncio.fixture
async def test_tenant(db_session: AsyncSession) -> str:
    """Create a tenant for entity resolution tests."""
    tenant = Tenant(name="ER Test Tenant", slug=f"er-tenant-{uuid.uuid4().hex[:8]}")
    db_session.add(tenant)
    await db_session.flush()
    return str(tenant.id)


@pytest_asyncio.fixture
async def test_tenant_2(db_session: AsyncSession) -> str:
    """A second tenant for isolation testing."""
    tenant = Tenant(name="ER Test Tenant 2", slug=f"er-tenant-{uuid.uuid4().hex[:8]}")
    db_session.add(tenant)
    await db_session.flush()
    return str(tenant.id)
