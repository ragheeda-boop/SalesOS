"""Decision Events — published through EventRuntime for every decision lifecycle step."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class DecisionEventType(str, Enum):
    CREATED = "decision.created"
    ACCEPTED = "decision.accepted"
    REJECTED = "decision.rejected"
    EXECUTED = "decision.executed"
    EXPIRED = "decision.expired"
    SUPERSEDED = "decision.superseded"
    FEEDBACK_RECEIVED = "decision.feedback_received"
    LEARNING_UPDATED = "decision.learning_updated"


@dataclass
class DecisionEvent:
    event_type: DecisionEventType
    decision_id: str
    company_id: str
    tenant_id: str
    decision_type: str
    previous_status: Optional[str] = None
    new_status: Optional[str] = None
    feedback: Optional[dict] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_domain_event(self) -> dict:
        return {
            "event_id": f"{self.event_type.value}_{self.decision_id}",
            "event_type": self.event_type.value,
            "event_version": 1,
            "aggregate_id": self.decision_id,
            "aggregate_type": "decision",
            "tenant_id": self.tenant_id,
            "occurred_at": self.occurred_at.isoformat(),
            "data": {
                "decision_id": self.decision_id,
                "company_id": self.company_id,
                "decision_type": self.decision_type,
                "previous_status": self.previous_status,
                "new_status": self.new_status,
                "feedback": self.feedback,
            },
            "metadata": self.metadata,
        }
