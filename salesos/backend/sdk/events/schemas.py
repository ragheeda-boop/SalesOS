"""Event schema definitions for SalesOS domain events.

Every event is a dataclass inheriting from DomainEvent with a typed
event_type string and optional domain-specific helper methods.
"""

from __future__ import annotations

from dataclasses import dataclass

from sdk.events.base import DomainEvent


# ── Opportunity / Pipeline ─────────────────────────────────────────────────


@dataclass
class OpportunityCreated(DomainEvent):
    event_type: str = "opportunity.created"


@dataclass
class OpportunityUpdated(DomainEvent):
    event_type: str = "opportunity.updated"


@dataclass
class OpportunityDeleted(DomainEvent):
    event_type: str = "opportunity.deleted"


@dataclass
class OpportunityStageChanged(DomainEvent):
    event_type: str = "opportunity.stage_changed"


@dataclass
class PipelineStageChanged(DomainEvent):
    event_type: str = "pipeline.stage_changed"


# ── NBA (Next Best Action) ─────────────────────────────────────────────────


@dataclass
class NBAGenerated(DomainEvent):
    event_type: str = "nba.generated"


@dataclass
class NBAActionTaken(DomainEvent):
    event_type: str = "nba.action_taken"


# ── Meeting Intelligence ────────────────────────────────────────────────────


@dataclass
class MeetingBriefGenerated(DomainEvent):
    event_type: str = "meeting.brief_generated"


@dataclass
class MeetingCompleted(DomainEvent):
    event_type: str = "meeting.completed"


# ── Email Intelligence ──────────────────────────────────────────────────────


@dataclass
class EmailAnalyzed(DomainEvent):
    event_type: str = "email.analyzed"
