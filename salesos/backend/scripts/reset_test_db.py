"""Rebuild the disposable integration-test database from migrations.

The integration fixture (`backend/conftest.py::setup_database`) no longer drops
tables at the end of a session, so `salesos_test` is expected to persist between
runs at migration head. This script puts it back in that state.

It refuses to touch anything other than a database whose name ends in `_test`.
That guard is the whole point: the same Alembic configuration resolves to the
development database when DATABASE_URL says so, and running this script against
it would drop a live schema.

    python scripts/reset_test_db.py
    python scripts/reset_test_db.py --yes   # skip the confirmation

`--yes` exists for non-interactive use; the database-name check runs either way
and is not bypassable.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    # Running `python scripts/reset_test_db.py` puts scripts/ on sys.path, not the
    # backend root, so `import app...` would fail for Alembic's env.py.
    sys.path.insert(0, str(BACKEND_ROOT))

# Set before importing app.config: `settings` is a module-level singleton built at
# import time, and app.database builds its engine from it.
os.environ.setdefault("POSTGRES_DB", "salesos_test")

from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine  # noqa: E402


def _target() -> str:
    from app.config import settings

    return settings.resolved_database_url


#: Schemas the migrations create. 0001_baseline.py opens audit/identity/company/
#: activity/crm explicitly and then declares tables with `schema="audit"` etc.
_MIGRATED_SCHEMAS = ("public", "audit", "identity", "company", "activity", "crm")


def _migrate() -> None:
    """Bring the (now empty) public schema to head via Alembic.

    Runs in a subprocess rather than in-process: `alembic upgrade` resolves its
    own engine and sync session, and calling it while this script's asyncpg pool
    is live trips MissingGreenlet. A subprocess also guarantees a clean import
    graph, which matters because `app.config` caches a settings singleton.
    """
    proc = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=str(BACKEND_ROOT), env={**os.environ},
        capture_output=True, text=True, check=False,
    )
    if proc.returncode != 0:
        raise SystemExit(
            f"alembic upgrade head failed:\n{proc.stdout}\n{proc.stderr}"
        )


async def _rebuild_and_report(engine, url: str) -> tuple[str, int, str | None]:
    async with engine.begin() as conn:
        # Dropping the schema rather than calling Base.metadata.drop_all is the
        # point of this script: it removes every trace of a previous run,
        # including tables the ORM models no longer describe, so the migrations
        # are unambiguously the only source of truth for the resulting shape.
        #
        # `audit` and the other Alembic-created schemas have to go too. 0001
        # declares audit_log as schema="audit" (0001_baseline.py:60), so
        # dropping only public leaves it behind and the next `alembic upgrade`
        # dies with DuplicateTableError: relation "audit_log" already exists.
        # The list is taken from the migrations rather than hardcoded as
        # public-only for that reason.
        for schema in _MIGRATED_SCHEMAS:
            await conn.execute(text(f"DROP SCHEMA IF EXISTS {schema} CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))

    # Alembic's `upgrade` resolves its own engine, so this script's asyncpg pool
    # has to be gone first. Disposing has to happen off the event loop:
    # `engine.dispose()` from inside async context reaches asyncpg's close()
    # without greenlet context and raises MissingGreenlet.
    await asyncio.to_thread(engine.sync_engine.dispose)
    _migrate()

    check_engine = create_async_engine(url, echo=False)
    async with check_engine.connect() as conn:
        name = await conn.scalar(text("SELECT current_database()"))
        tables = await conn.scalar(
            text("SELECT count(*) FROM information_schema.tables "
                 "WHERE table_schema='public'")
        )
        version = await conn.scalar(
            text("SELECT version_num FROM alembic_version LIMIT 1")
        )
    await asyncio.to_thread(check_engine.sync_engine.dispose)
    return name, tables, version


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--yes", action="store_true", help="skip confirmation")
    args = parser.parse_args()

    url = _target()
    if not url.rsplit("/", 1)[-1].split("?")[0].endswith("_test"):
        print(f"REFUSING: {url} is not a _test database.", file=sys.stderr)
        return 2

    if not args.yes:
        answer = input(f"Rebuild {url} from migrations? [y/N] ")
        if answer.strip().lower() not in ("y", "yes"):
            print("aborted")
            return 1

    engine = create_async_engine(url, echo=False)
    try:
        name, tables, version = asyncio.run(_rebuild_and_report(engine, url))
    finally:
        pass

    print(f"{name}: {tables} tables in public, alembic_version={version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
