from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ActorSchema(BaseModel):
    id: str
    type: str = "system"
    name: str = ""


class TargetSchema(BaseModel):
    id: str
    type: str
    label: str = ""


class TimelineEventCreate(BaseModel):
    actor: ActorSchema
    activity: str
    target: TargetSchema
    outcome: str = "success"
    metadata: dict[str, Any] = Field(default_factory=dict)
    tenant_id: str = ""


class TimelineEventResponse(BaseModel):
    event_id: str
    actor: ActorSchema
    activity: str
    target: TargetSchema
    outcome: str
    metadata: dict[str, Any]
    timestamp: str
    tenant_id: str


class TimelineSearchParams(BaseModel):
    target_id: str | None = None
    target_type: str | None = None
    actor_id: str | None = None
    activity_types: list[str] | None = None
    tenant_id: str = ""
    from_date: datetime | None = None
    to_date: datetime | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
    sort_order: str = "desc"


class TimelineSearchResponse(BaseModel):
    events: list[TimelineEventResponse]
    total: int
    page: int
    page_size: int


class TimelineSummaryResponse(BaseModel):
    entity_type: str
    entity_id: str
    total_events: int
    unique_event_types: int
    first_event: str | None
    last_event: str | None
    event_breakdown: dict[str, int]
