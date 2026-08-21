"""Tests for webhooks.schemas — event validation, no DB."""

from __future__ import annotations

import pytest

from app.modules.webhooks.schemas import (
    SUPPORTED_EVENTS,
    WebhookSubscriptionCreate,
)


# ── SUPPORTED_EVENTS ─────────────────────────────────────────────────────────


class TestSupportedEvents:
    def test_non_empty(self):
        assert len(SUPPORTED_EVENTS) > 0

    def test_has_company_events(self):
        assert "company.created" in SUPPORTED_EVENTS
        assert "company.updated" in SUPPORTED_EVENTS

    def test_has_opportunity_events(self):
        assert "opportunity.created" in SUPPORTED_EVENTS
        assert "opportunity.stage_changed" in SUPPORTED_EVENTS
        assert "opportunity.won" in SUPPORTED_EVENTS
        assert "opportunity.lost" in SUPPORTED_EVENTS

    def test_all_strings(self):
        for ev in SUPPORTED_EVENTS:
            assert isinstance(ev, str)
            assert "." in ev, f"Event {ev} missing domain separator"


# ── WebhookSubscriptionCreate ────────────────────────────────────────────────


class TestWebhookSubscriptionCreate:
    def test_valid(self):
        sub = WebhookSubscriptionCreate(
            url="https://example.com/webhook",
            events=["company.created"],
            secret="a" * 16,
        )
        assert sub.url == "https://example.com/webhook"
        assert sub.events == ["company.created"]
        assert sub.secret == "a" * 16

    def test_empty_url_rejected(self):
        with pytest.raises(Exception):
            WebhookSubscriptionCreate(
                url="",
                events=["company.created"],
                secret="a" * 16,
            )

    def test_url_too_long(self):
        with pytest.raises(Exception):
            WebhookSubscriptionCreate(
                url="https://x.com/" + "a" * 2048,
                events=["company.created"],
                secret="a" * 16,
            )

    def test_empty_events_rejected(self):
        with pytest.raises(Exception):
            WebhookSubscriptionCreate(
                url="https://example.com",
                events=[],
                secret="a" * 16,
            )

    def test_secret_too_short(self):
        with pytest.raises(Exception):
            WebhookSubscriptionCreate(
                url="https://example.com",
                events=["company.created"],
                secret="short",
            )

    def test_secret_max_length(self):
        with pytest.raises(Exception):
            WebhookSubscriptionCreate(
                url="https://example.com",
                events=["company.created"],
                secret="a" * 257,
            )


# ── validate_events ──────────────────────────────────────────────────────────


class TestValidateEvents:
    def test_valid_events(self):
        sub = WebhookSubscriptionCreate(
            url="https://example.com",
            events=["company.created", "opportunity.won"],
            secret="a" * 16,
        )
        sub.validate_events()  # should not raise

    def test_invalid_event(self):
        sub = WebhookSubscriptionCreate(
            url="https://example.com",
            events=["nonexistent.event"],
            secret="a" * 16,
        )
        with pytest.raises(ValueError, match="Unsupported event"):
            sub.validate_events()

    def test_mixed_valid_invalid(self):
        sub = WebhookSubscriptionCreate(
            url="https://example.com",
            events=["company.created", "bad.event"],
            secret="a" * 16,
        )
        with pytest.raises(ValueError, match="bad.event"):
            sub.validate_events()

    def test_all_events_valid(self):
        sub = WebhookSubscriptionCreate(
            url="https://example.com",
            events=list(SUPPORTED_EVENTS),
            secret="a" * 16,
        )
        sub.validate_events()  # should not raise
