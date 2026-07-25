from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.common.models import Base


class EmployeeSignalModel(Base):
    __tablename__ = "employee_signals"

    id = Column(UUID(as_uuid=True), primary_key=True)
    employee_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    signal_type = Column(String(50), nullable=False)
    source = Column(String(30), nullable=False)
    signal_metadata = Column("metadata", JSONB, nullable=True, default=dict)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_employee_signals_tenant_employee", "tenant_id", "employee_id"),
        Index("ix_employee_signals_tenant_employee_ts", "tenant_id", "employee_id", "timestamp"),
        Index("ix_employee_signals_source", "source"),
        Index("ix_employee_signals_type", "signal_type"),
        Index("ix_employee_signals_timestamp", "timestamp"),
    )


class EmployeeScoreModel(Base):
    __tablename__ = "employee_scores"

    id = Column(UUID(as_uuid=True), primary_key=True)
    employee_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    overall_score = Column(Float, nullable=False, default=0.0)
    signal_volume_score = Column(Float, nullable=False, default=0.0)
    recency_score = Column(Float, nullable=False, default=0.0)
    diversity_score = Column(Float, nullable=False, default=0.0)
    completion_rate = Column(Float, nullable=False, default=0.0)
    confidence_interval_low = Column(Float, nullable=False, default=0.0)
    confidence_interval_high = Column(Float, nullable=False, default=0.0)
    signal_count = Column(Integer, nullable=False, default=0)
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_employee_scores_tenant_employee", "tenant_id", "employee_id"),
        Index("ix_employee_scores_tenant_employee_gen", "tenant_id", "employee_id", "generated_at"),
    )
