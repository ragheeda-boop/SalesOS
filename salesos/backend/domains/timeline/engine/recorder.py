"""TimelineRecorder — listens to domain events and records timeline activities.

Connects to EventBus and automatically creates TimelineEvents
for domain events. This is the bridge between the Event system
and the Timeline Domain.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from ..contracts.models import (
    ActivityOutcome,
    ActivityType,
    Actor,
    ActorType,
    Target,
    TimelineEvent,
)
from ..contracts.repository import TimelineRepository


def _activity_type_from_event(event_type: str) -> ActivityType:
    """Map a domain event type to a timeline activity type."""
    mapping: dict[str, ActivityType] = {
        "user.registered": ActivityType.USER_REGISTERED,
        "user.logged_in": ActivityType.USER_LOGGED_IN,
        "user.role_changed": ActivityType.USER_ROLE_CHANGED,
        "tenant.created": ActivityType.TENANT_CREATED,
        "company.created": ActivityType.COMPANY_CREATED,
        "company.updated": ActivityType.COMPANY_UPDATED,
        "company.ingested": ActivityType.COMPANY_INGESTED,
        "branch.created": ActivityType.BRANCH_CREATED,
        "license.created": ActivityType.LICENSE_CREATED,
        "contact.created": ActivityType.CONTACT_CREATED,
    }
    return mapping.get(event_type, ActivityType.ACTIVITY_LOGGED)


def _actor_from_json(data: dict[str, Any]) -> Actor:
    """Extract Actor from event data or default to system."""
    actor_type = data.get("actor_type", "system")
    type_map = {
        "user": ActorType.USER,
        "ai_agent": ActorType.AI_AGENT,
        "system": ActorType.SYSTEM,
        "workflow": ActorType.WORKFLOW,
        "integration": ActorType.INTEGRATION,
    }
    return Actor(
        id=data.get("actor_id", "system"),
        type=type_map.get(actor_type, ActorType.SYSTEM),
        name=data.get("actor_name", ""),
    )


def _target_from_event(event_type: str, data: dict[str, Any]) -> Target:
    """Extract Target from event data."""
    type_map: dict[str, str] = {
        "company": "company",
        "user": "user",
        "tenant": "tenant",
        "branch": "branch",
        "license": "license",
        "contact": "contact",
    }
    agg_type = data.get("aggregate_type", "unknown")
    entity_type = type_map.get(agg_type, agg_type)
    return Target(
        id=data.get("aggregate_id", ""),
        type=entity_type,
        label=data.get("data", {}).get("name_ar", ""),
    )


class TimelineRecorder:
    """Records domain events as timeline activities.

    Usage:
        recorder = TimelineRecorder(repository)
        event = TimelineEvent(...)
        await recorder.append(event)

    Or subscribe to EventBus:
        event_bus.subscribe(recorder.on_domain_event)
    """

    def __init__(self, repository: TimelineRepository):
        self._repository = repository

    async def append(
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
        await self._repository.append(event)
        return event

    async def on_domain_event(self, event_data: dict[str, Any]) -> None:
        """Handle a domain event (from EventBus) and record it as a timeline activity.

        Expected event_data shape (CloudEvents-like):
        {
            "type": "company.created",
            "source": "...",
            "data": {
                "aggregate_id": "...",
                "aggregate_type": "company",
                "tenant_id": "...",
                "actor_id": "...",
                ...
            }
        }
        """
        event_type = event_data.get("type", "")
        data = event_data.get("data", {})
        tenant_id = data.get("tenant_id", event_data.get("tenant_id", ""))

        activity_type = _activity_type_from_event(event_type)
        actor = _actor_from_json(event_data)
        target = _target_from_event(event_type, data)

        await self.append(
            actor=actor,
            activity=activity_type,
            target=target,
            metadata=data,
            tenant_id=tenant_id,
        )
