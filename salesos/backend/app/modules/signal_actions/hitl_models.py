"""Human-in-the-Loop models for Seller Operating Model.

Three linked tables:
- NbaFeedback: seller decision on recommendation (accept/reject/modify)
- ActionOutcome: call/email/meeting result
- SalesFollowup: generated next action from outcome

Each preserves full decision chain with parent linkage.
"""
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import Any


class FeedbackDecision(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    MODIFIED = "modified"


class ReasonCode(str, Enum):
    WRONG_PERSON = "wrong_person"
    BAD_TIMING = "bad_timing"
    NOT_RELEVANT = "not_relevant"
    ALREADY_CONTACTED = "already_contacted"
    BUDGET_CONSTRAINT = "budget_constraint"
    OTHER = "other"


class OutcomeType(str, Enum):
    CONNECTED = "connected"
    NO_ANSWER = "no_answer"
    LEFT_VOICEMAIL = "left_voicemail"
    EMAIL_SENT = "email_sent"
    MEETING_SET = "meeting_set"
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    PROPOSAL_SENT = "proposal_sent"


class FollowupStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    EXPIRED = "expired"


@dataclass
class NbaFeedback:
    id: str = ""
    tenant_id: str = ""
    company_name: str = ""
    action_id: str = ""
    recommendation_id: str = ""
    seller_id: str = ""
    decision: str = ""  # FeedbackDecision value
    reason_code: str = ""  # ReasonCode value
    notes: str = ""
    original_action_type: str = ""
    modified_action_type: str = ""
    modified_target_contact_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "company_name": self.company_name,
            "action_id": self.action_id,
            "recommendation_id": self.recommendation_id,
            "seller_id": self.seller_id,
            "decision": self.decision,
            "reason_code": self.reason_code,
            "notes": self.notes,
            "original_action_type": self.original_action_type,
            "modified_action_type": self.modified_action_type,
            "modified_target_contact_id": self.modified_target_contact_id,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


@dataclass
class ActionOutcome:
    id: str = ""
    tenant_id: str = ""
    action_id: str = ""
    company_name: str = ""
    # Optional verified link to the commercial opportunity affected by this
    # outcome. Historical outcomes remain valid when this is absent.
    opportunity_id: str | None = None
    idempotency_key: str | None = None
    seller_id: str = ""
    outcome_type: str = ""  # OutcomeType value
    notes: str = ""
    contact_reached: str = ""
    duration_seconds: int | None = None
    followup_required: bool = False
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    # Internal control signal: omitted from the API response so a retried
    # outcome request does not generate a duplicate follow-up.
    is_replay: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "action_id": self.action_id,
            "company_name": self.company_name,
            "opportunity_id": self.opportunity_id,
            "seller_id": self.seller_id,
            "outcome_type": self.outcome_type,
            "notes": self.notes,
            "contact_reached": self.contact_reached,
            "duration_seconds": self.duration_seconds,
            "followup_required": self.followup_required,
            "occurred_at": self.occurred_at.isoformat() if self.occurred_at else None,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


@dataclass
class SalesFollowup:
    id: str = ""
    tenant_id: str = ""
    parent_action_id: str = ""
    parent_outcome_id: str = ""
    company_name: str = ""
    seller_id: str = ""
    generated_action_type: str = ""
    title: str = ""
    description: str = ""
    due_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    rationale: str = ""
    status: str = FollowupStatus.PENDING.value
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "parent_action_id": self.parent_action_id,
            "parent_outcome_id": self.parent_outcome_id,
            "company_name": self.company_name,
            "seller_id": self.seller_id,
            "generated_action_type": self.generated_action_type,
            "title": self.title,
            "description": self.description,
            "due_at": self.due_at.isoformat() if self.due_at else None,
            "rationale": self.rationale,
            "status": self.status,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
