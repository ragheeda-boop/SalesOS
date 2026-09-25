"""LicenseRepository.find_expiring() must use the local calendar date, not
a UTC-shifted one.

Mechanical finding (same class as tests/integration/test_feature_store_licenses_table_db.py):
`find_expiring()` computed its lower/upper bounds via `datetime.now(UTC).date()`,
while every other date-only "today" computation in this codebase uses
`date.today()` (contract/quote expiry, cost-tracker billing periods,
runtime/feature_store's own expiry lookups). For any positive-UTC-offset
deployment (e.g. Saudi Arabia, UTC+3), during the local-midnight-to-UTC-offset
window each night, `datetime.now(UTC).date()` still returns *yesterday* while
the real local calendar date is already *today* — so a license expiring
exactly today would fail the `expiry_date >= <UTC "today">` bound by one full
day's slack rather than by design, and, more importantly, the method's notion
of "expiring within N days" silently drifts by a day relative to what any
local caller (a seller's dashboard, a cron job scheduled in local time) means
by "today".
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import async_session, engine
from app.modules.company.repositories import LicenseRepository


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    yield
    await engine.dispose()


async def _seed_company_with_license(session, tenant_id: str, expiry: date) -> str:
    await session.execute(
        text("INSERT INTO tenants (id, name, slug) VALUES (:id, 'License Test', :slug)"),
        {"id": tenant_id, "slug": f"lic-test-{tenant_id[:8]}"},
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
async def test_find_expiring_includes_a_license_expiring_exactly_today():
    tenant_id = str(uuid.uuid4())
    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        company_id = await _seed_company_with_license(session, tenant_id, date.today())
        await session.commit()
        # GUC is transaction-local; commit() ended the transaction it was
        # pinned in, so it must be re-pinned before the next statement.
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )

        repo = LicenseRepository(session)
        results = await repo.find_expiring(within_days=30)

        assert [str(r.company_id) for r in results] == [company_id]
        await session.rollback()


@pytest.mark.asyncio
async def test_find_expiring_excludes_a_license_that_expired_yesterday():
    tenant_id = str(uuid.uuid4())
    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        await _seed_company_with_license(session, tenant_id, date.today() - timedelta(days=1))
        await session.commit()
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )

        repo = LicenseRepository(session)
        results = await repo.find_expiring(within_days=30)

        assert results == []
        await session.rollback()


@pytest.mark.asyncio
async def test_find_expiring_excludes_a_license_outside_the_window():
    tenant_id = str(uuid.uuid4())
    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        await _seed_company_with_license(session, tenant_id, date.today() + timedelta(days=31))
        await session.commit()
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )

        repo = LicenseRepository(session)
        results = await repo.find_expiring(within_days=30)

        assert results == []
        await session.rollback()
