"""
Agent Runtime data models — Phase 1.

SQLAlchemy 2.0 ORM models for durable agent execution:
  - AgentTask: lease-based work queue with fencing token
  - AgentRun: execution session with budget/cost tracking
  - AgentAction: side-effect ledger with idempotency
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from sdk.database import Base, TimestampMixin


class AgentTask(Base, TimestampMixin):
    __tablename__ = "agent_tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    kind: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(50))
    entity_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    completion_reason: Mapped[str | None] = mapped_column(String(30))

    priority: Mapped[int] = mapped_column(Integer, default=0)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    budget: Mapped[int] = mapped_column(Integer, default=4)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    attempts: Mapped[int] = mapped_column(Integer, default=0)

    lease_generation: Mapped[int] = mapped_column(Integer, default=0)
    leased_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    leased_by: Mapped[str | None] = mapped_column(String(100))

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    outcome: Mapped[str | None] = mapped_column(Text)
    session_id: Mapped[str | None] = mapped_column(String(255))

    input_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    idempotency_key: Mapped[str | None] = mapped_column(String(255))


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("agent_tasks.id"), nullable=False)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    agent_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="RUNNING")

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    budget_spent: Mapped[int] = mapped_column(Integer, default=0)
    input_tokens: Mapped[int] = mapped_column(BigInteger, default=0)
    output_tokens: Mapped[int] = mapped_column(BigInteger, default=0)
    cost_usd: Mapped[float] = mapped_column(Numeric(12, 6), default=0)

    result_summary: Mapped[str | None] = mapped_column(Text)
    result_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    session_data: Mapped[dict] = mapped_column(JSONB, default=dict)


class AgentAction(Base):
    __tablename__ = "agent_actions"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("agent_runs.id"), nullable=False)
    task_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("agent_tasks.id"), nullable=False)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    action_type: Mapped[str] = mapped_column(String(20), nullable=False)
    target_entity: Mapped[str] = mapped_column(String(100), nullable=False)
    target_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)

    status: Mapped[str] = mapped_column(String(20), default="PENDING")
    idempotency_key: Mapped[str | None] = mapped_column(String(255))
    pdp_result: Mapped[str | None] = mapped_column(String(20))
    approval_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# Index declarations (PostgreSQL partial indexes done in migration)
idx_agent_tasks_dispatch = Index(
    "idx_agent_tasks_dispatch",
    AgentTask.tenant_id, AgentTask.status, AgentTask.due_at,
    postgresql_where=AgentTask.status == "PENDING",
)

idx_agent_tasks_entity = Index(
    "idx_agent_tasks_entity",
    AgentTask.tenant_id, AgentTask.entity_type, AgentTask.entity_id, AgentTask.kind,
)

idx_agent_runs_task = Index("idx_agent_runs_task", AgentRun.task_id)
