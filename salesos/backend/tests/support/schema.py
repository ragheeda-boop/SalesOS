"""Defensive schema sync for tests that need a table `Base.metadata` knows
about but that wasn't necessarily created by the current test run's
session-scoped `setup_database` fixture (backend/conftest.py).

Why this exists: `setup_database` calls `Base.metadata.create_all()` exactly
once per pytest session, using whatever's registered in `Base.metadata` *at
that moment*. SQLAlchemy only registers a table when its model class's
module has actually been imported (declarative registration happens at
class-definition time), and pytest's collection order — which module gets
imported first — varies depending on which test files are passed on the
command line. Observed empirically during Sprint 02: running a single new
test file in isolation intermittently left a table absent even though the
test file itself imports the model that defines it, and re-running
`create_all()` (idempotent, `checkfirst=True` by default) from inside the
test reliably fixes it. This is the same root cause documented in
docs/program/RISK_REGISTER.md R-11 (the `testpaths` blind spot), just
manifesting one level down — a variant worth naming here rather than
re-diagnosing per test file.

This is a workaround for a test-harness limitation, not a fix for it — the
proper fix (build schema from the real Alembic migration chain instead of
`Base.metadata.create_all()`, so test schema always matches what Sprint 03's
CI already does — see `.github/workflows/ci.yml`'s `test-backend` job) is a
larger change than any single Sprint 02 story's scope and is not attempted
here.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession


async def ensure_tables_created(db_session: AsyncSession) -> None:
    from app.database import Base

    conn = await db_session.connection()
    await conn.run_sync(Base.metadata.create_all)
