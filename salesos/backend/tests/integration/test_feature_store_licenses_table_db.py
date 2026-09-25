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
