"""ADR-031: Sales Activity Attribution Engine — Shadow Mode Phase 1.

Writes attribution results to `activity_attributions`. Does NOT affect
scoring or user-visible decisions. Runs in shadow mode until validated.

Resolution chain (priority descending):
  1. explicit_reference — tagged deal ID in subject/body
  2. contact_match — contact → opportunity_contacts → opportunity
  3. domain_match — email domain → company → opportunities
  4. company_match — related_company_ids → company → opportunities
  5. ai_match — LLM-based (deferred)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Index, Numeric, String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from sdk.database import Base

logger = logging.getLogger(__name__)

ALGORITHM_VERSION = "v1.0.0-shadow"


class ActivityAttribution(Base):
    __tablename__ = "activity_attributions"

    id: Mapped[str] = mapped_column(PGUUID(as_uuid=True), primary_key=True,
                                     default=lambda: str(uuid4()))
    tenant_id: Mapped[str] = mapped_column(PGUUID(as_uuid=True),
                                            ForeignKey("tenants.id", ondelete="CASCADE"),
                                            nullable=False, index=True)

    activity_type: Mapped[str] = mapped_column(String(20), nullable=False)
    activity_id: Mapped[str] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    activity_source_table: Mapped[str] = mapped_column(String(50), nullable=False)

    opportunity_id: Mapped[str] = mapped_column(String(36), nullable=False)

    resolution_method: Mapped[str] = mapped_column(String(30), nullable=False)
    resolution_chain: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)

    evidence: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False, default=0)
    confidence_breakdown: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    algorithm_version: Mapped[str] = mapped_column(String(30), nullable=False)
    resolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                   default=lambda: datetime.now(timezone.utc))

    resolution_state: Mapped[str] = mapped_column(String(20), nullable=False,
                                                    default="confirmed")
    alternative_candidates: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                  default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                  default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("tenant_id", "activity_type", "activity_id", "opportunity_id",
                         name="uq_aa_activity_opp"),
        Index("idx_aa_tenant", "tenant_id"),
        Index("idx_aa_activity", "activity_type", "activity_id"),
        Index("idx_aa_opportunity", "opportunity_id"),
        Index("idx_aa_resolution_state", "tenant_id", "resolution_state"),
        Index("idx_aa_tenant_opp", "tenant_id", "opportunity_id"),
    )


@dataclass
class AttributionResult:
    activity_type: str
    activity_id: UUID
    activity_source_table: str
    opportunity_id: str
    resolution_method: str
    evidence: dict = field(default_factory=dict)
    confidence: float = 0.0
    confidence_breakdown: dict = field(default_factory=dict)
    resolution_state: str = "confirmed"
    resolution_chain: list = field(default_factory=list)
    alternative_candidates: list | None = None


class AttributionEngine:
    """ADR-031 Phase 1: shadow-mode attribution engine.

    Reads employee email/calendar events, resolves through the entity
    chain, and writes results to activity_attributions. Does NOT modify
    scoring or user-visible decisions.
    """

    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def attribute_email(
        self,
        tenant_id: UUID,
        email_event: dict,
    ) -> list[AttributionResult]:
        """Attribute an email event to opportunities. Shadow mode only."""
        results: list[AttributionResult] = []

        # Phase 1: domain_match only (simplest, highest-confidence path)
        # Future phases will add explicit_ref, contact_match, company_match, ai_match
        from_address = (email_event.get("from_address") or "").lower()
        domain = from_address.split("@")[-1] if "@" in from_address else ""

        if not domain:
            return results

        results.append(AttributionResult(
            activity_type="email",
            activity_id=UUID(str(email_event["id"])),
            activity_source_table="employee_email_events",
            opportunity_id="",  # Resolved by caller
            resolution_method="domain_match",
            evidence={"email_domain": domain},
            confidence=0.3,
            resolution_state="unresolved",
            resolution_chain=[{"step": "domain_match", "domain": domain}],
        ))

        return results

    async def run_shadow_batch(
        self,
        tenant_id: UUID,
        limit: int = 100,
    ) -> int:
        """Run attribution for unprocessed events. Returns count processed."""
        # Phase 1 skeleton: scan for events, run attribution, store results
        # Full implementation deferred to Phase 2
        logger.info(
            "Attribution shadow batch: tenant=%s limit=%d (skeleton — Phase 2)",
            tenant_id, limit,
        )
        return 0
