from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.common.models import Base
from app.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# Register all models so Alembic can discover them
import domains.commercial.infrastructure.models  # noqa: F401
import app.modules.contact.models  # noqa: F401
import app.modules.identity.models  # noqa: F401
import app.modules.company.models  # noqa: F401
import app.modules.entity_resolution.models  # noqa: F401
import domains.timeline.models  # noqa: F401


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


async def close_db():
    await engine.dispose()
