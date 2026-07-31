from contextvars import ContextVar
from typing import Any

from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

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
engine = create_async_engine(
    settings.app_database_url,
    echo=settings.debug,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_timeout=30,
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
    pool = engine.pool
    return {
        "pool_size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "total_open": pool.checkedout() + pool.checkedin(),
    }


async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# Register all models so Alembic can discover them
import app.modules.api_keys.models  # noqa: F401
import app.modules.audit.models  # noqa: F401
import app.modules.company.models  # noqa: F401
import app.modules.contact.models  # noqa: F401
import app.modules.entity_resolution.models  # noqa: F401
import app.modules.identity.models  # noqa: F401
import app.modules.signal_marketplace.models  # noqa: F401
import app.modules.sso.models  # noqa: F401
import app.modules.telemetry.models  # noqa: F401
import domains.analytics.infrastructure.models  # noqa: F401
import domains.commercial.infrastructure.models  # noqa: F401
import domains.timeline.models  # noqa: F401


async def get_db() -> AsyncSession:
    async with async_session() as session:
        tenant_id = _current_tenant_id.get(None)
        if tenant_id:
            await session.execute(
                sa_text("SET LOCAL app.tenant_id = :tenant_id"),
                {"tenant_id": tenant_id},
            )
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        else:
            # Prefer rollback over raising when the session is already aborted
            # (e.g. swallowed DB errors mid-request). Re-raise unexpected commit
            # failures so write endpoints still fail closed.
            try:
                await session.commit()
            except Exception:
                await session.rollback()
                raise


async def init_db():
    """Initialize database: ensure extensions, schemas, and Alembic migrations are up to date."""
    _extensions = [
        ("pg_trgm", "pg_trgm"),
        ("uuid-ossp", "uuid-ossp"),
        ("vector", "vector"),
    ]
    async with owner_engine.begin() as conn:
        for ext_name, ext_name_dq in _extensions:
            try:
                await conn.execute(sa_text(f'CREATE EXTENSION IF NOT EXISTS "{ext_name_dq}"'))
            except Exception as exc:
                import logging

                logging.getLogger("salesos.db").warning(
                    "Could not create extension %s (%s) — skipping", ext_name, exc
                )
        await conn.execute(sa_text("CREATE SCHEMA IF NOT EXISTS audit"))
    try:
        await _run_migrations_if_needed()
    except Exception as exc:
        import logging

        logging.getLogger("salesos.db").error(
            "Alembic migrations failed (%s) — app will start with degraded schema", exc
        )


async def _run_migrations_if_needed() -> None:
    """Skip Alembic entirely when database is already at head revision."""
    import logging
    import os as _os

    from alembic.config import Config as AlembicConfig
    from alembic.script import ScriptDirectory

    log = logging.getLogger("salesos.db")
    try:
        _cfg = AlembicConfig(_os.path.join(_os.path.dirname(__file__), "..", "alembic.ini"))
        _cfg.set_main_option("sqlalchemy.url", settings.resolved_database_url)
        _script = ScriptDirectory.from_config(_cfg)
        _head = _script.get_current_head()
        async with owner_engine.connect() as conn:
            from sqlalchemy import text as sa_text

            _result = await conn.execute(sa_text("SELECT version_num FROM alembic_version LIMIT 1"))
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


async def close_db():
    await engine.dispose()
    await owner_engine.dispose()
