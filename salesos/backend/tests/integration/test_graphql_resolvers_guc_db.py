"""Every GraphQL resolver in app/graphql/query.py and app/graphql/mutation.py
opened its own bare async_session() with no tenant GUC pin at all -- unlike
ordinary REST routes, Strawberry resolvers never go through FastAPI's
Depends(get_db_session) (the only place that calls set_config() on a
per-request session; TenantContextMiddleware itself only sets a Python
ContextVar, per its own docstring: "storing it in a ContextVar so get_db()
can SET LOCAL app.tenant_id -- without this, RLS policies return zero rows").

Every table these 6 resolvers touch (companies, commercial_opportunities,
and the pipeline tables) has FORCE RLS. The tenant_id string each resolver
reads (from info.context or the ContextVar) was always correct -- the gap is
that it was never actually pinned into Postgres via set_config(), so RLS
silently filtered every real row to zero regardless of any explicit
application-layer WHERE tenant_id = ... filter already present. This means
the entire /graphql API surface -- company, search, opportunities, pipeline,
createOpportunity, updateCompany -- has returned None/empty for every real
tenant since inception.

A second, independent bug found in the same investigation: `_search_companies`
never passed `tenant_id` to `SearchQuery` at all (default ""), which would
raise `ValueError: badly formed hexadecimal UUID string` inside
`CompanySearchRepository`'s `uuid.UUID(query.tenant_id)` call on every
request -- unrelated to the GUC gap, fixed in the same edit.

The existing tests/unit/test_graphql.py stubs the session entirely for
unrelated middleware reasons and asserts only "no crash" / "returns None or
empty, either is fine" for the exact code paths this bug lives in --
explaining why it was never caught. This file calls the resolver functions
directly (Strawberry's own invocation contract: an Info-like object exposing
.context, plus positional args) against a real, RLS-enforced disposable
database with real seeded rows, to prove the resolvers now actually see them.
"""

from __future__ import annotations

import uuid
from datetime import date

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import async_session, engine, reset_current_tenant_id, set_current_tenant_id
from app.graphql.mutation import _create_opportunity, _update_company
from app.graphql.query import _get_company, _opportunities, _pipeline, _search_companies
from app.graphql.types import CompanyUpdateInput, CreateOpportunityInput


class _FakeInfo:
    def __init__(self, tenant_id: str, user_id: str = "") -> None:
        self.context = {"tenant_id": tenant_id, "user_id": user_id}


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    async with engine.connect() as conn:
        db_name = await conn.scalar(text("SELECT current_database()"))
    assert db_name != "salesos", (
        f"REFUSING: connected to {db_name!r} — this is the persistent "
        "local dev database, not a disposable/test one."
    )
    yield
    await engine.dispose()


async def _seed_tenant_and_company(tenant_id: str, company_id: str) -> None:
    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        await session.execute(
            text("INSERT INTO tenants (id, name, slug) VALUES (:id, 'GraphQL Test', :slug)"),
            {"id": tenant_id, "slug": f"gql-test-{tenant_id[:8]}"},
        )
        await session.execute(
            text("""
                INSERT INTO companies (id, tenant_id, name_ar, name_en, cr_number, status)
                VALUES (:id, :tid, 'شركة الاختبار', 'Test Co', '1010101010', 'active')
            """),
            {"id": company_id, "tid": tenant_id},
        )
        await session.commit()


@pytest.mark.asyncio
async def test_get_company_finds_the_real_seeded_company():
    tenant_id = str(uuid.uuid4())
    company_id = str(uuid.uuid4())
    await _seed_tenant_and_company(tenant_id, company_id)

    token = set_current_tenant_id(tenant_id)
    try:
        result = await _get_company(_FakeInfo(tenant_id), company_id)
    finally:
        reset_current_tenant_id(token)

    assert result is not None, "GUC was not pinned — the real company was invisible under RLS"
    assert result.id == company_id
    assert result.name_en == "Test Co"


@pytest.mark.asyncio
async def test_search_companies_finds_the_real_seeded_company_and_does_not_raise():
    tenant_id = str(uuid.uuid4())
    company_id = str(uuid.uuid4())
    await _seed_tenant_and_company(tenant_id, company_id)

    result = await _search_companies(_FakeInfo(tenant_id), query="Test Co", limit=10)

    assert result.total >= 1, "GUC was not pinned — the real company was invisible under RLS"
    assert any(item.id == company_id for item in result.items)


@pytest.mark.asyncio
async def test_create_and_list_opportunity_round_trips_under_the_same_tenant():
    tenant_id = str(uuid.uuid4())
    company_id = str(uuid.uuid4())
    await _seed_tenant_and_company(tenant_id, company_id)

    created = await _create_opportunity(
        _FakeInfo(tenant_id),
        CreateOpportunityInput(
            company_id=company_id,
            name="Test Deal",
            value=1000.0,
            owner_id="owner-1",
            expected_close_date=date.today().isoformat(),
            description="",
        ),
    )
    assert created is not None, "GUC was not pinned — create_opportunity could not see its tenant"
    assert created.name == "Test Deal"

    listed = await _opportunities(_FakeInfo(tenant_id))
    assert any(o.id == created.id for o in listed), (
        "GUC was not pinned — the just-created opportunity was invisible under RLS"
    )

    summary = await _pipeline(_FakeInfo(tenant_id))
    assert summary is not None


@pytest.mark.asyncio
async def test_update_company_persists_and_is_visible_afterward():
    tenant_id = str(uuid.uuid4())
    company_id = str(uuid.uuid4())
    await _seed_tenant_and_company(tenant_id, company_id)

    token = set_current_tenant_id(tenant_id)
    try:
        updated = await _update_company(
            _FakeInfo(tenant_id),
            company_id,
            CompanyUpdateInput(city="Riyadh"),
        )
    finally:
        reset_current_tenant_id(token)

    assert updated is not None, "GUC was not pinned — update_company could not see its tenant"
    assert updated.city == "Riyadh"
