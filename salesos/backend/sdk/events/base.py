"""Domain event base classes and event store interface.

All events conform to CloudEvents 1.0 specification
(https://github.com/cloudevents/spec) for maximum interoperability
with Kafka, NATS, Azure Event Grid, Google Eventarc, etc.
"""

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class DomainEvent:
    """Base class for all domain events (CloudEvents 1.0 compatible).

    Maps to CloudEvents attributes:
      specversion -> "1.0" (constant)
      id         -> event_id
      source     -> "salesos.{aggregate_type}"
      type       -> event_type
      subject    -> "{aggregate_type}/{aggregate_id}"
      time       -> occurred_at
      datacontenttype -> "application/json"
      data       -> event payload

    Extra fields beyond CloudEvents:
      event_version, tenant_id, metadata (correlation_id, etc.)
    """

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = ""
    event_version: int = 1
    aggregate_id: str = ""
    aggregate_type: str = ""
    tenant_id: str = ""
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    data: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.event_type:
            self.event_type = self._derive_event_type()

    def _derive_event_type(self) -> str:
        """Derive event type from class name, e.g. 'CompanyCreated' -> 'company.created'."""
        name = self.__class__.__name__
        parts = []
        current = ""
        for char in name:
            if char.isupper() and current:
                parts.append(current.lower())
                current = char
            else:
                current += char
        if current:
            parts.append(current.lower())
        return ".".join(parts)

    def to_dict(self) -> dict:
        """Return dict with CloudEvents 1.0 envelope."""
        return {
            "specversion": "1.0",
            "id": self.event_id,
            "source": f"salesos.{self.aggregate_type}" if self.aggregate_type else "salesos",
            "type": self.event_type,
            "subject": f"{self.aggregate_type}/{self.aggregate_id}" if self.aggregate_id else "",
            "time": self.occurred_at.isoformat(),
            "datacontenttype": "application/json",
            "data": {
                "event_version": self.event_version,
                "tenant_id": self.tenant_id,
                "payload": self.data,
                "metadata": self.metadata,
            },
        }

    def to_dict_legacy(self) -> dict:
        """Return dict in legacy format (without CloudEvents envelope)."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "event_version": self.event_version,
            "aggregate_id": self.aggregate_id,
            "aggregate_type": self.aggregate_type,
            "tenant_id": self.tenant_id,
            "occurred_at": self.occurred_at.isoformat(),
            "data": self.data,
            "metadata": self.metadata,
        }


class EventStore(ABC):
    """Event store interface for persisting and replaying domain events."""

    @abstractmethod
    async def append(self, event: DomainEvent) -> None:
        """Append an event to the store."""

    @abstractmethod
    async def read_stream(
        self, aggregate_type: str, aggregate_id: str
    ) -> list[DomainEvent]:
        """Read all events for a specific aggregate (event sourcing replay)."""

    @abstractmethod
    async def read_by_type(
        self, event_type: str, since: datetime | None = None, limit: int = 100
    ) -> list[DomainEvent]:
        """Read events filtered by type."""
