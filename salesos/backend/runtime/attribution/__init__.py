"""ADR-031: Sales Activity Attribution Engine — Shadow Mode Phase 1.

Writes attribution results to `activity_attributions`. Does NOT affect
scoring or user-visible decisions. Runs in shadow mode until validated.

Resolution chain (priority descending):
  1. explicit_reference — tagged deal ID in subject/body
  2. contact_match — contact → opportunity_contacts → opportunity
  3. company_match — related_company_ids → company → opportunities
  4. domain_match — email domain → company → opportunities
  5. ai_match — LLM-based (deferred)
"""
from __future__ import annotations

import json
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

ALGORITHM_VERSION = "v1.1.1-shadow"

_CONFIDENCE = {
    "explicit_reference": 1.0,
    "contact_match": 0.90,
    "company_match": 0.60,
    "domain_match": 0.30,
    "opportunity_contact_bonus": 0.90,
}

_CONFIRMED_THRESHOLD = 0.50
_CANDIDATE_THRESHOLD = 0.20

_EXPLICIT_REF_PATTERNS = [
    r"\[OPP-([^\]]+)\]",
    r"\[DEAL-([^\]]+)\]",
    r"#OPP-([^\s]+)",
]


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
    """ADR-031 Phase 2: shadow-mode attribution engine.

    Resolves activities through a priority chain:
      1. explicit_reference — tagged deal ID
      2. contact_match — contact → opportunity_contacts → opportunity
      3. company_match — related_company_ids → company → opportunities
      4. domain_match — email domain → company → opportunity

    Writes to activity_attributions. Shadow mode: does NOT affect scoring.
    """

    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def attribute_email(
        self,
        tenant_id: str,
        email_event: dict,
    ) -> list[AttributionResult]:
        """Attribute an email event through the full resolution chain."""
        results: list[AttributionResult] = []
        from_addr = (email_event.get("from_address") or "").lower()
        domain = from_addr.split("@")[-1] if "@" in from_addr else ""
        subject = str(email_event.get("subject") or "")
        body = str(email_event.get("body_preview") or "")
        related_company_ids = email_event.get("related_company_ids") or []
        related_contact_ids = email_event.get("related_contact_ids") or []

        if not domain and not related_company_ids:
            return results

        # ── Step 1: explicit_reference ──
        import re
        for pattern in _EXPLICIT_REF_PATTERNS:
            for match in re.finditer(pattern, subject + " " + body, re.IGNORECASE):
                opp_ref = match.group(1).strip()
                async with self._session_factory() as session:
                    from sqlalchemy import select, text
                    r = await session.execute(
                        select(text("id, name")).select_from(text("commercial_opportunities"))
                        .where(text(f"id LIKE '%{opp_ref}%' OR name ILIKE '%{opp_ref}%'"))
                        .limit(1)
                    )
                    row = r.fetchone()
                    if row:
                        results.append(AttributionResult(
                            activity_type="email",
                            activity_id=email_event.get("id"),
                            activity_source_table="employee_email_events",
                            opportunity_id=row[0],
                            resolution_method="explicit_reference",
                            evidence={"matched_pattern": match.group(0), "opportunity_ref": opp_ref},
                            confidence=_CONFIDENCE["explicit_reference"],
                            confidence_breakdown={"explicit_reference": 1.0},
                            resolution_state="confirmed",
                            resolution_chain=[{"step": "explicit_reference", "pattern": match.group(0)}],
                        ))
                        return results  # highest confidence, return immediately

        # ── Step 2: contact_match via opportunity_contacts ──
        if related_contact_ids:
            async with self._session_factory() as session:
                from sqlalchemy import select, text
                contact_ids_str = ",".join(f"'{cid}'" for cid in related_contact_ids[:10])
                r = await session.execute(
                    select(text("DISTINCT opportunity_id, contact_id, role"))
                    .select_from(text("opportunity_contacts"))
                    .where(text(f"contact_id IN ({contact_ids_str})"))
                    .limit(5)
                )
                oc_rows = r.fetchall()
                if oc_rows:
                    for oc in oc_rows:
                        opp_id = oc[0]
                        if opp_id and opp_id.strip():
                            results.append(AttributionResult(
                                activity_type="email",
                                activity_id=email_event.get("id"),
                                activity_source_table="employee_email_events",
                                opportunity_id=opp_id,
                                resolution_method="contact_match",
                                evidence={"contact_ids": related_contact_ids[:5]},
                                confidence=_CONFIDENCE["contact_match"],
                                confidence_breakdown={"contact_match": _CONFIDENCE["contact_match"]},
                                resolution_state="confirmed",
                                resolution_chain=[{
                                    "step": "contact_match",
                                    "contact_ids": related_contact_ids[:5],
                                    "opportunity_contact_id": oc[0],
                                }],
                            ))
                    if results:
                        return results

        # ── Step 3: company_match via related_company_ids ──
        if related_company_ids:
            async with self._session_factory() as session:
                from sqlalchemy import select, text
                cids = ",".join(f"'{cid}'" for cid in related_company_ids[:5])
                r = await session.execute(
                    select(text("id, name, stage, value"))
                    .select_from(text("commercial_opportunities"))
                    .where(text(f"company_id IN ({cids}) AND status = 'open'"))
                    .order_by(text("created_at DESC"))
                    .limit(3)
                )
                opps = r.fetchall()
                if opps:
                    results.append(AttributionResult(
                        activity_type="email",
                        activity_id=email_event.get("id"),
                        activity_source_table="employee_email_events",
                        opportunity_id=opps[0][0],
                        resolution_method="company_match",
                        evidence={"related_company_ids": related_company_ids[:5]},
                        confidence=_CONFIDENCE["company_match"],
                        confidence_breakdown={"company_match": _CONFIDENCE["company_match"]},
                        resolution_state="confirmed",
                        resolution_chain=[{"step": "company_match", "company_ids": related_company_ids[:5]}],
                    ))
                    return results

        # ── Step 4: domain_match + Company → Opportunities ──
        if domain:
            async with self._session_factory() as session:
                from sqlalchemy import select, text
                r = await session.execute(
                    select(text("id, name_ar, cr_number"))
                    .select_from(text("companies"))
                    .where(text(f"email ILIKE '%{domain}%' OR website ILIKE '%{domain}%'"))
                    .limit(1)
                )
                company_row = r.fetchone()
                if company_row:
                    company_id = company_row[0]
                    r2 = await session.execute(
                        select(text("id, name, stage, value"))
                        .select_from(text("commercial_opportunities"))
                        .where(text(f"company_id = '{company_id}' AND status = 'open'"))
                        .order_by(text("created_at DESC"))
                        .limit(3)
                    )
                    opps = r2.fetchall()
                    if opps:
                        primary = opps[0]
                        alternatives = []
                        for alt in opps[1:]:
                            alternatives.append({
                                "opportunity_id": alt[0],
                                "name": alt[1],
                                "stage": alt[2],
                                "confidence": _CONFIDENCE["domain_match"] * 0.5,
                            })
                        results.append(AttributionResult(
                            activity_type="email",
                            activity_id=email_event.get("id"),
                            activity_source_table="employee_email_events",
                            opportunity_id=primary[0],
                            resolution_method="domain_match",
                            evidence={
                                "email_domain": domain,
                                "company_id": company_id,
                                "company_name": company_row[1],
                            },
                            confidence=_CONFIDENCE["domain_match"],
                            confidence_breakdown={"domain_match": _CONFIDENCE["domain_match"]},
                            resolution_state="confirmed" if not alternatives else "confirmed",
                            resolution_chain=[{
                                "step": "domain_match",
                                "domain": domain,
                                "company_id": company_id,
                            }],
                            alternative_candidates=alternatives if alternatives else None,
                        ))
                        return results

        # ── Fallthrough: unresolved ──
        results.append(AttributionResult(
            activity_type="email",
            activity_id=email_event.get("id"),
            activity_source_table="employee_email_events",
            opportunity_id="",
            resolution_method="domain_match",
            evidence={"email_domain": domain} if domain else {},
            confidence=0.0,
            confidence_breakdown={},
            resolution_state="unresolved",
            resolution_chain=[{"step": "no_match"}],
        ))
        return results

    async def run_shadow_batch(
        self,
        tenant_id: str,
        limit: int = 100,
    ) -> int:
        """Run attribution for unprocessed events. Shadow mode."""
        processed = 0
        async with self._session_factory() as session:
            from sqlalchemy import select, text

            # Get events not yet attributed
            r = await session.execute(
                select(text("*")).select_from(text("employee_email_events"))
                .where(text(
                    "tenant_id = :tid AND id NOT IN ("
                    "SELECT activity_id FROM activity_attributions "
                    "WHERE activity_type = 'email' AND tenant_id = :tid"
                    ")"
                ))
                .order_by(text("created_at DESC"))
                .limit(limit),
                {"tid": str(tenant_id)}
            )
            events = [dict(row._mapping) for row in r.fetchall()]

            for event in events:
                results = await self.attribute_email(tenant_id, event)
                for result in results:
                    existing = await session.execute(
                        select(text("1")).select_from(text("activity_attributions"))
                        .where(text(
                            "tenant_id=:tid AND activity_type=:at AND activity_id=:aid AND opportunity_id=:oid"
                        )),
                        {"tid": str(tenant_id), "at": result.activity_type,
                         "aid": str(result.activity_id), "oid": result.opportunity_id}
                    )
                    if existing.fetchone():
                        continue  # idempotent skip

                    await session.execute(text("""
                        INSERT INTO activity_attributions (
                            id, tenant_id, activity_type, activity_id, activity_source_table,
                            opportunity_id, resolution_method, resolution_chain,
                            evidence, confidence, confidence_breakdown,
                            algorithm_version, resolution_state, alternative_candidates
                        ) VALUES (
                            gen_random_uuid(), :tid, :at, :aid, :ast,
                            :oid, :rm, :rc::jsonb,
                            :ev::jsonb, :cf, :cb::jsonb,
                            :av, :rs, :ac::jsonb
                        )
                    """), {
                        "tid": str(tenant_id), "at": result.activity_type,
                        "aid": str(result.activity_id), "ast": result.activity_source_table,
                        "oid": result.opportunity_id, "rm": result.resolution_method,
                        "rc": json.dumps(result.resolution_chain),
                        "ev": json.dumps(result.evidence),
                        "cf": result.confidence, "cb": json.dumps(result.confidence_breakdown),
                        "av": ALGORITHM_VERSION, "rs": result.resolution_state,
                        "ac": json.dumps(result.alternative_candidates) if result.alternative_candidates else None,
                    })
                    processed += 1
        logger.info("Attribution shadow batch: tenant=%s processed=%d", tenant_id, processed)
        return processed
