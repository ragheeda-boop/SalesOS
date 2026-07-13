"""TimelineService — CRUD, aggregation, search, and Decision Platform integration."""
from __future__ import annotations

import uuid
import logging
from datetime import datetime, timezone
from typing import Any

from domains.timeline.contracts.models import (
    ActivityOutcome,
    ActivityType,
    Actor,
    Target,
    TimelineEvent,
)
from domains.timeline.contracts.repository import TimelineQuery, TimelineRepository

logger = logging.getLogger(__name__)


class TimelineService:
    def __init__(
        self,
        repository: TimelineRepository,
        decision_platform: Any = None,
    ) -> None:
        self._repo = repository
        self._decision_platform = decision_platform

    async def create_event(
        self,
        actor: Actor,
        activity: ActivityType,
        target: Target,
        outcome: ActivityOutcome = ActivityOutcome.SUCCESS,
        metadata: dict[str, Any] | None = None,
        tenant_id: str = "",
    ) -> TimelineEvent:
        event = TimelineEvent(
            event_id=str(uuid.uuid4()),
            actor=actor,
            activity=activity,
            target=target,
            outcome=outcome,
            metadata=metadata or {},
            timestamp=datetime.now(timezone.utc),
            tenant_id=tenant_id,
        )
        if self._decision_platform:
            try:
                score = await self._decision_platform.evaluate(
                    {"event_id": event.event_id, "activity": activity.value, "target_type": target.type, "target_id": target.id, "tenant_id": tenant_id}
                )
                if score and "importance" in score:
                    event.metadata["decision_score"] = score.get("score", 0)
                    event.metadata["decision_reason"] = score.get("reason", "")
            except Exception as exc:
                logger.warning("Decision Platform scoring failed (non-blocking): %s", exc)
        await self._repo.append(event)
        return event

    async def get_entity_timeline(
        self,
        entity_type: str,
        entity_id: str,
        tenant_id: str = "",
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[TimelineEvent], int]:
        query = TimelineQuery(
            target_id=entity_id,
            target_type=entity_type,
            tenant_id=tenant_id,
            page=page,
            page_size=page_size,
        )
        result = await self._repo.query(query)
        return result.events, result.total

    async def get_recent(
        self,
        tenant_id: str,
        limit: int = 20,
    ) -> list[TimelineEvent]:
        query = TimelineQuery(tenant_id=tenant_id, page=1, page_size=limit, sort_order="desc")
        result = await self._repo.query(query)
        return result.events

    async def search(
        self,
        query: TimelineQuery,
    ) -> tuple[list[TimelineEvent], int]:
        result = await self._repo.query(query)
        return result.events, result.total

    async def get_summary(
        self,
        entity_type: str,
        entity_id: str,
        tenant_id: str = "",
    ) -> dict[str, Any]:
        return await self._repo.get_summary(entity_type, entity_id, tenant_id)

    async def delete_events_for_entity(
        self,
        entity_type: str,
        entity_id: str,
        tenant_id: str = "",
    ) -> None:
        await self._repo.delete_by_target(entity_type, entity_id, tenant_id)
