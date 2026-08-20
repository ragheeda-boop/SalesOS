"""SQLAlchemy models for all commercial domains — the persistence layer."""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import (
    Boolean, Column, Date, DateTime, Enum as SAEnum,
    Float, ForeignKey, Index, Integer, JSON, String, Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sdk.database import Base


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

    __table_args__ = (
        Index("ix_commercial_opps_tenant_stage", "tenant_id", "stage"),
        Index("ix_commercial_opps_tenant_status", "tenant_id", "status"),
        Index("ix_commercial_opps_owner", "owner_id"),
    )


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

    __table_args__ = (
        Index("ix_stage_entries_opportunity", "opportunity_id"),
        Index("ix_stage_entries_tenant_entered", "tenant_id", "entered_at"),
    )


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
    # P1-5: direct FK links for unified activity spine
    company_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    contact_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    deal_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    __table_args__ = (
        Index("ix_activity_sessions_tenant_status", "tenant_id", "status"),
        Index("ix_activity_sessions_target", "target_id", "target_type"),
        Index("ix_activity_sessions_company", "company_id"),
        Index("ix_activity_sessions_contact", "contact_id"),
        Index("ix_activity_sessions_deal", "deal_id"),
        Index("ix_activity_sessions_tenant_deal", "tenant_id", "deal_id"),
    )


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

    __table_args__ = (
        Index("ix_activities_type_status", "activity_type", "status"),
        Index("ix_activities_owner", "owner_id"),
        # Live name (0007) — register to silence remove_index (DEC-130g)
        Index("ix_activities_session_type", "session_id", "activity_type"),
    )


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

    __table_args__ = (
        Index("ix_commercial_quotes_tenant_status", "tenant_id", "status"),
        # Live name (0007) — keep alongside ORM rename (DEC-130g)
        Index("ix_quotes_opportunity_status", "opportunity_id", "status"),
    )


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

    __table_args__ = (
        Index("ix_commercial_proposals_tenant_status", "tenant_id", "status"),
    )


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

    __table_args__ = (
        Index("ix_commercial_contracts_tenant_status", "tenant_id", "status"),
        Index("ix_commercial_contracts_expiry", "expiry_date"),
        # Live legacy name (0007) — keep twin (DEC-130g; no DROP)
        Index("ix_contracts_tenant_status", "tenant_id", "status"),
    )


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

    __table_args__ = (
        # Live name (0007) — register to silence remove_index (DEC-130g)
        Index("ix_decision_contexts_target", "target_id", "target_type"),
    )


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


class MeetingModel(Base, TimestampMixin):
    __tablename__ = "meetings"

    # DEC-121 / DB-05 Slice 2: Alembic `0013` + live DB use UUID; keep Mapped[str]
    # via as_uuid=False (domain/repos stay str). Do not ALTER DDL → String(36).
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(UUID(as_uuid=False), index=True)
    opportunity_id: Mapped[str] = mapped_column(UUID(as_uuid=False), index=True)
    title: Mapped[str] = mapped_column(String(500))
    meeting_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="scheduled")

    __table_args__ = (
        Index("ix_meetings_tenant_date", "tenant_id", "meeting_date"),
        Index("ix_meetings_status", "status"),
        # Live name (0013) — register to silence remove_index (DEC-130g)
        Index("ix_meetings_opportunity", "opportunity_id", "tenant_id"),
    )


class EmailModel(Base, TimestampMixin):
    __tablename__ = "emails"

    # DEC-121 / DB-05 Slice 2: same UUID authority as MeetingModel (see above).
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(UUID(as_uuid=False), index=True)
    opportunity_id: Mapped[str] = mapped_column(UUID(as_uuid=False), index=True)
    subject: Mapped[str] = mapped_column(String(500))
    from_address: Mapped[str] = mapped_column(String(254))
    to_addresses: Mapped[Any] = mapped_column(JSON, default=list)
    direction: Mapped[str] = mapped_column(String(10), default="outbound")
    email_type: Mapped[str] = mapped_column(String(50), default="general")
    body: Mapped[str] = mapped_column(Text, default="")
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_emails_tenant_sent", "tenant_id", "sent_at"),
        Index("ix_emails_direction", "direction"),
        # Live name (0013) — register to silence remove_index (DEC-130g)
        Index("ix_emails_opportunity", "opportunity_id", "tenant_id"),
    )


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

    __table_args__ = (
        Index("ix_commercial_recs_tenant_status", "tenant_id", "status"),
        Index("ix_commercial_recs_target", "target_id", "target_type"),
        # Live legacy name (0007) — keep twin (DEC-130g; no DROP)
        Index("ix_recommendations_target", "target_id", "target_type"),
    )


