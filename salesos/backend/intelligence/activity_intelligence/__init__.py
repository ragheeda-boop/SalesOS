"""Activity Intelligence — Platform Capability (ADR-012).

Single entry point for all activity data consumed by Dashboard, Company 360,
Employee 360, Opportunity 360, and AI Copilot.
"""

from __future__ import annotations

from intelligence.activity_intelligence.contracts.models import (
    Communication,
    CommunicationChannel,
    CommunicationDirection,
    Participant,
)
from intelligence.activity_intelligence.contracts.provider import (
    CalendarProvider,
    EmailProvider,
    ProviderProfile,
)
from intelligence.activity_intelligence.mapping import MappingPipeline

__all__ = [
    "Communication",
    "CommunicationChannel",
    "CommunicationDirection",
    "Participant",
    "EmailProvider",
    "CalendarProvider",
    "ProviderProfile",
    "MappingPipeline",
]
