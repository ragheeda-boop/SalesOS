"""InMemoryTimelineRepository — for development/testing without a database.

Production deployments should use PostgresTimelineRepository with
an actual timeline_events table.
"""

from __future__ import annotations

from datetime import datetime

from ..contracts.models import TimelineEvent
from ..contracts.repository import TimelineQuery, TimelineRepository, TimelineResult


class InMemoryTimelineRepository(TimelineRepository):

    def __init__(self):
        self._events: list[TimelineEvent] = []

    async def append(self, event: TimelineEvent) -> None:
        self._events.append(event)

    async def query(self, query: TimelineQuery) -> TimelineResult:
        filtered = list(self._events)

        if query.target_id:
            filtered = [e for e in filtered if e.target.id == query.target_id]
        if query.target_type:
            filtered = [e for e in filtered if e.target.type == query.target_type]
        if query.actor_id:
            filtered = [e for e in filtered if e.actor.id == query.actor_id]
        if query.tenant_id:
            filtered = [e for e in filtered if e.tenant_id == query.tenant_id]
        if query.activity_types:
            types_set = set(query.activity_types)
            filtered = [e for e in filtered if e.activity.value in types_set]

        filtered.sort(key=lambda e: e.timestamp, reverse=(query.sort_order == "desc"))

        total = len(filtered)
        start = (query.page - 1) * query.page_size
        end = start + query.page_size
        return TimelineResult(events=filtered[start:end], total=total, page=query.page, page_size=query.page_size)

    async def get_by_target(self, target_id: str, target_type: str, page: int = 1, page_size: int = 50) -> TimelineResult:
        return await self.query(TimelineQuery(target_id=target_id, target_type=target_type, page=page, page_size=page_size))

    async def get_by_actor(self, actor_id: str, page: int = 1, page_size: int = 50) -> TimelineResult:
        return await self.query(TimelineQuery(actor_id=actor_id, page=page, page_size=page_size))

    async def count(self, tenant_id: str) -> int:
        return len([e for e in self._events if e.tenant_id == tenant_id])

    async def get_summary(self, entity_type: str, entity_id: str, tenant_id: str = "") -> dict:
        filtered = [e for e in self._events if e.target.type == entity_type and e.target.id == entity_id]
        if tenant_id:
            filtered = [e for e in filtered if e.tenant_id == tenant_id]
        if not filtered:
            return {"entity_type": entity_type, "entity_id": entity_id, "total_events": 0, "unique_event_types": 0, "first_event": None, "last_event": None, "event_breakdown": {}}
        types = set(e.activity.value for e in filtered)
        breakdown = {}
        for e in filtered:
            act = e.activity.value
            breakdown[act] = breakdown.get(act, 0) + 1
        first = min(e.timestamp for e in filtered)
        last = max(e.timestamp for e in filtered)
        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "total_events": len(filtered),
            "unique_event_types": len(types),
            "first_event": first.isoformat(),
            "last_event": last.isoformat(),
            "event_breakdown": breakdown,
        }
