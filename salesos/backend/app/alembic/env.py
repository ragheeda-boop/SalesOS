"""Alembic migrations environment configuration.

Supports both CLI invocation (alembic upgrade head) and
programmatic invocation from init_db().
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from alembic.config import Config as AlembicConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.config import settings
from app.database import Base

# When invoked via `alembic` CLI, context.config is set by Alembic.
# When invoked programmatically, we create a Config from alembic.ini.
_alembic_cfg: AlembicConfig | None = getattr(context, "config", None)
if _alembic_cfg is None:
    import os

    _alembic_cfg = AlembicConfig(os.path.join(os.path.dirname(__file__), "../../alembic.ini"))

config = _alembic_cfg
config.set_main_option("sqlalchemy.url", settings.resolved_database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# DEC-130g: expression GIN indexes whose Postgres-reflected form (::regconfig /
# ::text casts) cannot be mirrored in SQLAlchemy metadata without DROP+CREATE.
# KEEP live indexes; exclude from autogenerate/check. No blind DROP.
_KEEP_EXPRESSION_INDEXES = frozenset({"ix_graph_nodes_search"})


def include_object(_object, name, type_, _reflected, _compare_to):
    # Alembic include_object callback arity; unused args are protocol-required.
    if type_ == "index" and name in _KEEP_EXPRESSION_INDEXES:
        return False
    return True


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = settings.resolved_database_url
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if _alembic_cfg is not None and getattr(context, "config", None) is not None:
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()
