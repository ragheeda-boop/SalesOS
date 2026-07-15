from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SignalResponse(BaseModel):
    id: str
    name: str
    ar_name: str
    description: str
    domain: str
    category: str
    severity: str
    source: str
    pack_id: str
    priority: str
    weight: float
    decay_days: int
    triggers: list[str]
    relevance_sectors: list[str]
    created_at: datetime


class SignalListResponse(BaseModel):
    total: int
    signals: list[SignalResponse]


class SubscribeRequest(BaseModel):
    signal_id: str = Field(..., description="Signal ID to subscribe to")
    company_id: str = Field(..., description="Company ID to subscribe for")
    channel: str = Field("in-app", description="Notification channel: email, webhook, in-app")


class SubscribeResponse(BaseModel):
    id: str
    signal_id: str
    company_id: str
    tenant_id: str
    channel: str
    active: bool
    created_at: datetime


class SignalEventResponse(BaseModel):
    id: str
    signal_id: str
    company_id: str
    tenant_id: str
    data: dict[str, Any]
    detected_at: datetime
    acknowledged: bool
    acknowledged_at: datetime | None


class SignalFeedResponse(BaseModel):
    total: int
    events: list[SignalEventResponse]


class AcknowledgeResponse(BaseModel):
    id: str
    signal_id: str
    company_id: str
    acknowledged: bool
    acknowledged_at: datetime | None
