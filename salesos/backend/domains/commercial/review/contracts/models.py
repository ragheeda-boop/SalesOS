"""Review domain models — manager/deal/exception review workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ReviewType(Enum):
    DEAL_REVIEW = "deal_review"
    MANAGER_REVIEW = "manager_review"
    EXCEPTION_REVIEW = "exception_review"
    QUOTE_REVIEW = "quote_review"
    PROPOSAL_REVIEW = "proposal_review"


class ReviewStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    CANCELLED = "cancelled"


@dataclass
class ReviewDecision:
    """A single decision within a review."""
    decision: str  # approve / reject / escalate
    decided_by: str
    decided_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    comments: str = ""


@dataclass
class Review:
    """A review instance — tracks approval workflow for commercial objects."""
    id: str
    tenant_id: str
    review_type: ReviewType
    target_id: str  # opportunity_id, quote_id, or proposal_id
    target_type: str  # "opportunity", "quote", "proposal"
    status: ReviewStatus = ReviewStatus.PENDING
    assigned_to: str = ""  # user_id of reviewer
    requested_by: str = ""  # user_id who requested review
    decisions: list[ReviewDecision] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_terminal(self) -> bool:
        return self.status in (ReviewStatus.APPROVED, ReviewStatus.REJECTED, ReviewStatus.CANCELLED)

    @property
    def decision_count(self) -> int:
        return len(self.decisions)

    @property
    def latest_decision(self) -> ReviewDecision | None:
        return self.decisions[-1] if self.decisions else None
