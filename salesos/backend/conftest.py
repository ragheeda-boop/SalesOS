"""Shared test fixtures for all tests (root conftest, visible to all sub-packages)."""

import os
from pathlib import Path
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

_env_path = Path(__file__).resolve().parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

os.environ["SALESOS_TESTING"] = "true"

from sdk.database import Base
from sdk.permissions import PermissionRegistry, Role
from app.alembic.lib.rls import ALL_TENANT_TABLES

# Import all ORM models so Base.metadata.create_all creates their tables
import domains.commercial.infrastructure.models  # noqa: F401
import domains.approval.infrastructure.models  # noqa: F401
import domains.copilot.models  # noqa: F401

# Register default roles (skipped in production when SALESOS_TESTING is set)
for role_name, perms in PermissionRegistry.default_roles().items():
    PermissionRegistry.register_role(Role(name=role_name, permissions=set(perms)))


def _db_url():
    from urllib.parse import urlparse, urlunparse
    from app.config import settings

    if os.environ.get("TEST_DATABASE_URL"):
        return os.environ["TEST_DATABASE_URL"]

    _host = os.environ.get("TEST_POSTGRES_HOST") or os.environ.get("POSTGRES_HOST") or settings.postgres_host
    _port = os.environ.get("TEST_POSTGRES_PORT") or os.environ.get("POSTGRES_PORT") or str(settings.postgres_port)
    _password = os.environ.get("POSTGRES_PASSWORD") or settings.postgres_password
    _user = settings.postgres_user

    if not _password and settings.database_url:
        parsed = urlparse(settings.database_url)
        _user = parsed.username or _user
        _password = parsed.password or ""
    if not _password:
        _password = "test"

    return f"postgresql+asyncpg://{_user}:{_password}@{_host}:{_port}/salesos_test"


@pytest_asyncio.fixture(scope="session")
async def setup_database():
    engine = create_async_engine(_db_url(), echo=False)
    async with engine.begin() as conn:
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS pg_trgm'))
        await conn.run_sync(Base.metadata.create_all)
        # Base.metadata.create_all does not execute Alembic's RLS DDL. Keep
        # the ephemeral test schema aligned with the production evidence
        # migration so tenant-isolation tests are repeatable after teardown.
        for table, policy in (
            ("commercial_insights", "tenant_isolation_commercial_insights"),
            ("commercial_evidence_items", "tenant_isolation_commercial_evidence_items"),
            ("commercial_contracts", "tenant_isolation_commercial_contracts"),
        ):
            await conn.execute(text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY"))
            await conn.execute(text(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY"))
            await conn.execute(text(f"DROP POLICY IF EXISTS {policy} ON {table}"))
            await conn.execute(text(
                f"CREATE POLICY {policy} ON {table} FOR ALL "
                "USING (tenant_id::text = current_setting('app.tenant_id', true)) "
                "WITH CHECK (tenant_id::text = current_setting('app.tenant_id', true))"
            ))
        # Base.metadata.create_all does not run the full Alembic RLS graph.
        # Mirror the direct-tenant policies for every tenant table that is
        # present in this ephemeral database so adversarial isolation tests
        # exercise the same fail-closed boundary as the migrated schemas.
        for table in ALL_TENANT_TABLES:
            present = await conn.scalar(
                text("SELECT to_regclass(:qualified)"),
                {"qualified": f"public.{table}"},
            )
            has_tenant_id = await conn.scalar(
                text(
                    "SELECT 1 FROM information_schema.columns "
                    "WHERE table_schema='public' AND table_name=:table "
                    "AND column_name='tenant_id'"
                ),
                {"table": table},
            )
            if not present or not has_tenant_id:
                continue
            policy = f"tenant_isolation_{table}"
            already = await conn.scalar(
                text(
                    "SELECT 1 FROM pg_policies "
                    "WHERE schemaname='public' AND tablename=:table AND policyname=:policy"
                ),
                {"table": table, "policy": policy},
            )
            if already:
                continue
            await conn.execute(text(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY'))
            await conn.execute(text(f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY'))
            await conn.execute(
                text(
                    f'CREATE POLICY "{policy}" ON "{table}" FOR ALL '
                    "USING (tenant_id::text = current_setting('app.tenant_id', true)) "
                    "WITH CHECK (tenant_id::text = current_setting('app.tenant_id', true))"
                )
            )
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
    # pytest-xdist: each worker has its own session-scoped teardown. drop_all
    # against the shared salesos_test DB races workers still running (near-end
    # UndefinedTableError on companies/tenants). Ephemeral CI DBs need no cleanup.
    if os.environ.get("PYTEST_XDIST_WORKER"):
        return
    engine = create_async_engine(_db_url(), echo=False)
    async with engine.begin() as conn:
        # A few legacy migrations create tables that are intentionally not
        # represented in the ORM metadata used by this fixture. Drop the
        # dependent signal table first so metadata teardown remains reliable
        # on a reused local salesos_test database.
        await conn.execute(text("DROP TABLE IF EXISTS company_signals, tenants CASCADE"))
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
