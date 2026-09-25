"""HybridSearchEngine's _fulltext_search() and _semantic_search() never
pinned the tenant GUC, and its "activity" filter field pointed at a
nonexistent column — the same two bug classes found repeatedly this
session across the sibling search implementations (reports 79, 81).

Mechanical findings, `domains/search/engine/hybrid_search.py` — dead code
(confirmed via repo-wide grep: `HybridSearchEngine` is instantiated only
inside its own module docstring's usage example; zero real callers, zero
test coverage of any kind before this session):

1. **No tenant GUC pinning in either query method.** `companies` has
   RLS + FORCE RLS; without `app.tenant_id` pinned, the `c.tenant_id = :tid`
   predicate in both `_fulltext_search()` and `_semantic_search()` is never
   satisfied and both silently return 0 rows regardless of how much
   matching data exists — confirmed directly.
2. **The `"activity"` filter field does not exist on `companies`** — only
   `activity_description` does (confirmed via `\\d companies`, and the
   identical finding in reports 79/81's sibling files). The field was
   interpolated directly into a dynamically-built raw SQL WHERE clause
   (`"c." + field_name + " = :fltr_" + field_name`), so using it would
   raise `UndefinedColumnError` on every real call. Renamed to
   `activity_description`.

Fixed ahead of any future wiring decision, same posture as this session's
other dead-code findings (reports 73/74/76/77).
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import async_session, engine
from domains.search.engine.hybrid_search import HybridSearchEngine


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    yield
    await engine.dispose()


class _FakeSearchEmbeddingService:
    async def get_embedding(self, text: str) -> list[float]:
        return [0.03] * 3072


async def _seed(tenant_id: str, other_tenant_id: str) -> str:
    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        await session.execute(
            text("INSERT INTO tenants (id, name, slug) VALUES (:id, 'Hybrid Search Test', :slug)"),
            {"id": tenant_id, "slug": f"hs-test-{tenant_id[:8]}"},
        )
        company_id = str(uuid.uuid4())
        await session.execute(
            text("""
                INSERT INTO companies (id, tenant_id, name_ar, name_en, cr_number,
                                        activity_description, is_active, embedding_vector)
                VALUES (:id, :tid, :name_ar, :name_en, :cr, 'General trade', true, CAST(:vec AS vector))
            """),
            {
                "id": company_id, "tid": tenant_id,
                "name_ar": "شركة الدمج", "name_en": "Fusion Search Co",
                "cr": "400000001",
                "vec": str([0.03] * 3072),
            },
        )
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": other_tenant_id}
        )
        await session.execute(
            text("INSERT INTO tenants (id, name, slug) VALUES (:id, 'Hybrid Search Test B', :slug)"),
            {"id": other_tenant_id, "slug": f"hs-test-b-{other_tenant_id[:8]}"},
        )
        await session.commit()
    return company_id


@pytest.mark.asyncio
async def test_fulltext_search_finds_the_seeded_company_and_is_tenant_scoped():
    tenant_a, tenant_b = str(uuid.uuid4()), str(uuid.uuid4())
    company_id = await _seed(tenant_a, tenant_b)

    engine_ = HybridSearchEngine(session_factory=async_session)
    results_a = await engine_._fulltext_search("Fusion", tenant_a, limit=10, offset=0)
    assert len(results_a) == 1
    assert results_a[0].id == company_id

    # Fail-closed: tenant B must never see tenant A's company.
    results_b = await engine_._fulltext_search("Fusion", tenant_b, limit=10, offset=0)
    assert results_b == []


@pytest.mark.asyncio
async def test_semantic_search_finds_the_seeded_company():
    tenant_a, tenant_b = str(uuid.uuid4()), str(uuid.uuid4())
    company_id = await _seed(tenant_a, tenant_b)

    engine_ = HybridSearchEngine(
        session_factory=async_session, embedding_service=_FakeSearchEmbeddingService()
    )
    results = await engine_._semantic_search("anything", tenant_a, limit=10)
    assert len(results) == 1
    assert results[0].id == company_id


@pytest.mark.asyncio
async def test_activity_description_filter_is_a_real_column():
    tenant_a, tenant_b = str(uuid.uuid4()), str(uuid.uuid4())
    company_id = await _seed(tenant_a, tenant_b)

    engine_ = HybridSearchEngine(session_factory=async_session)
    results = await engine_._fulltext_search(
        "Fusion", tenant_a, limit=10, offset=0,
        filters={"activity_description": "General trade"},
    )
    assert len(results) == 1
    assert results[0].id == company_id
