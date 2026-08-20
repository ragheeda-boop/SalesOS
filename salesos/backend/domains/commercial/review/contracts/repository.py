"""Review repository — abstract + in-memory for testing."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .models import Review


class ReviewRepository(ABC):

    @abstractmethod
    async def save(self, review: Review) -> Review:
        ...

    @abstractmethod
    async def get(self, review_id: str) -> Review | None:
        ...

    @abstractmethod
    async def list_by_tenant(self, tenant_id: str, target_type: str | None = None) -> list[Review]:
        ...

    @abstractmethod
    async def list_pending(self, tenant_id: str, assigned_to: str | None = None) -> list[Review]:
        ...

    @abstractmethod
    async def count_by_status(self, tenant_id: str) -> dict[str, int]:
        ...
