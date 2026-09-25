"""Persistence schema for evidence-backed canonical fact proposals.

This module defines storage only. It intentionally does not expose a writer or
an auto-apply path; those require the ownership, dismissal, and transactional
guards documented in ADR-0114.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.common.models import BaseModel


class EvidenceRecord(BaseModel):
    """Source evidence snapshot; facts link through FactEvidence."""

    __tablename__ = "evidence_records"
    __table_args__ = (
        UniqueConstraint("id", "tenant_id", name="uq_evidence_records_id_tenant"),
        UniqueConstraint("tenant_id", "evidence_hash", name="uq_evidence_records_tenant_hash"),
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1", name="ck_evidence_records_confidence"
        ),
        Index("ix_evidence_records_tenant_observed", "tenant_id", "observed_at"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    source_domain: Mapped[str] = mapped_column(String(64), nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_id: Mapped[str | None] = mapped_column(String(255))
    source_name: Mapped[str | None] = mapped_column(String(255))
    evidence_kind: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    evidence_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CanonicalFact(BaseModel):
    """A tenant-scoped proposal or governed decision for one CRM field."""

    __tablename__ = "canonical_facts"
    __table_args__ = (
        UniqueConstraint("id", "tenant_id", name="uq_canonical_facts_id_tenant"),
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_canonical_facts_idempotency"),
        CheckConstraint(
            "subject_type IN ('company', 'contact')", name="ck_canonical_facts_subject_type"
        ),
        CheckConstraint(
            "status IN ('PROPOSED', 'APPROVED', 'REJECTED', 'DISMISSED', 'APPLIED', 'SUPERSEDED', 'STALE')",
            name="ck_canonical_facts_status",
        ),
        CheckConstraint("score >= 0 AND score <= 1", name="ck_canonical_facts_score"),
        Index("ix_canonical_facts_tenant_subject", "tenant_id", "subject_type", "subject_id"),
        Index("ix_canonical_facts_tenant_status", "tenant_id", "status"),
        Index(
            "uq_canonical_facts_open_value",
            "tenant_id",
            "subject_type",
            "subject_id",
            "field_name",
            "value_hash",
            unique=True,
            postgresql_where=text("status = 'PROPOSED'"),
        ),
        # A dismissed value remains blocked even if a later fact is applied or superseded.
        Index(
            "uq_canonical_facts_dismissed_value",
            "tenant_id",
            "subject_type",
            "subject_id",
            "field_name",
            "value_hash",
            unique=True,
            postgresql_where=text("status = 'DISMISSED'"),
        ),
        ForeignKeyConstraint(
            ["supersedes_fact_id", "tenant_id"],
            ["canonical_facts.id", "canonical_facts.tenant_id"],
            name="fk_canonical_facts_supersedes_tenant",
        ),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    subject_type: Mapped[str] = mapped_column(String(16), nullable=False)
    # Polymorphic CRM target. The proposal service must verify the target under tenant RLS.
    subject_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    proposed_value: Mapped[Any] = mapped_column(JSONB, nullable=False)
    value_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="PROPOSED")
    evidence_band: Mapped[str] = mapped_column(String(20), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    decision_reason: Mapped[str] = mapped_column(Text, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_type: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_id: Mapped[str | None] = mapped_column(String(128))
    reviewer_id: Mapped[str | None] = mapped_column(String(128))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    supersedes_fact_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    evidence_snapshot: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list
    )


class FactEvidence(BaseModel):
    """Many-to-many evidence link with tenant consistency enforced by composite FKs."""

    __tablename__ = "fact_evidence"
    __table_args__ = (
        ForeignKeyConstraint(
            ["fact_id", "tenant_id"],
            ["canonical_facts.id", "canonical_facts.tenant_id"],
            ondelete="CASCADE",
            name="fk_fact_evidence_fact_tenant",
        ),
        ForeignKeyConstraint(
            ["evidence_id", "tenant_id"],
            ["evidence_records.id", "evidence_records.tenant_id"],
            ondelete="CASCADE",
            name="fk_fact_evidence_evidence_tenant",
        ),
        UniqueConstraint(
            "tenant_id",
            "fact_id",
            "evidence_id",
            name="uq_fact_evidence_tenant_fact_evidence",
        ),
        Index("ix_fact_evidence_tenant_evidence", "tenant_id", "evidence_id"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    fact_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    evidence_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    relation: Mapped[str] = mapped_column(String(24), nullable=False, server_default="SUPPORTS")


class CanonicalFactEvent(BaseModel):
    """Append-oriented audit event for proposal and future reviewer transitions."""

    __tablename__ = "canonical_fact_events"
    __table_args__ = (
        ForeignKeyConstraint(
            ["fact_id", "tenant_id"],
            ["canonical_facts.id", "canonical_facts.tenant_id"],
            ondelete="CASCADE",
            name="fk_canonical_fact_events_fact_tenant",
        ),
        Index("ix_canonical_fact_events_tenant_fact", "tenant_id", "fact_id", "created_at"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    fact_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    from_status: Mapped[str | None] = mapped_column(String(20))
    to_status: Mapped[str] = mapped_column(String(20), nullable=False)
    actor_type: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_id: Mapped[str | None] = mapped_column(String(128))
    reason: Mapped[str | None] = mapped_column(Text)
    event_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
