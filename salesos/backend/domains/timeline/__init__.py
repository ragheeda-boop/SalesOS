"""Timeline Domain — immutable activity logging.

Architecture:
  Actor → Activity → Target → Outcome

  Every state change in the platform produces an immutable TimelineEvent.
  No UPDATE, only APPEND. The timeline is the source of truth for history.

  Actor types: User, AI Agent, System, Workflow, Integration
"""

from .contracts.models import ActivityOutcome, ActivityType, Actor, ActorType, Target, TimelineEvent
from .contracts.repository import TimelineQuery, TimelineRepository
from .engine.recorder import TimelineRecorder

__all__ = [
    "ActivityOutcome",
    "ActivityType",
    "Actor",
    "ActorType",
    "Target",
    "TimelineEvent",
    "TimelineQuery",
    "TimelineRecorder",
    "TimelineRepository",
]
