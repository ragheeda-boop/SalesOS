"""STORY-02-01 (Sprint 02) — hand-test for scripts/generate_rls_policies.py.

Two things are proven here, deliberately kept separate:

1. Breadth: the generator produces valid, applicable DDL for all 10 pilot
   tables' *real* schema shapes (both the uuid.UUID and the String/varchar
   tenant_id representations that exist in this codebase today).
2. Depth: on two representative pilot tables, the resulting policy actually
   blocks a raw, unfiltered, no-WHERE-clause query from one tenant reading
   another tenant's row — i.e. it would have caught the class of bug fixed
   in Sprint 01 (STORY-01-01, the Decision Center cross-tenant IDOR) even if
   the application-layer filter had been forgotten entirely.

Why this test targets *clone* tables instead of the real companies/users/
workflow_definitions/etc. tables directly, unlike this repo's existing
tests/integration/test_migration_0029.py precedent (which commits CREATE
INDEX/DROP INDEX directly against the real `companies` table with manual
cleanup): `ALTER TABLE ... ENABLE/FORCE ROW LEVEL SECURITY` takes an
ACCESS EXCLUSIVE lock — the heaviest lock Postgres has, blocking every
concurrent reader and writer of that table, including this project's own
integration suite (CI runs it with `-n auto`, i.e. parallel workers). A
`CREATE TABLE ... (LIKE real_table INCLUDING ALL)` needs only an ACCESS
SHARE lock to read the source table's definition, so cloning proves the
generator against the exact real column types/constraints/defaults without
ever contending for a lock on a table other tests are concurrently using.
Everything below runs inside the single `db_session` transaction, which the
root conftest.py fixture always rolls back at teardown — nothing here is
ever committed, so there is no manual cleanup step to forget or fail.
"""

from __future__ import annotations

import os
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from scripts.generate_rls_policies import ALL_TENANT_TABLES as PILOT_TABLES, generate_policy_sql

# SQLAlchemy only knows about a table once its model class has been imported
# (Base.metadata is populated lazily, at class-definition time). The root
# conftest.py's session-scoped `setup_database` fixture runs
# `Base.metadata.create_all()` once per test session using whatever has been
# imported *by then* — which depends on pytest's collection order. Running
# this file in isolation (not alongside domains/decision_center/tests/, whose
# import of postgres_repo.py is what registers DecisionModel today) meant
# `decision_center_decisions` silently didn't exist yet and the clone step
# failed with UndefinedTableError. Importing the modules explicitly here
# makes this file's outcome independent of which other tests happen to be
# collected alongside it.
from domains.decision_center import postgres_repo as _decision_center_postgres_repo  # noqa: F401
from domains.workflow import db_models as _workflow_db_models  # noqa: F401
from app.modules.company import models as _company_models  # noqa: F401
from app.modules.contact import models as _contact_models  # noqa: F401
from app.modules.identity import models as _identity_models  # noqa: F401
from app.modules.admin import db_models as _admin_db_models  # noqa: F401
from domains.commercial.infrastructure import models as _commercial_models  # noqa: F401

pytestmark = pytest.mark.asyncio


def _test_db_url() -> str:
    """Mirror backend/conftest.py's `_db_url()` exactly (duplicated, not
    imported, since conftest.py is not meant to be imported as a regular
    module) — this test needs its own short-lived autocommit connection to
    manage a role's lifecycle independently of the db_session transaction."""
    from app.config import settings

    host = os.environ.get("TEST_POSTGRES_HOST") or os.environ.get("POSTGRES_HOST") or settings.postgres_host
    password = os.environ.get("POSTGRES_PASSWORD") or settings.postgres_password or "test"
    port = os.environ.get("TEST_POSTGRES_PORT") or os.environ.get("POSTGRES_PORT") or str(settings.postgres_port)
    return os.environ.get(
        "TEST_DATABASE_URL",
        f"postgresql+asyncpg://{settings.postgres_user}:{password}@{host}:{port}/salesos_test",
    )


def _clone_name(table: str) -> str:
    return f"rls_pilot_clone_{table}"


async def _make_clone(db_session: AsyncSession, table: str) -> str:
    clone = _clone_name(table)
    await db_session.execute(text(f'DROP TABLE IF EXISTS "{clone}"'))
    await db_session.execute(text(f'CREATE TABLE "{clone}" (LIKE "{table}" INCLUDING ALL)'))
    return clone


