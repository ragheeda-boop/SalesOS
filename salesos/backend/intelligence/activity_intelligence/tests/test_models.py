"""Tests for Communication Model (ADR-012 §13)."""

import pytest
from datetime import datetime, timezone

from intelligence.activity_intelligence.contracts.models import (
    Communication,
    CommunicationChannel,
    CommunicationDirection,
    Participant,
    RawEmail,
    RawCalendarEvent,
    NormalizedAddress,
    NormalizedSubject,
    NormalizedDomain,
    ResolvedEntities,
    CandidateMatch,
    ScoredCandidate,
    MappingResult,
    EngagementScore,
    FollowUpStatus,
)


class TestCommunicationModel:
    """Verify the unified Communication base type works for all channels."""

    def test_communication_creation(self):
        comm = Communication(
            id="comm-1",
            tenant_id="t1",
            channel=CommunicationChannel.EMAIL,
            direction=CommunicationDirection.OUTBOUND,
            subject="Hello",
            source_provider="gmail",
            source_id="msg-1",
        )
        assert comm.id == "comm-1"
        assert comm.channel == CommunicationChannel.EMAIL
        assert comm.direction == CommunicationDirection.OUTBOUND

    def test_communication_channel_enum_all_values(self):
        channels = [c.value for c in CommunicationChannel]
        assert "email" in channels
        assert "meeting" in channels
        assert "call" in channels
        assert "whatsapp" in channels
        assert "slack" in channels
        assert "teams" in channels
        assert "sms" in channels
        assert "linkedin" in channels
        assert "zoom" in channels

    def test_communication_direction_enum(self):
        assert CommunicationDirection.INBOUND.value == "inbound"
        assert CommunicationDirection.OUTBOUND.value == "outbound"
        assert CommunicationDirection.INTERNAL.value == "internal"

    def test_participant_defaults(self):
        p = Participant()
        assert p.name == ""
        assert p.email == ""
        assert p.contact_id is None
        assert p.role == ""

    def test_participant_with_data(self):
        p = Participant(name="John", email="john@test.com", role="from")
        assert p.name == "John"
        assert p.email == "john@test.com"
        assert p.role == "from"


class TestRawEmail:
    def test_raw_email_defaults(self):
        raw = RawEmail(message_id="msg-1")
        assert raw.message_id == "msg-1"
        assert raw.subject == ""
        assert raw.from_address == ""
        assert raw.to_addresses == []
        assert raw.thread_id is None

    def test_raw_email_full(self):
        raw = RawEmail(
            message_id="msg-1",
            thread_id="thread-1",
            subject="Test",
            from_address="sender@test.com",
            to_addresses=["recv@test.com"],
            body_text="Hello world",
            labels=["INBOX", "UNREAD"],
        )
        assert raw.thread_id == "thread-1"
        assert "recv@test.com" in raw.to_addresses
        assert "INBOX" in raw.labels


class TestRawCalendarEvent:
    def test_raw_calendar_event_defaults(self):
        ev = RawCalendarEvent(event_id="ev-1")
        assert ev.event_id == "ev-1"
        assert ev.title == ""
        assert ev.status == "confirmed"
        assert not ev.is_recurring

    def test_recurring_event(self):
        ev = RawCalendarEvent(
            event_id="ev-1",
            is_recurring=True,
            recurrence_rule="RRULE:FREQ=WEEKLY",
        )
        assert ev.is_recurring
        assert ev.recurrence_rule == "RRULE:FREQ=WEEKLY"


class TestNormalizedAddress:
    def test_normalized_address(self):
        addr = NormalizedAddress(
            raw="John <john@test.com>",
            display_name="John",
            email="john@test.com",
            domain="test.com",
        )
        assert addr.display_name == "John"
        assert addr.email == "john@test.com"
        assert addr.domain == "test.com"


class TestMappingResult:
    def test_mapped_result(self):
        result = MappingResult(
            source_id="msg-1",
            mapped=True,
            entity_type="company",
            entity_id="comp-1",
            company_id="comp-1",
            confidence=0.85,
            method="domain_match",
        )
        assert result.mapped
        assert result.company_id == "comp-1"
        assert result.confidence == 0.85

    def test_unresolved(self):
        result = MappingResult.unresolved("msg-1", "no match")
        assert not result.mapped
        assert result.reason == "no match"
        assert result.company_id is None


class TestEngagementScore:
    def test_engagement_score_defaults(self):
        score = EngagementScore(company_id="comp-1")
        assert score.company_id == "comp-1"
        assert score.email_count_sent == 0
        assert score.reply_rate == 0.0
        assert score.relationship_health == 0.0


class TestFollowUpStatus:
    def test_followup_defaults(self):
        status = FollowUpStatus(company_id="comp-1")
        assert not status.assigned
        assert not status.need_followup
        assert not status.overdue
        assert status.priority == "low"

    def test_followup_overdue(self):
        status = FollowUpStatus(
            company_id="comp-1",
            overdue=True,
            last_outbound_days=30,
            priority="critical",
        )
        assert status.overdue
        assert status.last_outbound_days == 30
        assert status.priority == "critical"
