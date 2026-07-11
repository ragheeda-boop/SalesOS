"""Domain Events Library — all typed domain events in the system.

Every module publishes typed events through the SDK EventBus.
Consumers subscribe by event_type string.

To add a new event: create a dataclass inheriting from DomainEvent
and set `event_type: str = "<module>.<action>"`.
"""

from __future__ import annotations

from dataclasses import dataclass

from sdk.events.base import DomainEvent
from sdk.events.schemas import (
    EmailAnalyzed,
    MeetingBriefGenerated,
    MeetingCompleted,
    NBAActionTaken,
    NBAGenerated,
    OpportunityDeleted,
    OpportunityUpdated,
    PipelineStageChanged,
)


# ── Identity & Tenant ─────────────────────────────────────────────────────

@dataclass
class TenantCreated(DomainEvent):
    event_type: str = "tenant.created"

@dataclass
class TenantUpdated(DomainEvent):
    event_type: str = "tenant.updated"

@dataclass
class TenantSuspended(DomainEvent):
    event_type: str = "tenant.suspended"

@dataclass
class TenantReactivated(DomainEvent):
    event_type: str = "tenant.reactivated"

@dataclass
class UserRegistered(DomainEvent):
    event_type: str = "user.registered"

@dataclass
class UserInvited(DomainEvent):
    event_type: str = "user.invited"

@dataclass
class UserActivated(DomainEvent):
    event_type: str = "user.activated"

@dataclass
class UserDeactivated(DomainEvent):
    event_type: str = "user.deactivated"

@dataclass
class UserRoleChanged(DomainEvent):
    event_type: str = "user.role_changed"

@dataclass
class UserLoggedIn(DomainEvent):
    event_type: str = "user.logged_in"

@dataclass
class UserPasswordChanged(DomainEvent):
    event_type: str = "user.password_changed"


# ── Company ────────────────────────────────────────────────────────────────

@dataclass
class CompanyCreated(DomainEvent):
    event_type: str = "company.created"

@dataclass
class CompanyUpdated(DomainEvent):
    event_type: str = "company.updated"

@dataclass
class CompanyMerged(DomainEvent):
    event_type: str = "company.merged"

@dataclass
class CompanyEnriched(DomainEvent):
    event_type: str = "company.enriched"

@dataclass
class CompanyDeleted(DomainEvent):
    event_type: str = "company.deleted"

@dataclass
class CompanyIngested(DomainEvent):
    event_type: str = "company.ingested"

@dataclass
class BranchCreated(DomainEvent):
    event_type: str = "branch.created"

@dataclass
class LicenseCreated(DomainEvent):
    event_type: str = "license.created"

@dataclass
class LicenseUpdated(DomainEvent):
    event_type: str = "license.updated"

@dataclass
class ContactCreated(DomainEvent):
    event_type: str = "contact.created"

@dataclass
class ContactUpdated(DomainEvent):
    event_type: str = "contact.updated"


# ── Entity Resolution ──────────────────────────────────────────────────────

@dataclass
class EntityResolutionCompleted(DomainEvent):
    event_type: str = "entity_resolution.completed"

@dataclass
class EntityResolutionMatchFound(DomainEvent):
    event_type: str = "entity_resolution.match_found"

@dataclass
class GoldenRecordCreated(DomainEvent):
    event_type: str = "golden_record.created"

@dataclass
class GoldenRecordUpdated(DomainEvent):
    event_type: str = "golden_record.updated"


# ── Timeline & Activity ────────────────────────────────────────────────────

@dataclass
class ActivityLogged(DomainEvent):
    event_type: str = "activity.logged"

@dataclass
class TimelineUpdated(DomainEvent):
    event_type: str = "timeline.updated"


# ── Opportunity / Pipeline ─────────────────────────────────────────────────

@dataclass
class OpportunityCreated(DomainEvent):
    event_type: str = "opportunity.created"

@dataclass
class OpportunityStageChanged(DomainEvent):
    event_type: str = "opportunity.stage_changed"

