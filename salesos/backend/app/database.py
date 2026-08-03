import contextlib
import os
from collections.abc import AsyncGenerator
from contextvars import ContextVar
from typing import Any, cast

from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import QueuePool

from app.common.models import Base  # noqa: F401
from app.config import settings

_current_tenant_id: ContextVar[str | None] = ContextVar("current_tenant_id", default=None)


def set_current_tenant_id(tenant_id: str | None) -> None:
    _current_tenant_id.set(tenant_id)


def get_current_tenant_id_context() -> str | None:
    return _current_tenant_id.get(None)


# STORY-02-01 / R-14 remediation (docs/program/RISK_REGISTER.md): request-
# serving traffic connects through app_database_url (salesos_app — non-
# superuser, non-BYPASSRLS — falls back to resolved_database_url if
# salesos_app isn't provisioned in this environment yet, so this is safe to
# deploy everywhere at once). Bootstrap/admin operations (init_db()'s
# CREATE EXTENSION/CREATE SCHEMA, and the Alembic migration check below)
# keep using owner_engine (resolved_database_url, the salesos owner role) —
# CREATE SCHEMA IF NOT EXISTS still requires database-level CREATE
# privilege even when the schema already exists (verified directly:
# `psql -U salesos_app` on an *existing* schema still raises "permission
# denied for database" — Postgres checks the privilege before the
# existence check), so a restricted role cannot run these calls.
# command_timeout: asyncpg-level bound so asyncio.wait_for can observe failure
# when a query stalls (Railway register: wait_for alone did not surface 503).
engine = create_async_engine(
    settings.app_database_url,
    echo=settings.debug,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_timeout=30,
    connect_args={"command_timeout": 10},
)

owner_engine = create_async_engine(
    settings.resolved_database_url,
    echo=settings.debug,
    pool_size=5,
    max_overflow=2,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_timeout=30,
)


def get_pool_metrics() -> dict[str, Any]:
    """Return live connection pool metrics for the metrics endpoint."""
    pool = cast(QueuePool, engine.pool)
    return {
        "pool_size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "total_open": pool.checkedout() + pool.checkedin(),
    }


async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# Register all models so Alembic can discover them
import app.modules.admin.db_models  # noqa: F401  # admin_plans Stripe price cols
import app.modules.api_keys.models  # noqa: F401
import app.modules.audit.models  # noqa: F401
import app.modules.billing.models  # noqa: F401  # STORY-05-01/02 OBJ-321/323
import app.modules.communication_hub.models  # noqa: F401  # DEC-130g
import app.modules.company.models  # noqa: F401
import app.modules.contact.models  # noqa: F401
import app.modules.entity_resolution.models  # noqa: F401
import app.modules.identity.models  # noqa: F401
import app.modules.signal_marketplace.models  # noqa: F401
import app.modules.sso.models  # noqa: F401
import app.modules.telemetry.models  # noqa: F401
import app.modules.webhooks.repository  # noqa: F401  # DEC-130g
import domains.analytics.infrastructure.models  # noqa: F401
import domains.commercial.infrastructure.models  # noqa: F401
import domains.decision_center.postgres_repo  # noqa: F401  # DEC-130b FP
import domains.employee.intelligence_models  # noqa: F401  # DEC-130g
import domains.feature_store.postgres_repo  # noqa: F401  # DEC-130g
import domains.marketplace.db_models  # noqa: F401  # DEC-130b FP
import domains.notifications.db_models  # noqa: F401  # DEC-130g
import domains.revenue.analytics.postgres_repo  # noqa: F401  # DEC-130b FP
import domains.scoring.infrastructure.postgres_repository  # noqa: F401  # DEC-130b FP
import domains.timeline.models  # noqa: F401
import runtime.feature_store  # noqa: F401  # DEC-130b FP company_features

# DEC-130b: Core Table() objects live on private MetaData — copy onto Base so
# alembic check stops proposing false remove_table for live GA paths.
from domains.search.engine.vector_store import _collection_table as _vs_table  # noqa: E402
from runtime.activity_runtime import activity_records as _activity_records  # noqa: E402
from runtime.knowledge_graph_runtime.repository.sql_repository import (  # noqa: E402
    graph_edges as _graph_edges,
)
from sdk.events.store import domain_events as _domain_events  # noqa: E402

for _tbl in (_activity_records, _domain_events, _graph_edges, _vs_table("vectors")):
    if _tbl.key not in Base.metadata.tables:
        _tbl.to_metadata(Base.metadata)
del _tbl, _activity_records, _domain_events, _graph_edges, _vs_table

