"""ExpansionScoreComputer / RevenueScoreComputer must query the real `licenses`
table, not a non-existent `company_licenses` table.

Mechanical finding: both computers issued raw SQL against
`public.company_licenses`, a table that does not exist anywhere in the
schema (the real table, created in 0001_baseline.py, is `licenses`, has no
`tenant_id` column, and its expiry column is `expiry_date`, not
`expires_at`). Every call with a real company_id/tenant_id raised an
unhandled UndefinedTableError, caught only by the orchestration-level
`except Exception` in FeatureStore.recompute_all (runtime/feature_store/__init__.py),
which silently recorded the feature as failed. Neither computer had any
prior test coverage.
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import async_session, engine
from runtime.feature_store.features import ExpansionScoreComputer, RevenueScoreComputer


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    """Report 118 safety net: `app.database.engine` is built from
    `settings.app_database_url` at import time, and this repo's checked-in
    `.env` sets `APP_POSTGRES_PASSWORD` — which takes precedence over a
    bare `DATABASE_URL` shell export (see `app/config.py`'s
    `app_database_url` property). A host-side `pytest` invocation of this
    file that exports only `DATABASE_URL` therefore silently targets
    `localhost:5432/salesos` (this repo's persistent local dev Postgres,
    33 tenants / 5 companies) instead of the intended disposable/ephemeral
    database — caught live once (an INSERT there failed on a stale
    pre-`p7q8r9s0t1u2` NOT NULL constraint and rolled back before commit,
    so nothing was written, but nothing here should get that close again).
    Refuse outright rather than risk it a second time; run with
    `APP_POSTGRES_PASSWORD=""` (or `APP_DATABASE_URL_OVERRIDE=...`) set to
    the intended disposable database.
    """
    async with engine.connect() as conn:
        db_name = await conn.scalar(text("SELECT current_database()"))
    assert db_name != "salesos", (
        f"REFUSING: connected to {db_name!r} — this is the persistent "
        "local dev database, not a disposable/test one. Set "
        'APP_POSTGRES_PASSWORD="" (or APP_DATABASE_URL_OVERRIDE) to point '
        "app.database.engine at an ephemeral container before running "
        "this file."
    )
    yield
    await engine.dispose()


async def _seed_company_with_license(session, tenant_id: str, expiry: date) -> str:
    await session.execute(
        text("INSERT INTO tenants (id, name, slug) VALUES (:id, 'Feature Store Test', :slug)"),
        {"id": tenant_id, "slug": f"fs-test-{tenant_id[:8]}"},
    )
    company_id = str(uuid.uuid4())
    await session.execute(
        text(
            "INSERT INTO companies (id, tenant_id, name_ar, status) "
            "VALUES (:id, :tid, 'شركة اختبار', 'active')"
        ),
        {"id": company_id, "tid": tenant_id},
    )
    await session.execute(
        text(
            "INSERT INTO licenses (id, company_id, license_number, license_type, "
            "status, expiry_date) "
            "VALUES (:id, :cid, 'LIC-1', 'commercial', 'active', :expiry)"
        ),
        {"id": str(uuid.uuid4()), "cid": company_id, "expiry": expiry},
    )
    return company_id


@pytest.mark.asyncio
async def test_expansion_score_computer_reads_real_licenses_table():
    tenant_id = str(uuid.uuid4())
    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        expiry = date.today() + timedelta(days=20)
        company_id = await _seed_company_with_license(session, tenant_id, expiry)
        await session.commit()
        # GUC is transaction-local; commit() ended the transaction it was
        # pinned in, so it must be re-pinned before the next statement.
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )

        computer = ExpansionScoreComputer()
        result = await computer.compute(
            {"id": company_id, "tenant_id": tenant_id}, session
        )

        assert result.contributing_signals["days_to_renewal"] <= 30
        await session.rollback()


@pytest.mark.asyncio
async def test_revenue_score_computer_reads_real_licenses_table():
    tenant_id = str(uuid.uuid4())
    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        expiry = date.today() + timedelta(days=90)
        company_id = await _seed_company_with_license(session, tenant_id, expiry)
        await session.commit()
        # GUC is transaction-local; commit() ended the transaction it was
        # pinned in, so it must be re-pinned before the next statement.
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )

        computer = RevenueScoreComputer()
        # Must not raise (previously an unhandled UndefinedTableError) and
        # must actually find the seeded active license, proving the query
        # reads the real `licenses` table, not a silently-empty wrong table.
        result = await computer.compute(
            {"id": company_id, "tenant_id": tenant_id, "annual_revenue": 0}, session
        )
        # deal_equity = total_deal_value (0, none seeded) + active_licenses * 50000
        # — 50000 only appears if the query found exactly the 1 seeded license.
        assert result.contributing_signals.get("deal_equity") == 50000
        await session.rollback()


@pytest.mark.asyncio
async def test_expansion_score_computer_uses_local_calendar_date_not_utc(monkeypatch):
    """Report 118 — `days_to_renewal` must be computed against `date.today()`,
    not `datetime.now(timezone.utc).date()`.

    On a positive-UTC-offset host, the UTC calendar date can be one day
    *behind* the local calendar date. `ExpansionScoreComputer.compute()`
    previously used `datetime.now(timezone.utc).date()` for this "today"
    comparison, silently off-by-one during that window (e.g. reporting 31
    days to renewal instead of 30). This test is independent of the host's
    real timezone/date: it monkeypatches the module's `date` name so
    `date.today()` returns a fixed, arbitrary value far from the real UTC
    date, then seeds a license expiring exactly 30 days after that fixed
    date. Only an implementation that actually calls `date.today()` (as
    opposed to deriving "today" from `datetime.now(timezone.utc)`) can land
    on exactly 30 — the real UTC date is nowhere near this fixed date, so a
    regression to the old UTC-based line would produce a wildly different,
    clearly-failing value here rather than an off-by-one that could be
    mistaken for a coincidence.
    """
    import runtime.feature_store.features as features_module

    fixed_today = date(2020, 1, 1)

    class _FixedDate:
        @staticmethod
        def today():
            return fixed_today

    monkeypatch.setattr(features_module, "date", _FixedDate)

    tenant_id = str(uuid.uuid4())
    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        expiry = fixed_today + timedelta(days=30)
        company_id = await _seed_company_with_license(session, tenant_id, expiry)
        await session.commit()
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )

        computer = ExpansionScoreComputer()
        result = await computer.compute(
            {"id": company_id, "tenant_id": tenant_id}, session
        )

        assert result.contributing_signals["days_to_renewal"] == 30
        await session.rollback()
