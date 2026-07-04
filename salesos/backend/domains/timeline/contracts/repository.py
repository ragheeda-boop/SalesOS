"""TimelineRepository — append-only event store for timeline activities.

This is NOT SearchRepository. Timeline has its own contract
because it is append-only and has a different access pattern.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .models import TimelineEvent


@dataclass
class TimelineQuery:
    """Query for retrieving timeline events."""

    target_id: str = ""
    target_type: str = ""
    actor_id: str = ""
    activity_types: list[str] | None = None
    tenant_id: str = ""
    from_date: datetime | None = None
    to_date: datetime | None = None
    page: int = 1
    page_size: int = 50
    sort_order: str = "desc"  # asc | desc


@dataclass
class TimelineResult:
    events: list[TimelineEvent] = field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 50


class TimelineRepository(ABC):

    @abstractmethod
    async def append(self, event: TimelineEvent) -> None:
        """Append an event to the timeline.

        Immutable — once appended, events should never be updated or deleted.
        """

    @abstractmethod
    async def query(self, query: TimelineQuery) -> TimelineResult:
        """Query timeline events."""

    @abstractmethod
    async def get_by_target(self, target_id: str, target_type: str, page: int = 1, page_size: int = 50) -> TimelineResult:
        """Get all events for a specific target entity."""

    @abstractmethod
    async def get_by_actor(self, actor_id: str, page: int = 1, page_size: int = 50) -> TimelineResult:
        """Get all events by a specific actor."""

    @abstractmethod
    async def count(self, tenant_id: str) -> int:
        """Total number of events for a tenant."""
