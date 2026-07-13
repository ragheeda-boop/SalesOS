from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


SUPPORTED_EVENTS = [
    "company.created", "company.updated",
    "opportunity.created", "opportunity.stage_changed", "opportunity.won", "opportunity.lost",
    "decision.evaluated",
    "pipeline.updated",
    "search.performed",
    "workflow.completed",
    "employee.updated",
]


class WebhookSubscriptionCreate(BaseModel):
    url: str = Field(..., min_length=1, max_length=2048)
    events: list[str] = Field(..., min_length=1)
    secret: str = Field(..., min_length=16, max_length=256)

    def validate_events(self):
        for e in self.events:
            if e not in SUPPORTED_EVENTS:
                raise ValueError(f"Unsupported event: {e}. Supported: {', '.join(SUPPORTED_EVENTS)}")


class WebhookSubscriptionUpdate(BaseModel):
    url: str | None = None
    events: list[str] | None = None
    is_active: bool | None = None


class WebhookSubscriptionResponse(BaseModel):
    id: str
    tenant_id: str
    url: str
    events: list[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class WebhookDeliveryResponse(BaseModel):
    id: str
    subscription_id: str
    event_type: str
    payload: dict
    status: str
    response_code: int | None
    response_body: str | None
    attempt: int
    next_retry_at: datetime | None
    created_at: datetime
