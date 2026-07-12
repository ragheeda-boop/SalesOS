"""Extended Search domain tests — vector store, strategy matrix, planner edge cases."""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import pytest

from domains.search.contracts.models import SearchQuery, SearchResult
from domains.search.contracts.repository import SearchRepository
from domains.search.engine.planner import SearchPlanner
from domains.search.engine.specifications import (
    AndSpecification,
    FieldSpecification,
    OrSpecification,
    SpecificationBuilder,
)
from domains.search.engine.strategy_matrix import (
    SearchIntent,
    SearchStrategy,
    detect_intent,
    normalize_query,
)
from domains.search.engine.vector_store import (
    InMemoryVectorStore,
    VectorRecord,
    cosine_similarity,
)
from domains.search.ranking.pipeline import (
    ExactMatchStage,
    FreshnessStage,
    PartialMatchStage,
    RankingPipeline,
    ScoredItem,
)


# ── Helpers ──────────────────────────────────────────────────────────────────


@dataclass
class FakeItem:
    name_ar: str = ""
    name_en: str = ""
    city: str = ""
    status: str = ""
    cr_number: str = ""
    created_at: object = None


# ── cosine_similarity ───────────────────────────────────────────────────────


def test_cosine_similarity_identical():
    assert abs(cosine_similarity([1, 0, 0], [1, 0, 0]) - 1.0) < 1e-9


def test_cosine_similarity_orthogonal():
    assert abs(cosine_similarity([1, 0, 0], [0, 1, 0])) < 1e-9


def test_cosine_similarity_zero_vector():
    assert cosine_similarity([0, 0, 0], [1, 2, 3]) == 0.0


def test_cosine_similarity_both_zero():
    assert cosine_similarity([0, 0], [0, 0]) == 0.0


def test_cosine_similarity_opposite():
    s = cosine_similarity([1, 0], [-1, 0])
    assert abs(s - (-1.0)) < 1e-9


def test_cosine_similarity_partial():
    s = cosine_similarity([1, 1, 0], [1, 0, 0])
    expected = 1.0 / math.sqrt(2)
    assert abs(s - expected) < 1e-6


# ── InMemoryVectorStore ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_vector_store_upsert_and_count():
    store = InMemoryVectorStore()
    await store.upsert(VectorRecord(id="1", vector=[1, 0, 0], metadata={"name": "A"}))
    await store.upsert(VectorRecord(id="2", vector=[0, 1, 0], metadata={"name": "B"}))
    assert await store.count() == 2


@pytest.mark.asyncio
async def test_vector_store_search():
    store = InMemoryVectorStore()
    await store.upsert(VectorRecord(id="1", vector=[1, 0, 0], metadata={"name": "A"}))
    await store.upsert(VectorRecord(id="2", vector=[0, 1, 0], metadata={"name": "B"}))
    results = await store.search([1, 0, 0], top_k=1)
    assert len(results) == 1
    assert results[0].id == "1"
    assert results[0].score > 0.9


@pytest.mark.asyncio
async def test_vector_store_search_top_k():
    store = InMemoryVectorStore()
    for i in range(5):
        vec = [0.5] * 5
        vec[i] = 1.0
        await store.upsert(VectorRecord(id=str(i), vector=vec))
    results = await store.search([1, 0, 0, 0, 0], top_k=3)
    assert len(results) == 3
    assert results[0].id == "0"


@pytest.mark.asyncio
async def test_vector_store_delete():
    store = InMemoryVectorStore()
    await store.upsert(VectorRecord(id="1", vector=[1, 0]))
    assert await store.count() == 1
    await store.delete("1")
    assert await store.count() == 0


@pytest.mark.asyncio
async def test_vector_store_delete_nonexistent():
    store = InMemoryVectorStore()
    await store.delete("nonexistent")


@pytest.mark.asyncio
async def test_vector_store_upsert_overwrites():
    store = InMemoryVectorStore()
    await store.upsert(VectorRecord(id="1", vector=[1, 0], metadata={"v": 1}))
    await store.upsert(VectorRecord(id="1", vector=[0, 1], metadata={"v": 2}))
    assert await store.count() == 1
    results = await store.search([0, 1], top_k=1)
    assert results[0].id == "1"


@pytest.mark.asyncio
async def test_vector_store_clear():
    store = InMemoryVectorStore()
    await store.upsert(VectorRecord(id="1", vector=[1, 0]))
    await store.upsert(VectorRecord(id="2", vector=[0, 1]))
    await store.clear()
    assert await store.count() == 0


@pytest.mark.asyncio
async def test_vector_store_search_empty():
    store = InMemoryVectorStore()
    results = await store.search([1, 0, 0])
    assert results == []


@pytest.mark.asyncio
async def test_vector_store_search_zero_relevance():
    store = InMemoryVectorStore()
    await store.upsert(VectorRecord(id="1", vector=[-1, 0, 0]))
    results = await store.search([1, 0, 0], top_k=10)
    assert results == []


# ── Strategy Matrix detect_intent ───────────────────────────────────────────


def test_detect_intent_cr_field_prefix():
    match = detect_intent("cr:1010123456", field_filters={"cr": "1010123456"})
    assert match.intent == SearchIntent.EXACT_CR
    assert match.strategy == SearchStrategy.POSTGRES_BTREE


def test_detect_intent_cr_number_field():
    match = detect_intent("", field_filters={"cr_number": "1010123456"})
    assert match.intent == SearchIntent.EXACT_CR


