from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 20
    cursor: str | None = None
    sort_by: str = "created_at"
    sort_dir: str = "desc"

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list
    next_cursor: str | None = None
    has_next: bool = False


class CursorResponse(BaseModel):
    data: list
    next_cursor: str | None = None
    previous_cursor: str | None = None
    has_next: bool = False
    has_previous: bool = False
    total: int | None = None


class MessageResponse(BaseModel):
    message: str
    code: str = "OK"


class ErrorResponse(BaseModel):
    detail: str
    code: str = "ERROR"
    errors: list | None = None


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    cache: str
    graph: str = "not_configured"
    kafka: str = "not_configured"
    redis: str = "unknown"
    rate_limiter: str = "unknown"
    uptime_seconds: float = 0.0


class PingResponse(BaseModel):
    """GET /ping — process-local liveness (no dependency checks)."""

    ping: str


class HealthLiveResponse(BaseModel):
    """GET /health/live — Kubernetes-style liveness (no DB/cache)."""

    status: str
    uptime_seconds: float


class HealthReadyResponse(BaseModel):
    """GET /health/ready - readiness probe (DB + cache required for ready)."""

    status: str
    checks: dict


class AuditLogEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    entity_type: str
    entity_id: str
    action: str
    changes: dict | None = None
    performed_by: UUID | None = None
    performed_at: datetime
    ip_address: str | None = None
