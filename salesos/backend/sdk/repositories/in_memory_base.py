from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Generic, Optional, TypeVar

T = TypeVar("T")


@dataclass
class PaginatedResult[T]:
    items: list[T]
    total: int
    page: int
    page_size: int


class InMemoryRepository(Generic[T]):
    """Base in-memory repository with common CRUD + filtering + pagination."""

    def __init__(self):
        self._store: dict[str, T] = {}

    async def save(self, entity: T) -> T:
        entity_id = getattr(entity, "id", None)
        if entity_id is None:
            entity_id = str(uuid.uuid4())
            if hasattr(entity, "id"):
                entity.id = entity_id
        self._store[str(entity_id)] = entity
        return entity

    async def get(self, id: str) -> Optional[T]:
        return self._store.get(id)

    async def delete(self, id: str) -> bool:
        return self._store.pop(id, None) is not None

    async def list_all(self) -> list[T]:
        return list(self._store.values())

    def _filter(self, items: list[T], **filters) -> list[T]:
        """Override in subclass for domain-specific filtering."""
        result = list(items)
        for key, value in filters.items():
            if value is not None:
                result = [i for i in result if getattr(i, key, None) == value]
        return result

    def _paginate(self, items: list[T], page: int = 1, page_size: int = 20) -> PaginatedResult[T]:
        start = (page - 1) * page_size
        end = start + page_size
        total = len(items)
        return PaginatedResult(items=items[start:end], total=total, page=page, page_size=page_size)

    async def count(self, tenant_id: str) -> int:
        return len(
            [i for i in self._store.values() if getattr(i, "tenant_id", None) == tenant_id]
        )