@dataclass
class OpportunityWon(DomainEvent):
    event_type: str = "opportunity.won"

@dataclass
class OpportunityLost(DomainEvent):
    event_type: str = "opportunity.lost"


# ── Scoring & AI ───────────────────────────────────────────────────────────

@dataclass
class CompanyScored(DomainEvent):
    event_type: str = "company.scored"

@dataclass
class LeadScored(DomainEvent):
    event_type: str = "lead.scored"

@dataclass
class RecommendationGenerated(DomainEvent):
    event_type: str = "recommendation.generated"

@dataclass
class EmbeddingGenerated(DomainEvent):
    event_type: str = "embedding.generated"


# ── Integration & Import ───────────────────────────────────────────────────

@dataclass
class IntegrationConnected(DomainEvent):
    event_type: str = "integration.connected"

@dataclass
class IntegrationDisconnected(DomainEvent):
    event_type: str = "integration.disconnected"

@dataclass
class DataImportCompleted(DomainEvent):
    event_type: str = "data_import.completed"

@dataclass
class DataExportCompleted(DomainEvent):
    event_type: str = "data_export.completed"


# ── Billing & Usage ────────────────────────────────────────────────────────

@dataclass
class SubscriptionCreated(DomainEvent):
    event_type: str = "subscription.created"

@dataclass
class SubscriptionChanged(DomainEvent):
    event_type: str = "subscription.changed"

@dataclass
class UsageRecorded(DomainEvent):
    event_type: str = "usage.recorded"


# ── Workflow & Automation ──────────────────────────────────────────────────

@dataclass
class WorkflowTriggered(DomainEvent):
    event_type: str = "workflow.triggered"

@dataclass
class WorkflowCompleted(DomainEvent):
    event_type: str = "workflow.completed"

@dataclass
class WorkflowFailed(DomainEvent):
    event_type: str = "workflow.failed"


# ── AI Agent ───────────────────────────────────────────────────────────────

@dataclass
class AgentTaskCreated(DomainEvent):
    event_type: str = "agent.task_created"

@dataclass
class AgentTaskCompleted(DomainEvent):
    event_type: str = "agent.task_completed"

@dataclass
class AgentTaskFailed(DomainEvent):
    event_type: str = "agent.task_failed"

@dataclass
class AgentMemoryUpdated(DomainEvent):
    event_type: str = "agent.memory_updated"


# ── Registry ───────────────────────────────────────────────────────────────

EVENT_REGISTRY: dict[str, type[DomainEvent]] = {
    cls.event_type: cls
    for cls in [
        TenantCreated, TenantUpdated, TenantSuspended, TenantReactivated,
        UserRegistered, UserInvited, UserActivated, UserDeactivated,
        UserRoleChanged, UserLoggedIn, UserPasswordChanged,
        CompanyCreated, CompanyUpdated, CompanyMerged, CompanyEnriched,
        CompanyDeleted, CompanyIngested,
        BranchCreated, LicenseCreated, LicenseUpdated,
        ContactCreated, ContactUpdated,
        EntityResolutionCompleted, EntityResolutionMatchFound,
        GoldenRecordCreated, GoldenRecordUpdated,
        ActivityLogged, TimelineUpdated,
        OpportunityCreated, OpportunityStageChanged, OpportunityWon, OpportunityLost,
        OpportunityUpdated, OpportunityDeleted,
        PipelineStageChanged,
        NBAGenerated, NBAActionTaken,
        MeetingBriefGenerated, MeetingCompleted,
        EmailAnalyzed,
        CompanyScored, LeadScored, RecommendationGenerated, EmbeddingGenerated,
        IntegrationConnected, IntegrationDisconnected,
        DataImportCompleted, DataExportCompleted,
        SubscriptionCreated, SubscriptionChanged, UsageRecorded,
        WorkflowTriggered, WorkflowCompleted, WorkflowFailed,
        AgentTaskCreated, AgentTaskCompleted, AgentTaskFailed, AgentMemoryUpdated,
    ]
}
