"""Master Data API schemas — Pydantic models for request/response."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

# ═══════════════════════════════════════════════════════════════════════════════
# Global Company
# ═══════════════════════════════════════════════════════════════════════════════


class GlobalCompanyCreate(BaseModel):
    canonical_name: str = Field(..., min_length=1, max_length=500)
    canonical_name_ar: str | None = Field(None, max_length=500)
    cr_number: str | None = Field(None, max_length=50)
    vat_number: str | None = Field(None, max_length=50)
    unified_national_number: str | None = Field(None, max_length=50)
    status: str = "active"


class GlobalCompanyUpdate(BaseModel):
    canonical_name: str | None = Field(None, min_length=1, max_length=500)
    canonical_name_ar: str | None = Field(None, max_length=500)
    cr_number: str | None = None
    vat_number: str | None = None
    unified_national_number: str | None = None
    status: str | None = None


class GlobalCompanyResponse(BaseModel):
    id: UUID
    slug: str
    canonical_name: str
    canonical_name_ar: str | None
    cr_number: str | None
    vat_number: str | None
    unified_national_number: str | None
    status: str
    created_at: datetime
    updated_at: datetime | None


# ═══════════════════════════════════════════════════════════════════════════════
# Global Person
# ═══════════════════════════════════════════════════════════════════════════════


class GlobalPersonCreate(BaseModel):
    canonical_name: str = Field(..., min_length=1, max_length=500)
    email: str | None = Field(None, max_length=255)
    phone: str | None = Field(None, max_length=50)
    company_global_id: str | None = None
    job_title: str | None = Field(None, max_length=255)
    status: str = "active"


class GlobalPersonUpdate(BaseModel):
    canonical_name: str | None = Field(None, min_length=1, max_length=500)
    email: str | None = None
    phone: str | None = None
    company_global_id: str | None = None
    job_title: str | None = None
    status: str | None = None


class GlobalPersonResponse(BaseModel):
    id: UUID
    slug: str
    canonical_name: str
    email: str | None
    phone: str | None
    company_global_id: UUID | None
    job_title: str | None
    status: str
    created_at: datetime
    updated_at: datetime | None


# ═══════════════════════════════════════════════════════════════════════════════
# Legacy ID Mapping
# ═══════════════════════════════════════════════════════════════════════════════


class LegacyIDMappingCreate(BaseModel):
    legacy_id_type: str = Field(..., min_length=1, max_length=32)
    legacy_id: str = Field(..., min_length=1, max_length=255)
    global_entity_type: str = Field(..., pattern=r"^[CP]$")
    global_entity_id: str = Field(..., pattern=r"^G-[CP]-[0-9A-HJKMNP-TV-Z]{8}$")
    confidence: float = Field(1.0, ge=0.0, le=1.0)


class LegacyIDMappingResponse(BaseModel):
    id: str
    legacy_id_type: str
    legacy_id: str
    global_entity_type: str
    global_entity_id: str
    confidence: float
    created_at: datetime


# ═══════════════════════════════════════════════════════════════════════════════
# Source File / Source Row
# ═══════════════════════════════════════════════════════════════════════════════


class SourceFileCreate(BaseModel):
    filename: str = Field(..., min_length=1, max_length=512)
    file_hash_sha256: str = Field(..., min_length=1, max_length=64)
    file_size_bytes: int = Field(..., ge=0)
    source_system: str = Field(..., min_length=1, max_length=64)
    mime_type: str = Field(..., min_length=1, max_length=128)
    storage_path: str = Field(..., min_length=1, max_length=1024)
    uploaded_by: str = Field(..., min_length=1)
    sheet_count: int = Field(0, ge=0)
    total_rows: int = Field(0, ge=0)
    schema_mapping: dict[str, Any] | None = None


class SourceFileResponse(BaseModel):
    id: str
    tenant_id: str
    filename: str
    storage_path: str
    file_hash_sha256: str
    file_size_bytes: int
    mime_type: str
    sheet_count: int
    total_rows: int
    source_system: str
    schema_mapping: dict[str, Any] | None
    uploaded_by: str
    uploaded_at: datetime
    status: str


class SourceRowCreate(BaseModel):
    source_file_id: str
    source_id: str = Field(..., min_length=1, max_length=64)
    source_record_id: str = Field(..., min_length=1, max_length=255)
    row_number: int = Field(..., ge=0)
    raw_payload: dict[str, Any]
    sheet_name: str | None = Field(None, max_length=255)
    entity_type: str = Field("company", max_length=32)


class SourceRowResponse(BaseModel):
    id: str
    tenant_id: str
    source_file_id: str
    source_id: str
    source_record_id: str
    row_number: int
    sheet_name: str | None
    raw_payload: dict[str, Any]
    entity_type: str
    resolution_status: str
    created_at: datetime


# ═══════════════════════════════════════════════════════════════════════════════
# Pagination
# ═══════════════════════════════════════════════════════════════════════════════


class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[Any]
    has_next: bool
