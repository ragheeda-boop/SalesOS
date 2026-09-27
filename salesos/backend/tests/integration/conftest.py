"""Integration test conftest — lightweight fixtures for Kafka integration tests.

These tests mock Kafka and PostgreSQL but exercise the full
outbox → relay → consumer flow in-process.

It also owns the *single* safety rule for DB-backed integration tests, so the
rule cannot be forgotten per-file (see `_refuse_persistent_dev_database`).
"""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock

import pytest

#: Persistent local development database. AGENTS.md forbids writing to it, and
#: nothing in the suite may seed, migrate, or mutate it.
PERSISTENT_DEV_DATABASE = "salesos"

#: Runtime role that is subject to RLS. `app/config.py` defaults the *owner*
#: role to `salesos` (DEC-013 keeps a separate `app_postgres_user` for runtime),
#: so a test that builds its own engine can silently end up on a role that
#: bypasses RLS entirely.
RLS_ENFORCING_ROLE = "salesos_app"


async def assert_rls_enforcing_role(conn) -> None:
    """Fail closed unless `conn` runs as a role that cannot bypass RLS.

    A superuser bypasses RLS unconditionally — even against tables declared
    `FORCE ROW LEVEL SECURITY`. A role carrying BYPASSRLS, or one that *owns*
    an RLS-protected table, bypasses it too. Any of those makes a test's
    "this tenant cannot see that tenant's rows" assertion meaningless, because
    the rows were visible for the wrong reason.

    Call this from any test whose conclusion depends on row visibility.
    Seeding/DDL tests that legitimately need the owner role should not.
    """
    from sqlalchemy import text

    privileged = await conn.scalar(
        text("SELECT rolsuper OR rolbypassrls FROM pg_roles WHERE rolname = current_user")
    )
    assert privileged is False, (
        f"REFUSING: connected as {await conn.scalar(text('SELECT current_user'))!r}, "
        "which is superuser and/or carries BYPASSRLS — it bypasses RLS even on "
        "FORCE ROW LEVEL SECURITY tables, so any tenant-isolation assertion "
        "here would be a false green. Apply "
        "infra/docker/postgres/init/02-app-role.sql and run as salesos_app."
    )

    owns_rls_tables = await conn.scalar(
        text(
            "SELECT count(*) FROM pg_class c "
            "JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE c.relrowsecurity AND c.relowner = "
            "(SELECT oid FROM pg_roles WHERE rolname = current_user)"
        )
    )
    assert not owns_rls_tables, (
        f"REFUSING: connected as {await conn.scalar(text('SELECT current_user'))!r}, "
        f"which owns {owns_rls_tables} RLS-protected table(s) and therefore "
        "bypasses their policies. Run as salesos_app."
    )


@pytest.fixture(scope="session", autouse=True)
def _refuse_persistent_dev_database():
    """Session-wide guard: never let the suite touch the persistent dev DB.

    Previously this rule was copy-pasted into 15 of 65 DB-backed integration
    files; the other 50 had no guard at all, so a misconfigured
    DATABASE_URL/APP_POSTGRES_PASSWORD could seed or migrate real dev data.
    Enforcing it once here makes it impossible to forget.

    Fails CLOSED. If a database is configured, the guard must be able to reach
    it — an authentication or connection error propagates rather than being
    swallowed, because a guard that skips on failure is a guard that verifies
    nothing. It skips only when no database is configured at all, which is the
    case for the fully-mocked Kafka/Postgres tests in this directory.
    """
    import asyncio

    from sqlalchemy import text

    from app.config import settings

    if not settings.app_database_url_override and not settings.app_postgres_password:
        return  # no database configured; nothing to verify

    async def _check() -> None:
        from app.database import engine

        async with engine.connect() as conn:
            db_name = await conn.scalar(text("SELECT current_database()"))
        assert db_name != PERSISTENT_DEV_DATABASE, (
            f"REFUSING: connected to {db_name!r} — the persistent local dev "
            "database. Set APP_POSTGRES_PASSWORD='' (or "
            "APP_DATABASE_URL_OVERRIDE) so app.database.engine points at a "
            "disposable/test database before running the suite."
        )
        await engine.dispose()

    asyncio.run(_check())


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Set test environment variables."""
    os.environ.setdefault("SALESOS_TESTING", "true")
    os.environ.setdefault("SECRET_KEY", "test")
    os.environ.setdefault("POSTGRES_PASSWORD", "test")
    os.environ.setdefault("NEO4J_PASSWORD", "test")
    os.environ.setdefault("JWT_SECRET_KEY", "test")
    os.environ.setdefault("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    yield


def make_mock_session() -> MagicMock:
    """Create a mock DB session whose execute() returns a proper result."""
    session = MagicMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    exec_result = MagicMock()
    exec_result.fetchall.return_value = []
    exec_result.fetchone.return_value = None
    exec_result.scalar.return_value = 0
    exec_result.rowcount = 0
    session.execute.return_value = exec_result
    return session


def make_mock_session_factory(session: MagicMock | None = None) -> MagicMock:
    """Create a mock session factory yielding the given session."""
    if session is None:
        session = make_mock_session()
    factory = MagicMock()
    factory.return_value.__aenter__.return_value = session
    factory.return_value.__aexit__.return_value = None
    return factory
