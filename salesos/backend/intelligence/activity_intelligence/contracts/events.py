"""Event types for the Event Bus — decoupled ingestion (ADR-012 §15).

Providers emit CommunicationEvent → Event Bus delivers to handlers.
MappedCommunicationEvent is emitted after Mapping Pipeline resolves entities.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from sdk.events.base import DomainEvent


@dataclass
class CommunicationReceived(DomainEvent):
    """Emitted when a raw communication is received from any provider."""

    event_type: str = "communication.received"

    # Override base fields with specific types for this event
    channel: str = ""  # "email", "meeting"
    source_provider: str = ""  # "gmail", "google_calendar"
    source_id: str = ""  # original ID in source system
    raw_data: dict = field(default_factory=dict)


@dataclass
class CommunicationMapped(DomainEvent):
    """Emitted after Mapping Pipeline resolves a communication to CRM entities."""

    event_type: str = "communication.mapped"

    channel: str = ""
    communication_id: str = ""
    company_id: str | None = None
    contact_id: str | None = None
    opportunity_id: str | None = None
    confidence: float = 0.0
    mapping_method: str = ""
    mapping_provenance: dict = field(default_factory=dict)


@dataclass
class CommunicationSynced(DomainEvent):
    """Emitted after a sync worker completes a sync cycle."""

    event_type: str = "communication.synced"

    provider: str = ""
    channel: str = ""
    synced_count: int = 0
    new_count: int = 0
    updated_count: int = 0
    errors: list[str] = field(default_factory=list)


@dataclass
class CommunicationDeduplicated(DomainEvent):
    """Emitted after deduplication runs on a batch."""

    event_type: str = "communication.deduplicated"

    total_processed: int = 0
    duplicates_found: int = 0
    channel: str = ""
