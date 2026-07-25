"""SQLAlchemy models for Analytics & Reporting persistence layer."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.common.models import Base


class ReportModel(Base):
    __tablename__ = "analytics_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False, default="custom")
    config: Mapped[Any] = mapped_column(JSON, nullable=False, default=dict)
    metrics: Mapped[Any] = mapped_column(JSON, nullable=False, default=list)
    dimensions: Mapped[Any] = mapped_column(JSON, nullable=False, default=list)
    filters: Mapped[Any] = mapped_column(JSON, nullable=False, default=dict)
    visualization_type: Mapped[str] = mapped_column(String(50), nullable=False, default="table")
    created_by: Mapped[str] = mapped_column(String(36), nullable=False, default="")
    schedule: Mapped[str] = mapped_column(String(100), nullable=False, default="one-time")
    recipients: Mapped[Any] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )


class ReportExecutionModel(Base):
    __tablename__ = "analytics_report_executions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    report_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    output_format: Mapped[str] = mapped_column(String(10), nullable=False, default="json")
    output_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ReportShareModel(Base):
    __tablename__ = "analytics_report_shares"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    report_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    permission: Mapped[str] = mapped_column(String(20), nullable=False, default="view")
    shared_by: Mapped[str] = mapped_column(String(36), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )


class ScheduledReportModel(Base):
    __tablename__ = "analytics_scheduled_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    report_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    cadence: Mapped[str] = mapped_column(String(20), nullable=False, default="weekly")
    recipients: Mapped[Any] = mapped_column(JSON, nullable=False, default=list)
    next_run: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_run: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
