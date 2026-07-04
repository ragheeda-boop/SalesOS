from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 20

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
    kafka: str


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
