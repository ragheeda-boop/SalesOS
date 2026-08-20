"""SQLAlchemy models for the approval domain — HITL persistence layer."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Float, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from sdk.database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class ApprovalRequestModel(Base, TimestampMixin):
    """P3-5: Human-in-the-loop approval request for AI-generated actions."""

    __tablename__ = "approval_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    target_type: Mapped[str] = mapped_column(String(50), index=True)
    target_id: Mapped[str] = mapped_column(String(36), index=True)
    requested_by: Mapped[str] = mapped_column(String(36), default="system")
    action_summary: Mapped[str] = mapped_column(Text, default="")
    action_evidence: Mapped[Any] = mapped_column(JSON, default=list)
    required_level: Mapped[str] = mapped_column(String(20), default="manager")
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    assigned_to: Mapped[str] = mapped_column(String(36), default="")
    decisions: Mapped[Any] = mapped_column(JSON, default=list)
    extra_metadata: Mapped[Any] = mapped_column("metadata", JSON, default=dict)
    priority: Mapped[float] = mapped_column(Float, default=5.0)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_approval_requests_tenant_status", "tenant_id", "status"),
        Index("ix_approval_requests_tenant_target", "tenant_id", "target_type", "target_id"),
        Index("ix_approval_requests_assigned", "tenant_id", "assigned_to", "status"),
    )
