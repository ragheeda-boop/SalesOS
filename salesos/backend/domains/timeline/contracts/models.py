"""Timeline domain models — immutable event contracts.

Actor → Activity → Target → Outcome

Every event is append-only. Once committed, it never changes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any


class ActorType(Enum):
    USER = "user"
    AI_AGENT = "ai_agent"
    SYSTEM = "system"
    WORKFLOW = "workflow"
    INTEGRATION = "integration"


class ActivityType(Enum):
    # Identity
    USER_REGISTERED = "user.registered"
    USER_LOGGED_IN = "user.logged_in"
    USER_ROLE_CHANGED = "user.role_changed"
    TENANT_CREATED = "tenant.created"

    # Company
    COMPANY_CREATED = "company.created"
    COMPANY_UPDATED = "company.updated"
    COMPANY_INGESTED = "company.ingested"
    COMPANY_MERGED = "company.merged"
    BRANCH_CREATED = "branch.created"
    LICENSE_CREATED = "license.created"
    CONTACT_CREATED = "contact.created"

    # Timeline (meta)
    ACTIVITY_LOGGED = "activity.logged"


class ActivityOutcome(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"
    SKIPPED = "skipped"


@dataclass
class Actor:
    """Who performed the activity."""

    id: str
    type: ActorType
    name: str = ""

    @staticmethod
    def user(user_id: str, name: str = "") -> Actor:
        return Actor(id=user_id, type=ActorType.USER, name=name)

    @staticmethod
    def system(name: str = "system") -> Actor:
        return Actor(id="system", type=ActorType.SYSTEM, name=name)

    @staticmethod
    def ai_agent(agent_id: str, name: str = "") -> Actor:
        return Actor(id=agent_id, type=ActorType.AI_AGENT, name=name)

    @staticmethod
    def workflow(workflow_id: str, name: str = "") -> Actor:
        return Actor(id=workflow_id, type=ActorType.WORKFLOW, name=name)

    @staticmethod
    def integration(integration_id: str, name: str = "") -> Actor:
        return Actor(id=integration_id, type=ActorType.INTEGRATION, name=name)


@dataclass
class Target:
    """What the activity was performed on."""

    id: str
    type: str  # entity type: "company", "user", "tenant", etc.
    label: str = ""


@dataclass
class TimelineEvent:
    """An immutable record of something that happened.

    Fields:
      event_id: unique identifier
      actor: who did it
      activity: what was done
      target: what it was done to
      outcome: result
      metadata: additional context (changes, reason, IP, etc.)
      timestamp: when it happened
      tenant_id: tenant scope
    """

    event_id: str
    actor: Actor
    activity: ActivityType
    target: Target
    outcome: ActivityOutcome = ActivityOutcome.SUCCESS
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tenant_id: str = ""