# DEC-130f: orphan KEEP stubs (raw-SQL live tables; no DROP without dedicated DEC).
from app.db05_orphan_keep import register_orphan_keep_tables  # noqa: E402

register_orphan_keep_tables(Base.metadata)


async def abort_db_session(session: AsyncSession) -> None:
    """Force-drop a stuck asyncpg connection so the pool is not poisoned."""
    import asyncio
    import logging

    log = logging.getLogger("salesos.db")
    try:
        conn = await asyncio.wait_for(session.connection(), timeout=1.0)
        raw = await conn.get_raw_connection()
        driver = getattr(raw, "driver_connection", None)
        if driver is not None and hasattr(driver, "terminate"):
            driver.terminate()
            return
    except Exception as exc:
        log.warning("db_abort_terminate_failed err=%s", type(exc).__name__)
    try:
        await asyncio.wait_for(session.invalidate(), timeout=1.0)
    except Exception as exc:
        log.warning("db_abort_invalidate_failed err=%s", type(exc).__name__)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    import asyncio
    import logging

    from fastapi import HTTPException

    log = logging.getLogger("salesos.db")
    # Bound pool checkout — hung checkouts run BEFORE route handlers (no
    # register_enter log). pool_timeout=30 alone still leaves clients at 499.
    cm = async_session()
    try:
        session = await asyncio.wait_for(cm.__aenter__(), timeout=8.0)
    except TimeoutError as exc:
        log.error("db_checkout_timeout")
        with contextlib.suppress(Exception):
            await cm.__aexit__(TimeoutError, exc, None)
        raise HTTPException(
            status_code=503,
            detail="database.pool_checkout_timeout",
        ) from exc

    try:
        tenant_id = _current_tenant_id.get(None)
        if tenant_id:
            # HARD STOP — DEC-085 / R-26: ALWAYS use set_config(), NEVER SET LOCAL.
            # Postgres rejects bind params in SET/SET LOCAL ("syntax error at or
            # near $1"). Parallel agents reintroduced SET LOCAL a 4th time
            # (2026-08-01); do not revert for mypy/ruff/style. See DEC-085.
            # Bounded: X-Tenant-Id on register/login used to hang here pre-handler.
            try:
                await asyncio.wait_for(
                    session.execute(
                        sa_text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                        {"tenant_id": tenant_id},
                    ),
                    timeout=5.0,
                )
            except TimeoutError as exc:
                log.error("db_set_config_timeout tenant_len=%s", len(tenant_id))
                await abort_db_session(session)
                raise HTTPException(
                    status_code=503,
                    detail="database.set_config_timeout",
                ) from exc
        try:
            yield session
        except Exception:
            try:
                await asyncio.wait_for(session.rollback(), timeout=3.0)
            except Exception:
                await abort_db_session(session)
            raise
        else:
            # Prefer rollback over raising when the session is already aborted
            # (e.g. swallowed DB errors mid-request). Re-raise unexpected commit
            # failures so write endpoints still fail closed.
            try:
                await asyncio.wait_for(session.commit(), timeout=10.0)
            except TimeoutError as exc:
                log.error("db_commit_timeout")
                await abort_db_session(session)
                raise HTTPException(
                    status_code=503,
                    detail="database.commit_timeout",
                ) from exc
            except Exception:
                try:
                    await asyncio.wait_for(session.rollback(), timeout=3.0)
                except Exception:
                    await abort_db_session(session)
                raise
    finally:
        try:
            await asyncio.wait_for(cm.__aexit__(None, None, None), timeout=5.0)
        except Exception as exc:
            log.warning("db_session_exit_failed err=%s", type(exc).__name__)
            await abort_db_session(session)


# CI-19 Wave 2: allowlisted bootstrap DDL identifiers (no sqlalchemy.text).
_ALLOWED_EXTENSIONS = frozenset({"pg_trgm", "uuid-ossp", "vector"})


async def init_db():
    """Initialize database: ensure extensions, schemas, and Alembic migrations are up to date."""
    _extensions = [
        ("pg_trgm", "pg_trgm"),
        ("uuid-ossp", "uuid-ossp"),
        ("vector", "vector"),
    ]
    async with owner_engine.begin() as conn:
        for ext_name, ext_name_dq in _extensions:
            if ext_name_dq not in _ALLOWED_EXTENSIONS:
                raise ValueError(f"Disallowed extension name: {ext_name_dq!r}")
            try:
                # Allowlisted DDL via exec_driver_sql (CI-19 Slice 2 pattern) — not sa_text.
                await conn.exec_driver_sql(f'CREATE EXTENSION IF NOT EXISTS "{ext_name_dq}"')
            except Exception as exc:
                import logging

                logging.getLogger("salesos.db").warning(
                    "Could not create extension %s (%s) — skipping", ext_name, exc
                )
        await conn.exec_driver_sql("CREATE SCHEMA IF NOT EXISTS audit")
    try:
        await _run_migrations_if_needed()
    except Exception as exc:
        import logging

        logging.getLogger("salesos.db").error(
            "Alembic migrations failed (%s) — app will start with degraded schema", exc
        )
    await _verify_tenants_deleted_at()


