"""Pydantic schemas for Entity Resolution module."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProvenanceField(BaseModel):
    value: str | int | float | bool | None = None
    source: str
    source_record_id: str | None = None
    confidence: float = 0.0
    timestamp: datetime | None = None
    verified_by: str | None = None


class GoldenRecordResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    cr_number: str
    company_id: UUID | None = None
    data: dict
    confidence_score: float
    source_ids: list | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GoldenRecordListResponse(BaseModel):
    id: UUID
    cr_number: str
    company_id: UUID | None = None
    confidence_score: float
    source_count: int = 0
    created_at: datetime


class ConflictResponse(BaseModel):
    id: UUID
    golden_record_id: UUID
    field_name: str
    source_a_value: str | None
    source_a_source: str
    source_b_value: str | None
    source_b_source: str
    resolution_strategy: str | None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConflictResolveRequest(BaseModel):
    resolution_strategy: str = Field(
        ...,
        pattern=r"^(use_source_a|use_source_b|merge|custom)$",
        description="Resolution strategy: use_source_a, use_source_b, merge, custom",
    )
    custom_value: str | None = Field(None, description="Custom value when strategy is 'custom'")


class ResolutionRunRequest(BaseModel):
    source_slug: str | None = Field(None, description="Source to resolve (None = all sources)")
    confidence_threshold: float = Field(0.7, ge=0.0, le=1.0)
    records: list[dict] = Field(default_factory=list, description="List of records to resolve (each must contain 'cr_number')")


class ResolutionRunResponse(BaseModel):
    operation_id: str
    source_slug: str | None
    records_processed: int
    records_matched: int
    records_created: int
    records_merged: int
    conflicts_detected: int
    duration_seconds: float


class ResolutionLogResponse(BaseModel):
    id: UUID
    operation: str
    source_slug: str | None
    records_processed: int
    records_matched: int
    records_created: int
    records_merged: int
    performed_at: datetime = Field(alias="created_at")

    class Config:
        from_attributes = True
        populate_by_name = True