@pytest_asyncio.fixture
async def nonsuperuser_role(db_session: AsyncSession):
    """A throwaway, non-superuser, non-BYPASSRLS role.

    Load-bearing discovery this fixture exists to work around: the
    application's own database role (`salesos`, verified via
    `SELECT rolsuper, rolbypassrls FROM pg_roles`) is a Postgres superuser
    with BYPASSRLS. Per Postgres's documented behavior, superusers and
    BYPASSRLS roles bypass every RLS policy unconditionally — FORCE ROW
    LEVEL SECURITY has no effect on them, full stop. Testing (or, later,
    running the app) as `salesos` can never observe RLS actually isolating
    anything, regardless of how correct the policy is.

    This is why the two tests below run their read/write assertions as this
    throwaway role via `SET LOCAL ROLE`, rather than as whatever `db_session`
    already connects as. It also means: **Sprint 03's full RLS rollout
    cannot ship as designed until the application itself stops connecting as
    a superuser/BYPASSRLS role** — recorded as a named blocker in the
    Sprint 02 report and risk register, not silently worked around only in
    this test.

    First-attempt bug, kept here as a comment because it will bite anyone who
    "simplifies" this fixture the same way: dropping the role in `finally`
    without first releasing `db_session`'s own `SET LOCAL ROLE` assumption
    deadlocks — reproduced live during Sprint 02 (docker Postgres, PIDs
    visible in `pg_stat_activity` with `wait_event=object` on the DROP ROLE,
    the other session `idle in transaction`). `DROP ROLE` blocks until every
    session currently assuming that role releases it — but `db_session`'s
    assumption is only released by its own rollback(), which is a *separate*
    fixture's teardown that has not run yet at the point this fixture's
    `finally` executes (finalizers run in reverse dependency order, and this
    fixture depends on — so tears down before — db_session). Roll back
    db_session's transaction explicitly, first, before ever attempting the
    drop; see the finally block below for why a full rollback is used
    instead of `RESET ROLE`.
    """
    role = f"rls_test_role_{uuid.uuid4().hex[:8]}"
    engine = create_async_engine(_test_db_url(), isolation_level="AUTOCOMMIT")
    try:
        async with engine.connect() as conn:
            await conn.execute(text(f'CREATE ROLE "{role}" NOSUPERUSER NOBYPASSRLS NOLOGIN'))
        yield role
    finally:
        # A full rollback, not `RESET ROLE` — `RESET ROLE` requires an active,
        # non-aborted transaction to succeed, and a test whose assertion
        # about a *rejected* statement (e.g. the WITH CHECK violation test)
        # leaves db_session's transaction in Postgres's "aborted" state,
        # where anything short of ROLLBACK just raises again. A full
        # rollback unconditionally releases the SET LOCAL ROLE assumption
        # either way, is safe to call even with nothing to roll back, and
        # the outer db_session fixture's own later rollback() is then a
        # harmless no-op.
        try:
            await db_session.rollback()
        except Exception:
            pass
        async with engine.connect() as conn:
            await conn.execute(text(f'DROP ROLE IF EXISTS "{role}"'))
        await engine.dispose()


class TestGeneratorBreadthAcrossAllPilotTables:
    """Prove the generated DDL applies cleanly to every pilot table's real schema."""

    async def test_policy_applies_and_is_visible_in_catalog_for_every_pilot_table(
        self, db_session: AsyncSession
    ):
        failures: list[str] = []
        for table in PILOT_TABLES:
            clone = await _make_clone(db_session, table)
            sql = generate_policy_sql(clone, policy_name=f"tenant_isolation_{clone}")
            try:
                for statement in filter(None, (s.strip() for s in sql.split(";"))):
                    await db_session.execute(text(statement))
            except Exception as exc:  # noqa: BLE001 — we want to attribute the failure to `table`
                failures.append(f"{table}: DDL failed — {exc}")
                continue

            row = (
                await db_session.execute(
                    text(
                        "SELECT relrowsecurity, relforcerowsecurity FROM pg_class "
                        "WHERE relname = :clone"
                    ),
                    {"clone": clone},
                )
            ).fetchone()
            if row is None:
                failures.append(f"{table}: clone table not found in pg_class after CREATE")
                continue
            row_security, force_security = row
            if not row_security:
                failures.append(f"{table}: ENABLE ROW LEVEL SECURITY did not take effect")
            if not force_security:
                failures.append(f"{table}: FORCE ROW LEVEL SECURITY did not take effect")

            policy_count = (
                await db_session.execute(
                    text("SELECT count(*) FROM pg_policies WHERE tablename = :clone"),
                    {"clone": clone},
                )
            ).scalar()
            if policy_count != 1:
                failures.append(f"{table}: expected exactly 1 policy, found {policy_count}")

        assert not failures, "RLS generator failed for one or more pilot tables:\n" + "\n".join(failures)


