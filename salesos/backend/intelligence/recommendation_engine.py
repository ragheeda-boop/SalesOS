"""Recommendation Engine — Data → Intelligence → Evidence → Recommendation.

P2-7: Single durable recommendation spine that reads from Intelligence layer
(not LLM → recommendation). Uses Evidence chain for grounding.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import uuid


class RecommendationPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RecommendationStatus(str, Enum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


@dataclass
class RecommendationEvidence:
    """Evidence supporting a recommendation."""
    source_domain: str
    source_type: str
    description: str
    confidence: float


@dataclass
class Recommendation:
    """A data-grounded recommendation with evidence chain."""
    id: str
    tenant_id: str
    title: str
    description: str
    reasoning: str
    priority: RecommendationPriority
    confidence: float
    target_id: str
    target_type: str             # "company", "opportunity", "proposal"
    evidence: list[RecommendationEvidence] = field(default_factory=list)
    status: RecommendationStatus = RecommendationStatus.PROPOSED
    created_at: Any = None

    @property
    def evidence_summary(self) -> list[str]:
        return [e.description for e in self.evidence if e.description]


class RecommendationEngine:
    """Produces recommendations from Intelligence layer data (not LLM)."""

    def __init__(self):
        pass

    def recommend_from_account_health(
        self,
        tenant_id: str,
        account_id: str,
        account_name: str,
        health_level: str,
        health_score: float,
        won_deals: int = 0,
        lost_deals: int = 0,
        active_opportunities: int = 0,
    ) -> Recommendation:
        """Generate recommendation from account health intelligence."""
        evidence = []
        reasoning_parts = []

        if health_level == "critical":
            priority = RecommendationPriority.CRITICAL
            title = f"Urgent: {account_name} account at critical risk"
            description = f"Account health score is {health_score:.0%} (critical). Immediate attention required."
            reasoning_parts.append(f"Health score {health_score:.0%} below 40% threshold")
            evidence.append(RecommendationEvidence(
                source_domain="account_intelligence", source_type="health_score",
                description=f"Health score: {health_score:.0%}", confidence=0.9,
            ))
        elif health_level == "at_risk":
            priority = RecommendationPriority.HIGH
            title = f"Review: {account_name} account at risk"
            description = f"Account health score is {health_score:.0%} (at risk). Schedule review meeting."
            reasoning_parts.append(f"Health score {health_score:.0%} below 70% threshold")
            evidence.append(RecommendationEvidence(
                source_domain="account_intelligence", source_type="health_score",
                description=f"Health score: {health_score:.0%}", confidence=0.8,
            ))
        else:
            priority = RecommendationPriority.LOW
            title = f"Monitor: {account_name} account healthy"
            description = f"Account health score is {health_score:.0%} (healthy). Continue current approach."
            reasoning_parts.append(f"Health score {health_score:.0%} above 70% threshold")
            evidence.append(RecommendationEvidence(
                source_domain="account_intelligence", source_type="health_score",
                description=f"Health score: {health_score:.0%}", confidence=0.7,
            ))

        if won_deals > 0:
            evidence.append(RecommendationEvidence(
                source_domain="commercial_memory", source_type="deal_outcome",
                description=f"{won_deals} deals won", confidence=0.9,
            ))
        if lost_deals > 0:
            evidence.append(RecommendationEvidence(
                source_domain="commercial_memory", source_type="deal_outcome",
                description=f"{lost_deals} deals lost", confidence=0.9,
            ))

        return Recommendation(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            title=title,
            description=description,
            reasoning="; ".join(reasoning_parts),
            priority=priority,
            confidence=min(1.0, health_score + 0.1),
            target_id=account_id,
            target_type="company",
            evidence=evidence,
        )

    def recommend_from_deal_health(
        self,
        tenant_id: str,
        deal_id: str,
        deal_name: str,
        health_level: str,
        health_score: float,
        risk_factors: list[str] | None = None,
        opportunity_factors: list[str] | None = None,
    ) -> Recommendation:
        """Generate recommendation from deal health intelligence."""
        evidence = []
        reasoning_parts = []
        risk_factors = risk_factors or []
        opportunity_factors = opportunity_factors or []

        if health_level == "critical":
            priority = RecommendationPriority.CRITICAL
            title = f"Escalate: {deal_name} at critical risk"
            description = f"Deal health is {health_score:.0%} (critical). Escalate to management."
            reasoning_parts.append(f"Health score {health_score:.0%} below 40%")
        elif health_level == "at_risk":
            priority = RecommendationPriority.HIGH
            title = f"Action needed: {deal_name} at risk"
            description = f"Deal health is {health_score:.0%} (at risk). Take corrective action."
            reasoning_parts.append(f"Health score {health_score:.0%} below 70%")
        else:
            priority = RecommendationPriority.MEDIUM
            title = f"Advance: {deal_name} on track"
            description = f"Deal health is {health_score:.0%} (healthy). Push to close."
            reasoning_parts.append(f"Health score {health_score:.0%} above 70%")

        for rf in risk_factors:
            evidence.append(RecommendationEvidence(
                source_domain="deal_intelligence", source_type="risk_factor",
                description=rf, confidence=0.8,
            ))
        for of in opportunity_factors:
            evidence.append(RecommendationEvidence(
                source_domain="deal_intelligence", source_type="opportunity_factor",
                description=of, confidence=0.7,
            ))

        return Recommendation(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            title=title,
            description=description,
            reasoning="; ".join(reasoning_parts),
            priority=priority,
            confidence=min(1.0, health_score + 0.1),
            target_id=deal_id,
            target_type="opportunity",
            evidence=evidence,
        )

    def recommend_from_forecast(
        self,
        tenant_id: str,
        coverage_ratio: float,
        commit_amount: float,
        risk_amount: float,
    ) -> Recommendation:
        """Generate recommendation from forecast intelligence."""
        evidence = []
        reasoning_parts = []

        if coverage_ratio < 1.0:
            priority = RecommendationPriority.HIGH
            title = "Forecast gap: pipeline coverage below 1.0x"
            description = f"Pipeline coverage is {coverage_ratio:.1f}x — below 1.0x target. Need more pipeline."
            reasoning_parts.append(f"Coverage {coverage_ratio:.1f}x below 1.0x")
            evidence.append(RecommendationEvidence(
                source_domain="forecasting", source_type="coverage",
                description=f"Pipeline coverage: {coverage_ratio:.1f}x", confidence=0.9,
            ))
        elif coverage_ratio > 3.0:
            priority = RecommendationPriority.LOW
            title = "Forecast surplus: pipeline coverage above 3.0x"
            description = f"Pipeline coverage is {coverage_ratio:.1f}x — above 3.0x. Focus on qualification."
            reasoning_parts.append(f"Coverage {coverage_ratio:.1f}x above 3.0x")
            evidence.append(RecommendationEvidence(
                source_domain="forecasting", source_type="coverage",
                description=f"Pipeline coverage: {coverage_ratio:.1f}x", confidence=0.8,
            ))
        else:
            priority = RecommendationPriority.MEDIUM
            title = f"Forecast healthy: {coverage_ratio:.1f}x coverage"
            description = f"Pipeline coverage is {coverage_ratio:.1f}x — within target range."
            reasoning_parts.append(f"Coverage {coverage_ratio:.1f}x within 1.0-3.0x range")
            evidence.append(RecommendationEvidence(
                source_domain="forecasting", source_type="coverage",
                description=f"Pipeline coverage: {coverage_ratio:.1f}x", confidence=0.7,
            ))

        if risk_amount > 0:
            evidence.append(RecommendationEvidence(
                source_domain="forecasting", source_type="risk",
                description=f"At-risk amount: {risk_amount:,.0f}", confidence=0.8,
            ))

        return Recommendation(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            title=title,
            description=description,
            reasoning="; ".join(reasoning_parts),
            priority=priority,
            confidence=min(1.0, 0.6 + abs(coverage_ratio - 2.0) * 0.1),
            target_id="",
            target_type="forecast",
            evidence=evidence,
        )
