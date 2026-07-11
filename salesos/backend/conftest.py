"""Shared test fixtures for all tests (root conftest, visible to all sub-packages)."""

import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

os.environ["SALESOS_TESTING"] = "true"

from app.database import Base
from sdk.permissions import PermissionRegistry, Role

# Register default roles (skipped in production when SALESOS_TESTING is set)
for role_name, perms in PermissionRegistry.default_roles().items():
    PermissionRegistry.register_role(Role(name=role_name, permissions=set(perms)))


def _db_url():
    from app.config import settings
    _host = os.environ.get("TEST_POSTGRES_HOST") or os.environ.get("POSTGRES_HOST", "localhost")
    _password = os.environ.get("POSTGRES_PASSWORD", settings.postgres_password if settings.postgres_password else "test")
    _port = os.environ.get("TEST_POSTGRES_PORT") or os.environ.get("POSTGRES_PORT", "5432")
    return os.environ.get(
        "TEST_DATABASE_URL",
        f"postgresql+asyncpg://{settings.postgres_user}:{_password}@{_host}:{_port}/salesos_test",
    )


@pytest_asyncio.fixture(scope="session")
async def setup_database():
    engine = create_async_engine(_db_url(), echo=False)
    async with engine.begin() as conn:
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS audit"))
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS audit.audit_log (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                tenant_id VARCHAR(255) NOT NULL,
                entity_type VARCHAR(100) NOT NULL,
                entity_id VARCHAR(255) NOT NULL,
                action VARCHAR(50) NOT NULL,
                changes JSONB,
                performed_by VARCHAR(255),
                performed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                ip_address VARCHAR(50),
                request_id VARCHAR(100),
                metadata JSONB
            )
        """))
    await engine.dispose()
    yield
    engine = create_async_engine(_db_url(), echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(text("DROP SCHEMA IF EXISTS audit CASCADE"))
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(_db_url(), echo=False, poolclass=NullPool)
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    session = session_maker()
    try:
        yield session
    finally:
        await session.rollback()
        await session.close()
        await engine.dispose()
