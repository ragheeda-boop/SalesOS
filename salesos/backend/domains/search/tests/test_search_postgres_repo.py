"""Tests for PostgresSearchRepository — ABC contract + raw SQL methods.

All tests use fakes/mocks — no real database required.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from domains.search.contracts.models import SearchQuery, SearchResult
from domains.search.engine.postgres_repo import (
    ALLOWED_FACET_FIELDS,
    ALLOWED_FILTER_FIELDS,
    ALLOWED_SUGGEST_FIELDS,
    MAX_PAGE_SIZE,
    PostgresSearchRepository,
)


# ── Helpers ──────────────────────────────────────────────────────


def _make_mapping(**kwargs) -> MagicMock:
    """Create a mock row with a _mapping attribute for dict() conversion."""
    row = MagicMock()
    row._mapping = kwargs
    return row


def _make_session(rows: list | None = None, scalar: int | None = None) -> AsyncMock:
    """Create a mock async session that yields rows or a scalar."""
    session = AsyncMock()
    mock_result = MagicMock()

    if rows is not None:
        mock_result.fetchall.return_value = rows
    if scalar is not None:
        mock_result.scalar.return_value = scalar

    session.execute = AsyncMock(return_value=mock_result)
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)
    return session


def _make_session_factory(session: AsyncMock):
    return MagicMock(return_value=session)


# DEC-085 live order on search_raw / search_by_filters:
# tenant GUC → statement_timeout → query. Index 0/1 assertions that assume
# timeout-first are stale (GUC added in 942907b; MetaData land 8ed3608 did not
# change execute order).
_EXEC_GUC, _EXEC_TIMEOUT, _EXEC_QUERY = 0, 1, 2


# ── search_raw() Tests ──────────────────────────────────────────


class TestSearchRaw:
    """Test the raw search_raw method."""

    @pytest.mark.asyncio
    async def test_search_raw_empty_query_returns_empty(self):
        repo = PostgresSearchRepository(session_factory=MagicMock())
        rows, total, _cursor = await repo.search_raw("", tenant_id="t1")
        assert rows == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_search_raw_whitespace_query_returns_empty(self):
        repo = PostgresSearchRepository(session_factory=MagicMock())
        rows, total, _cursor = await repo.search_raw("   ", tenant_id="t1")
        assert rows == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_search_raw_returns_results(self):
        mock_rows = [
            _make_mapping(
                id="c1", name_ar="شركة الأمل", name_en="Al Amal Co",
                cr_number="1010123456", city="الرياض", region="الرياض",
                industry="تقنية", status="active",
                activity_description="خدمات تقنية", rank=0.8, total_count=1,
            ),
        ]
        session = _make_session(rows=mock_rows)
        repo = PostgresSearchRepository(session_factory=_make_session_factory(session))

        rows, total, _cursor = await repo.search_raw("الأمل", tenant_id="t1")

        assert len(rows) == 1
        assert total == 1
        assert rows[0]["name_ar"] == "شركة الأمل"
        assert rows[0]["rank"] == 0.8

    @pytest.mark.asyncio
    async def test_search_raw_applies_statement_timeout(self):
        session = _make_session(rows=[])
        repo = PostgresSearchRepository(
            session_factory=_make_session_factory(session),
            timeout_seconds=5.0,
        )
        await repo.search_raw("test", tenant_id="t1")
        guc_sql = str(session.execute.call_args_list[_EXEC_GUC].args[0])
        assert "app.tenant_id" in guc_sql and "set_config" in guc_sql
        timeout_call = session.execute.call_args_list[_EXEC_TIMEOUT]
        sql_clause = timeout_call.args[0]
        rendered = str(sql_clause.compile(compile_kwargs={"literal_binds": True}))
        assert "statement_timeout" in rendered and "set_config" in rendered

    @pytest.mark.asyncio
    async def test_search_raw_respects_max_page_size(self):
        session = _make_session(rows=[])
        repo = PostgresSearchRepository(session_factory=_make_session_factory(session))
        await repo.search_raw("test", tenant_id="t1", limit=999)
        assert session.execute.called

    @pytest.mark.asyncio
    async def test_search_raw_uses_correct_fts_language(self):
        session = _make_session(rows=[])
        repo = PostgresSearchRepository(
            session_factory=_make_session_factory(session),
            fts_language="simple",
        )
        await repo.search_raw("test", tenant_id="t1")
        query_call = session.execute.call_args_list[_EXEC_QUERY]
        sql_clause = query_call.args[0]
        compiled = sql_clause.compile()
        assert "simple" in str(compiled.params.values()) or "simple" in str(compiled)


# ── search_by_filters() Tests ───────────────────────────────────


class TestSearchByFilters:
    """Test the search_by_filters method."""

    @pytest.mark.asyncio
    async def test_search_by_filters_empty_query(self):
        repo = PostgresSearchRepository(session_factory=MagicMock())
        rows, total, _cursor = await repo.search_by_filters("", tenant_id="t1")
        assert rows == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_search_by_filters_with_city(self):
        mock_rows = [_make_mapping(id="c1", rank=0.5, total_count=1)]
        session = _make_session(rows=mock_rows)
        repo = PostgresSearchRepository(session_factory=_make_session_factory(session))

        # search_by_filters uses count(*) OVER() — 3 execute calls (GUC + timeout + query)
        await repo.search_by_filters(
            "test", tenant_id="t1", filters={"city": "الرياض"},
        )

    @pytest.mark.asyncio
    async def test_search_by_filters_ignores_unknown_fields(self):
        mock_rows = [_make_mapping(id="c1", rank=0.5, total_count=1)]
        session = _make_session(rows=mock_rows)
        repo = PostgresSearchRepository(session_factory=_make_session_factory(session))

        rows, total, _cursor = await repo.search_by_filters(
            "test", tenant_id="t1", filters={"unknown_field": "value"},
        )
        assert total == 1

    @pytest.mark.asyncio
    async def test_search_by_filters_with_multiple_filters(self):
        session = _make_session(rows=[])
        repo = PostgresSearchRepository(session_factory=_make_session_factory(session))

        rows, total, _cursor = await repo.search_by_filters(
            "test", tenant_id="t1",
            filters={"city": "الرياض", "industry": "تقنية"},
        )
        assert total == 0


# ── count_raw() Tests ───────────────────────────────────────────


class TestCountRaw:
    """Test the count_raw method."""

    @pytest.mark.asyncio
    async def test_count_raw_empty_query(self):
        repo = PostgresSearchRepository(session_factory=MagicMock())
        result = await repo.count_raw("", tenant_id="t1")
        assert result == 0

    @pytest.mark.asyncio
    async def test_count_raw_returns_scalar(self):
        session = _make_session(scalar=42)
        repo = PostgresSearchRepository(session_factory=_make_session_factory(session))
        result = await repo.count_raw("test", tenant_id="t1")
        assert result == 42

    @pytest.mark.asyncio
    async def test_count_raw_with_filters(self):
        session = _make_session(scalar=5)
        repo = PostgresSearchRepository(session_factory=_make_session_factory(session))
        result = await repo.count_raw("test", tenant_id="t1", filters={"city": "جدة"})
        assert result == 5


# ── facets_raw() Tests ──────────────────────────────────────────


class TestFacetsRaw:
    """Test the facets_raw method."""

    @pytest.mark.asyncio
    async def test_facets_raw_empty_fields(self):
        repo = PostgresSearchRepository(session_factory=MagicMock())
        result = await repo.facets_raw("test", tenant_id="t1", fields=[])
        assert result == {}

    @pytest.mark.asyncio
    async def test_facets_raw_ignores_unknown_fields(self):
        repo = PostgresSearchRepository(session_factory=MagicMock())
        result = await repo.facets_raw("test", tenant_id="t1", fields=["unknown"])
        assert result == {}

    @pytest.mark.asyncio
    async def test_facets_raw_returns_data(self):
        facet_result = MagicMock()
        facet_result.__iter__ = lambda self: iter(
            [("city", "الرياض", 5), ("city", "جدة", 3)]
        )

        session = AsyncMock()
        session.execute = AsyncMock(return_value=facet_result)
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock(return_value=False)

        repo = PostgresSearchRepository(session_factory=_make_session_factory(session))
        result = await repo.facets_raw("test", tenant_id="t1", fields=["city"])

        assert "city" in result
        assert result["city"]["الرياض"] == 5
        assert result["city"]["جدة"] == 3

    @pytest.mark.asyncio
    async def test_facets_raw_empty_query(self):
        repo = PostgresSearchRepository(session_factory=MagicMock())
        result = await repo.facets_raw("", tenant_id="t1", fields=["city"])
        assert result == {}


# ── suggest_raw() Tests ─────────────────────────────────────────


class TestSuggestRaw:
    """Test the suggest_raw method."""

    @pytest.mark.asyncio
    async def test_suggest_raw_empty_prefix(self):
        repo = PostgresSearchRepository(session_factory=MagicMock())
        result = await repo.suggest_raw("", tenant_id="t1")
        assert result == []

    @pytest.mark.asyncio
    async def test_suggest_raw_unknown_field(self):
        repo = PostgresSearchRepository(session_factory=MagicMock())
        result = await repo.suggest_raw("test", tenant_id="t1", field="unknown")
        assert result == []

    @pytest.mark.asyncio
    async def test_suggest_raw_returns_results(self):
        suggest_result = MagicMock()
        suggest_result.__iter__ = lambda self: iter([("شركة الأمل",), ("شركة البشائر",)])

        session = AsyncMock()
        session.execute = AsyncMock(return_value=suggest_result)
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock(return_value=False)

        repo = PostgresSearchRepository(session_factory=_make_session_factory(session))
        result = await repo.suggest_raw("شركة", tenant_id="t1", field="name_ar")

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_suggest_raw_ignores_none_values(self):
        suggest_result = MagicMock()
        suggest_result.__iter__ = lambda self: iter([("أول قيمة",), (None,)])

        session = AsyncMock()
        session.execute = AsyncMock(return_value=suggest_result)
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock(return_value=False)

        repo = PostgresSearchRepository(session_factory=_make_session_factory(session))
        result = await repo.suggest_raw("test", tenant_id="t1")
        assert None not in result


# ── ABC Contract Tests ──────────────────────────────────────────


class TestABCContract:
    """Verify the class satisfies the SearchRepository ABC contract."""

    def test_implements_search_repository_abc(self):
        from domains.search.contracts.repository import SearchRepository
        assert issubclass(PostgresSearchRepository, SearchRepository)

    def test_max_page_size_enforced(self):
        assert MAX_PAGE_SIZE == 50


# ── Specific Test Cases (VIO-103) ──────────────────────────────


class TestCrudWithMockSession:
    """test_crud_with_mock_session — full lifecycle with mock session."""

    @pytest.mark.asyncio
    async def test_crud_with_mock_session(self):
        mock_rows = [
            _make_mapping(
                id="c1", name_ar="شركة التقنية", name_en="Tech Co",
                cr_number="2020202020", city="جدة", region="مكة",
                industry="تقنية المعلومات", status="active",
                activity_description="تطوير برمجيات", rank=0.9, total_count=1,
            ),
        ]
        session = _make_session(rows=mock_rows, scalar=1)
        repo = PostgresSearchRepository(session_factory=_make_session_factory(session))

        # Search (ABC)
        sq = SearchQuery(query="تقنية", tenant_id="t1", page=1, page_size=20)
        result = await repo.search(sq)
        assert isinstance(result, SearchResult)
        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0]["name_ar"] == "شركة التقنية"

        # Count (ABC)
        count = await repo.count(sq)
        assert count == 1

        # Suggest (ABC) — use name_ar which is in ALLOWED_SUGGEST_FIELDS
        suggest_result = MagicMock()
        suggest_result.__iter__ = lambda self: iter([("شركة التقنية",)])
        session.execute = AsyncMock(return_value=suggest_result)
        suggestions = await repo.suggest(sq, field="name_ar", prefix="شر")
        assert len(suggestions) == 1


class TestSearchLimitsEnforced:
    """test_search_limits_enforced — MAX_PAGE_SIZE is capped server-side."""

    @pytest.mark.asyncio
    async def test_search_limits_enforced(self):
        session = _make_session(rows=[])
        repo = PostgresSearchRepository(session_factory=_make_session_factory(session))

        # Request 999 — should be clamped to MAX_PAGE_SIZE (50)
        await repo.search_raw("test", tenant_id="t1", limit=999)
        assert session.execute.called

        # Verify the SQL param was clamped (DEC-085: query is execute index 2)
        sql_call = session.execute.call_args_list[_EXEC_QUERY]
        stmt = sql_call.args[0]
        compiled = stmt.compile()
        assert MAX_PAGE_SIZE in compiled.params.values() or str(MAX_PAGE_SIZE) in str(compiled)

    @pytest.mark.asyncio
    async def test_search_by_filters_limit_enforced(self):
        session = _make_session(rows=[])
        repo = PostgresSearchRepository(session_factory=_make_session_factory(session))

        # search_by_filters uses count(*) OVER() — 3 execute calls (GUC + timeout + query)
        await repo.search_by_filters("test", tenant_id="t1", limit=200)
        # Should be clamped to MAX_PAGE_SIZE (50)
        sql_call = session.execute.call_args_list[_EXEC_QUERY]
        stmt = sql_call.args[0]
        compiled = stmt.compile()
        assert MAX_PAGE_SIZE in compiled.params.values() or str(MAX_PAGE_SIZE) in str(compiled)


class TestEmptyResults:
    """test_empty_results — empty/whitespace queries return empty."""

    @pytest.mark.asyncio
    async def test_empty_results(self):
        repo = PostgresSearchRepository(session_factory=MagicMock())

        # Empty string
        rows, total, _cursor = await repo.search_raw("", tenant_id="t1")
        assert rows == []
        assert total == 0

        # Whitespace only
        rows, total, _cursor = await repo.search_raw("   ", tenant_id="t1")
        assert rows == []
        assert total == 0

        # ABC contract — empty query
        sq = SearchQuery(query="", tenant_id="t1")
        result = await repo.search(sq)
        assert result.items == []
        assert result.total == 0

    @pytest.mark.asyncio
    async def test_empty_results_count(self):
        repo = PostgresSearchRepository(session_factory=MagicMock())
        assert await repo.count_raw("", tenant_id="t1") == 0

    @pytest.mark.asyncio
    async def test_empty_results_suggest(self):
        repo = PostgresSearchRepository(session_factory=MagicMock())
        assert await repo.suggest_raw("", tenant_id="t1") == []
        assert await repo.suggest_raw("test", tenant_id="t1", field="unknown") == []


class TestFilterByIndustry:
    """test_filter_by_industry — filters work correctly."""

    @pytest.mark.asyncio
    async def test_filter_by_industry(self):
        mock_rows = [
            _make_mapping(
                id="c1", name_ar="شركة تقنية", rank=0.7, total_count=1,
            ),
        ]
        session = _make_session(rows=mock_rows)
        repo = PostgresSearchRepository(session_factory=_make_session_factory(session))

        rows, total, _cursor = await repo.search_by_filters(
            "تقنية", tenant_id="t1",
            filters={"industry": "تقنية المعلومات"},
        )
        assert total == 1

    @pytest.mark.asyncio
    async def test_filter_by_industry_abc(self):
        mock_rows = [
            _make_mapping(
                id="c1", name_ar="شركة تقنية", rank=0.7, total_count=1,
            ),
        ]
        session = _make_session(rows=mock_rows)
        repo = PostgresSearchRepository(session_factory=_make_session_factory(session))

        sq = SearchQuery(
            query="تقنية",
            tenant_id="t1",
            filters={"industry": "تقنية المعلومات"},
        )
        result = await repo.search(sq)
        assert result.total == 1
        assert result.strategy == "postgres"

    @pytest.mark.asyncio
    async def test_filter_by_industry_and_city(self):
        session = _make_session(rows=[])
        repo = PostgresSearchRepository(session_factory=_make_session_factory(session))

        rows, total, _cursor = await repo.search_by_filters(
            "test", tenant_id="t1",
            filters={"industry": "تقنية", "city": "الرياض"},
        )
        assert total == 0


# ── Constants Tests ──────────────────────────────────────────────


class TestConstants:
    """Verify constants are correctly defined."""

    def test_max_page_size(self):
        assert MAX_PAGE_SIZE == 50

    def test_allowed_filter_fields_contains_common_fields(self):
        assert "city" in ALLOWED_FILTER_FIELDS
        assert "industry" in ALLOWED_FILTER_FIELDS
        assert "status" in ALLOWED_FILTER_FIELDS

    def test_allowed_facet_fields(self):
        assert "city" in ALLOWED_FACET_FIELDS
        assert "industry" in ALLOWED_FACET_FIELDS

    def test_allowed_suggest_fields(self):
        assert "name_ar" in ALLOWED_SUGGEST_FIELDS
        assert "cr_number" in ALLOWED_SUGGEST_FIELDS
