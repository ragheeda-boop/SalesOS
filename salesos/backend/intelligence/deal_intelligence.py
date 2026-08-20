"""Deal Intelligence — health, risk, opportunity insights with evidence chain.

P2-3: Reads Product Core facts (opportunities, pipeline, activities, proposals,
reviews) and produces deal-level insights with evidence citations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from domains.commercial.evidence.contracts.models import (
    InsightCategory, EvidenceType, ConfidenceLevel,
)
from domains.commercial.evidence.engine.service import EvidenceService
from domains.commercial.memory.engine.service import CommercialMemoryService
from domains.commercial.memory.contracts.models import MemoryEventType


@dataclass
class DealHealth:
    """Aggregated deal health metrics from Product Core facts."""
    deal_id: str
    deal_name: str
    health_score: float             # 0.0 - 1.0
    health_level: str               # healthy / at_risk / critical
    risk_factors: list[str] = field(default_factory=list)
    opportunity_factors: list[str] = field(default_factory=list)
    stage: str = ""
    value: float = 0.0
    probability: float = 0.0
    days_in_stage: int = 0
    activity_count: int = 0
    proposal_status: str = ""
    review_status: str = ""


class DealIntelligenceService:
    """Produces deal-level insights from Product Core facts with evidence chain."""

    def __init__(
        self,
        evidence_service: EvidenceService,
        memory_service: CommercialMemoryService,
    ):
        self._evidence = evidence_service
        self._memory = memory_service

    async def analyze_deal(
        self,
        tenant_id: str,
        deal_id: str,
        deal_name: str = "",
        stage: str = "",
        value: float = 0.0,
        probability: float = 0.0,
        days_in_stage: int = 0,
        activity_count: int = 0,
        proposal_status: str = "",
        review_status: str = "",
    ) -> DealHealth:
        """Analyze deal health from Product Core facts."""
        risk_factors = []
        opportunity_factors = []

        if days_in_stage > 30:
            risk_factors.append(f"Stalled {days_in_stage} days in {stage}")
        if activity_count == 0:
            risk_factors.append("No activities recorded")
        if proposal_status == "rejected":
            risk_factors.append("Proposal was rejected")
        if review_status == "rejected":
            risk_factors.append("Review was rejected")
        if probability < 0.3:
            risk_factors.append(f"Low probability ({probability:.0%})")

        if probability > 0.7:
            opportunity_factors.append(f"High probability ({probability:.0%})")
        if value > 100000:
            opportunity_factors.append(f"High value deal ({value:,.0f})")
        if proposal_status == "accepted":
            opportunity_factors.append("Proposal accepted")
        if review_status == "approved":
            opportunity_factors.append("Review approved")
        if activity_count > 5:
            opportunity_factors.append(f"Active engagement ({activity_count} activities)")

        health_score = self._compute_health_score(
            probability, value, days_in_stage, activity_count,
            len(risk_factors), len(opportunity_factors),
        )
        health_level = "healthy" if health_score >= 0.7 else "at_risk" if health_score >= 0.4 else "critical"

        return DealHealth(
            deal_id=deal_id,
            deal_name=deal_name,
            health_score=health_score,
            health_level=health_level,
            risk_factors=risk_factors,
            opportunity_factors=opportunity_factors,
            stage=stage,
            value=value,
            probability=probability,
            days_in_stage=days_in_stage,
            activity_count=activity_count,
            proposal_status=proposal_status,
            review_status=review_status,
        )

    async def record_deal_insight(
        self,
        tenant_id: str,
        deal_id: str,
        deal_name: str,
        health: DealHealth,
    ) -> str:
        """Record deal health insight with evidence chain."""
        evidence_items = []

        evidence_items.append(self._make_evidence(
            EvidenceType.PIPELINE_SIGNAL, "opportunity", "field",
            f"Stage: {health.stage}, probability: {health.probability:.0%}, value: {health.value:,.0f}",
            min(0.9, 0.5 + health.probability * 0.4),
        ))

        for rf in health.risk_factors:
            evidence_items.append(self._make_evidence(
                EvidenceType.BUSINESS_RULE, "opportunity", "rule",
                rf, 0.8,
            ))

        for of in health.opportunity_factors:
            evidence_items.append(self._make_evidence(
                EvidenceType.DATA_AGGREGATE, "opportunity", "aggregate",
                of, 0.7,
            ))

        category = InsightCategory.DEAL_RISK if health.health_level == "critical" else InsightCategory.DEAL_OPPORTUNITY if health.health_level == "healthy" else InsightCategory.DEAL_RISK

        insight = await self._evidence.record_insight(
            tenant_id=tenant_id,
            category=category,
            title=f"Deal health: {health.health_level} ({health.health_score:.0%})",
            description=f"{deal_name} — {health.health_level}",
            target_id=deal_id,
            target_type="opportunity",
            evidence_items=evidence_items,
            metadata={
                "health_score": health.health_score,
                "health_level": health.health_level,
                "stage": health.stage,
                "value": health.value,
                "probability": health.probability,
                "risk_factors": health.risk_factors,
                "opportunity_factors": health.opportunity_factors,
            },
        )
        return insight.id

    async def get_deal_insights(self, tenant_id: str, deal_id: str):
        """Get all insights for a deal."""
        return await self._evidence.list_insights(
            tenant_id, target_id=deal_id, target_type="opportunity",
        )

    @staticmethod
    def _compute_health_score(
        probability: float, value: float, days_in_stage: int,
        activity_count: int, risk_count: int, opportunity_count: int,
    ) -> float:
        score = probability * 0.4
        if value > 0:
            score += min(0.2, value / 500000 * 0.2)
        if activity_count > 0:
            score += min(0.15, activity_count * 0.03)
        if days_in_stage < 14:
            score += 0.1
        score += opportunity_count * 0.05
        score -= risk_count * 0.1
        return round(max(0.0, min(1.0, score)), 3)

    @staticmethod
    def _make_evidence(
        evidence_type: EvidenceType,
        source_domain: str,
        source_type: str,
        description: str,
        confidence: float,
    ) -> Any:
        from domains.commercial.evidence.contracts.models import EvidenceItem, EvidenceSource, ConfidenceLevel
        level = ConfidenceLevel.HIGH if confidence >= 0.8 else ConfidenceLevel.MEDIUM if confidence >= 0.5 else ConfidenceLevel.LOW
        import uuid
        return EvidenceItem(
            id=str(uuid.uuid4()),
            evidence_type=evidence_type,
            source=EvidenceSource(source_domain=source_domain, source_type=source_type),
            description=description,
            confidence=confidence,
            confidence_level=level,
        )
