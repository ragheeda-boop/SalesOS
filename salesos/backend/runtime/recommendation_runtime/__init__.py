"""Recommendation Runtime — generates actionable recommendations from decisions.

Turns a DecisionObject into concrete recommendations with:
  - Actions (what to do)
  - Workflow (how to do it)
  - AI prompts (optional)
  - Metrics (expected impact)
  - Audit trail
  - Feedback hook
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Optional


logger = logging.getLogger(__name__)

_DEFAULT_MAX_RECS = 10000
_DEFAULT_REC_TTL_SECONDS = 3600


class RecommendationStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COMPLETED = "completed"


@dataclass
class RecommendationAction:
    order: int
    action_type: str
    description: str
    owner: Optional[str] = None
    deadline: Optional[datetime] = None
    depends_on: list[int] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Recommendation:
    recommendation_id: str
    decision_id: str
    company_id: str
    tenant_id: str
    title: str
    description: str
    priority: int
    confidence: float
    expected_impact: Optional[float] = None
    expected_impact_metric: str = "revenue"
    reasoning: str = ""
    evidence: list[str] = field(default_factory=list)
    actions: list[RecommendationAction] = field(default_factory=list)
    suggested_workflow: Optional[str] = None
    ai_prompt: Optional[str] = None
    status: RecommendationStatus = RecommendationStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    accepted_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    feedback: Optional[dict] = None

    def to_dict(self) -> dict:
        return {
            "recommendation_id": self.recommendation_id,
            "decision_id": self.decision_id,
            "company_id": self.company_id,
            "tenant_id": self.tenant_id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "confidence": self.confidence,
            "expected_impact": self.expected_impact,
            "expected_impact_metric": self.expected_impact_metric,
            "reasoning": self.reasoning,
            "evidence": self.evidence,
            "actions": [vars(a) for a in self.actions],
            "suggested_workflow": self.suggested_workflow,
            "ai_prompt": self.ai_prompt,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
            "rejected_at": self.rejected_at.isoformat() if self.rejected_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "feedback": self.feedback,
        }


# ── Built-in Decision Templates ──────────────────────────────

TEMPLATES: dict[str, dict] = {
    "high_intent": {
        "name": "High Buying Intent",
        "description": "Company shows strong buying signals — recommend demo sequence",
        "decision_type": "recommend_demo",
        "priority": 85,
        "min_confidence": 0.7,
        "actions": [
            {"order": 1, "action_type": "call", "description": "Schedule discovery call with decision maker"},
            {"order": 2, "action_type": "demo", "description": "Deliver product demo tailored to their industry"},
            {"order": 3, "action_type": "proposal", "description": "Send proposal with pricing"},
        ],
        "suggested_workflow": "sequence_a",
    },
    "funding_trigger": {
        "name": "Funding Event",
        "description": "Company raised funding — recommend executive outreach",
        "decision_type": "recommend_outreach",
        "priority": 90,
        "min_confidence": 0.65,
        "actions": [
            {"order": 1, "action_type": "research", "description": "Research funding round details and new hiring"},
            {"order": 2, "action_type": "outreach", "description": "Executive-to-executive outreach"},
            {"order": 3, "action_type": "meeting", "description": "Schedule strategic alignment meeting"},
        ],
        "suggested_workflow": "executive_outreach",
    },
    "hiring_surge": {
        "name": "Hiring Surge",
        "description": "Company is rapidly hiring — recommend HR campaign",
        "decision_type": "recommend_campaign",
        "priority": 75,
        "min_confidence": 0.6,
        "actions": [
            {"order": 1, "action_type": "campaign", "description": "Launch HR / talent acquisition campaign"},
            {"order": 2, "action_type": "content", "description": "Share relevant case studies on scaling teams"},
            {"order": 3, "action_type": "call", "description": "Follow up with CHRO / HR Director"},
        ],
        "suggested_workflow": "hr_campaign",
    },
    "renewal_risk": {
        "name": "Renewal At Risk",
        "description": "Contract expiring soon — recommend renewal sequence",
        "decision_type": "recommend_sequence",
        "priority": 95,
        "min_confidence": 0.8,
        "actions": [
            {"order": 1, "action_type": "review", "description": "Review usage and satisfaction data"},
            {"order": 2, "action_type": "call", "description": "Schedule business review with decision maker"},
            {"order": 3, "action_type": "proposal", "description": "Prepare renewal proposal with expansion options"},
        ],
        "suggested_workflow": "renewal_sequence",
    },
    "expansion_potential": {
        "name": "Expansion Potential",
        "description": "Company has high expansion potential — recommend upsell campaign",
        "decision_type": "recommend_campaign",
        "priority": 80,
        "min_confidence": 0.6,
        "actions": [
            {"order": 1, "action_type": "analysis", "description": "Analyze current product usage and gaps"},
            {"order": 2, "action_type": "call", "description": "Schedule expansion discovery call"},
            {"order": 3, "action_type": "proposal", "description": "Present expansion proposal"},
        ],
        "suggested_workflow": "expansion_campaign",
    },
}


class RecommendationEngine:
    """Generates structured Recommendation objects from decisions + templates."""

    def __init__(self, logger: Any = None):
        self._logger = logger
        self._generated = 0
        self._recommendations: dict[str, Recommendation] = {}
        self._max_recommendations = _DEFAULT_MAX_RECS
        self._rec_ttl = _DEFAULT_REC_TTL_SECONDS

    async def generate(
        self,
        decision_id: str,
        company_id: str,
        tenant_id: str,
        decision_type: str,
        priority: int,
        confidence: float,
        reasoning: str,
        evidence: list[str],
        context: dict,
    ) -> Recommendation:
        template = self._match_template(decision_type, context)
        actions = []
        for i, a in enumerate(template.get("actions", [])):
            actions.append(RecommendationAction(
                order=a["order"],
                action_type=a["action_type"],
                description=a["description"],
            ))

        self._evict_recommendations()
        self._generated += 1
        rec = Recommendation(
            recommendation_id=f"rec_{decision_id}",
            decision_id=decision_id,
            company_id=company_id,
            tenant_id=tenant_id,
            title=template.get("name", "Recommendation"),
            description=template.get("description", ""),
            priority=priority,
            confidence=confidence,
            reasoning=reasoning.split(".")[0] if "." in reasoning else reasoning,
            evidence=evidence,
            actions=actions,
            suggested_workflow=template.get("suggested_workflow"),
        )
        self._recommendations[rec.recommendation_id] = rec
        return rec

    def _match_template(self, decision_type: str, context: dict) -> dict:
        features = context.get("features", {})
        intent = features.get("intent_score", 0)
        funding = features.get("funding_score", 0)
        hiring = features.get("hiring_score", 0)
        expansion = features.get("expansion_score", 0)

        if expansion > 70:
            return TEMPLATES.get("expansion_potential", TEMPLATES["high_intent"])
        if funding > 70:
            return TEMPLATES.get("funding_trigger", TEMPLATES["high_intent"])
        if hiring > 70:
            return TEMPLATES.get("hiring_surge", TEMPLATES["high_intent"])
        if intent > 70:
            return TEMPLATES.get("high_intent", TEMPLATES["high_intent"])

        return {
            "name": "General Recommendation",
            "description": "Standard recommendation based on available data",
            "decision_type": decision_type,
            "priority": priority,
            "actions": [
                {"order": 1, "action_type": "call", "description": "Reach out to key contacts"},
                {"order": 2, "action_type": "follow_up", "description": "Follow up with relevant content"},
            ],
            "suggested_workflow": "standard_sequence",
        }

    def metrics(self) -> dict:
        return {"recommendations_generated": self._generated}

    def _evict_recommendations(self) -> int:
        """Evict expired and overflow recommendations. Returns number evicted."""
        evicted = 0
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(seconds=self._rec_ttl)

        expired = [
            rid for rid, r in self._recommendations.items()
            if r.created_at < cutoff
        ]
        for rid in expired:
            del self._recommendations[rid]
            evicted += 1

        overflow = len(self._recommendations) - self._max_recommendations
        if overflow > 0:
            oldest = sorted(
                self._recommendations.items(),
                key=lambda x: x[1].created_at,
            )[:overflow]
            for rid, _ in oldest:
                del self._recommendations[rid]
                evicted += 1

        if evicted > 0 and self._logger:
            self._logger.warning(
                "Recommendation store evicted %d entries. Current: %d",
                evicted, len(self._recommendations),
            )

        return evicted
