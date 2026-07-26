from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.common.models import Base
from app.config import settings

engine = create_async_engine(
    settings.resolved_database_url,
    echo=settings.debug,
    pool_size=20,
    max_overflow=10,
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
import domains.commercial.infrastructure.models  # noqa: F401
import app.modules.contact.models  # noqa: F401
import app.modules.identity.models  # noqa: F401
import app.modules.company.models  # noqa: F401
import app.modules.entity_resolution.models  # noqa: F401
import domains.timeline.models  # noqa: F401
import domains.analytics.infrastructure.models  # noqa: F401
import app.modules.sso.models  # noqa: F401
import app.modules.audit.models  # noqa: F401
import app.modules.api_keys.models  # noqa: F401
import app.modules.signal_marketplace.models  # noqa: F401


async def get_db() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database: ensure extensions, schemas, and Alembic migrations are up to date."""
    async with engine.begin() as conn:
        from sqlalchemy import text as sa_text
        await conn.execute(sa_text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        await conn.execute(sa_text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        await conn.execute(sa_text('CREATE EXTENSION IF NOT EXISTS "vector"'))
        await conn.execute(sa_text("CREATE SCHEMA IF NOT EXISTS audit"))
    await _run_migrations_if_needed()

async def _run_migrations_if_needed() -> None:
    """Skip Alembic entirely when database is already at head revision."""
    from alembic.script import ScriptDirectory
    from alembic.config import Config as AlembicConfig
    import os as _os
    import logging

    log = logging.getLogger("salesos.db")
    try:
        _cfg = AlembicConfig(
            _os.path.join(_os.path.dirname(__file__), "..", "alembic.ini")
        )
        _cfg.set_main_option("sqlalchemy.url", settings.resolved_database_url)
        _script = ScriptDirectory.from_config(_cfg)
        _head = _script.get_current_head()
        async with engine.connect() as conn:
            from sqlalchemy import text as sa_text
            _result = await conn.execute(
                sa_text("SELECT version_num FROM alembic_version LIMIT 1")
            )
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
