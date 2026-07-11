from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class PlanTier(str, Enum):
    FREE = "free"
    STARTER = "starter"
    GROWTH = "growth"
    ENTERPRISE = "enterprise"


class TenantStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class PlanCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    tier: PlanTier = PlanTier.FREE
    price_monthly: float = 0
    price_yearly: float = 0
    max_users: int = 1
    max_storage_mb: int = 100
    max_api_calls: int = 1000
    features: list[str] = []


class PlanResponse(BaseModel):
    id: UUID
    name: str
    tier: PlanTier
    price_monthly: float
    price_yearly: float
    max_users: int
    max_storage_mb: int
    max_api_calls: int
    features: list[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PlanUpdate(BaseModel):
    name: str | None = None
    price_monthly: float | None = None
    price_yearly: float | None = None
    max_users: int | None = None
    max_storage_mb: int | None = None
    max_api_calls: int | None = None
    features: list[str] | None = None
    is_active: bool | None = None


class TenantCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")
    domain: str | None = None
    plan_id: UUID | None = None


class TenantUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None
    plan_id: UUID | None = None
    settings: dict | None = None


class TenantListItem(BaseModel):
    id: UUID
    name: str
    slug: str
    domain: str | None
    plan: str
    is_active: bool
    user_count: int
    created_at: datetime
    updated_at: datetime


class TenantDetail(BaseModel):
    id: UUID
    name: str
    slug: str
    domain: str | None
    plan: str
    is_active: bool
    settings: dict
    features: dict
    user_count: int
    subscription_ends_at: datetime | None
    created_at: datetime
    updated_at: datetime


class TenantUsage(BaseModel):
    tenant_id: UUID
    tenant_name: str
    api_calls: int
    storage_mb: float
    active_users: int
    total_users: int
    period_start: datetime
    period_end: datetime


class LicenseCreate(BaseModel):
    tenant_id: UUID
    plan_id: UUID
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class LicenseResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    tenant_name: str
    plan_id: UUID
    plan_name: str
    tier: PlanTier
    is_active: bool
    starts_at: datetime | None
    ends_at: datetime | None
    created_at: datetime
    updated_at: datetime


class UserAdminListItem(BaseModel):
    id: UUID
    email: str
    full_name: str
    full_name_ar: str | None
    role: str
    is_active: bool
    is_verified: bool
    tenant_id: UUID
    tenant_name: str
    created_at: datetime
    last_login_at: datetime | None


class UserAdminUpdate(BaseModel):
    role: str | None = None
    is_active: bool | None = None


class UserAdminDetail(BaseModel):
    id: UUID
    email: str
    full_name: str
    full_name_ar: str | None
    role: str
    is_active: bool
    is_verified: bool
    tenant_id: UUID
    tenant_name: str
    permissions: list[str]
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None


class InvoiceResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    tenant_name: str
    amount: float
    currency: str
    status: str
    description: str
    due_date: datetime | None
    paid_at: datetime | None
    created_at: datetime


class TransactionResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    tenant_name: str
    amount: float
    currency: str
    status: str
    method: str
    description: str
    reference: str | None
    created_at: datetime


class FeatureFlagCreate(BaseModel):
    key: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9_-]+$")
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    enabled: bool = False


class FeatureFlagResponse(BaseModel):
    id: UUID
    key: str
    name: str
    description: str | None
    enabled: bool
    is_global: bool
    created_at: datetime
    updated_at: datetime


class FeatureFlagUpdate(BaseModel):
    enabled: bool | None = None
    name: str | None = None
    description: str | None = None


class FeatureFlagTenantResponse(BaseModel):
    flag_id: UUID
    flag_key: str
    tenant_id: UUID
    tenant_name: str
    enabled: bool


class JobResponse(BaseModel):
    id: str
    type: str
    status: str
    progress: int
    tenant_id: str | None
    created_by: str | None
    payload: dict
    result: dict | None
    error_message: str | None
    retry_count: int
    max_retries: int
    scheduled_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class JobDetailResponse(JobResponse):
    logs: list[dict]


class AICostResponse(BaseModel):
    id: UUID
    model: str
    tenant_id: UUID | None
    tenant_name: str | None
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float
    operation: str
    created_at: datetime


class AICostSummary(BaseModel):
    total_cost: float
    total_tokens: int
    by_model: list[dict]
    by_tenant: list[dict]
    by_operation: list[dict]


class AIUsageResponse(BaseModel):
    total_prompt_tokens: int
    total_completion_tokens: int
    total_tokens: int
    by_model: list[dict]
    by_tenant: list[dict]


class HealthComponentStatus(BaseModel):
    component: str
    status: str
    latency_ms: float | None
    last_check: datetime | None
    details: str | None


class DetailedHealthResponse(BaseModel):
    overall_status: str
    uptime_seconds: float
    components: list[HealthComponentStatus]


class HealthHistoryEntry(BaseModel):
    timestamp: datetime
    overall_status: str
    components: dict[str, str]
