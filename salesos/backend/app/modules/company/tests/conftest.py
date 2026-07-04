"""Fixtures for Company tests."""

import uuid

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.models import Tenant


@pytest_asyncio.fixture
async def test_tenant(db_session: AsyncSession) -> str:
    tenant = Tenant(name="Company Test Tenant", slug=f"co-tenant-{uuid.uuid4().hex[:8]}")
    db_session.add(tenant)
    await db_session.flush()
    return str(tenant.id)
