import uuid

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID

from sdk.database import Base


class Opportunity(Base):
    __tablename__ = "opportunities"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    # Index name owned by __table_args__ (ix_opportunities_company) — no index=True
    # (avoids duplicate ix_opportunities_company_id vs rename target).
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    title = Column(String(500), nullable=False)
    stage = Column(String(20), default="identified")
    estimated_value = Column(Numeric(15, 2))
    confidence = Column(Numeric(3, 2))
    win_probability = Column(Numeric(3, 2))
    source = Column(String(20), default="manual")
    source_action_id = Column(String(100))
    buying_intent = Column(Numeric(3, 2))
    relationship_strength = Column(Numeric(3, 2))
    risk_level = Column(String(10))
    assignee_id = Column(UUID(as_uuid=True))
    expected_close_date = Column(Date)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    stage_changed_at = Column(DateTime(timezone=True))
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_opportunities_tenant_stage", "tenant_id", "stage"),
        Index("ix_opportunities_company", "company_id"),
    )


class Task(Base):
    __tablename__ = "tasks"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), index=True)
    # FE SoT opportunity ids live on commercial_opportunities (String 36). No FK —
    # revenue `opportunities.id` is a different table (A.2 dual-table).
    opportunity_id = Column(String(36), nullable=True)
    title = Column(String(500), nullable=False)
    priority = Column(String(10))
    source = Column(String(20), default="manual")
    assignee_id = Column(UUID(as_uuid=True))
    due_date = Column(Date)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_tasks_tenant_priority", "tenant_id", "priority"),
        Index("ix_tasks_assignee_completed", "assignee_id", "completed"),
        Index("ix_tasks_tenant_opportunity", "tenant_id", "opportunity_id"),
    )
