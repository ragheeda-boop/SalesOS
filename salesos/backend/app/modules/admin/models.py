from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Plan:
    id: uuid.UUID
    name: str
    tier: str
    price_monthly: float
    price_yearly: float
    max_users: int
    max_storage_mb: int
    max_api_calls: int
    features: list[str]
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class License:
    id: uuid.UUID
    tenant_id: uuid.UUID
    plan_id: uuid.UUID
    is_active: bool = True
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Invoice:
    id: uuid.UUID
    tenant_id: uuid.UUID
    amount: float
    currency: str = "SAR"
    status: str = "pending"
    description: str = ""
    due_date: datetime | None = None
    paid_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Transaction:
    id: uuid.UUID
    tenant_id: uuid.UUID
    invoice_id: uuid.UUID | None = None
    amount: float = 0
    currency: str = "SAR"
    status: str = "completed"
    method: str = "card"
    description: str = ""
    reference: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class FeatureFlag:
    id: uuid.UUID
    key: str
    name: str
    description: str | None = None
    enabled: bool = False
    is_global: bool = True
    tenant_overrides: dict[str, bool] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Job:
    id: str
    type: str
    status: str = "pending"
    progress: int = 0
    tenant_id: str | None = None
    created_by: str | None = None
    payload: dict = field(default_factory=dict)
    result: dict | None = None
    error_message: str | None = None
    retry_count: int = 0
    max_retries: int = 3
    logs: list[dict] = field(default_factory=list)
    scheduled_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class AICostRecord:
    id: uuid.UUID
    model: str
    tenant_id: uuid.UUID | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0
    operation: str = "completion"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class HealthSnapshot:
    timestamp: datetime
    overall_status: str
    components: dict[str, str]
