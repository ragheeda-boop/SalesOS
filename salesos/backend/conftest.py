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

# Select a disposable test database BEFORE load_dotenv() below.
#
# This must run first for two reasons:
#   1. `app.config` builds its `settings` singleton at import time, and the
#      first import happens further down this file. Setting it later is a no-op.
#   2. `load_dotenv()` *populates* `os.environ` (it does not override values
#      already present), so the `.env` `POSTGRES_DB=salesos` would otherwise
#      already be in the environment by the time any later conftest tried to
#      `setdefault` it — which is exactly the bug that made a bare
#      `pytest tests/integration` seed, migrate and mutate the persistent dev
#      database (a run that did not complete within 10 minutes).
#
# Placed here, `setdefault` means: an explicitly exported POSTGRES_DB still
# wins, and .env can no longer silently redirect the suite to dev data.
os.environ.setdefault("POSTGRES_DB", "salesos_test")

# Remember which database selectors the *caller* chose, before load_dotenv can
# populate os.environ and make "came from .env" indistinguishable from "came
# from the shell". Only an explicit choice is honoured; anything inherited from
# .env is retargeted to the disposable database.
_CALLER_CHOSE_DB = {
    key
    for key in ("DATABASE_URL", "APP_DATABASE_URL_OVERRIDE", "POSTGRES_DB", "TEST_DATABASE_URL")
    if key in os.environ
}

# Keep the `db_session` fixture (TEST_DATABASE_URL, see _db_url) and
# `app.database.engine` from pointing at two *different* databases.
_test_db_url = os.environ.get("TEST_DATABASE_URL")
if _test_db_url:
    _db_name = _test_db_url.rstrip("/").rsplit("/", 1)[-1].split("?", 1)[0]
    if _db_name and _db_name != os.environ["POSTGRES_DB"]:
        os.environ["POSTGRES_DB"] = _db_name

_env_path = Path(__file__).resolve().parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)


def _retarget_database_url(url: str, db_name: str) -> str:
    """Return `url` pointed at `db_name`, preserving driver prefix and query."""
    from urllib.parse import urlsplit, urlunsplit

    parts = urlsplit(url)
    return urlunsplit(parts._replace(path=f"/{db_name}"))


# POSTGRES_DB alone is NOT enough. `settings.resolved_database_url` prefers
# `database_url`, and `app/database.py` builds `owner_engine` from it — the DDL
# path used by init_db(), tenant bootstrap and the migration tests. So without
# this, `owner_engine` (and `alembic upgrade`, which reads the same property at
# app/alembic/env.py:37) still pointed at the persistent dev database even
# though `engine` had been retargeted. That left a silent hole: app queries
# disposable, DDL still on dev.
if "DATABASE_URL" not in _CALLER_CHOSE_DB:
    _dotenv_db_url = os.environ.get("DATABASE_URL")
    if _dotenv_db_url:
        os.environ["DATABASE_URL"] = _retarget_database_url(
            _dotenv_db_url, os.environ["POSTGRES_DB"]
        )


os.environ["SALESOS_TESTING"] = "true"

from sdk.database import Base
from sdk.permissions import PermissionRegistry, Role
from app.alembic.lib.rls import ALL_TENANT_TABLES

# Import all ORM models so Base.metadata.create_all creates their tables.
# Every module that contributes a mapped class must be imported here, or
# create_all silently skips its tables: a ForeignKey to an unimported model
# raises NoReferencedTableError, and a test that only touches a leaf table just
# gets UndefinedTableError. The chain is transitive — `contacts.company_id`
# needs `companies`, which needs more again — so these must stay in sync with
# the FK graph, not just with what tests appear to touch.
import app.modules.company.models  # noqa: F401
import app.modules.contact.models  # noqa: F401
import app.modules.identity.models  # noqa: F401
import domains.approval.infrastructure.models  # noqa: F401
import domains.commercial.infrastructure.models  # noqa: F401
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


#: Schemas granted to the runtime role, matching
#: infra/docker/postgres/init/02-app-role.sql.
_RUNTIME_GRANT_SCHEMAS = ("public", "audit", "identity", "company", "activity", "crm")


def _sql_str(value: str) -> str:
    """Quote `value` as a Postgres string literal.

    Used only for identifiers interpolated into a DO/EXECUTE body, where bound
    parameters are not permitted. Doubling embedded quotes is the standard
    literal escape, so the result is safe regardless of content.
    """
    escaped = value.replace("'", "''")
    return f"'{escaped}'"


