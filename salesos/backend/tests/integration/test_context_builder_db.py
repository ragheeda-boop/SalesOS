"""ContextBuilder.build() had 2 independent bugs and had never once been
exercised against a real database by any existing test — every caller
(`runtime/decision_runtime`'s tests) injects a `MagicMock()`/fake in place
of a real `ContextBuilder`.

Mechanical findings, `runtime/context_runtime/__init__.py` — this class IS
live: instantiated at boot (`app/boot/startup.py::_init_context_builder`,
`_init_decision_engine`) with the real `async_session` factory, and its
`build()` is the one real call site inside
`runtime/decision_runtime/__init__.py::DecisionEngine.evaluate()`. However,
`DecisionEngine.evaluate()` itself has zero callers from any router or
scheduled job (confirmed via repo-wide grep — `app.state.decision_engine` is
only ever assigned, never read back), so end-to-end reachability from a
live HTTP request is currently zero. Still: any future wiring of that entry
point would hit these bugs immediately, and this was fixed ahead of that.

1. **No tenant GUC pinning anywhere in `build()`.** `companies`,
   `company_deals`, and `company_intent_visits` all have RLS + FORCE RLS.
   Without `app.tenant_id` pinned, the main company SELECT (which also has
   its own `WHERE ... AND c.tenant_id = :tid` predicate) still returns 0
   rows under RLS for a genuinely matching, real company — confirmed
   directly. `build()` would then silently return on its
   `if not r: return ctx` early-exit, producing an almost-entirely-empty
   context for a company that actually has real data. Not an error, just
   silently wrong.
2. **The license-expiry query filtered on `licenses.tenant_id`, a column
   that does not exist on `licenses` at all** — confirmed via `\\d licenses`
   and a direct query attempt: `ERROR: column "tenant_id" does not exist`.
   Unlike bug 1, this is a hard SQL error with no surrounding try/except in
   `build()`, so it would crash the entire context build outright. Fixed by
   removing the (nonexistent) `tenant_id` filter — `company_id` alone is
   sufficient scoping, since it was already resolved from a tenant-scoped
   company row.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import async_session, engine
from runtime.context_runtime import ContextBuilder


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    yield
    await engine.dispose()


@pytest.mark.asyncio
async def test_build_returns_real_context_for_a_genuinely_matching_company():
    tenant_id = str(uuid.uuid4())
    company_id = str(uuid.uuid4())

    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        await session.execute(
            text("INSERT INTO tenants (id, name, slug) VALUES (:id, 'Context Test', :slug)"),
            {"id": tenant_id, "slug": f"ctx-test-{tenant_id[:8]}"},
        )
        await session.execute(
            text("""
                INSERT INTO companies
                    (id, tenant_id, name_ar, name_en, industry, city, region,
                     legal_form, employees_count, annual_revenue, revenue_prev_year, is_active)
                VALUES
                    (:id, :tid, 'شركة', 'Context Co', 'Tech', 'Riyadh', 'Central',
                     'llc', 20, 200000, 100000, true)
            """),
            {"id": company_id, "tid": tenant_id},
        )
        await session.execute(
            text("""
                INSERT INTO licenses (id, company_id, license_number, license_type, status, expiry_date)
                VALUES (:id, :cid, 'LIC-1', 'commercial', 'active', :expiry)
            """),
            {"id": str(uuid.uuid4()), "cid": company_id, "expiry": date.today() + timedelta(days=45)},
        )
        await session.execute(
            text("""
                INSERT INTO company_deals (id, tenant_id, company_id, deal_name, amount, status)
                VALUES (:id, :tid, :cid, 'Deal 1', 50000, 'open')
            """),
            {"id": str(uuid.uuid4()), "tid": tenant_id, "cid": company_id},
        )
        await session.execute(
            text("""
                INSERT INTO company_intent_visits (id, tenant_id, company_id, page_url, visited_at)
                VALUES (:id, :tid, :cid, '/pricing', :visited_at)
            """),
            {
                "id": str(uuid.uuid4()),
                "tid": tenant_id,
                "cid": company_id,
                "visited_at": datetime.now(timezone.utc) - timedelta(days=1),
            },
        )
        await session.commit()

    builder = ContextBuilder(session_factory=async_session, feature_store=None)
    ctx = await builder.build(company_id, tenant_id)

    # Business context: must be genuinely populated, not the empty default.
    assert ctx.business.industry == "Tech"
    assert ctx.business.city == "Riyadh"
    assert ctx.business.size == "small"

    # Sales context: the one open deal must be counted.
    assert ctx.sales.total_deals == 1
    assert ctx.sales.active_deals == 1
    assert ctx.sales.total_deal_value == 50000.0

    # Marketing context: the one recent visit must be counted.
    assert ctx.marketing.website_visits_30d == 1

    # Customer context: the one active license must be counted.
    assert ctx.customer.licenses_active == 1
    assert ctx.customer.is_existing_customer is True

    # Revenue context: growth + the license-expiry query must not crash.
    assert ctx.revenue.annual_revenue == 200000
    assert ctx.revenue.revenue_growth == pytest.approx(100.0)
    assert ctx.revenue.days_to_renewal is not None
    assert 40 <= ctx.revenue.days_to_renewal <= 46


@pytest.mark.asyncio
async def test_build_returns_empty_context_for_a_nonexistent_company():
    tenant_id = str(uuid.uuid4())
    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        await session.execute(
            text("INSERT INTO tenants (id, name, slug) VALUES (:id, 'Context Test 2', :slug)"),
            {"id": tenant_id, "slug": f"ctx-test2-{tenant_id[:8]}"},
        )
        await session.commit()

    builder = ContextBuilder(session_factory=async_session, feature_store=None)
    ctx = await builder.build(str(uuid.uuid4()), tenant_id)
    assert ctx.business.industry is None
    assert ctx.sales.total_deals == 0
