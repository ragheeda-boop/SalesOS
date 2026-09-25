"""NBAEngine had zero tenant GUC pinning anywhere — this is genuinely LIVE:
`runtime/nba_engine/api/router.py` is mounted at boot and its 3 endpoints
(`GET /opportunities/{id}/nba`, `POST .../nba/refresh`, `POST .../nba/feedback`)
call straight into `NBAEngine.get_or_compute()` / `.recompute()` /
`.record_feedback()`.

`commercial_opportunities`, `company_features`, and `activity_records` all
carry FORCE RLS with the canonical `tenant_id::text =
current_setting('app.tenant_id', true)` policy. Every one of `NBAEngine`'s
DB-touching methods (`_load_cached`, `_normalize`, `_cache_result`,
`_batch_load_cached`, `_batch_normalize`) opened a session and queried these
tables without ever pinning `app.tenant_id` — confirmed directly: under the
restricted, non-superuser `salesos_app` role, an unpinned SELECT against a
genuinely-matching, real opportunity in `commercial_opportunities` returns
ZERO rows (RLS's USING clause evaluates to NULL/false when the GUC is unset,
regardless of any WHERE-clause tenant_id filter already present in the SQL).
This meant `recompute()` (and therefore both `GET .../nba` and
`POST .../nba/refresh`) would ALWAYS return None / 404 for every real
opportunity, and cached results written by `_cache_result()` could never be
read back by `_load_cached()` either. Fixed by pinning
`apply_tenant_guc(session, tenant_id)` immediately after opening each session,
matching the established pattern used throughout this codebase (DEC-085).

A second, separate, NOT-fixed finding is documented directly in
`NBAEngine.record_feedback()`'s source: that method has no `tenant_id`
parameter at all, and its INSERT into `nba_feedback` targets columns
(`nba_id`, `opportunity_id`, `user_id`, `action`) that do not exist on the
real table (real schema per migration `m8n9o0p1q2r3`: NOT NULL
`tenant_id`/`company_name`/`action_id`/`recommendation_id`/`seller_id`/
`decision`/`original_action_type` — none of which `record_feedback()`'s
caller can supply). That is a genuine schema/architecture gap, not a
one-line fix, and is intentionally left unpatched here.
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import async_session, engine
from runtime.nba_engine import NBAEngine


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    yield
    await engine.dispose()


async def _seed_tenant_and_opportunity(tenant_id: str, opportunity_id: str, company_id: str, name: str) -> None:
    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        await session.execute(
            text("INSERT INTO tenants (id, name, slug) VALUES (:id, 'NBA Engine Test', :slug)"),
            {"id": tenant_id, "slug": f"nba-test-{tenant_id[:8]}"},
        )
        await session.execute(
            text("""
                INSERT INTO commercial_opportunities
                    (id, tenant_id, company_id, name, stage)
                VALUES (:id, :tid, :cid, :name, 'prospecting')
            """),
            {"id": opportunity_id, "tid": tenant_id, "cid": company_id, "name": name},
        )
        await session.commit()


@pytest.mark.asyncio
async def test_recompute_finds_a_genuinely_matching_real_opportunity():
    tenant_id = str(uuid.uuid4())
    opportunity_id = str(uuid.uuid4())
    company_id = str(uuid.uuid4())
    await _seed_tenant_and_opportunity(tenant_id, opportunity_id, company_id, "Real Deal Co")

    engine_ = NBAEngine(session_factory=async_session)
    nba = await engine_.recompute(opportunity_id, tenant_id)

    assert nba is not None
    assert nba.opportunity_id == opportunity_id


@pytest.mark.asyncio
async def test_recompute_does_not_leak_across_tenants():
    tenant_a = str(uuid.uuid4())
    tenant_b = str(uuid.uuid4())
    opportunity_id = str(uuid.uuid4())
    company_id = str(uuid.uuid4())
    await _seed_tenant_and_opportunity(tenant_a, opportunity_id, company_id, "Tenant A Deal")

    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_b}
        )
        await session.execute(
            text("INSERT INTO tenants (id, name, slug) VALUES (:id, 'NBA Engine Test B', :slug)"),
            {"id": tenant_b, "slug": f"nba-test-b-{tenant_b[:8]}"},
        )
        await session.commit()

    engine_ = NBAEngine(session_factory=async_session)
    nba = await engine_.recompute(opportunity_id, tenant_b)

    assert nba is None


@pytest.mark.asyncio
async def test_cached_result_is_read_back_by_the_same_tenant():
    tenant_id = str(uuid.uuid4())
    opportunity_id = str(uuid.uuid4())
    company_id = str(uuid.uuid4())
    await _seed_tenant_and_opportunity(tenant_id, opportunity_id, company_id, "Cache Round Trip Co")

    engine_ = NBAEngine(session_factory=async_session)
    first = await engine_.get_or_compute(opportunity_id, tenant_id)
    assert first is not None

    second = await engine_.get_or_compute(opportunity_id, tenant_id)
    assert second is not None
    assert second.action == "cached"