async def _grant_runtime_role(conn) -> None:
    """Give the restricted runtime role the privileges the app engine needs.

    The runtime engine connects as `salesos_app` (DEC-013/R-14), but this
    fixture provisions the schema as the owner role. Nothing in the provisioning
    path issues GRANTs: `Base.metadata.create_all` does not, and neither do the
    Alembic migrations beyond a handful of targeted ones
    (`r4s5t6u7v8w9` grants three parent reads). So the restricted role could
    not read tables that had just been created for it, and an RLS test failed on
    `permission denied for table tenant_llm_budgets` rather than on the tenant
    boundary it exists to prove.

    Grants are driven off the live catalog, not a static table list: tables reach
    this schema from three routes — ORM metadata, the hand-written
    `audit.audit_log` below, and the real Alembic migrations that provisioned
    the database — and no hard-coded list covers all three. (Listing ORM tables
    plus ALL_TENANT_TABLES still missed `tenant_llm_budgets`, which is in
    neither.)

    This mirrors infra/docker/postgres/init/02-app-role.sql, which does the same
    thing at container init. The append-only REVOKEs on the `md_source_*`
    evidence tables are deliberately NOT reproduced here: those are Phase 6
    master-data controls, not a property of this fixture, and silently copying
    them would let a test conftest change production access rules.
    """
    runtime_role = os.environ.get("APP_POSTGRES_USER", "salesos_app")
    if not await conn.scalar(
        text("SELECT 1 FROM pg_roles WHERE rolname = :role"), {"role": runtime_role}
    ):
        return  # role not provisioned in this environment; nothing to grant

    # The identifiers are interpolated, not bound, because Postgres rejects
    # parameters inside a DO/EXECUTE body ("the server expects 0 arguments for
    # this query"). Both values come from this module's own constants plus
    # os.environ — never test input — and every one of them is emitted through
    # `%I`, which quotes as an identifier, so there is no injection path.
    for schema_name in _RUNTIME_GRANT_SCHEMAS:
        await conn.execute(
            text(
                f"""
                DO $grant$ BEGIN
                  IF to_regnamespace({_sql_str(schema_name)}) IS NOT NULL THEN
                    EXECUTE format('GRANT USAGE ON SCHEMA %I TO %I',
                                   {_sql_str(schema_name)}, {_sql_str(runtime_role)});
                    EXECUTE format('GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA %I TO %I',
                                   {_sql_str(schema_name)}, {_sql_str(runtime_role)});
                    EXECUTE format('GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA %I TO %I',
                                   {_sql_str(schema_name)}, {_sql_str(runtime_role)});
                  END IF;
                END
                $grant$;
                """
            )
        )


@pytest_asyncio.fixture(scope="session")
async def setup_database():
    engine = create_async_engine(_db_url(), echo=False)
    async with engine.begin() as conn:
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS pg_trgm'))

        # Fail loudly if the database is not at migration head. Without this the
        # fixture cannot tell a correctly-provisioned schema from a degraded one,
        # because `alembic upgrade head` is a no-op when the version row already
        # says head — even when the tables behind it are missing or were rebuilt
        # from ORM metadata. Better a clear setup error than 40 misleading
        # NotNullViolationErrors pointing at unrelated tests.
        version = await conn.scalar(
            text("SELECT version_num FROM alembic_version LIMIT 1")
        ) if await conn.scalar(
            text("SELECT to_regclass('public.alembic_version') IS NOT NULL")
        ) else None
        if version is None:
            raise RuntimeError(
                "salesos_test is not provisioned. `alembic_version` is absent or "
                "empty, so this fixture would build tables from ORM metadata "
                "alone — which omits the server defaults the migrations define, "
                "and makes raw-INSERT tests fail for the wrong reason. Rebuild "
                "it: drop schema public cascade; create schema public; "
                "alembic upgrade head. See the teardown note below."
            )
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
                ip_address VARCHAR(100),
                request_id VARCHAR(100),
                metadata JSONB
            )
        """))

        await _grant_runtime_role(conn)
    await engine.dispose()
    yield
    # No teardown.
    #
    # This fixture used to end with `Base.metadata.drop_all` plus explicit drops
    # of `tenants` and the `audit` schema, on the assumption that a disposable
    # database should be left empty for the next session. That is backwards, and
    # it was the cause of ~40 phantom integration failures.
    #
    # `create_all` above builds tables from the ORM models, which express
    # defaults on the Python side (`default=0.0` in
    # domains/commercial/infrastructure/models.py) whereas the migrations that
    # define the real schema set them in the database
    # (`server_default="0"` in 0007_commercial_domain.py). Raw INSERT statements
    # in the tests bypass the ORM entirely, so they need the *server* default.
    # Dropping the tables at the end of a session therefore left the next
    # session with ORM-shaped tables that have no server defaults, while
    # `alembic_version` still read `head` so `alembic upgrade` refused to
    # rebuild anything. The result was NotNullViolationError across unrelated
    # tests, and the outcome depended on file ordering: a file that ran first
    # against an intact migrated schema passed, and every file after it
    # inherited the degraded one.
    #
    # It also could not be worked around by re-running migrations, because
    # `alembic upgrade head` is a no-op at head — the damage was invisible to
    # Alembic while being fatal to the tests.
    #
    # The database is disposable by name, and `salesos_test` is rebuilt from
    # migrations by `scripts/reset_test_db.py` (or by hand: drop schema public,
    # create schema public, `alembic upgrade head`). Isolation between tests
    # comes from each test's own fixtures and the GUC scoping in
    # tests/integration/conftest.py, not from truncating a shared schema after
    # the fact.
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
