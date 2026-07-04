"""SearchRepository<T> — universal contract for searchable modules.

Every module that wants to expose search must implement this interface.
The Search Domain never imports module-specific code.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from .models import SearchQuery, SearchResult

T = TypeVar("T")


class SearchRepository(ABC, Generic[T]):
    """Contract every searchable module implements.

    The Search Domain calls these methods through the SearchExecutor.
    Never imports the concrete module — only this interface.
    """

    @abstractmethod
    async def search(self, query: SearchQuery) -> SearchResult[T]: ...

    @abstractmethod
    async def count(self, query: SearchQuery) -> int: ...

    @abstractmethod
    async def facets(self, query: SearchQuery, fields: list[str]) -> dict[str, dict[str, int]]: ...

    @abstractmethod
    async def suggest(self, query: SearchQuery, field: str, prefix: str, limit: int = 10) -> list[str]: ...
