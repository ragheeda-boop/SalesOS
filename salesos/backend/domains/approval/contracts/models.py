"""Approval domain models — human-in-the-loop approval workflow for AI recommendations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any


class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ApprovalLevel(Enum):
    SELF = "self"
    MANAGER = "manager"
    VP = "vp"
    EXECUTIVE = "executive"


class ApprovalTargetType(Enum):
    NBA_RECOMMENDATION = "nba_recommendation"
    AI_ACTION = "ai_action"
    REVENUE_ACTION = "revenue_action"
    DEAL_ACTION = "deal_action"
    PROPOSAL_ACTION = "proposal_action"


@dataclass
class ApprovalDecision:
    """A single approval decision within an approval request."""
    decision: str  # approve / reject / escalate
    decided_by: str
    decided_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    comments: str = ""
    authority_level: ApprovalLevel = ApprovalLevel.SELF


@dataclass
class ApprovalRequest:
    """A request for human approval before AI-generated actions can execute."""
    id: str
    tenant_id: str
    target_type: ApprovalTargetType
    target_id: str  # nba_result_id, action_id, etc.
    requested_by: str  # user_id or "system"
    action_summary: str  # human-readable description of what will happen
    action_evidence: list[str] = field(default_factory=list)  # evidence chain items
    required_level: ApprovalLevel = ApprovalLevel.MANAGER
    status: ApprovalStatus = ApprovalStatus.PENDING
    assigned_to: str = ""  # user_id of approver
    decisions: list[ApprovalDecision] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    priority: int = 5  # 1=highest, 10=lowest
    expires_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_terminal(self) -> bool:
        return self.status in (
            ApprovalStatus.APPROVED,
            ApprovalStatus.REJECTED,
            ApprovalStatus.CANCELLED,
            ApprovalStatus.EXPIRED,
        )

    @property
    def decision_count(self) -> int:
        return len(self.decisions)

    @property
    def latest_decision(self) -> ApprovalDecision | None:
        return self.decisions[-1] if self.decisions else None

    @property
    def is_approved(self) -> bool:
        return self.status == ApprovalStatus.APPROVED

    @property
    def is_rejected(self) -> bool:
        return self.status == ApprovalStatus.REJECTED

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "target_type": self.target_type.value,
            "target_id": self.target_id,
            "requested_by": self.requested_by,
            "action_summary": self.action_summary,
            "action_evidence": self.action_evidence,
            "required_level": self.required_level.value,
            "status": self.status.value,
            "assigned_to": self.assigned_to,
            "decisions": [
                {
                    "decision": d.decision,
                    "decided_by": d.decided_by,
                    "decided_at": d.decided_at.isoformat(),
                    "comments": d.comments,
                    "authority_level": d.authority_level.value,
                }
                for d in self.decisions
            ],
            "metadata": self.metadata,
            "priority": self.priority,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
