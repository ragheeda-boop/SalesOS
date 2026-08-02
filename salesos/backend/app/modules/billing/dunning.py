"""STORY-05-04 — Dunning grace math (pure).

Failed payment → grace window → auto-suspend. No Stripe secrets.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from enum import StrEnum


class DunningCaseStatus(StrEnum):
    OPEN = "open"  # in grace
    SUSPENDED = "suspended"  # auto-suspended after grace
    CLEARED = "cleared"  # payment recovered / manual clear


def grace_ends_at(
    failed_at: datetime,
    *,
    grace_days: int,
) -> datetime:
    if failed_at.tzinfo is None:
        failed_at = failed_at.replace(tzinfo=UTC)
    days = max(0, int(grace_days))
    return failed_at.astimezone(UTC) + timedelta(days=days)


def grace_elapsed(
    grace_end: datetime,
    *,
    now: datetime | None = None,
) -> bool:
    clock = now or datetime.now(UTC)
    if clock.tzinfo is None:
        clock = clock.replace(tzinfo=UTC)
    end = grace_end if grace_end.tzinfo else grace_end.replace(tzinfo=UTC)
    return clock >= end.astimezone(UTC)
