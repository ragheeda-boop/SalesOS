"""SearchRuntime's similar_to() and _semantic_search() referenced a
nonexistent `embedding` column, and the "activity" filter field pointed at
a second, equally nonexistent column.

Mechanical findings, `runtime/search_runtime/__init__.py` — this class is
genuinely LIVE: registered at boot (`app/boot/startup.py`) and mounted as
real REST endpoints via `runtime/search_runtime/router.py`, including
`GET /api/v1/search/similar/{company_id}`, which calls `similar_to()` with
**no exception handling at all** at either the router or method level.

1. **`companies.c.embedding` does not exist** — the real pgvector column is
   `embedding_vector` (confirmed via `\\d companies` and this test). Every
   real call to `similar_to()` with a configured embedding service would
   raise `UndefinedColumnError`, unhandled, surfacing as a 500 to the
   caller. `_semantic_search()` has the same bug, but its two callers
   (`search(strategy=SEMANTIC)`, and `_hybrid_search()`'s semantic boost
   step) both wrap it in a broad `except Exception`, so there it silently
   degrades to fulltext-only rather than raising — still broken, just less
   visibly.
2. **The `"activity"` filter field's underlying column stub was a second,
   separate, nonexistent `activity` column** — the table already declared
   a correct `activity_description` column further down, so the module had
   two declarations for what should be one field. Fixed by removing the
   duplicate stub and renaming the public `ALLOWED_FILTER_FIELDS` entry
   from `"activity"` to `"activity_description"` (matching the alias
   `"activity": "activity_description"` already used elsewhere in this
   codebase, e.g. `runtime/data_fabric_runtime/__init__.py`). Not
   independently reachable from the live router today (which only exposes
   city/region/industry/status filters), so this was fixed ahead of any
   future caller, same posture as this session's dead-code findings.
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import async_session, engine
from runtime.search_runtime import SearchRuntime


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    yield
    await engine.dispose()


class _FakeEmbeddingService:
    async def embed(self, query: str) -> list[float]:
        return [0.02] * 3072


async def _seed_tenant(tenant_id: str) -> None:
    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        await session.execute(
            text("""
                INSERT INTO tenants (id, name, slug) VALUES (:id, 'Search Test', :slug)
                ON CONFLICT (id) DO NOTHING
            """),
            {"id": tenant_id, "slug": f"search-test-{tenant_id[:8]}"},
        )
        await session.commit()


async def _seed_company(tenant_id: str, company_id: str, name_en: str) -> None:
    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        await session.execute(
            text("""
                INSERT INTO companies (id, tenant_id, name_ar, name_en, city, industry,
                                        activity_description, is_active, embedding_vector)
                VALUES (:id, :tid, :name_ar, :name_en, 'Riyadh', 'Tech', 'General trade', true,
                        CAST(:vec AS vector))
            """),
            {
                "id": company_id, "tid": tenant_id,
                "name_ar": "شركة", "name_en": name_en,
                "vec": str([0.02] * 3072),
            },
        )
        await session.commit()


@pytest.mark.asyncio
async def test_similar_to_finds_a_neighbor_via_real_embedding_column():
    tenant_id = str(uuid.uuid4())
    subject_id, neighbor_id = str(uuid.uuid4()), str(uuid.uuid4())
    await _seed_tenant(tenant_id)
    await _seed_company(tenant_id, subject_id, "Subject Co")
    await _seed_company(tenant_id, neighbor_id, "Neighbor Co")

    runtime = SearchRuntime(
        session_factory=async_session, embedding_service=_FakeEmbeddingService()
    )
    result = await runtime.similar_to(subject_id, tenant_id, limit=10)
    assert result.total == 1
    assert result.items[0].id == neighbor_id


@pytest.mark.asyncio
async def test_semantic_search_finds_the_seeded_company():
    tenant_id = str(uuid.uuid4())
    company_id = str(uuid.uuid4())
    await _seed_tenant(tenant_id)
    await _seed_company(tenant_id, company_id, "Semantic Co")

    runtime = SearchRuntime(
        session_factory=async_session, embedding_service=_FakeEmbeddingService()
    )
    result = await runtime._semantic_search("anything", tenant_id, limit=10, offset=0)
    assert result.total == 1
    assert result.items[0].id == company_id


@pytest.mark.asyncio
async def test_activity_description_is_a_valid_filter_field_end_to_end():
    tenant_id = str(uuid.uuid4())
    company_id = str(uuid.uuid4())
    await _seed_tenant(tenant_id)
    await _seed_company(tenant_id, company_id, "Filtered Co")

    runtime = SearchRuntime(session_factory=async_session)
    assert "activity_description" in runtime.ALLOWED_FILTER_FIELDS
    assert "activity" not in runtime.ALLOWED_FILTER_FIELDS

    result = await runtime._fulltext_search(
        "Filtered", tenant_id,
        filters={"activity_description": "General trade"},
        limit=10, offset=0, entity_types=None,
    )
    assert result.total == 1
    assert result.items[0].id == company_id
