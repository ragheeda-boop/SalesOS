"""RecommendationEngine — consumes Decision Context, produces explainable recommendations.

Each recommendation includes reasoning, confidence, evidence, alternatives.
AI agents consume recommendations — the engine itself is deterministic rules + ML optional.
"""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any

from ..context.models import DecisionContext
from .models import Alternative, Recommendation, RecommendationEvidence, RecommendationStatus


class RecommendationEngine:
    """Rule-based recommendation engine. Deterministic, explainable, auditable."""

    def __init__(self, event_bus: Any = None):
        self._event_bus = event_bus

    async def evaluate(self, context: DecisionContext) -> Recommendation | None:
        """Evaluate a decision context and produce a recommendation."""

        # Collect evidence from critical factors
        evidence: list[RecommendationEvidence] = []
        recommendations: list[dict] = []

        for factor in context.factors:
            if factor.severity == "critical" and factor.key == "stage_aging":
                evidence.append(RecommendationEvidence(
                    source_layer=factor.source_layer, source_domain=factor.source_domain,
                    key=factor.key, value=factor.value,
                    narrative=f"Stage aging: {factor.label}",
                ))
                recommendations.append({
                    "title": "Schedule executive engagement",
                    "desc": f"Opportunity has been in stage for {factor.value} days with no recent activity.",
                    "reason": "Stage aging detected: no activity, high risk of stall or loss.",
                    "confidence": 0.87,
                    "risk": "Low — recommendation only, no automated action.",
                    "impact": "Re-engaging decision maker reduces stall risk.",
                    "alternatives": [
                        ("Send follow-up proposal", "Lower effort, but may not escalate urgency."),
                        ("Add new decision maker contact", "Expands relationship surface."),
                    ],
                })

            if factor.severity == "warning" and factor.key in ("forecast_drop", "revenue_variance"):
                evidence.append(RecommendationEvidence(
                    source_layer=factor.source_layer, source_domain=factor.source_domain,
                    key=factor.key, value=factor.value,
                    narrative=f"{'Forecast drop' if factor.key == 'forecast_drop' else 'Revenue variance'}: {factor.label}",
                ))
                recommendations.append({
                    "title": "Review deal health",
                    "desc": f"Revenue variance or forecast drop detected ({factor.value}). Review deal status.",
                    "reason": f"Signal from {factor.source_domain}: {factor.label}",
                    "confidence": 0.75,
                    "risk": "Medium — requires manual review.",
                    "impact": "Early detection prevents unexpected revenue loss.",
                    "alternatives": [
                        ("Schedule pipeline review", "Broader scope, more time investment."),
                        ("Request updated forecast", "Improves accuracy with minimal effort."),
                    ],
                })

            if factor.severity == "critical" and factor.key == "stalled_pipeline":
                evidence.append(RecommendationEvidence(
                    source_layer=factor.source_layer, source_domain=factor.source_domain,
                    key=factor.key, value=factor.value,
                    narrative=f"Pipeline stalled: {factor.label}",
                ))
                recommendations.append({
                    "title": "Unblock pipeline stage",
                    "desc": f"Pipeline stage progression stalled for {factor.value} days.",
                    "reason": "Pipeline stage duration exceeds SLA with no exit criteria met.",
                    "confidence": 0.82,
                    "risk": "Low — monitoring recommendation.",
                    "impact": "Removing blockers accelerates deal cycle.",
                    "alternatives": [
                        ("Escalate to manager", "Increases visibility, adds pressure."),
                        ("Re-evaluate deal qualification", "May reveal stage is incorrect."),
                    ],
                })

        if not recommendations:
            return None

        # Take the highest priority recommendation
        rec = recommendations[0]
        result = Recommendation(
            id=str(uuid.uuid4()),
            tenant_id=context.tenant_id,
            context_id=context.id,
            title=rec["title"],
            description=rec["desc"],
            reasoning=rec["reason"],
            confidence=rec["confidence"],
            risk=rec["risk"],
            expected_impact=rec["impact"],
            evidence=evidence,
            alternatives=[Alternative(title=a[0], description=a[1]) for a in rec["alternatives"]],
            target_id=context.target_id,
            target_type=context.target_type,
        )

        if self._event_bus:
            from sdk.events.base import DomainEvent
            event = DomainEvent(event_type="recommendation.generated", tenant_id=context.tenant_id,
                                aggregate_id=result.id,
                                data={"target_id": context.target_id, "title": result.title, "confidence": result.confidence})
            event.event_type = "recommendation.generated"
            await self._event_bus.publish(event)

        return result
