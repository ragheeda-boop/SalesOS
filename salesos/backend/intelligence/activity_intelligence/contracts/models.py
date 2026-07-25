"""Shared value objects for Activity Intelligence (ADR-012).

Unified Communication Model (§13) — all channels under a single hierarchy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class CommunicationChannel(Enum):
    EMAIL = "email"
    MEETING = "meeting"
    CALL = "call"
    WHATSAPP = "whatsapp"
    SLACK = "slack"
    TEAMS = "teams"
    SMS = "sms"
    LINKEDIN = "linkedin"
    ZOOM = "zoom"


class CommunicationDirection(Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    INTERNAL = "internal"


@dataclass
class Participant:
    name: str = ""
    email: str = ""
    contact_id: str | None = None
    role: str = ""  # "from", "to", "cc", "bcc", "organizer", "attendee"


@dataclass
class Communication:
    """Unified communication base type — all channels implement this interface.

    Each channel stores its channel-specific data in `channel_metadata`.
    The Activity Intelligence engines treat all channels uniformly via this type.
    """

    id: str
    tenant_id: str
    channel: CommunicationChannel
    direction: CommunicationDirection
    participants: list[Participant] = field(default_factory=list)
    subject: str | None = None
    body: str | None = None
    channel_metadata: dict[str, Any] = field(default_factory=dict)
    company_id: str | None = None  # resolved via Mapping Pipeline
    contact_id: str | None = None
    opportunity_id: str | None = None
    source_provider: str = ""  # "gmail", "google_calendar", "outlook", "slack"
    source_id: str = ""  # original ID in the source system
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class RawEmail:
    """Raw email data before normalization and mapping."""

    message_id: str
    thread_id: str | None = None
    subject: str = ""
    from_address: str = ""
    to_addresses: list[str] = field(default_factory=list)
    cc_addresses: list[str] = field(default_factory=list)
    bcc_addresses: list[str] = field(default_factory=list)
    body_text: str = ""
    body_html: str = ""
    attachments: list[dict[str, Any]] = field(default_factory=list)
    in_reply_to: str | None = None
    references: str | None = None
    sent_at: datetime | None = None
    received_at: datetime | None = None
    labels: list[str] = field(default_factory=list)
    headers: dict[str, str] = field(default_factory=dict)


@dataclass
class RawCalendarEvent:
    """Raw calendar event data before normalization and mapping."""

    event_id: str
    calendar_id: str = ""
    title: str = ""
    description: str = ""
    location: str = ""
    start_time: datetime | None = None
    end_time: datetime | None = None
    attendees: list[dict[str, str]] = field(default_factory=list)
    organizer: dict[str, str] = field(default_factory=dict)
    is_recurring: bool = False
    recurrence_rule: str | None = None
    status: str = "confirmed"  # confirmed | tentative | cancelled
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class NormalizedAddress:
    """Normalized email address after cleaning."""

    raw: str
    display_name: str = ""
    email: str = ""
    domain: str = ""


@dataclass
class NormalizedSubject:
    """Normalized email subject after cleaning."""

    raw: str
    cleaned: str = ""
    has_re: bool = False
    has_fwd: bool = False
    prefix: str = ""


@dataclass
class NormalizedDomain:
    """Normalized domain extracted from email addresses."""

    raw: str
    normalized: str = ""
    is_free_provider: bool = False  # gmail.com, yahoo.com, etc.


@dataclass
class ResolvedEntities:
    """Entities extracted from normalized communication data."""

    person_name: str | None = None
    person_email: str | None = None
    company_hint: str | None = None  # extracted from domain or signature
    domain: str | None = None
    opportunity_hint: str | None = None  # e.g., "[OPP-123]" in subject


@dataclass
class CandidateMatch:
    """A potential CRM match with confidence score."""

    entity_id: str
    entity_type: str  # "company", "contact", "opportunity"
    method: str  # "explicit_ref", "opportunity_lookup", "contact_lookup", "domain_match", "ai_match"
    confidence: float = 0.0
    reason: str = ""


@dataclass
class ScoredCandidate:
    """A matched candidate after confidence scoring."""

    candidate: CandidateMatch
    score: float
    reason: str
    threshold: float = 0.5


@dataclass
class MappingResult:
    """Final result of the Mapping Pipeline for one communication."""

    source_id: str
    mapped: bool = False
    entity_type: str | None = None
    entity_id: str | None = None
    company_id: str | None = None
    contact_id: str | None = None
    opportunity_id: str | None = None
    confidence: float = 0.0
    method: str = ""
    reason: str = ""

    @staticmethod
    def unresolved(source_id: str, reason: str = "") -> "MappingResult":
        return MappingResult(source_id=source_id, reason=reason)


@dataclass
class EngagementScore:
    """Per-company engagement metrics."""

    company_id: str
    email_count_sent: int = 0
    email_count_received: int = 0
    reply_rate: float = 0.0
    meeting_count: int = 0
    meeting_hours: float = 0.0
    meeting_completion_rate: float = 0.0
    last_email_days: int | None = None
    last_meeting_days: int | None = None
    last_activity_days: int | None = None
    communication_velocity: float = 0.0
    response_time_avg_hours: float | None = None
    followup_delay_days: int | None = None
    relationship_health: float = 0.0


@dataclass
class FollowUpStatus:
    """Follow-up status for a company."""

    company_id: str
    assigned: bool = False
    need_followup: bool = False
    waiting_customer: bool = False
    waiting_you: bool = False
    overdue: bool = False
    last_outbound_days: int | None = None
    priority: str = "low"  # low | medium | high | critical


@dataclass
class ActivityDashboardDTO:
    """Dashboard-level activity summary DTO."""

    email_count: int = 0
    meeting_count: int = 0
    followup_count: int = 0
    overdue_count: int = 0
    top_companies: list[dict[str, Any]] = field(default_factory=list)
    engagement_trend: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class CompanyEngagementDTO:
    """Company-level engagement DTO."""

    company_id: str
    email_count: int = 0
    meeting_count: int = 0
    last_activity: str | None = None
    last_email: str | None = None
    last_meeting: str | None = None
    followup_status: str = ""
    score: EngagementScore | None = None
