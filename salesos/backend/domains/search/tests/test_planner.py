"""Tests for SearchPlanner — orchestrator that ties repository + ranking + parser together."""

import asyncio
from dataclasses import dataclass
from typing import Any

import pytest

from domains.search.contracts.models import SearchQuery, SearchResult, SearchSort
from domains.search.contracts.repository import SearchRepository
from domains.search.engine.planner import SearchPlanner
from domains.search.ranking.pipeline import ExactMatchStage, RankingPipeline


@dataclass
class FakeItem:
    id: str = ""
    name_ar: str = ""
    cr_number: str = ""


class FakeCompanyRepository(SearchRepository[Any]):

    def __init__(self):
        self._companies = [
            FakeItem(id="1", name_ar="شركة الأمل", cr_number="CR-100"),
            FakeItem(id="2", name_ar="شركة النور", cr_number="CR-200"),
            FakeItem(id="3", name_ar="مؤسسة السلام", cr_number="CR-300"),
        ]

    async def search(self, query: SearchQuery) -> SearchResult[Any]:
        filtered = list(self._companies)

        # Handle parsed field filters
        parsed = query.context.get("parsed")
        if parsed and parsed.field_filters:
            cr_val = parsed.field_filters.get("cr") or parsed.field_filters.get("cr_number")
            if cr_val:
                filtered = [c for c in filtered if cr_val.lower() in c.cr_number.lower()]

        if query.query:
            q = query.query.lower()
            # If query is just a field filter pattern, don't double-filter
            if not (parsed and parsed.field_filters):
                filtered = [c for c in filtered if q in c.name_ar.lower()]

        return SearchResult(
            items=filtered,
            total=len(filtered),
            page=query.page,
            page_size=query.page_size,
            query=query.query,
        )

    async def count(self, query: SearchQuery) -> int:
        return len(self._companies)

    async def facets(self, query: SearchQuery, fields: list[str]) -> dict[str, dict[str, int]]:
        return {}

    async def suggest(self, query: SearchQuery, field: str, prefix: str, limit: int = 10) -> list[str]:
        return []


@pytest.mark.asyncio
async def test_planner_search_no_ranking():
    repo = FakeCompanyRepository()
    planner = SearchPlanner(repository=repo)

    query = SearchQuery(query="شركة")
    result = await planner.search(query)

    assert result.total == 2
    assert len(result.items) == 2
    assert result.duration_ms >= 0
    assert result.query == "شركة"
    assert result.strategy == "postgres"


@pytest.mark.asyncio
async def test_planner_search_with_ranking():
    repo = FakeCompanyRepository()
    ranking = RankingPipeline([ExactMatchStage(fields=["name_ar"], boost=10.0)])
    planner = SearchPlanner(repository=repo, ranking_pipeline=ranking)

    query = SearchQuery(query="شركة الأمل")
    result = await planner.search(query)

    assert len(result.items) > 0
    assert result.ranking is not None


@pytest.mark.asyncio
async def test_planner_search_all():
    repo = FakeCompanyRepository()
    planner = SearchPlanner(repository=repo)

    query = SearchQuery(query="")
    result = await planner.search(query)

    assert result.total == 3
    assert len(result.items) == 3


@pytest.mark.asyncio
async def test_planner_search_empty():
    repo = FakeCompanyRepository()
    planner = SearchPlanner(repository=repo)

    query = SearchQuery(query="غير موجود")
    result = await planner.search(query)

    assert result.total == 0
    assert result.items == []


@pytest.mark.asyncio
async def test_planner_count():
    repo = FakeCompanyRepository()
    planner = SearchPlanner(repository=repo)

    total = await planner.count(SearchQuery())
    assert total == 3


@pytest.mark.asyncio
async def test_planner_facets():
    repo = FakeCompanyRepository()
    planner = SearchPlanner(repository=repo)

    result = await planner.facets(SearchQuery(), ["status"])
    assert result == {}


@pytest.mark.asyncio
async def test_planner_suggest():
    repo = FakeCompanyRepository()
    planner = SearchPlanner(repository=repo)

    result = await planner.suggest(SearchQuery(), "name_ar", "شركة")
    assert result == []


@pytest.mark.asyncio
async def test_planner_set_repository():
    repo1 = FakeCompanyRepository()
    repo2 = FakeCompanyRepository()
    planner = SearchPlanner(repository=repo1)
    assert planner._repository is repo1

    planner.set_repository(repo2)
    assert planner._repository is repo2


@pytest.mark.asyncio
async def test_planner_set_ranking():
    repo = FakeCompanyRepository()
    ranking = RankingPipeline()
    planner = SearchPlanner(repository=repo)
    assert planner._ranking_pipeline is None

    planner.set_ranking_pipeline(ranking)
    assert planner._ranking_pipeline is ranking


@pytest.mark.asyncio
async def test_planner_parses_query():
    repo = FakeCompanyRepository()
    planner = SearchPlanner(repository=repo)

    query = SearchQuery(query="cr:CR-100")
    result = await planner.search(query)

    assert result.total == 1
    assert result.items[0].cr_number == "CR-100"
