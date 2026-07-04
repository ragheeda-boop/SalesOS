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


def _db_url():
    _host = os.environ.get("TEST_POSTGRES_HOST") or os.environ.get("POSTGRES_HOST", "localhost")
    _password = os.environ.get("POSTGRES_PASSWORD", "salesos_dev_password")
    return os.environ.get(
        "TEST_DATABASE_URL",
        f"postgresql+asyncpg://salesos:{_password}@{_host}:5432/salesos_test",
    )


@pytest_asyncio.fixture(scope="session", autouse=True)
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
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(_db_url(), echo=False, poolclass=NullPool)
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    session = session_maker()
    try:
        yield session
    finally:
        await session.rollback()
        await session.close()
        await engine.dispose()
