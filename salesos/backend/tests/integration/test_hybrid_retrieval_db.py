"""HybridRetriever's _vector_search() and _bm25_search() had 2 independent
bugs that meant real hybrid retrieval could never return any results:

Mechanical findings, `runtime/knowledge_graph_runtime/hybrid_retrieval.py` —
dead code (confirmed via repo-wide grep: `HybridRetriever` is referenced
only by its own test file, which exercises `_reciprocal_rank_fusion()` and
metrics with in-memory fixtures, never `_vector_search`/`_bm25_search`
against a real database):

1. **`_vector_search()` referenced a nonexistent `embedding` column** —
   `companies`' real pgvector column is `embedding_vector` (confirmed via
   `\\d companies` and a direct query attempt:
   `ERROR: column "embedding" does not exist`). Fixed by using the real
   column name.
2. **Neither `_vector_search()` nor `_bm25_search()` ever pinned
   `app.tenant_id`** — `companies` has RLS + FORCE RLS; without the GUC
   pinned, `current_setting('app.tenant_id', true)` returns NULL, the
   `tenant_id = :tid` predicate in the `USING` clause is never satisfied,
   and the SELECT silently returns 0 rows regardless of how much matching
   data actually exists (confirmed directly: an unpinned session sees
   `count(*) = 0` against a row that is genuinely there). Fixed by pinning
   `app.tenant_id` in both methods.
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import async_session, engine
from runtime.knowledge_graph_runtime.hybrid_retrieval import HybridRetriever


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    yield
    await engine.dispose()


class _FakeEmbeddingService:
    async def embed(self, query: str) -> list[float]:
        return [0.01] * 3072


async def _seed_tenant_and_company(tenant_id: str, company_id: str) -> None:
    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        await session.execute(
            text("INSERT INTO tenants (id, name, slug) VALUES (:id, 'Hybrid Test', :slug)"),
            {"id": tenant_id, "slug": f"hybrid-test-{tenant_id[:8]}"},
        )
        await session.execute(
            text("""
                INSERT INTO companies (id, tenant_id, name_ar, name_en, cr_number, is_active, embedding_vector)
                VALUES (:id, :tid, :name_ar, :name_en, :cr, true, CAST(:vec AS vector))
            """),
            {
                "id": company_id,
                "tid": tenant_id,
                "name_ar": "شركة اختبار",
                "name_en": "Test Retrieval Co",
                "cr": "1234567890",
                "vec": str([0.01] * 3072),
            },
        )
        await session.commit()


@pytest.mark.asyncio
async def test_bm25_search_finds_the_seeded_company_and_is_tenant_scoped():
    tenant_a, tenant_b = str(uuid.uuid4()), str(uuid.uuid4())
    company_id = str(uuid.uuid4())
    await _seed_tenant_and_company(tenant_a, company_id)
    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_b}
        )
        await session.execute(
            text("INSERT INTO tenants (id, name, slug) VALUES (:id, 'Hybrid Test B', :slug)"),
            {"id": tenant_b, "slug": f"hybrid-test-b-{tenant_b[:8]}"},
        )
        await session.commit()

    retriever = HybridRetriever(session_factory=async_session, embedding_service=None)

    results_a = await retriever._bm25_search("Test Retrieval Co", tenant_a, limit=10)
    assert len(results_a) == 1
    assert results_a[0].id == company_id

    # Fail-closed: tenant B must never see tenant A's company.
    results_b = await retriever._bm25_search("Test Retrieval Co", tenant_b, limit=10)
    assert results_b == []


@pytest.mark.asyncio
async def test_vector_search_finds_the_seeded_company():
    tenant_id = str(uuid.uuid4())
    company_id = str(uuid.uuid4())
    await _seed_tenant_and_company(tenant_id, company_id)

    retriever = HybridRetriever(
        session_factory=async_session, embedding_service=_FakeEmbeddingService()
    )
    results = await retriever._vector_search("anything", tenant_id, limit=10)
    assert len(results) == 1
    assert results[0].id == company_id
    assert results[0].score is not None