class TestGeneratorDepthOnRepresentativeTables:
    """Prove the mechanism actually blocks cross-tenant reads and forged writes.

    webhook_endpoints and workflow_definitions are used because they are the
    two pilot tables with the fewest NOT-NULL, no-default columns (id,
    tenant_id, url / id, tenant_id, name) — the point of this test is the RLS
    mechanism, not exercising every column's business validation, so the
    leanest real schemas keep the fixture data honest without unrelated
    boilerplate.

    Every test here runs its actual read/write assertions as a throwaway
    non-superuser role (see the `nonsuperuser_role` fixture docstring) — not
    as whatever `db_session` connects as, since that role is a superuser
    that unconditionally bypasses RLS and would make every assertion below
    pass regardless of whether the policy is correct.
    """

    async def _setup(self, db_session: AsyncSession, table: str, role: str) -> str:
        clone = await _make_clone(db_session, table)
        sql = generate_policy_sql(clone, policy_name=f"tenant_isolation_{clone}")
        for statement in filter(None, (s.strip() for s in sql.split(";"))):
            await db_session.execute(text(statement))
        await db_session.execute(text(f'GRANT SELECT, INSERT, UPDATE, DELETE ON "{clone}" TO "{role}"'))
        await db_session.execute(text(f'SET LOCAL ROLE "{role}"'))
        return clone

    # webhook_endpoints / workflow_definitions columns supplied below cover every
    # NOT NULL column that has no database-level (server_default=) default.
    # Several columns declare a Python-side `default=` on the ORM model (e.g.
    # description="", auth_type="none") — that is applied by SQLAlchemy when
    # *the ORM* constructs the INSERT, not by Postgres itself, so it does not
    # carry over via `LIKE ... INCLUDING ALL` and must be supplied here since
    # this test deliberately issues raw SQL to exercise RLS independently of
    # the ORM/application layer.
    _WEBHOOK_INSERT_COLS = "id, tenant_id, url, name, auth_type, auth_config, secret, status"
    _WEBHOOK_INSERT_VALS = ":id, :tenant_id, :url, '', 'none', '{}', '', 'active'"
    _WORKFLOW_INSERT_COLS = "id, tenant_id, name, description, trigger_type, status, steps"
    _WORKFLOW_INSERT_VALS = ":id, :tenant_id, :name, '', 'manual', 'draft', '[]'"

    async def test_webhook_endpoints_raw_query_hides_other_tenants_row(
        self, db_session: AsyncSession, nonsuperuser_role: str
    ):
        clone = await self._setup(db_session, "webhook_endpoints", nonsuperuser_role)
        tenant_a, tenant_b = f"tenant-a-{uuid.uuid4().hex[:8]}", f"tenant-b-{uuid.uuid4().hex[:8]}"
        row_id = uuid.uuid4().hex[:12]

        await db_session.execute(text(f"SET LOCAL app.tenant_id = '{tenant_a}'"))
        await db_session.execute(
            text(f'INSERT INTO "{clone}" ({self._WEBHOOK_INSERT_COLS}) VALUES ({self._WEBHOOK_INSERT_VALS})'),
            {"id": row_id, "tenant_id": tenant_a, "url": "https://example.com/hook"},
        )

        # This is the exact shape of query that caused Sprint 01's Decision
        # Center IDOR: no WHERE clause on tenant_id at all. RLS, not
        # application code, is what must stop this from leaking.
        await db_session.execute(text(f"SET LOCAL app.tenant_id = '{tenant_b}'"))
        as_b = (await db_session.execute(text(f'SELECT id FROM "{clone}"'))).fetchall()
        assert as_b == [], "tenant B's raw, unfiltered SELECT saw tenant A's row — RLS did not isolate it"

        await db_session.execute(text(f"SET LOCAL app.tenant_id = '{tenant_a}'"))
        as_a = (await db_session.execute(text(f'SELECT id FROM "{clone}"'))).fetchall()
        assert [r[0] for r in as_a] == [row_id], "tenant A could not see its own row under the same policy"

    async def test_webhook_endpoints_rejects_forged_tenant_id_on_insert(
        self, db_session: AsyncSession, nonsuperuser_role: str
    ):
        clone = await self._setup(db_session, "webhook_endpoints", nonsuperuser_role)
        tenant_a, tenant_b = f"tenant-a-{uuid.uuid4().hex[:8]}", f"tenant-b-{uuid.uuid4().hex[:8]}"

        # Session is tenant B, but the row claims to belong to tenant A —
        # this is the write-forgery half of the IDOR class, distinct from
        # the read-leak half tested above. WITH CHECK, not USING, is what
        # must stop this.
        await db_session.execute(text(f"SET LOCAL app.tenant_id = '{tenant_b}'"))
        with pytest.raises(Exception, match="(?i)row-level security|policy"):
            await db_session.execute(
                text(f'INSERT INTO "{clone}" ({self._WEBHOOK_INSERT_COLS}) VALUES ({self._WEBHOOK_INSERT_VALS})'),
                {"id": uuid.uuid4().hex[:12], "tenant_id": tenant_a, "url": "https://example.com/hook"},
            )

    async def test_workflow_definitions_raw_query_hides_other_tenants_row(
        self, db_session: AsyncSession, nonsuperuser_role: str
    ):
        clone = await self._setup(db_session, "workflow_definitions", nonsuperuser_role)
        tenant_a, tenant_b = f"tenant-a-{uuid.uuid4().hex[:8]}", f"tenant-b-{uuid.uuid4().hex[:8]}"
        row_id = uuid.uuid4().hex[:12]

        await db_session.execute(text(f"SET LOCAL app.tenant_id = '{tenant_a}'"))
        await db_session.execute(
            text(f'INSERT INTO "{clone}" ({self._WORKFLOW_INSERT_COLS}) VALUES ({self._WORKFLOW_INSERT_VALS})'),
            {"id": row_id, "tenant_id": tenant_a, "name": "RLS pilot workflow"},
        )

        await db_session.execute(text(f"SET LOCAL app.tenant_id = '{tenant_b}'"))
        as_b = (await db_session.execute(text(f'SELECT id FROM "{clone}"'))).fetchall()
        assert as_b == [], "tenant B's raw, unfiltered SELECT saw tenant A's workflow — RLS did not isolate it"

        await db_session.execute(text(f"SET LOCAL app.tenant_id = '{tenant_a}'"))
        as_a = (await db_session.execute(text(f'SELECT id FROM "{clone}"'))).fetchall()
        assert [r[0] for r in as_a] == [row_id]

    async def test_unset_session_variable_denies_by_default_fail_closed(
        self, db_session: AsyncSession, nonsuperuser_role: str
    ):
        """No `SET app.tenant_id` at all (e.g. a forgotten code path) must see
        nothing, not everything — current_setting(..., true) plus the
        equality predicate is what guarantees this."""
        clone = await self._setup(db_session, "workflow_definitions", nonsuperuser_role)
        tenant_a = f"tenant-a-{uuid.uuid4().hex[:8]}"

        await db_session.execute(text(f"SET LOCAL app.tenant_id = '{tenant_a}'"))
        await db_session.execute(
            text(f'INSERT INTO "{clone}" ({self._WORKFLOW_INSERT_COLS}) VALUES ({self._WORKFLOW_INSERT_VALS})'),
            {"id": uuid.uuid4().hex[:12], "tenant_id": tenant_a, "name": "RLS pilot workflow"},
        )

        # RESET, not SET — simulates a session that never established a tenant context.
        await db_session.execute(text("RESET app.tenant_id"))
        rows = (await db_session.execute(text(f'SELECT id FROM "{clone}"'))).fetchall()
        assert rows == [], "a session with no tenant context set saw rows — fail-open, not fail-closed"
