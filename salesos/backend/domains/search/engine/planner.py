"""SearchPlanner — central orchestrator for all search operations.

The Planner is the single entry point for search. It:
1. Parses the raw query into structured tokens
2. Delegates to a SearchRepository for backend execution
3. Applies the ranking pipeline
4. Collects telemetry
5. Returns a generic SearchResult

To swap backends, provide a different SearchRepository implementation.
The Planner, controller, and UI never change.
"""

from __future__ import annotations

import time
from typing import Any, Generic, TypeVar

from ..contracts.models import SearchQuery, SearchResult
from ..contracts.repository import SearchRepository
from ..ranking.pipeline import RankingPipeline
from .parser import QueryParser

T = TypeVar("T")


class SearchPlanner(Generic[T]):

    def __init__(
        self,
        repository: SearchRepository[T],
        ranking_pipeline: RankingPipeline[T] | None = None,
        parser: QueryParser | None = None,
    ):
        self._repository = repository
        self._ranking_pipeline = ranking_pipeline
        self._parser = parser or QueryParser.default()

    def set_repository(self, repository: SearchRepository[T]) -> None:
        """Swap the backend without changing controller or UI."""
        self._repository = repository

    def set_ranking_pipeline(self, pipeline: RankingPipeline[T]) -> None:
        """Swap the ranking strategy."""
        self._ranking_pipeline = pipeline

    async def search(self, query: SearchQuery) -> SearchResult[T]:
        parsed = self._parser.parse(query.query)
        query.context["parsed"] = parsed

        start = time.monotonic()
        result = await self._repository.search(query)
        duration_ms = (time.monotonic() - start) * 1000

        result.duration_ms = duration_ms
        result.query = query.query
        result.execution_time = f"{duration_ms:.1f}ms"
        result.strategy = "postgres"
        result.ranking_version = "1.0"

        if self._ranking_pipeline:
            result = await self._ranking_pipeline.apply(query, result)

        return result

    async def count(self, query: SearchQuery) -> int:
        return await self._repository.count(query)

    async def facets(self, query: SearchQuery, fields: list[str]) -> dict[str, dict[str, int]]:
        return await self._repository.facets(query, fields)

    async def suggest(self, query: SearchQuery, field: str, prefix: str, limit: int = 10) -> list[str]:
        return await self._repository.suggest(query, field, prefix, limit)
