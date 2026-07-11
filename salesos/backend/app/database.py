from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.common.models import Base
from app.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# Register all models so Alembic can discover them
import domains.commercial.infrastructure.models  # noqa: F401
import app.modules.contact.models  # noqa: F401
import app.modules.identity.models  # noqa: F401
import app.modules.company.models  # noqa: F401
import app.modules.entity_resolution.models  # noqa: F401
import domains.timeline.models  # noqa: F401
import domains.analytics.infrastructure.models  # noqa: F401


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
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Create audit schema and audit_log table (not in ORM metadata)
        from sqlalchemy import text as sa_text
        await conn.execute(sa_text("CREATE SCHEMA IF NOT EXISTS audit"))
        await conn.execute(sa_text("""
            CREATE TABLE IF NOT EXISTS audit.audit_log (
                id              BIGSERIAL PRIMARY KEY,
                tenant_id       UUID NOT NULL,
                entity_type     VARCHAR(100) NOT NULL,
                entity_id       UUID NOT NULL,
                action          VARCHAR(50) NOT NULL,
                changes         JSONB DEFAULT '{}',
                performed_by    UUID,
                performed_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                ip_address      VARCHAR(45),
                request_id      VARCHAR(100),
                metadata        JSONB DEFAULT '{}'
            )
        """))
        await conn.execute(sa_text(
            "CREATE INDEX IF NOT EXISTS ix_audit_log_entity "
            "ON audit.audit_log (entity_type, entity_id)"
        ))
        await conn.execute(sa_text(
            "CREATE INDEX IF NOT EXISTS ix_audit_log_tenant_performed "
            "ON audit.audit_log (tenant_id, performed_at DESC)"
        ))
        # Create domain_events table (for PostgresEventStore)
        await conn.execute(sa_text("""
            CREATE TABLE IF NOT EXISTS domain_events (
                event_id VARCHAR(64) PRIMARY KEY,
                event_type VARCHAR(100) NOT NULL,
                event_version INTEGER DEFAULT 1,
                aggregate_id VARCHAR(64) NOT NULL,
                aggregate_type VARCHAR(50) NOT NULL,
                tenant_id VARCHAR(36),
                occurred_at TIMESTAMPTZ DEFAULT now(),
                data JSONB DEFAULT '{}',
                metadata JSONB DEFAULT '{}'
            )
        """))
        await conn.execute(sa_text("CREATE INDEX IF NOT EXISTS ix_domain_events_type ON domain_events(event_type)"))
        await conn.execute(sa_text("CREATE INDEX IF NOT EXISTS ix_domain_events_aggregate ON domain_events(aggregate_type, aggregate_id)"))
        # Create activity_records table (for ActivityRuntime)
        await conn.execute(sa_text("""
            CREATE TABLE IF NOT EXISTS activity_records (
                id VARCHAR(64) PRIMARY KEY,
                actor VARCHAR(255) NOT NULL,
                action VARCHAR(100) NOT NULL,
                entity_type VARCHAR(50) NOT NULL,
                entity_id VARCHAR(64) NOT NULL,
                target_type VARCHAR(50),
                target_id VARCHAR(64),
                metadata JSONB DEFAULT '{}',
                tenant_id VARCHAR(36),
                timestamp TIMESTAMPTZ DEFAULT now()
            )
        """))
        await conn.execute(sa_text("CREATE INDEX IF NOT EXISTS ix_activity_entity ON activity_records(entity_type, entity_id, timestamp DESC)"))
        await conn.execute(sa_text("CREATE INDEX IF NOT EXISTS ix_activity_tenant_action ON activity_records(tenant_id, action, timestamp DESC)"))
        await conn.execute(sa_text("CREATE INDEX IF NOT EXISTS ix_activity_actor ON activity_records(actor, timestamp DESC)"))
        await conn.execute(sa_text("CREATE INDEX IF NOT EXISTS ix_activity_action ON activity_records(action, timestamp DESC)"))


async def close_db():
    await engine.dispose()
