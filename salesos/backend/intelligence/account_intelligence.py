"""Account Intelligence — insights from Account data with evidence chain.

P2-2: Reads Product Core facts (companies, contacts, opportunities, activities,
proposals, reviews) and produces account-level insights with evidence citations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from domains.commercial.evidence.contracts.models import (
    InsightCategory, EvidenceType, ConfidenceLevel,
)
from domains.commercial.evidence.engine.service import EvidenceService
from domains.commercial.memory.engine.service import CommercialMemoryService
from domains.commercial.memory.contracts.models import MemoryEntity, MemoryEventType


@dataclass
class AccountHealth:
    """Aggregated account health metrics from Product Core facts."""
    account_id: str
    account_name: str
    health_score: float             # 0.0 - 1.0
    health_level: str               # healthy / at_risk / critical
    total_opportunities: int = 0
    active_opportunities: int = 0
    won_deals: int = 0
    lost_deals: int = 0
    total_revenue: float = 0.0
    last_activity_days: int = 0
    activity_frequency: float = 0.0  # events per month
    engagement_trend: str = "stable"  # improving / stable / declining


class AccountIntelligenceService:
    """Produces account-level insights from Product Core facts with evidence chain."""

    def __init__(
        self,
        evidence_service: EvidenceService,
        memory_service: CommercialMemoryService,
    ):
        self._evidence = evidence_service
        self._memory = memory_service

    async def analyze_account(
        self,
        tenant_id: str,
        account_id: str,
        account_name: str = "",
        opportunities: list[dict] | None = None,
        activities: list[dict] | None = None,
    ) -> AccountHealth:
        """Analyze account health from Product Core facts."""
        opportunities = opportunities or []
        activities = activities or []

        total = len(opportunities)
        active = sum(1 for o in opportunities if o.get("status") != "won" and o.get("status") != "lost")
        won = sum(1 for o in opportunities if o.get("status") == "won")
        lost = sum(1 for o in opportunities if o.get("status") == "lost")
        revenue = sum(o.get("won_amount", 0.0) or o.get("value", 0.0) for o in opportunities if o.get("status") == "won")

        health_score = self._compute_health_score(total, active, won, lost, revenue, len(activities))
        health_level = "healthy" if health_score >= 0.7 else "at_risk" if health_score >= 0.4 else "critical"

        return AccountHealth(
            account_id=account_id,
            account_name=account_name,
            health_score=health_score,
            health_level=health_level,
            total_opportunities=total,
            active_opportunities=active,
            won_deals=won,
            lost_deals=lost,
            total_revenue=revenue,
            last_activity_days=0,
            activity_frequency=len(activities) / max(1, 1),
            engagement_trend="stable",
        )

    async def record_account_insight(
        self,
        tenant_id: str,
        account_id: str,
        account_name: str,
        health: AccountHealth,
    ) -> str:
        """Record account health insight with evidence chain."""
        evidence_items = []

        if health.total_opportunities > 0:
            evidence_items.append(self._make_evidence(
                EvidenceType.DATA_AGGREGATE, "opportunity", "table_aggregate",
                f"{health.total_opportunities} total opportunities, {health.won_deals} won",
                min(0.9, 0.5 + health.total_opportunities * 0.05),
            ))

        if health.won_deals > 0:
            evidence_items.append(self._make_evidence(
                EvidenceType.FINANCIAL_SIGNAL, "revenue", "aggregate",
                f"Won {health.won_deals} deals worth {health.total_revenue:,.0f}",
                0.9,
            ))

        if health.lost_deals > 0:
            evidence_items.append(self._make_evidence(
                EvidenceType.BUSINESS_RULE, "opportunity", "aggregate",
                f"Lost {health.lost_deals} deals",
                0.8,
            ))

        if health.activity_frequency > 0:
            evidence_items.append(self._make_evidence(
                EvidenceType.ACTIVITY_SIGNAL, "activity", "count",
                f"{health.activity_frequency:.1f} activities",
                min(0.8, 0.3 + health.activity_frequency * 0.1),
            ))

        insight = await self._evidence.record_insight(
            tenant_id=tenant_id,
            category=InsightCategory.ACCOUNT_HEALTH,
            title=f"Account health: {health.health_level} ({health.health_score:.0%})",
            description=f"{account_name} — {health.health_level}",
            target_id=account_id,
            target_type="company",
            evidence_items=evidence_items,
            metadata={
                "health_score": health.health_score,
                "health_level": health.health_level,
                "total_opportunities": health.total_opportunities,
                "won_deals": health.won_deals,
                "lost_deals": health.lost_deals,
                "total_revenue": health.total_revenue,
            },
        )
        return insight.id

    async def get_account_insights(self, tenant_id: str, account_id: str):
        """Get all insights for an account."""
        return await self._evidence.list_insights(
            tenant_id, target_id=account_id, target_type="company",
        )

    @staticmethod
    def _compute_health_score(
        total_opps: int, active: int, won: int, lost: int,
        revenue: float, activities: int,
    ) -> float:
        """Compute account health score from Product Core facts."""
        score = 0.5  # baseline
        if total_opps > 0:
            win_rate = won / total_opps
            score += win_rate * 0.2
        if active > 0:
            score += 0.1
        if revenue > 0:
            score += 0.1
        if activities > 0:
            score += min(0.1, activities * 0.02)
        return round(min(1.0, score), 3)

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