class OpportunityContactModel(Base, TimestampMixin):
    """ADR-030: Canonical Opportunity <-> Contact junction table.

    opportunity_id is String(36) referencing commercial_opportunities.id.
    FK is deferred — String(36) vs UUID type mismatch (ADR-030 readiness check Gate 5).
    Application-level orphan cleanup in PostgresOpportunityRepository.delete().
    """

    __tablename__ = "opportunity_contacts"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=lambda: str(__import__("uuid").uuid4()))
    tenant_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    opportunity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    contact_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_opportunity_contacts_lookup", "tenant_id", "opportunity_id", "contact_id", unique=True),
        Index("ix_oc_tenant_opp", "tenant_id", "opportunity_id"),
    )


class ReviewModel(Base, TimestampMixin):
    """P1-8: Review workflow — tracks approval for deals, quotes, proposals."""

    __tablename__ = "commercial_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    review_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_id: Mapped[str] = mapped_column(String(36), index=True)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    assigned_to: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    requested_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    decisions: Mapped[Any] = mapped_column(JSON, default=list)
    extra_metadata: Mapped[Any] = mapped_column("metadata", JSON, default=dict)

    __table_args__ = (
        Index("ix_commercial_reviews_tenant_status", "tenant_id", "status"),
        Index("ix_commercial_reviews_target", "target_type", "target_id"),
        Index("ix_commercial_reviews_assigned", "assigned_to"),
    )


class QuotaModel(Base, TimestampMixin):
    """P1-6: Revenue quota per rep per period."""

    __tablename__ = "commercial_quotas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    rep_id: Mapped[str] = mapped_column(String(36), index=True)
    rep_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    period: Mapped[str] = mapped_column(String(20), default="quarterly")
    target_amount: Mapped[float] = mapped_column(Float, default=0.0)
    attained_amount: Mapped[float] = mapped_column(Float, default=0.0)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="active")
    extra_metadata: Mapped[Any] = mapped_column("metadata", JSON, default=dict)

    __table_args__ = (
        Index("ix_commercial_quotas_tenant_status", "tenant_id", "status"),
        Index("ix_commercial_quotas_tenant_rep", "tenant_id", "rep_id"),
    )


class TerritoryModel(Base, TimestampMixin):
    """P1-6: Sales territory with assigned accounts."""

    __tablename__ = "commercial_territories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    region: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    rep_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    rep_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    account_ids: Mapped[Any] = mapped_column(JSON, default=list)
    extra_metadata: Mapped[Any] = mapped_column("metadata", JSON, default=dict)

    __table_args__ = (
        Index("ix_commercial_territories_tenant_rep", "tenant_id", "rep_id"),
        Index("ix_commercial_territories_tenant_region", "tenant_id", "region"),
    )


class InsightModel(Base, TimestampMixin):
    """P2-6: Commercial insight backed by evidence chain."""

    __tablename__ = "commercial_insights"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    category: Mapped[str] = mapped_column(String(50), index=True)
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text, default="")
    target_id: Mapped[str] = mapped_column(String(36), index=True)
    target_type: Mapped[str] = mapped_column(String(50), index=True)
    overall_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    confidence_level: Mapped[str] = mapped_column(String(20), default="unknown")
    extra_metadata: Mapped[Any] = mapped_column("metadata", JSON, default=dict)

    __table_args__ = (
        Index("ix_commercial_insights_tenant_category", "tenant_id", "category"),
        Index("ix_commercial_insights_tenant_confidence", "tenant_id", "confidence_level"),
    )


class EvidenceItemModel(Base, TimestampMixin):
    """P2-6: Individual evidence item linked to an insight."""

    __tablename__ = "commercial_evidence_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    insight_id: Mapped[str] = mapped_column(String(36), index=True)
    evidence_type: Mapped[str] = mapped_column(String(50))
    source_domain: Mapped[str] = mapped_column(String(50))
    source_type: Mapped[str] = mapped_column(String(50))
    source_id: Mapped[str] = mapped_column(String(36), default="")
    source_name: Mapped[str] = mapped_column(String(200), default="")
    description: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    confidence_level: Mapped[str] = mapped_column(String(20), default="unknown")
    extra_data: Mapped[Any] = mapped_column("data", JSON, default=dict)

    __table_args__ = (
        Index("ix_commercial_evidence_insight", "insight_id"),
        Index("ix_commercial_evidence_type", "evidence_type"),
    )
