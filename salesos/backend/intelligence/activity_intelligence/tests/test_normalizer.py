"""Tests for the Mapping Pipeline — Normalizer stage (ADR-012 §6)."""

import pytest
from intelligence.activity_intelligence.contracts.models import (
    RawEmail,
    NormalizedAddress,
    NormalizedSubject,
    NormalizedDomain,
)
from intelligence.activity_intelligence.mapping.normalizer import Normalizer


class TestNormalizer:
    def setup_method(self):
        self.normalizer = Normalizer()

    def test_normalize_address_simple(self):
        result = self.normalizer._normalize_address("john@test.com")
        assert result.email == "john@test.com"
        assert result.domain == "test.com"

    def test_normalize_address_with_display_name(self):
        result = self.normalizer._normalize_address("John Doe <john@test.com>")
        assert result.display_name == "John Doe"
        assert result.email == "john@test.com"
        assert result.domain == "test.com"

    def test_normalize_address_lowercase(self):
        result = self.normalizer._normalize_address("John@TEST.com")
        assert result.email == "john@test.com"

    def test_normalize_subject_plain(self):
        result = Normalizer._normalize_subject("Hello World")
        assert result.cleaned == "Hello World"
        assert not result.has_re
        assert not result.has_fwd

    def test_normalize_subject_re_prefix(self):
        result = Normalizer._normalize_subject("Re: Hello World")
        assert result.cleaned == "Hello World"
        assert result.has_re

    def test_normalize_subject_fwd_prefix(self):
        result = Normalizer._normalize_subject("Fwd: Important")
        assert result.cleaned == "Important"
        assert result.has_fwd
        assert not result.has_re

    def test_normalize_subject_arabic_re(self):
        result = Normalizer._normalize_subject("رد: مرحبا")
        assert result.cleaned == "مرحبا"
        assert result.has_re

    def test_normalize_subject_multiple_re(self):
        result = Normalizer._normalize_subject("Re: Re: Re: Final version")
        assert result.cleaned == "Final version"
        assert result.has_re

    def test_normalize_domain_free_provider(self):
        result = self.normalizer.normalize_domain("gmail.com")
        assert result.normalized == "gmail.com"
        assert result.is_free_provider

    def test_normalize_domain_corporate(self):
        result = self.normalizer.normalize_domain("sales.acme.com")
        assert result.is_free_provider is False

    def test_normalize_email_full(self):
        raw = RawEmail(
            message_id="msg-1",
            subject="Re: Meeting tomorrow",
            from_address="John Doe <john@acme.com>",
            to_addresses=["partner@client.com"],
        )
        from_addr, reply_to, subject = self.normalizer.normalize_email(raw)
        assert from_addr.display_name == "John Doe"
        assert from_addr.email == "john@acme.com"
        assert from_addr.domain == "acme.com"
        assert subject.cleaned == "Meeting tomorrow"
        assert subject.has_re
        assert reply_to is None

    def test_normalize_email_with_reply_to(self):
        raw = RawEmail(
            message_id="msg-1",
            subject="Hello",
            from_address="sender@test.com",
            headers={"Reply-To": "reply@test.com"},
        )
        from_addr, reply_to, subject = self.normalizer.normalize_email(raw)
        assert reply_to is not None
        assert reply_to.email == "reply@test.com"

    def test_extract_hints_opportunity(self):
        raw = RawEmail(
            message_id="msg-1",
            subject="[OPP-123] Proposal discussion",
            from_address="john@acme.com",
        )
        hints = self.normalizer.extract_hints(raw)
        assert hints.opportunity_hint == "OPP-123"
        assert hints.person_email == "john@acme.com"
        assert hints.domain == "acme.com"

    def test_normalize_calendar_attendees(self):
        from intelligence.activity_intelligence.contracts.models import RawCalendarEvent
        event = RawCalendarEvent(
            event_id="ev-1",
            attendees=[
                {"email": "john@test.com", "name": "John"},
                {"email": "jane@test.com", "name": "Jane"},
            ],
        )
        addresses = self.normalizer.normalize_calendar(event)
        assert len(addresses) == 2
        assert addresses[0].email == "john@test.com"
        assert addresses[1].email == "jane@test.com"