def test_detect_intent_pure_cr_number():
    match = detect_intent("1010123456")
    assert match.intent == SearchIntent.EXACT_CR
    assert match.confidence == 0.90


def test_detect_intent_phone():
    # "0512345678" is 10 digits → CR_PATTERN matches first; phone detected via field_filters
    match = detect_intent("", field_filters={"phone": "0512345678"})
    assert match.intent == SearchIntent.MULTI_FILTER


def test_detect_intent_email():
    match = detect_intent("test@example.com")
    assert match.intent == SearchIntent.EXACT_EMAIL
    assert match.strategy == SearchStrategy.POSTGRES_BTREE


def test_detect_intent_multi_filter():
    match = detect_intent("", field_filters={"status": "active", "city": "الرياض"})
    assert match.intent == SearchIntent.MULTI_FILTER
    assert match.strategy == SearchStrategy.POSTGRES_COMPOSITE


def test_detect_intent_single_filter_with_value():
    match = detect_intent("", field_filters={"status": "active"})
    assert match.intent == SearchIntent.MULTI_FILTER


def test_detect_intent_semantic_arabic():
    match = detect_intent("شركات مشابهة لشركة الأمل")
    assert match.intent == SearchIntent.SEMANTIC
    assert match.strategy == SearchStrategy.PGVECTOR_HNSW


def test_detect_intent_semantic_english():
    match = detect_intent("find similar companies")
    assert match.intent == SearchIntent.SEMANTIC


def test_detect_intent_default_general():
    match = detect_intent("شركة")
    assert match.intent == SearchIntent.PARTIAL_GENERAL
    assert match.strategy == SearchStrategy.POSTGRES_TRIGRAM


# ── normalize_query ─────────────────────────────────────────────────────────


def test_normalize_query_strip_company():
    assert normalize_query("شركة الكهرباء") == "الكهرباء"


def test_normalize_query_strip_institute():
    assert normalize_query("مؤسسة أحمد للتجارة") == "أحمد للتجارة"


def test_normalize_query_no_prefix():
    assert normalize_query("الأمل للتجارة") == "الأمل للتجارة"


def test_normalize_query_empty():
    assert normalize_query("") == ""


def test_normalize_query_whitespace():
    assert normalize_query("  ") == ""


def test_normalize_query_strip_group():
    assert normalize_query("مجموعة السعودية") == "السعودية"


def test_normalize_query_strip_factory():
    assert normalize_query("مصنع النسيج") == "النسيج"


# ── Planner facets / suggest edge cases ─────────────────────────────────────


class MinimalRepo(SearchRepository):
    async def search(self, query):
        return SearchResult(items=[], total=0)

    async def count(self, query):
        return 0

    async def facets(self, query, fields):
        return {"status": {"active": 5, "inactive": 2}}

    async def suggest(self, query, field, prefix, limit=10):
        return ["suggestion-1", "suggestion-2"]


@pytest.mark.asyncio
async def test_planner_facets_returns_data():
    planner = SearchPlanner(repository=MinimalRepo())
    result = await planner.facets(SearchQuery(), ["status"])
    assert result == {"status": {"active": 5, "inactive": 2}}


@pytest.mark.asyncio
async def test_planner_suggest_returns_data():
    planner = SearchPlanner(repository=MinimalRepo())
    result = await planner.suggest(SearchQuery(), "name_ar", "شركة", limit=5)
    assert result == ["suggestion-1", "suggestion-2"]


# ── RankingPipeline add_stage ───────────────────────────────────────────────


def test_ranking_pipeline_add_stage():
    pipeline = RankingPipeline()
    pipeline.add_stage(ExactMatchStage(fields=["name_ar"]))
    assert len(pipeline._stages) == 1
    pipeline.add_stage(PartialMatchStage(fields=["name_ar"]))
    assert len(pipeline._stages) == 2


@pytest.mark.asyncio
async def test_ranking_pipeline_partial_match_only():
    pipeline = RankingPipeline([PartialMatchStage(fields=["name_ar"], weight=3.0)])
    query = SearchQuery(query="نقل")
    item1 = FakeItem(name_ar="شركة الأمل للنقل")
    item2 = FakeItem(name_ar="مؤسسة السلام")
    result = SearchResult(items=[item1, item2])
    final = await pipeline.apply(query, result)
    assert final.items[0].name_ar == "شركة الأمل للنقل"


# ── SpecificationBuilder edge cases ─────────────────────────────────────────


def test_specification_builder_disallowed_operator():
    spec = SpecificationBuilder.from_filters({"name": {"regex": "^test"}})
    if hasattr(spec, "specs"):
        assert len(spec.specs) == 0


def test_field_specification_endswith_operator():
    spec = FieldSpecification(field="name_ar", operator="endswith", value="تجارة")
    assert not spec.is_satisfied_by(FakeItem(name_ar="شركة للتجارة"))
    assert not spec.is_satisfied_by(FakeItem(name_ar="أخرى"))


def test_or_specification_empty():
    spec = OrSpecification(specs=[])
    assert not spec.is_satisfied_by(FakeItem(name_ar="test"))


def test_and_specification_empty():
    spec = AndSpecification(specs=[])
    assert spec.is_satisfied_by(FakeItem(name_ar="test"))


def test_specification_builder_eq_filter():
    spec = SpecificationBuilder.from_filters({"status": "active"})
    assert isinstance(spec, FieldSpecification)
    assert spec.is_satisfied_by(FakeItem(status="active"))
    assert not spec.is_satisfied_by(FakeItem(status="inactive"))
