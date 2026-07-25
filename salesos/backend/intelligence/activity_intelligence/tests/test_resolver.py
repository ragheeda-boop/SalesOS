"""Tests for Mapping Pipeline — Resolver stage (ADR-012 §6)."""

import pytest
from intelligence.activity_intelligence.contracts.models import (
    RawEmail,
    NormalizedAddress,
)
from intelligence.activity_intelligence.mapping.resolver import EntityResolver


class TestEntityResolver:
    def setup_method(self):
        self.resolver = EntityResolver()

    def test_extract_person_name_from_display(self):
        addr = NormalizedAddress(
            raw="John Smith <john@test.com>",
            display_name="John Smith",
            email="john@test.com",
            domain="test.com",
        )
        raw = RawEmail(
            message_id="msg-1",
            subject="Hello",
            from_address="John Smith <john@test.com>",
        )
        entities = self.resolver.resolve_from_email(raw, addr)
        assert entities.person_name == "John Smith"

    def test_extract_person_name_from_email_local_part(self):
        addr = NormalizedAddress(
            raw="john.smith@test.com",
            email="john.smith@test.com",
            domain="test.com",
        )
        raw = RawEmail(
            message_id="msg-1",
            subject="Hello",
            from_address="john.smith@test.com",
        )
        entities = self.resolver.resolve_from_email(raw, addr)
        assert entities.person_name == "John Smith"

    def test_extract_opportunity_hint(self):
        hint = EntityResolver._extract_opportunity_hint("[OPP-456] Review")
        assert hint == "OPP-456"

    def test_extract_opportunity_hint_variants(self):
        assert EntityResolver._extract_opportunity_hint("[OPP_789]") == "OPP-789"
        assert EntityResolver._extract_opportunity_hint("OPP-123: Q1 plan") == "OPP-123"
        assert EntityResolver._extract_opportunity_hint("No opportunity here") is None

    def test_resolve_from_email_with_opportunity(self):
        addr = NormalizedAddress(
            raw="john@acme.com",
            email="john@acme.com",
            domain="acme.com",
        )
        raw = RawEmail(
            message_id="msg-1",
            subject="[OPP-123] Q1 Review",
            from_address="john@acme.com",
        )
        entities = self.resolver.resolve_from_email(raw, addr)
        assert entities.opportunity_hint == "OPP-123"
        assert entities.domain == "acme.com"
        assert entities.company_hint == "acme.com"

    def test_resolve_company_hint_free_provider(self):
        addr = NormalizedAddress(
            raw="john@gmail.com",
            email="john@gmail.com",
            domain="gmail.com",
        )
        raw = RawEmail(
            message_id="msg-1",
            subject="Hello",
            from_address="john@gmail.com",
            body_text="Hello\n\nBest,\nJohn\nAcme Corp",
        )
        entities = self.resolver.resolve_from_email(raw, addr)
        # Should extract from signature since gmail is free provider
        assert entities.company_hint == "Acme Corp"

    def test_resolve_domain(self):
        entities = self.resolver.resolve_domain("acme.com")
        assert entities.domain == "acme.com"
        assert entities.company_hint == "acme.com"
