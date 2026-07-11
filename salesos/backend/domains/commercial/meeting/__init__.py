"""Meeting domain model — pre/during/post meeting intelligence."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class Meeting:
    id: str
    tenant_id: str
    opportunity_id: str
    title: str
    date: datetime
    duration_minutes: int = 60
    attendees: list[str] = field(default_factory=list)
    agenda: str = ""
    notes: str = ""
    action_items: list[str] = field(default_factory=list)
    status: str = "scheduled"  # scheduled | completed | cancelled
    intelligence: dict[str, Any] = field(default_factory=dict)
    recording_url: str | None = None
    created_by: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class MeetingIntelligence:
    meeting_id: str
    company_brief: str = ""
    talking_points: list[str] = field(default_factory=list)
    questions_to_ask: list[str] = field(default_factory=list)
    recent_signals: list[str] = field(default_factory=list)
    ai_summary: str = ""
    sentiment: str = ""  # positive | neutral | negative
    key_topics: list[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
