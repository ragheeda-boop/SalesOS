"""Tests for Provider interface and implementations (ADR-012 §7)."""

import pytest
from intelligence.activity_intelligence.contracts.provider import (
    EmailProvider,
    CalendarProvider,
    ProviderProfile,
)
from intelligence.activity_intelligence.providers.google.gmail_provider import GoogleGmailProvider
from intelligence.activity_intelligence.providers.google.calendar_provider import GoogleCalendarProvider


class TestProviderProfile:
    def test_provider_profile_defaults(self):
        profile = ProviderProfile()
        assert profile.provider_id == ""
        assert not profile.connected
        assert profile.last_sync is None

    def test_provider_profile_connected(self):
        profile = ProviderProfile(
            provider_id="gmail",
            provider_type="email",
            email="test@gmail.com",
            display_name="Test User",
            connected=True,
        )
        assert profile.provider_type == "email"
        assert profile.connected


class TestGoogleGmailProvider:
    def test_provider_creation(self):
        provider = GoogleGmailProvider()
        assert provider is not None
        assert isinstance(provider, EmailProvider)

    def test_profile_before_auth(self):
        provider = GoogleGmailProvider()
        profile = provider.get_profile()
        import asyncio
        profile = asyncio.new_event_loop().run_until_complete(profile)
        assert not profile.connected

    def test_authenticate_success(self):
        provider = GoogleGmailProvider()
        import asyncio
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(
            provider.authenticate({"email": "test@gmail.com"})
        )
        assert result is True

    def test_fetch_emails_empty_when_not_auth(self):
        provider = GoogleGmailProvider()
        import asyncio
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(provider.fetch_emails())
        assert result == []


class TestGoogleCalendarProvider:
    def test_provider_creation(self):
        provider = GoogleCalendarProvider()
        assert provider is not None
        assert isinstance(provider, CalendarProvider)

    def test_authenticate_success(self):
        provider = GoogleCalendarProvider()
        import asyncio
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(
            provider.authenticate({"email": "test@gmail.com"})
        )
        assert result is True

    def test_fetch_events_empty_when_not_auth(self):
        provider = GoogleCalendarProvider()
        import asyncio
        loop = asyncio.new_event_loop()
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        result = loop.run_until_complete(provider.fetch_events(now, now))
        assert result == []
