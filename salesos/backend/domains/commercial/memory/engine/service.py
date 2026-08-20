"""CommercialMemoryService — business logic for durable CRM memory.

Handles:
- Recording commercial events from Product Core facts
- Building account timelines
- Building deal memory
- Querying commercial history
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from ..contracts.models import (
    CommercialEvent, AccountTimeline, DealMemory,
    MemoryEntity, MemoryEventType,
)
from ..contracts.repository import CommercialMemoryRepository


class CommercialMemoryService:

    def __init__(self, repository: CommercialMemoryRepository, event_bus: Any = None):
        self._repository = repository
        self._event_bus = event_bus

    async def _emit(self, event_type: str, tenant_id: str, data: dict[str, Any]) -> None:
        if not self._event_bus:
            return
        from sdk.events.base import DomainEvent
        event = DomainEvent(
            event_type=event_type, tenant_id=tenant_id,
            aggregate_id=data.get("event_id", ""), data=data,
        )
        event.event_type = event_type
        await self._event_bus.publish(event)

    async def record_event(
        self,
        tenant_id: str,
        entity_type: MemoryEntity,
        entity_id: str,
        event_type: MemoryEventType,
        title: str,
        description: str = "",
        actor_id: str = "",
        actor_name: str = "",
        outcome: str = "",
        reason: str = "",
        context: dict | None = None,
        related_ids: list[str] | None = None,
        occurred_at: datetime | None = None,
    ) -> CommercialEvent:
        """Record a commercial event in durable memory."""
        event = CommercialEvent(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            entity_type=entity_type,
            entity_id=entity_id,
            event_type=event_type,
            title=title,
            description=description,
            actor_id=actor_id,
            actor_name=actor_name,
            outcome=outcome,
            reason=reason,
            context=context or {},
            related_ids=related_ids or [],
            occurred_at=occurred_at or datetime.now(timezone.utc),
        )
        result = await self._repository.save_event(event)
        await self._emit("commercial_memory.event_recorded", tenant_id, {
            "event_id": event.id, "entity_type": entity_type.value,
            "entity_id": entity_id, "event_type": event_type.value,
        })
        return result

    async def build_account_timeline(
        self,
        tenant_id: str,
        account_id: str,
        account_name: str = "",
    ) -> AccountTimeline:
        """Build complete commercial memory timeline for an account."""
        events = await self._repository.get_account_events(tenant_id, account_id)
        won = sum(1 for e in events if e.event_type == MemoryEventType.OPPORTUNITY_WON)
        lost = sum(1 for e in events if e.event_type == MemoryEventType.OPPORTUNITY_LOST)
        active = sum(1 for e in events if e.event_type == MemoryEventType.OPPORTUNITY_CREATED)
        timeline = AccountTimeline(
            account_id=account_id,
            account_name=account_name,
            events=events,
            total_interactions=len(events),
            first_interaction=min((e.occurred_at for e in events), default=None),
            last_interaction=max((e.occurred_at for e in events), default=None),
            won_deals=won,
            lost_deals=lost,
            active_opportunities=active,
        )
        return timeline

    async def build_deal_memory(
        self,
        tenant_id: str,
        deal_id: str,
        deal_name: str = "",
        account_id: str = "",
    ) -> DealMemory:
        """Build commercial memory for a specific deal."""
        events = await self._repository.get_deal_events(tenant_id, deal_id)
        stage_events = [e for e in events if e.event_type == MemoryEventType.OPPORTUNITY_STAGE_CHANGED]
        current_stage = stage_events[-1].outcome if stage_events else ""
        activity_events = [e for e in events if e.event_type == MemoryEventType.ACTIVITY_LOGGED]
        last_activity = max((e.occurred_at for e in activity_events), default=None)
        return DealMemory(
            deal_id=deal_id,
            deal_name=deal_name,
            account_id=account_id,
            events=events,
            current_stage=current_stage,
            last_activity=last_activity,
        )

    async def get_events(
        self,
        tenant_id: str,
        entity_type: MemoryEntity | None = None,
        entity_id: str | None = None,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[CommercialEvent]:
        return await self._repository.get_events(tenant_id, entity_type, entity_id, since, limit)

    async def kpis(self, tenant_id: str) -> dict:
        entity_counts = await self._repository.count_by_entity(tenant_id)
        type_counts = await self._repository.count_by_event_type(tenant_id)
        total = sum(entity_counts.values())
        return {
            "total_events": total,
            "by_entity": entity_counts,
            "by_event_type": type_counts,
        }
