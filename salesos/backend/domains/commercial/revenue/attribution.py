"""Deterministic, explainable revenue attribution primitives."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Iterable


@dataclass(frozen=True)
class Touchpoint:
    touchpoint_id: str
    opportunity_id: str
    source: str
    occurred_at: datetime
    cost: Decimal = Decimal("0")


@dataclass(frozen=True)
class AttributionResult:
    opportunity_id: str
    revenue: Decimal
    attributed_source: str | None
    touchpoint_id: str | None
    source_cost: Decimal
    method: str


def first_touch_attribution(
    *,
    opportunity_id: str,
    revenue: Decimal,
    closed_at: datetime,
    touchpoints: Iterable[Touchpoint],
    window: timedelta = timedelta(days=90),
) -> AttributionResult:
    """Attribute to the earliest eligible touchpoint; preserve unknowns."""
    close = closed_at if closed_at.tzinfo and closed_at.utcoffset() else closed_at.replace(tzinfo=UTC)
    eligible = [
        item
        for item in touchpoints
        if item.opportunity_id == opportunity_id
        and item.occurred_at.astimezone(UTC) <= close.astimezone(UTC)
        and close.astimezone(UTC) - item.occurred_at.astimezone(UTC) <= window
    ]
    chosen = min(eligible, key=lambda item: item.occurred_at) if eligible else None
    return AttributionResult(
        opportunity_id=opportunity_id,
        revenue=Decimal(revenue),
        attributed_source=chosen.source if chosen else None,
        touchpoint_id=chosen.touchpoint_id if chosen else None,
        source_cost=chosen.cost if chosen else Decimal("0"),
        method="first_touch_90d" if chosen else "unattributed",
    )
