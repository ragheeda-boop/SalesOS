"""Search domain models — independent of any specific module.

SearchQuery and SearchResult are the universal contracts every
module uses to participate in search. No module-specific types here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

T = TypeVar("T")


@dataclass
class SearchSort:
    field: str
    direction: str = "desc"  # asc | desc


@dataclass
class SearchFacet:
    field: str
    values: dict[str, int] = field(default_factory=dict)


@dataclass
class SearchQuery:
    """Universal search query — same shape for all modules."""

    query: str = ""
    filters: dict[str, Any] = field(default_factory=dict)
    sort: SearchSort | None = None
    page: int = 1
    page_size: int = 20
    tenant_id: str = ""
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResult(Generic[T]):
    """Universal search result — generic over item type."""

    items: list[T] = field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20
    facets: list[SearchFacet] = field(default_factory=list)
    filters: dict[str, Any] = field(default_factory=dict)
    ranking: list[dict] = field(default_factory=list)
    duration_ms: float = 0.0
    query: str = ""
    execution_time: str = ""
    strategy: str = "postgres"
    ranking_version: str = "1.0"
    next_cursor: str | None = None
