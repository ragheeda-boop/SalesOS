from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class WebhookSubscription:
    id: str
    tenant_id: str
    url: str
    secret: str
    events: list[str]
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class WebhookDelivery:
    id: str
    subscription_id: str
    event_type: str
    payload: dict
    status: str = "pending"  # pending | success | failed
    response_code: int | None = None
    response_body: str | None = None
    attempt: int = 0
    next_retry_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
