"""Commercial Memory models — durable record of commercial interactions from Product Core facts.

Unlike AI session memory (intelligence/memory/), this reads from Product Core tables
(companies, contacts, opportunities, activities, proposals, reviews, approvals, revenue)
and produces a unified timeline of: what/when/who/why/outcome/prior decisions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class MemoryEventType(str, Enum):
    COMPANY_CREATED = "company_created"
    COMPANY_UPDATED = "company_updated"
    CONTACT_CREATED = "contact_created"
    CONTACT_UPDATED = "contact_updated"
    OPPORTUNITY_CREATED = "opportunity_created"
    OPPORTUNITY_STAGE_CHANGED = "opportunity_stage_changed"
    OPPORTUNITY_WON = "opportunity_won"
    OPPORTUNITY_LOST = "opportunity_lost"
    ACTIVITY_LOGGED = "activity_logged"
    PROPOSAL_CREATED = "proposal_created"
    PROPOSAL_APPROVED = "proposal_approved"
    PROPOSAL_DELIVERED = "proposal_delivered"
    PROPOSAL_ACCEPTED = "proposal_accepted"
    PROPOSAL_REJECTED = "proposal_rejected"
    REVIEW_CREATED = "review_created"
    REVIEW_APPROVED = "review_approved"
    REVIEW_REJECTED = "review_rejected"
    QUOTE_APPROVED = "quote_approved"
    REVENUE_RECORDED = "revenue_recorded"
    DECISION_MADE = "decision_made"
    NOTE_ADDED = "note_added"


class MemoryEntity(str, Enum):
    COMPANY = "company"
    CONTACT = "contact"
    OPPORTUNITY = "opportunity"
    ACTIVITY = "activity"
    PROPOSAL = "proposal"
    REVIEW = "review"
    QUOTE = "quote"
    REVENUE = "revenue"
    DECISION = "decision"


@dataclass
class CommercialEvent:
    """A single commercial event recorded in durable memory."""
    id: str
    tenant_id: str
    entity_type: MemoryEntity
    entity_id: str
    event_type: MemoryEventType
    title: str
    description: str
    actor_id: str               # who did it
    actor_name: str             # human-readable actor name
    outcome: str = ""           # won/lost/approved/rejected/etc
    reason: str = ""            # why it happened
    context: dict[str, Any] = field(default_factory=dict)
    related_ids: list[str] = field(default_factory=list)  # cross-references
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_positive(self) -> bool:
        return self.event_type in (
            MemoryEventType.OPPORTUNITY_WON,
            MemoryEventType.PROPOSAL_APPROVED,
            MemoryEventType.PROPOSAL_ACCEPTED,
            MemoryEventType.REVIEW_APPROVED,
            MemoryEventType.QUOTE_APPROVED,
        )

    @property
    def is_negative(self) -> bool:
        return self.event_type in (
            MemoryEventType.OPPORTUNITY_LOST,
            MemoryEventType.PROPOSAL_REJECTED,
            MemoryEventType.REVIEW_REJECTED,
        )


@dataclass
class AccountTimeline:
    """Complete commercial memory timeline for an account."""
    account_id: str
    account_name: str
    events: list[CommercialEvent] = field(default_factory=list)
    total_interactions: int = 0
    first_interaction: datetime | None = None
    last_interaction: datetime | None = None
    won_deals: int = 0
    lost_deals: int = 0
    active_opportunities: int = 0
    total_revenue: float = 0.0

    @property
    def win_rate(self) -> float:
        total = self.won_deals + self.lost_deals
        return self.won_deals / total if total > 0 else 0.0

    @property
    def recent_events(self) -> list[CommercialEvent]:
        return sorted(self.events, key=lambda e: e.occurred_at, reverse=True)[:10]


@dataclass
class DealMemory:
    """Commercial memory for a specific deal/opportunity."""
    deal_id: str
    deal_name: str
    account_id: str
    events: list[CommercialEvent] = field(default_factory=list)
    current_stage: str = ""
    value: float = 0.0
    probability: float = 0.0
    owner_id: str = ""
    created_at: datetime | None = None
    last_activity: datetime | None = None

    @property
    def stage_history(self) -> list[CommercialEvent]:
        return [e for e in self.events if e.event_type == MemoryEventType.OPPORTUNITY_STAGE_CHANGED]

    @property
    def activity_count(self) -> int:
        return sum(1 for e in self.events if e.event_type == MemoryEventType.ACTIVITY_LOGGED)
