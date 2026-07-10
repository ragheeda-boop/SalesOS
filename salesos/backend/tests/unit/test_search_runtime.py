"""Tests for SearchRuntime — full-text, semantic, and hybrid search strategies."""
from unittest.mock import AsyncMock, MagicMock, call

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from runtime.search_runtime import SearchRuntime, SearchStrategy, SearchResult


class FakeMapping:
    """Simulate a SQLAlchemy row mapping."""
    def __init__(self, data):
        self._data = data
    def __getitem__(self, key):
        return self._data[key]
    def get(self, key, default=None):
        return self._data.get(key, default)
    def keys(self):
        return self._data.keys()
    def __iter__(self):
        return iter(self._data)


class FakeMappings:
    """Simulate .mappings() result."""
    def __init__(self, rows=None, one=None):
        self._rows = rows or []
        self._one = one or {"id": "1", "name_ar": "Test", "relevance": 1.0, "count": 5}

    def one(self):
        return FakeMapping(self._one)

    def all(self):
        return [FakeMapping(r) for r in self._rows]


class FakeResult:
    """Simulate a SQLAlchemy result."""
    def __init__(self, one=None, rows=None, scalar_val=5):
        self._one = one or {"count": 5, "id": "1", "name_ar": "Test", "name_en": "Test EN",
                            "cr_number": "1234567890", "city": "Riyadh", "region": "Riyadh",
                            "industry": "Tech", "status": "active", "activity_description": "Desc",
                            "relevance": 1.0}
        self._rows = rows or [{"id": "1", "name_ar": "شركة أ", "name_en": "Co A",
                               "cr_number": "1234567890", "city": "Riyadh", "region": "Riyadh",
                               "industry": "Tech", "status": "active", "activity_description": "Desc",
                               "relevance": 1.0}]
        self._scalar_val = scalar_val

    def mappings(self):
        return FakeMappings(rows=self._rows, one=self._one)

    def scalar(self):
        return self._scalar_val

    def one_or_none(self):
        return self._one

    def __iter__(self):
        class FakeRow:
            def __getitem__(self, i):
                return list(self._row_vals.values())[i] if isinstance(self._row_vals, dict) else self._row_vals[i]
        for row_data in self._rows:
            r = FakeRow()
            r._row_vals = row_data
            yield r


@pytest.fixture
def mock_session():
    session = AsyncMock(spec=AsyncSession)
    session.execute.return_value = FakeResult()
    return session


@pytest.fixture
def mock_session_factory(mock_session):
    factory = MagicMock()
    factory.return_value.__aenter__.return_value = mock_session
    factory.return_value.__aexit__.return_value = None
    return factory


@pytest.fixture
def search_runtime(mock_session_factory):
    return SearchRuntime(
        session_factory=mock_session_factory,
        embedding_service=None,
        kg_engine=None,
    )


class TestSearchRuntime:
    async def test_search_returns_search_result(self, search_runtime):
        result = await search_runtime.search("test", "tenant-1")
        assert isinstance(result, SearchResult)
        assert result.query == "test"

    async def test_search_fulltext_strategy(self, search_runtime):
        result = await search_runtime.search("test", "tenant-1", strategy=SearchStrategy.FULLTEXT)
        assert result.strategy == SearchStrategy.FULLTEXT
        assert len(result.items) > 0

    async def test_search_semantic_without_embedding_service(self, search_runtime):
        result = await search_runtime.search("test", "tenant-1", strategy=SearchStrategy.SEMANTIC)
        assert result.strategy == SearchStrategy.SEMANTIC
        assert len(result.items) == 0

    async def test_search_graph_without_kg_engine(self, search_runtime):
        result = await search_runtime.search("test", "tenant-1", strategy=SearchStrategy.GRAPH)
        assert result.strategy == SearchStrategy.GRAPH
        assert len(result.items) == 0

    async def test_search_hybrid_falls_back_to_fulltext(self, search_runtime):
        result = await search_runtime.search("test", "tenant-1", strategy=SearchStrategy.HYBRID)
        assert result.strategy == SearchStrategy.HYBRID

    async def test_safe_col_validates_fields(self, search_runtime):
        col = search_runtime._safe_col("city", search_runtime.ALLOWED_FILTER_FIELDS)
        assert col == "city"

    async def test_safe_col_rejects_invalid_field(self, search_runtime):
        with pytest.raises(ValueError, match="Field not allowed"):
            search_runtime._safe_col("invalid", search_runtime.ALLOWED_FILTER_FIELDS)

    async def test_suggest_returns_list(self, search_runtime):
        result = await search_runtime.suggest("test", "tenant-1")
        assert isinstance(result, list)

    async def test_metrics_track_searches(self, search_runtime):
        before = search_runtime.metrics.searches
        await search_runtime.search("test", "tenant-1")
        assert search_runtime.metrics.searches >= before + 1

    async def test_metrics_track_strategies(self, search_runtime):
        before_ft = search_runtime.metrics.fulltext_searches
        await search_runtime.search("test", "tenant-1", strategy=SearchStrategy.FULLTEXT)
        assert search_runtime.metrics.fulltext_searches == before_ft + 1

    async def test_find_matched_fields(self, search_runtime):
        row = {"name_ar": "شركة الأمل", "name_en": "Al Amal Co", "cr_number": "1234567890"}
        matched = search_runtime._find_matched("الأمل", row)
        assert "name_ar" in matched

    async def test_find_matched_no_match(self, search_runtime):
        row = {"name_ar": "شركة الأمل", "name_en": "Al Amal Co"}
        matched = search_runtime._find_matched("غير موجود", row)
        assert len(matched) == 0
