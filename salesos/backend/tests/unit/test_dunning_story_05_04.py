"""STORY-05-04 — dunning grace math (pure)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.modules.billing.dunning import grace_elapsed, grace_ends_at


def test_grace_ends_and_elapsed() -> None:
    failed = datetime(2026, 8, 1, 12, 0, tzinfo=UTC)
    end = grace_ends_at(failed, grace_days=7)
    assert end == datetime(2026, 8, 8, 12, 0, tzinfo=UTC)
    assert grace_elapsed(end, now=datetime(2026, 8, 8, 11, 59, tzinfo=UTC)) is False
    assert grace_elapsed(end, now=datetime(2026, 8, 8, 12, 0, tzinfo=UTC)) is True


def test_grace_days_zero_is_immediate() -> None:
    failed = datetime(2026, 8, 2, tzinfo=UTC)
    end = grace_ends_at(failed, grace_days=0)
    assert end == failed
    assert grace_elapsed(end, now=failed + timedelta(seconds=1)) is True
