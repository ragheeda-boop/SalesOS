from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from sqlalchemy import Column, String, Numeric, DateTime, Date, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
import uuid

Base = declarative_base()

class Opportunity(Base):
    __tablename__ = "opportunities"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
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
    created_at = Column(DateTime, default=datetime.utcnow)
    stage_changed_at = Column(DateTime)
    last_activity_at = Column(DateTime, default=datetime.utcnow)


class Task(Base):
    __tablename__ = "tasks"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    title = Column(String(500), nullable=False)
    priority = Column(String(10))
    source = Column(String(20), default="manual")
    assignee_id = Column(UUID(as_uuid=True))
    due_date = Column(Date)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
