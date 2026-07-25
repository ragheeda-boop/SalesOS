"""Provider Interface — EmailProvider and CalendarProvider ABCs (ADR-012 §7).

Activity Intelligence does NOT couple directly to Gmail or Google Calendar.
All external communication goes through these abstract provider interfaces.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

from intelligence.activity_intelligence.contracts.models import (
    RawCalendarEvent,
    RawEmail,
)


@dataclass
class ProviderProfile:
    provider_id: str = ""
    provider_type: str = ""  # "email" | "calendar"
    email: str = ""
    display_name: str = ""
    connected: bool = False
    last_sync: datetime | None = None
    metadata: dict = field(default_factory=dict)


class EmailProvider(ABC):
    """Abstract interface for all email providers.

    Implementations: GoogleGmailProvider, OutlookEmailProvider, IMAPEmailProvider.
    Sync workers operate against this interface, not against any specific implementation.
    """

    @abstractmethod
    async def authenticate(self, credentials: dict) -> bool:
        """Authenticate with the provider. Returns True on success."""

    @abstractmethod
    async def fetch_emails(
        self, since: datetime | None = None, max_results: int = 50
    ) -> list[RawEmail]:
        """Fetch emails since a timestamp. Returns raw email objects."""

    @abstractmethod
    async def fetch_thread(self, thread_id: str) -> list[RawEmail]:
        """Fetch all emails in a thread."""

    @abstractmethod
    async def send_email(self, to: str, subject: str, body: str) -> str:
        """Send an email. Returns the message ID."""

    @abstractmethod
    async def get_profile(self) -> ProviderProfile:
        """Return provider profile information."""


class CalendarProvider(ABC):
    """Abstract interface for all calendar providers.

    Implementations: GoogleCalendarProvider, OutlookCalendarProvider.
    """

    @abstractmethod
    async def authenticate(self, credentials: dict) -> bool:
        """Authenticate with the provider. Returns True on success."""

    @abstractmethod
    async def fetch_events(
        self, since: datetime, until: datetime
    ) -> list[RawCalendarEvent]:
        """Fetch calendar events in a time range."""

    @abstractmethod
    async def create_event(self, event: dict) -> str:
        """Create a calendar event. Returns the event ID."""

    @abstractmethod
    async def update_event(self, event_id: str, updates: dict) -> bool:
        """Update an existing calendar event. Returns True on success."""

    @abstractmethod
    async def get_profile(self) -> ProviderProfile:
        """Return provider profile information."""
