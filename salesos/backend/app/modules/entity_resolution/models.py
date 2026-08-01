"""Entity Resolution models: GoldenRecord, conflicts, resolution log, and dead letter queue."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.common.models import Base, BaseModel


class GoldenRecord(BaseModel):
    __tablename__ = "golden_records"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    cr_number: Mapped[str] = mapped_column(String(50), nullable=False)
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True, index=True
    )
    data: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        # Align to live DB COMMENT (0001) — no verified_by (DEC-130g)
        comment="All fields with provenance: {field: {value, source, confidence, timestamp}}",
    )
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    source_ids: Mapped[list | None] = mapped_column(JSONB, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (
        Index("ix_golden_records_tenant_company", "tenant_id", "company_id"),
        Index("ix_golden_records_tenant_active", "tenant_id", "is_active"),
        # Live unique (0001) — register to silence remove_index (DEC-130g)
        Index("ix_golden_records_tenant_cr", "tenant_id", "cr_number", unique=True),
    )

    def __repr__(self) -> str:
        return f"<GoldenRecord cr={self.cr_number} confidence={self.confidence_score:.2f}>"


class EntityResolutionConflict(BaseModel):
    __tablename__ = "entity_resolution_conflicts"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    golden_record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("golden_records.id"), nullable=False, index=True
    )
    field_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_a_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_a_source: Mapped[str] = mapped_column(String(100), nullable=False)
    source_b_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_b_source: Mapped[str] = mapped_column(String(100), nullable=False)
    resolution_strategy: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="open", index=True)

    __table_args__ = (
        Index("ix_conflicts_tenant_status", "tenant_id", "status"),
        # Live name (0027) — register to silence remove_index (DEC-130g)
        Index("ix_conflicts_golden_status", "golden_record_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<Conflict {self.field_name}: {self.source_a_source} vs {self.source_b_source}>"


class EntityResolutionLog(Base):
    """Resolution batch log.

    Schema honesty (alembic 0001_baseline): column is ``performed_at``, not
    BaseModel ``created_at``/``updated_at``. CI runs alembic before pytest, so
    mapping must match the migrated table.
    """

    __tablename__ = "entity_resolution_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )
    operation: Mapped[str] = mapped_column(String(50), nullable=False)
    source_slug: Mapped[str | None] = mapped_column(String(100), nullable=True)
    records_processed: Mapped[int] = mapped_column(Integer, default=0)
    records_matched: Mapped[int] = mapped_column(Integer, default=0)
    records_created: Mapped[int] = mapped_column(Integer, default=0)
    records_merged: Mapped[int] = mapped_column(Integer, default=0)
    confidence_threshold: Mapped[float | None] = mapped_column(Float, nullable=True)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    performed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    @property
    def created_at(self) -> datetime:
        """Alias for API/schema consumers that still read ``created_at``."""
        return self.performed_at

    def __repr__(self) -> str:
        return f"<ResolutionLog {self.operation}: {self.records_processed} records>"


class DeadLetterRecord(Base):
    """Failed pipeline records (alembic 0011).

    Schema honesty: ``id`` is Integer PK; ``tenant_id`` is String(36);
    table has ``created_at`` only (no BaseModel ``updated_at``).
    """

    __tablename__ = "dead_letter_queue"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    source_slug: Mapped[str] = mapped_column(String(100), nullable=False)
    cr_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    stage: Mapped[str] = mapped_column(String(50), nullable=False)
    record_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    error_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="failed")
    # DB allows NULL (0011); do not SET NOT NULL without null inventory (DEC-130d)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=True,
    )
    last_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        # Live names (0011) — register to silence remove_index (DEC-130g)
        Index("ix_dlq_created_at", "created_at"),
        Index("ix_dlq_tenant_status", "tenant_id", "status"),
    )
