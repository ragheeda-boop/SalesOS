"""Decision Object — first-class entity for every decision the engine produces."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class DecisionStatus(str, Enum):
    SUGGESTED = "suggested"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXECUTED = "executed"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"


class DecisionType(str, Enum):
    RECOMMEND_DEMO = "recommend_demo"
    RECOMMEND_CALL = "recommend_call"
    RECOMMEND_PROPOSAL = "recommend_proposal"
    RECOMMEND_SEQUENCE = "recommend_sequence"
    RECOMMEND_OUTREACH = "recommend_outreach"
    RECOMMEND_CAMPAIGN = "recommend_campaign"
    RECOMMEND_ESCALATE = "recommend_escalate"
    ALERT = "alert"
    TASK_SUGGESTED = "task_suggested"
    WORKFLOW_SUGGESTED = "workflow_suggested"
    CRM_UPDATE = "crm_update"


@dataclass
class RequiredAction:
    action_type: str
    description: str
    owner: Optional[str] = None
    deadline: Optional[datetime] = None
    depends_on: list[str] = field(default_factory=list)


@dataclass
class DecisionFeedback:
    decision_id: str
    accepted: bool
    executed: bool
    outcome: Optional[str] = None
    outcome_value: Optional[float] = None
    notes: Optional[str] = None
    user_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class DecisionObject:
    decision_id: str
    company_id: str
    tenant_id: str
    decision_type: DecisionType
    priority: int
    confidence: float
    expected_revenue: Optional[float] = None
    expected_probability: Optional[float] = None
    reasoning: str = ""
    evidence: list[str] = field(default_factory=list)
    supporting_features: dict[str, float] = field(default_factory=dict)
    context_snapshot: dict[str, Any] = field(default_factory=dict)
    required_actions: list[RequiredAction] = field(default_factory=list)
    blocked_by: list[str] = field(default_factory=list)
    status: DecisionStatus = DecisionStatus.SUGGESTED
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    feedback: Optional[DecisionFeedback] = None

    def to_dict(self) -> dict:
        return {
            "decision_id": self.decision_id,
            "company_id": self.company_id,
            "tenant_id": self.tenant_id,
            "decision_type": self.decision_type.value,
            "priority": self.priority,
            "confidence": self.confidence,
            "expected_revenue": self.expected_revenue,
            "expected_probability": self.expected_probability,
            "reasoning": self.reasoning,
            "evidence": self.evidence,
            "supporting_features": self.supporting_features,
            "context_snapshot": self.context_snapshot,
            "required_actions": [vars(a) for a in self.required_actions],
            "blocked_by": self.blocked_by,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "feedback": vars(self.feedback) if self.feedback else None,
        }


@dataclass
class DecisionMetricsSnapshot:
    total_decisions: int = 0
    accepted: int = 0
    rejected: int = 0
    executed: int = 0
    revenue_generated: float = 0.0
    meetings_created: int = 0
    win_rate: float = 0.0
    confidence_accuracy: float = 0.0
    by_type: dict[str, int] = field(default_factory=dict)
    by_company: dict[str, int] = field(default_factory=dict)
