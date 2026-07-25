"""Decision Center domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class DecisionDomain(str, Enum):
    PIPELINE = "pipeline"
    EMPLOYEE = "employee"
    COMPANY = "company"
    REVENUE = "revenue"
    GENERAL = "general"


class DecisionType(str, Enum):
    LEAD_QUALIFICATION = "lead_qualification"
    DEAL_PROGRESSION = "deal_progression"
    RENEWAL_RISK = "renewal_risk"
    PRICING = "pricing"
    DEAL_SCORING = "deal_scoring"
    PERFORMANCE = "performance"
    HEALTH = "health"
    FORECAST = "forecast"
    OTHER = "other"


class DecisionStatus(str, Enum):
    ACTIVE = "active"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"


class FeedbackRating(str, Enum):
    UP = "up"
    DOWN = "down"


@dataclass
class EnsembleVote:
    provider: str
    decision: str
    confidence: float
    reasoning: str
    raw_response: Optional[dict[str, Any]] = None
    latency_ms: Optional[float] = None


@dataclass
class Decision:
    id: str
    domain: DecisionDomain
    type: DecisionType
    entity_id: str
    entity_type: str
    decision: str
    confidence: float
    reasoning: str
    provider: str
    alternatives: list[dict[str, Any]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: DecisionStatus = DecisionStatus.ACTIVE
    metadata: Optional[dict[str, Any]] = None
    ensemble_votes: Optional[list[EnsembleVote]] = None
    is_ensemble: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "domain": self.domain.value,
            "type": self.type.value,
            "entityId": self.entity_id,
            "entityType": self.entity_type,
            "decision": self.decision,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "provider": self.provider,
            "alternatives": self.alternatives,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status.value,
            "metadata": self.metadata,
            "isEnsemble": self.is_ensemble,
            "ensembleVotes": [
                {
                    "provider": v.provider,
                    "decision": v.decision,
                    "confidence": v.confidence,
                    "reasoning": v.reasoning,
                    "rawResponse": v.raw_response,
                    "latencyMs": v.latency_ms,
                }
                for v in self.ensemble_votes
            ]
            if self.ensemble_votes
            else None,
        }


@dataclass
class DecisionAudit:
    decision_id: str
    input_context: dict[str, Any]
    reasoning_steps: list[dict[str, Any]]
    confidence_breakdown: dict[str, Any]
    provider_used: str
    alternatives_considered: list[dict[str, Any]]
    timestamp: datetime
    ensemble_metadata: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "decisionId": self.decision_id,
            "inputContext": self.input_context,
            "reasoningSteps": self.reasoning_steps,
            "confidenceBreakdown": self.confidence_breakdown,
            "providerUsed": self.provider_used,
            "alternativesConsidered": self.alternatives_considered,
            "timestamp": self.timestamp.isoformat(),
            "ensembleMetadata": self.ensemble_metadata,
        }


@dataclass
class DecisionFeedback:
    id: str
    decision_id: str
    rating: FeedbackRating
    comment: Optional[str] = None
    actor_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "decisionId": self.decision_id,
            "rating": self.rating.value,
            "comment": self.comment,
            "actorId": self.actor_id,
            "createdAt": self.created_at.isoformat(),
        }


@dataclass
class DecisionTemplate:
    id: str
    name: str
    type: DecisionType
    config: dict[str, Any]
    tenant_id: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "config": self.config,
            "tenantId": self.tenant_id,
            "createdAt": self.created_at.isoformat(),
        }


@dataclass
class FeedbackAggregate:
    decision_type: str
    total_feedback: int
    up_count: int
    down_count: int
    approval_rate: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "decisionType": self.decision_type,
            "totalFeedback": self.total_feedback,
            "upCount": self.up_count,
            "downCount": self.down_count,
            "approvalRate": self.approval_rate,
        }
