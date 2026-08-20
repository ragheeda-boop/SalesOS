"""In-memory Commercial Memory repository for testing."""

from __future__ import annotations

from datetime import datetime

from ..contracts.models import CommercialEvent, MemoryEntity
from ..contracts.repository import CommercialMemoryRepository


class InMemoryCommercialMemoryRepository(CommercialMemoryRepository):

    def __init__(self):
        self._events: list[CommercialEvent] = []

    async def save_event(self, event: CommercialEvent) -> CommercialEvent:
        self._events.append(event)
        return event

    async def get_events(
        self,
        tenant_id: str,
        entity_type: MemoryEntity | None = None,
        entity_id: str | None = None,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[CommercialEvent]:
        results = [e for e in self._events if e.tenant_id == tenant_id]
        if entity_type:
            results = [e for e in results if e.entity_type == entity_type]
        if entity_id:
            results = [e for e in results if e.entity_id == entity_id]
        if since:
            results = [e for e in results if e.occurred_at >= since]
        return sorted(results, key=lambda e: e.occurred_at, reverse=True)[:limit]

    async def get_account_events(
        self, tenant_id: str, account_id: str, limit: int = 100,
    ) -> list[CommercialEvent]:
        return await self.get_events(tenant_id, entity_id=account_id, limit=limit)

    async def get_deal_events(
        self, tenant_id: str, deal_id: str, limit: int = 100,
    ) -> list[CommercialEvent]:
        return await self.get_events(tenant_id, entity_id=deal_id, limit=limit)

    async def count_by_entity(self, tenant_id: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for e in self._events:
            if e.tenant_id == tenant_id:
                key = e.entity_type.value
                counts[key] = counts.get(key, 0) + 1
        return counts

    async def count_by_event_type(self, tenant_id: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for e in self._events:
            if e.tenant_id == tenant_id:
                key = e.event_type.value
                counts[key] = counts.get(key, 0) + 1
        return counts