async def _verify_tenants_deleted_at() -> None:
    """Warn (and attempt migrate) if tenants.deleted_at missing — register flush hang risk."""
    import logging

    from sqlalchemy import text as sa_text

    log = logging.getLogger("salesos.db")
    try:
        async with owner_engine.connect() as conn:
            row = await conn.execute(
                sa_text(
                    "SELECT 1 FROM information_schema.columns "
                    "WHERE table_name='tenants' AND column_name='deleted_at' "
                    "LIMIT 1"
                )
            )
            present = row.fetchone() is not None
        if present:
            log.info("Schema check: tenants.deleted_at present")
            return
        log.error(
            "Schema check: tenants.deleted_at MISSING — register may hang. "
            "Running alembic upgrade head (d4b0e23f5a91)."
        )
        from app.alembic.env import run_async_migrations

        await run_async_migrations()
        log.info("Alembic upgrade after deleted_at miss complete")
    except Exception as exc:
        log.error("tenants.deleted_at verification failed (%s)", exc)


async def _run_migrations_if_needed() -> None:
    """Skip Alembic entirely when database is already at head revision."""
    import logging
    import os as _os

    from alembic.config import Config as AlembicConfig
    from alembic.script import ScriptDirectory
    from sqlalchemy import column, select, table

    log = logging.getLogger("salesos.db")
    try:
        _cfg = AlembicConfig(_os.path.join(_os.path.dirname(__file__), "..", "alembic.ini"))
        _cfg.set_main_option("sqlalchemy.url", settings.resolved_database_url)
        _script = ScriptDirectory.from_config(_cfg)
        _head = _script.get_current_head()
        _alembic_version = table("alembic_version", column("version_num"))
        async with owner_engine.connect() as conn:
            _result = await conn.execute(select(_alembic_version.c.version_num).limit(1))
            _row = _result.fetchone()
        current = _row[0] if _row is not None else None
        log.info("Alembic current=%s head=%s", current, _head)
        if current is not None and current == _head:
            return
    except Exception as exc:
        log.warning("Alembic head check failed (%s) — running migrations", exc)

    # Import only when an upgrade is required (avoids env.py side-effects on hot path).
    from app.alembic.env import run_async_migrations

    log.info("Running Alembic migrations to head…")
    await run_async_migrations()
    log.info("Alembic migrations complete")


async def probe_login_tenant_id(email: str) -> str | None:
    """Pre-auth tenant lookup for FORCE RLS login (DEC-149 / Stage 7).

    Email login has no JWT yet, so salesos_app cannot see ``users`` rows until
    ``app.tenant_id`` is pinned. Probe via owner_engine (BYPASSRLS) — same
    split as init_db / Alembic — then callers pin GUC on the request session.

    Retries once after ``owner_engine.dispose()`` when asyncpg reports a
    cross-event-loop Future (pytest function loops / adversarial suite dispose).
    Under ``SALESOS_TESTING``, dispose before the first attempt so unit tests
    never inherit a pool bound to a prior function-scoped event loop.
    """
    from sqlalchemy.ext.asyncio import AsyncSession as _AsyncSession

    async def _once() -> str | None:
        async with _AsyncSession(owner_engine, expire_on_commit=False) as owner_db:
            result = await owner_db.execute(
                sa_text("SELECT tenant_id::text FROM users WHERE email = :email LIMIT 1"),
                {"email": email},
            )
            row = result.first()
            return str(row[0]) if row and row[0] is not None else None

    if os.environ.get("SALESOS_TESTING"):
        await owner_engine.dispose()

    try:
        return await _once()
    except RuntimeError as exc:
        msg = str(exc).lower()
        if "different loop" not in msg and "attached to a different" not in msg:
            raise
        await owner_engine.dispose()
        try:
            return await _once()
        except RuntimeError:
            # Unit/integration loops may still race; caller treats None as miss.
            return None


async def close_db():
    await engine.dispose()
    await owner_engine.dispose()
