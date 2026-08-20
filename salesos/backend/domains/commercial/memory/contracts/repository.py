"""Commercial Memory repository — abstract interface for durable memory persistence."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from .models import CommercialEvent, AccountTimeline, DealMemory, MemoryEntity


class CommercialMemoryRepository(ABC):

    @abstractmethod
    async def save_event(self, event: CommercialEvent) -> CommercialEvent:
        ...

    @abstractmethod
    async def get_events(
        self,
        tenant_id: str,
        entity_type: MemoryEntity | None = None,
        entity_id: str | None = None,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[CommercialEvent]:
        ...

    @abstractmethod
    async def get_account_events(
        self,
        tenant_id: str,
        account_id: str,
        limit: int = 100,
    ) -> list[CommercialEvent]:
        ...

    @abstractmethod
    async def get_deal_events(
        self,
        tenant_id: str,
        deal_id: str,
        limit: int = 100,
    ) -> list[CommercialEvent]:
        ...

    @abstractmethod
    async def count_by_entity(self, tenant_id: str) -> dict[str, int]:
        ...

    @abstractmethod
    async def count_by_event_type(self, tenant_id: str) -> dict[str, int]:
        ...
