"""STORY-05-05 — Mid-cycle plan change proration (pure).

Upgrade: immediate charge for unused fraction of (new - old).
Downgrade (default): deferred to period end (no mid-cycle clawback).
Downgrade (immediate): credit for unused fraction of (old - new).

No Stripe secrets. Not Production GO.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum


class PlanChangeDirection(StrEnum):
    UPGRADE = "upgrade"
    DOWNGRADE = "downgrade"
    LATERAL = "lateral"


class PlanChangeTiming(StrEnum):
    IMMEDIATE = "immediate"
    PERIOD_END = "period_end"


@dataclass(frozen=True)
class ProrationQuote:
    direction: PlanChangeDirection
    timing: PlanChangeTiming
    old_price: float
    new_price: float
    remaining_fraction: float
    amount_due_now: float  # positive = charge, negative = credit
    currency_note: str = "plan_currency"


def remaining_period_fraction(
    *,
    period_start: datetime | None,
    period_end: datetime | None,
    now: datetime | None = None,
) -> float:
    """Fraction of billing period still remaining in [0, 1]."""
    clock = now or datetime.now(UTC)
    if clock.tzinfo is None:
        clock = clock.replace(tzinfo=UTC)
    if period_start is None or period_end is None:
        return 0.0
    start = period_start if period_start.tzinfo else period_start.replace(tzinfo=UTC)
    end = period_end if period_end.tzinfo else period_end.replace(tzinfo=UTC)
    start = start.astimezone(UTC)
    end = end.astimezone(UTC)
    total = (end - start).total_seconds()
    if total <= 0:
        return 0.0
    remaining = (end - clock).total_seconds()
    if remaining <= 0:
        return 0.0
    if remaining >= total:
        return 1.0
    return remaining / total


def classify_direction(old_price: float, new_price: float) -> PlanChangeDirection:
    if new_price > old_price:
        return PlanChangeDirection.UPGRADE
    if new_price < old_price:
        return PlanChangeDirection.DOWNGRADE
    return PlanChangeDirection.LATERAL


def quote_plan_change(
    *,
    old_price: float,
    new_price: float,
    period_start: datetime | None,
    period_end: datetime | None,
    downgrade_immediate: bool = False,
    now: datetime | None = None,
) -> ProrationQuote:
    direction = classify_direction(float(old_price), float(new_price))
    frac = remaining_period_fraction(
        period_start=period_start, period_end=period_end, now=now
    )
    delta = float(new_price) - float(old_price)

    if direction == PlanChangeDirection.UPGRADE:
        return ProrationQuote(
            direction=direction,
            timing=PlanChangeTiming.IMMEDIATE,
            old_price=float(old_price),
            new_price=float(new_price),
            remaining_fraction=frac,
            amount_due_now=round(delta * frac, 2),
        )
    if direction == PlanChangeDirection.DOWNGRADE:
        if downgrade_immediate:
            return ProrationQuote(
                direction=direction,
                timing=PlanChangeTiming.IMMEDIATE,
                old_price=float(old_price),
                new_price=float(new_price),
                remaining_fraction=frac,
                amount_due_now=round(delta * frac, 2),  # negative credit
            )
        return ProrationQuote(
            direction=direction,
            timing=PlanChangeTiming.PERIOD_END,
            old_price=float(old_price),
            new_price=float(new_price),
            remaining_fraction=frac,
            amount_due_now=0.0,
        )
    return ProrationQuote(
        direction=direction,
        timing=PlanChangeTiming.IMMEDIATE,
        old_price=float(old_price),
        new_price=float(new_price),
        remaining_fraction=frac,
        amount_due_now=0.0,
    )
