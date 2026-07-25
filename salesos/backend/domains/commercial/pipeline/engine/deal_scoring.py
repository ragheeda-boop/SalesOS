"""DealScorer — scores each deal using the Decision Platform.

Factors:
- Deal age (days since creation)
- Stage velocity (time in current stage vs average)
- Historical conversion rate at current stage
- Deal size vs average deal size
- Win probability alignment
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class DealRisk(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DealHealth(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    AT_RISK = "at_risk"


@dataclass
class DealScoreFactor:
    """A single scoring factor for a deal."""

    key: str
    label: str
    value: float  # 0.0 - 1.0
    weight: float = 1.0
    description: str = ""

    @property
    def weighted_value(self) -> float:
        return self.value * self.weight


@dataclass
class DealScore:
    """Complete scoring result for a single deal."""

    deal_id: str
    overall_score: float = 0.0  # 0.0 - 1.0
    health: DealHealth = DealHealth.FAIR
    risk: DealRisk = DealRisk.MEDIUM
    factors: list[DealScoreFactor] = field(default_factory=list)
    recommendation: str = ""
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def top_factors(self) -> list[DealScoreFactor]:
        return sorted(self.factors, key=lambda f: f.weighted_value, reverse=True)[:3]

    @property
    def risk_factors(self) -> list[DealScoreFactor]:
        return [f for f in self.factors if f.value < 0.3]

    def to_dict(self) -> dict:
        return {
            "deal_id": self.deal_id,
            "overall_score": self.overall_score,
            "health": self.health.value,
            "risk": self.risk.value,
            "recommendation": self.recommendation,
            "factors": [{"key": f.key, "label": f.label, "value": f.value, "weight": f.weight} for f in self.factors],
            "generated_at": self.generated_at.isoformat(),
        }


class DealScorer:
    """Scores deals using multi-factor analysis integrated with Decision Platform."""

    def __init__(self):
        self._stage_baselines: dict[str, float] = {
            "prospecting": 0.10,
            "qualification": 0.25,
            "proposal": 0.50,
            "negotiation": 0.75,
            "closed_won": 1.0,
            "closed_lost": 0.0,
        }
        self._avg_deal_size: float = 50000.0
        self._avg_cycle_days: float = 45.0
        self._historical_stage_conversion: dict[str, float] = {}

    def configure(
        self,
        avg_deal_size: float = 50000.0,
        avg_cycle_days: float = 45.0,
        stage_conversion: dict[str, float] | None = None,
    ) -> None:
        self._avg_deal_size = avg_deal_size
        self._avg_cycle_days = avg_cycle_days
        if stage_conversion:
            self._historical_stage_conversion = stage_conversion

    def score_deal(self, deal: dict[str, Any]) -> DealScore:
        """Score a single deal using multi-factor analysis."""
        factors: list[DealScoreFactor] = []

        # Factor 1: Deal age (newer = better, up to a point)
        age_score = self._score_deal_age(deal)
        factors.append(DealScoreFactor(
            key="deal_age",
            label="Deal Age",
            value=age_score,
            weight=0.15,
            description=f"Deal is {deal.get('age_days', 0)} days old",
        ))

        # Factor 2: Stage velocity
        velocity_score = self._score_stage_velocity(deal)
        factors.append(DealScoreFactor(
            key="stage_velocity",
            label="Stage Velocity",
            value=velocity_score,
            weight=0.20,
            description=f"Time in stage: {deal.get('days_in_stage', 0):.0f} days",
        ))

        # Factor 3: Historical conversion at stage
        conversion_score = self._score_stage_conversion(deal)
        factors.append(DealScoreFactor(
            key="historical_conversion",
            label="Historical Conversion",
            value=conversion_score,
            weight=0.25,
            description=f"Stage conversion rate: {conversion_score:.0%}",
        ))

        # Factor 4: Deal size vs average
        size_score = self._score_deal_size(deal)
        factors.append(DealScoreFactor(
            key="deal_size",
            label="Deal Size",
            value=size_score,
            weight=0.15,
            description=f"Deal value: {deal.get('value', 0):,.0f} vs avg {self._avg_deal_size:,.0f}",
        ))

        # Factor 5: Win probability alignment
        prob_score = self._score_probability(deal)
        factors.append(DealScoreFactor(
            key="probability_alignment",
            label="Probability Alignment",
            value=prob_score,
            weight=0.15,
            description=f"Probability: {deal.get('probability', 0):.0%}",
        ))

        # Factor 6: Activity signal (if available)
        activity_score = self._score_activity(deal)
        factors.append(DealScoreFactor(
            key="activity_signal",
            label="Activity Signal",
            value=activity_score,
            weight=0.10,
            description=f"Recent activity: {'Yes' if deal.get('has_activity', False) else 'No'}",
        ))

        # Compute overall score
        total_weight = sum(f.weight for f in factors)
        overall = sum(f.weighted_value for f in factors) / total_weight if total_weight > 0 else 0.0
        overall = round(min(max(overall, 0.0), 1.0), 2)

        health = self._resolve_health(overall)
        risk = self._resolve_risk(overall, factors)
        recommendation = self._generate_recommendation(overall, health, risk, factors)

        return DealScore(
            deal_id=deal.get("id", ""),
            overall_score=overall,
            health=health,
            risk=risk,
            factors=factors,
            recommendation=recommendation,
        )

    def score_batch(self, deals: list[dict[str, Any]]) -> list[DealScore]:
        """Score a batch of deals."""
        # Compute batch-level averages
        values = [d.get("value", 0) for d in deals if d.get("value", 0) > 0]
        if values:
            self._avg_deal_size = sum(values) / len(values)
        return [self.score_deal(d) for d in deals]

    def _score_deal_age(self, deal: dict[str, Any]) -> float:
        """Newer deals score higher (stale deals are risky)."""
        age_days = deal.get("age_days", 0)
        if age_days <= 7:
            return 1.0
        if age_days <= 30:
            return 0.8
        if age_days <= 60:
            return 0.6
        if age_days <= 90:
            return 0.4
        return 0.2

    def _score_stage_velocity(self, deal: dict[str, Any]) -> float:
        """Deals moving faster than average score higher."""
        days_in_stage = deal.get("days_in_stage", 0)
        avg_days = deal.get("avg_stage_days", self._avg_cycle_days / 4)
        if avg_days <= 0:
            return 0.5
        ratio = days_in_stage / avg_days
        if ratio <= 0.5:
            return 1.0
        if ratio <= 1.0:
            return 0.8
        if ratio <= 1.5:
            return 0.5
        if ratio <= 2.0:
            return 0.3
        return 0.1

    def _score_stage_conversion(self, deal: dict[str, Any]) -> float:
        """Use historical conversion rates at this stage."""
        stage = deal.get("stage", "prospecting")
        if stage in self._historical_stage_conversion:
            return self._historical_stage_conversion[stage]
        return self._stage_baselines.get(stage, 0.1)

    def _score_deal_size(self, deal: dict[str, Any]) -> float:
        """Deals close to average size score highest; outliers are riskier."""
        value = deal.get("value", 0)
        if self._avg_deal_size <= 0:
            return 0.5
        ratio = value / self._avg_deal_size
        if 0.5 <= ratio <= 2.0:
            return 0.9
        if 0.2 <= ratio <= 3.0:
            return 0.7
        if ratio > 0:
            return 0.4
        return 0.2

    def _score_probability(self, deal: dict[str, Any]) -> float:
        """Probability should align with stage position."""
        stage = deal.get("stage", "prospecting")
        probability = deal.get("probability", 0)
        expected = self._stage_baselines.get(stage, 0.1)
        if expected <= 0:
            return 0.5
        deviation = abs(probability - expected) / expected
        if deviation <= 0.1:
            return 1.0
        if deviation <= 0.3:
            return 0.7
        return 0.4

    def _score_activity(self, deal: dict[str, Any]) -> float:
        """Recent activity is a positive signal."""
        has_activity = deal.get("has_activity", False)
        activity_count = deal.get("activity_count", 0)
        if has_activity and activity_count >= 3:
            return 1.0
        if has_activity:
            return 0.7
        if activity_count > 0:
            return 0.5
        return 0.2

    def _resolve_health(self, score: float) -> DealHealth:
        if score >= 0.8:
            return DealHealth.EXCELLENT
        if score >= 0.6:
            return DealHealth.GOOD
        if score >= 0.4:
            return DealHealth.FAIR
        if score >= 0.2:
            return DealHealth.POOR
        return DealHealth.AT_RISK

    def _resolve_risk(self, score: float, factors: list[DealScoreFactor]) -> DealRisk:
        risk_count = sum(1 for f in factors if f.value < 0.3)
        if risk_count >= 3 or score < 0.2:
            return DealRisk.CRITICAL
        if risk_count >= 2 or score < 0.4:
            return DealRisk.HIGH
        if risk_count >= 1 or score < 0.6:
            return DealRisk.MEDIUM
        return DealRisk.LOW

    def _generate_recommendation(
        self,
        score: float,
        health: DealHealth,
        risk: DealRisk,
        factors: list[DealScoreFactor],
    ) -> str:
        if health == DealHealth.EXCELLENT:
            return "Deal is strong — maintain momentum and push for close."
        if health == DealHealth.GOOD:
            return "Deal is healthy — focus on moving through next stage."
        if risk == DealRisk.HIGH:
            return "Deal needs attention — review activity and engagement strategy."
        if risk == DealRisk.CRITICAL:
            return "Deal is at serious risk — escalate immediately and reassess."
        return "Deal requires monitoring — ensure consistent activity and follow-up."
