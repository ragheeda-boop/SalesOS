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


class ProvisioningStatus(str, Enum):
    """App-validated provisioning states (STORY-04-01/04-02). Stored as string."""

    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    FAILED = "failed"


PROVISIONING_STATUS_VALUES = frozenset(s.value for s in ProvisioningStatus)


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
    # Legacy: optional plan *label* (maps to tenants.plan). Prefer plan_id for catalog.
    plan: str | None = Field(None, max_length=50)
    # STORY-04-01: opaque catalog plan id (maps to tenants.plan_id String(64)).
    plan_id: str | None = Field(None, max_length=64)
    region: str | None = Field(None, max_length=32)
    data_residency: str | None = Field(None, max_length=32)
    trial_ends_at: datetime | None = None
    admin_email: str | None = None
    admin_password: str | None = None
    admin_full_name: str | None = None


class TenantUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None
    plan: str | None = Field(None, max_length=50)
    plan_id: str | None = Field(None, max_length=64)
    region: str | None = Field(None, max_length=32)
    data_residency: str | None = Field(None, max_length=32)
    provisioning_status: str | None = Field(None, max_length=32)
    trial_ends_at: datetime | None = None
    settings: dict | None = None


class TenantListItem(BaseModel):
    id: UUID
    name: str
    slug: str
    domain: str | None
    plan: str
    plan_id: str | None = None
    region: str | None = None
    data_residency: str | None = None
    provisioning_status: str = "pending"
    trial_ends_at: datetime | None = None
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
    plan_id: str | None = None
    region: str | None = None
    data_residency: str | None = None
    provisioning_status: str = "pending"
    trial_ends_at: datetime | None = None
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
    rollout_percentage: int = 100
    is_ci_test: bool = False


class FeatureFlagResponse(BaseModel):
    id: UUID
    key: str
    name: str
    description: str | None
    enabled: bool
    is_global: bool
    rollout_percentage: int
    is_ci_test: bool
    created_at: datetime
    updated_at: datetime


class FeatureFlagUpdate(BaseModel):
    enabled: bool | None = None
    name: str | None = None
    description: str | None = None
    rollout_percentage: int | None = None
    is_ci_test: bool | None = None


class FeatureFlagTenantResponse(BaseModel):
    flag_id: UUID
    flag_key: str
    tenant_id: UUID
    tenant_name: str
    enabled: bool


class FeatureFlagEvaluateRequest(BaseModel):
    flag_key: str
    tenant_id: str


class FeatureFlagEvaluateResponse(BaseModel):
    flag_key: str
    tenant_id: str
    enabled: bool
    reason: str


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


class RoleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = ""
    permissions: list[str] = []


class RoleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    permissions: list[str] | None = None


class RoleResponse(BaseModel):
    id: str
    name: str
    description: str
    is_system: bool
    tenant_id: str | None
    permissions: list[str]
    created_at: datetime
    updated_at: datetime


class PermissionResponse(BaseModel):
    id: str
    key: str
    name: str
    description: str
    group: str


class TenantConfigCreate(BaseModel):
    key: str = Field(..., min_length=1, max_length=255)
    yaml_content: str = Field(..., min_length=1)


class TenantConfigResponse(BaseModel):
    id: int
    tenant_id: str
    key: str
    yaml_content: str
    version: int
    created_by: str | None
    created_at: datetime


class TenantConfigVersionResponse(BaseModel):
    id: int
    version: int
    created_by: str | None
    created_at: datetime


class TenantConfigValidationResponse(BaseModel):
    valid: bool
    errors: list[dict]


class TenantSuspendRequest(BaseModel):
    reason: str = ""


class TenantActivateRequest(BaseModel):
    """Optional note for lifecycle restore (soft-delete or suspend → active)."""

    reason: str = ""


class TenantLifecycleResponse(BaseModel):
    """Shared shape for suspend / activate / soft-delete lifecycle actions."""

    message: str
    tenant_id: str
    is_active: bool
    provisioning_status: str
    reason: str = ""
    prior_provisioning_status: str | None = None


class TenantHardDeleteRequest(BaseModel):
    confirm: bool = Field(..., description="Must be True to confirm hard delete")


class AuditLogQueryResponse(BaseModel):
    total: int
    page: int
    size: int
    results: list[dict]


class AuditLogStatsResponse(BaseModel):
    total_events: int
    period_days: int
    top_users: list[dict]
    top_actions: list[dict]
    resource_breakdown: list[dict]
