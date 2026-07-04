"""SQLAlchemy models for all commercial domains — the persistence layer."""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import (
    Boolean, Column, Date, DateTime, Enum as SAEnum,
    Float, ForeignKey, Integer, JSON, String, Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid

from app.common.models import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class OpportunityModel(Base, TimestampMixin):
    __tablename__ = "commercial_opportunities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    company_id: Mapped[str] = mapped_column(String(36), index=True)
    name: Mapped[str] = mapped_column(String(500))
    value: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(3), default="SAR")
    stage: Mapped[str] = mapped_column(String(100), default="prospecting")
    probability: Mapped[float] = mapped_column(Float, default=0.10)
    expected_close_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    owner_id: Mapped[str] = mapped_column(String(36), default="")
    status: Mapped[str] = mapped_column(String(20), default="open")
    won_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    loss_reason: Mapped[str] = mapped_column(Text, default="")
    description: Mapped[str] = mapped_column(Text, default="")
    tags: Mapped[Any] = mapped_column(JSON, default=list)
    extra_data: Mapped[Any] = mapped_column("metadata", JSON, default=dict)


class StageEntryModel(Base):
    __tablename__ = "commercial_stage_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    opportunity_id: Mapped[str] = mapped_column(String(36), ForeignKey("commercial_opportunities.id"), index=True)
    pipeline_id: Mapped[str] = mapped_column(String(36), index=True)
    from_stage: Mapped[str] = mapped_column(String(100))
    to_stage: Mapped[str] = mapped_column(String(100))
    entered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    exited_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


class PipelineDefinitionModel(Base):
    __tablename__ = "commercial_pipeline_definitions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    name: Mapped[str] = mapped_column(String(200))
    stages: Mapped[Any] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class ActivitySessionModel(Base, TimestampMixin):
    __tablename__ = "commercial_activity_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    title: Mapped[str] = mapped_column(String(500))
    target_id: Mapped[str] = mapped_column(String(36), index=True)
    target_type: Mapped[str] = mapped_column(String(50), default="opportunity")
    start_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="scheduled")
    notes: Mapped[str] = mapped_column(Text, default="")


class ActivityModel(Base):
    __tablename__ = "commercial_activities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("commercial_activity_sessions.id"), index=True)
    activity_type: Mapped[str] = mapped_column(String(50))
    owner_id: Mapped[str] = mapped_column(String(36))
    owner_name: Mapped[str] = mapped_column(String(200), default="")
    outcome_id: Mapped[str] = mapped_column(String(100), default="")
    outcome_label: Mapped[str] = mapped_column(String(200), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="scheduled")
    external_id: Mapped[str] = mapped_column(String(200), default="")


class QuoteModel(Base, TimestampMixin):
    __tablename__ = "commercial_quotes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    opportunity_id: Mapped[str] = mapped_column(String(36), index=True)
    title: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(20), default="draft")
    total_value: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(3), default="SAR")
    notes: Mapped[str] = mapped_column(Text, default="")
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by: Mapped[str] = mapped_column(String(36), default="")
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)


class QuoteLineModel(Base):
    __tablename__ = "commercial_quote_lines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    quote_id: Mapped[str] = mapped_column(String(36), ForeignKey("commercial_quotes.id"), index=True)
    description: Mapped[str] = mapped_column(String(500))
    quantity: Mapped[float] = mapped_column(Float, default=1.0)
    unit_price: Mapped[float] = mapped_column(Float, default=0.0)
    total: Mapped[float] = mapped_column(Float, default=0.0)


class ProposalModel(Base, TimestampMixin):
    __tablename__ = "commercial_proposals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    opportunity_id: Mapped[str] = mapped_column(String(36), index=True)
    quote_id: Mapped[str] = mapped_column(String(36), index=True)
    title: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(20), default="draft")
    delivery_method: Mapped[str] = mapped_column(String(100), default="")
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    viewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str] = mapped_column(Text, default="")
    version: Mapped[int] = mapped_column(Integer, default=1)


class ContractModel(Base, TimestampMixin):
    __tablename__ = "commercial_contracts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    opportunity_id: Mapped[str] = mapped_column(String(36), index=True)
    quote_id: Mapped[str] = mapped_column(String(36))
    quote_revision: Mapped[int] = mapped_column(Integer, default=1)
    title: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(20), default="draft")
    parties: Mapped[Any] = mapped_column(JSON, default=list)
    obligations: Mapped[Any] = mapped_column(JSON, default=list)
    effective_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    renewal: Mapped[Any] = mapped_column(JSON, default=dict)
    legal_terms: Mapped[str] = mapped_column(Text, default="")
    governing_law: Mapped[str] = mapped_column(String(100), default="")
    signed_by_provider: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    signed_by_customer: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    version: Mapped[int] = mapped_column(Integer, default=1)


class ForecastSnapshotModel(Base):
    __tablename__ = "commercial_forecast_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    title: Mapped[str] = mapped_column(String(200), default="")
    horizon_months: Mapped[int] = mapped_column(Integer, default=3)
    status: Mapped[str] = mapped_column(String(20), default="calculated")
    lines: Mapped[Any] = mapped_column(JSON, default=list)
    assumptions: Mapped[Any] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    finalized_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)


class AnalyticsSnapshotModel(Base):
    __tablename__ = "commercial_analytics_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    kpis: Mapped[Any] = mapped_column(JSON, default=dict)
    insights: Mapped[Any] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class DecisionContextModel(Base):
    __tablename__ = "commercial_decision_contexts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    target_id: Mapped[str] = mapped_column(String(36), index=True)
    target_type: Mapped[str] = mapped_column(String(50))
    factors: Mapped[Any] = mapped_column(JSON, default=dict)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class PolicyModel(Base):
    __tablename__ = "commercial_policies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    name: Mapped[str] = mapped_column(String(200))
    rules: Mapped[Any] = mapped_column(JSON, default=list)
    outcome: Mapped[str] = mapped_column(String(50))
    priority: Mapped[int] = mapped_column(Integer, default=0)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class RecommendationModel(Base, TimestampMixin):
    __tablename__ = "commercial_recommendations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    target_id: Mapped[str] = mapped_column(String(36), index=True)
    target_type: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text, default="")
    recommendation_type: Mapped[str] = mapped_column(String(100))
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    evidence: Mapped[Any] = mapped_column(JSON, default=list)
    alternatives: Mapped[Any] = mapped_column(JSON, default=list)
    applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    dismissed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
