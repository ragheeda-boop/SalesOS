from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ContactCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    name_ar: str | None = None
    email: str | None = None
    phone: str | None = None
    mobile: str | None = None
    position: str | None = None
    position_ar: str | None = None
    department: str | None = None
    company_id: str | None = None
    is_primary: bool = False
    source: str | None = None
    tags: list[str] = []


class ContactUpdate(BaseModel):
    name: str | None = None
    name_ar: str | None = None
    email: str | None = None
    phone: str | None = None
    mobile: str | None = None
    position: str | None = None
    position_ar: str | None = None
    department: str | None = None
    is_primary: bool | None = None
    tags: list[str] | None = None


class ContactResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    company_id: UUID | None
    name: str
    name_ar: str | None
    email: str | None
    phone: str | None
    mobile: str | None
    position: str | None
    position_ar: str | None
    department: str | None
    is_primary: bool
    source: str | None
    confidence_score: float | None
    tags: list | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ContactListResponse(BaseModel):
    id: UUID
    name: str
    email: str | None
    phone: str | None
    position: str | None
    company_id: UUID | None
    is_primary: bool
    source: str | None
    created_at: datetime


class ContactSearchParams(BaseModel):
    q: str | None = None
    company_id: str | None = None
    email: str | None = None
    source: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: str = "created_at"
    sort_order: str = "desc"
