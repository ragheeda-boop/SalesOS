"""Entity Resolution models: GoldenRecord, conflicts, and resolution log."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.common.models import BaseModel


class GoldenRecord(BaseModel):
    __tablename__ = "golden_records"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    cr_number: Mapped[str] = mapped_column(String(50), nullable=False)
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True
    )
    data: Mapped[dict] = mapped_column(
        JSONB, nullable=False,
        comment="All fields with provenance: {field: {value, source, confidence, timestamp, verified_by}}",
    )
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    source_ids: Mapped[list | None] = mapped_column(JSONB, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self) -> str:
        return f"<GoldenRecord cr={self.cr_number} confidence={self.confidence_score:.2f}>"


class EntityResolutionConflict(BaseModel):
    __tablename__ = "entity_resolution_conflicts"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    golden_record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("golden_records.id"), nullable=False
    )
    field_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_a_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_a_source: Mapped[str] = mapped_column(String(100), nullable=False)
    source_b_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_b_source: Mapped[str] = mapped_column(String(100), nullable=False)
    resolution_strategy: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="open")

    def __repr__(self) -> str:
        return f"<Conflict {self.field_name}: {self.source_a_source} vs {self.source_b_source}>"


class EntityResolutionLog(BaseModel):
    __tablename__ = "entity_resolution_log"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    operation: Mapped[str] = mapped_column(String(50), nullable=False)
    source_slug: Mapped[str | None] = mapped_column(String(100), nullable=True)
    records_processed: Mapped[int] = mapped_column(Integer, default=0)
    records_matched: Mapped[int] = mapped_column(Integer, default=0)
    records_created: Mapped[int] = mapped_column(Integer, default=0)
    records_merged: Mapped[int] = mapped_column(Integer, default=0)
    confidence_threshold: Mapped[float | None] = mapped_column(Float, nullable=True)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<ResolutionLog {self.operation}: {self.records_processed} records>"
