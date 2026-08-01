"""SQLAlchemy ORM models for Workflow domain."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from sdk.database import Base


class WorkflowModel(Base):
    __tablename__ = "workflow_definitions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # DB nullable with defaults (DEC-130d — ORM align; no SET NOT NULL)
    description: Mapped[str | None] = mapped_column(Text, nullable=True, default="")
    trigger_type: Mapped[str | None] = mapped_column(String(50), nullable=True, default="manual")
    status: Mapped[str | None] = mapped_column(String(20), nullable=True, default="draft", index=True)
    steps: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)
    # Optional — older DBs may lack this column until migration 005/0031b applied.
    timeout_seconds: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class WorkflowExecutionModel(Base):
    __tablename__ = "workflow_executions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workflow_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    trigger_event: Mapped[str | None] = mapped_column(String(100), nullable=True, default="manual")
    status: Mapped[str | None] = mapped_column(String(20), nullable=True, default="running", index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    step_results: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)


class WebhookEndpointModel(Base):
    __tablename__ = "webhook_endpoints"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    name: Mapped[str] = mapped_column(String(255), default="")
    auth_type: Mapped[str] = mapped_column(String(20), default="none")
    auth_config: Mapped[dict] = mapped_column(JSONB, default=dict)
    secret: Mapped[str] = mapped_column(String(512), default="")
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ScheduledJobModel(Base):
    __tablename__ = "scheduled_jobs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    job_type: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    config: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    schedule: Mapped[str | None] = mapped_column(String(255), nullable=True, default="")
    status: Mapped[str | None] = mapped_column(String(20), nullable=True, default="active", index=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    run_count: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    max_retries: Mapped[int | None] = mapped_column(Integer, nullable=True, default=3)
    retry_count: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class JobExecutionModel(Base):
    __tablename__ = "job_executions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    job_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    status: Mapped[str | None] = mapped_column(String(20), nullable=True, default="pending", index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
