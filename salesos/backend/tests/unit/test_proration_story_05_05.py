"""STORY-05-05 — proration quote math (pure)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.modules.billing.proration import (
    PlanChangeDirection,
    PlanChangeTiming,
    quote_plan_change,
    remaining_period_fraction,
)


def test_remaining_fraction_mid_period() -> None:
    start = datetime(2026, 8, 1, tzinfo=UTC)
    end = datetime(2026, 8, 31, tzinfo=UTC)
    mid = datetime(2026, 8, 16, tzinfo=UTC)
    frac = remaining_period_fraction(period_start=start, period_end=end, now=mid)
    assert 0.48 < frac < 0.52


def test_upgrade_immediate_charge() -> None:
    start = datetime(2026, 8, 1, tzinfo=UTC)
    end = start + timedelta(days=30)
    now = start + timedelta(days=15)
    q = quote_plan_change(
        old_price=100.0,
        new_price=200.0,
        period_start=start,
        period_end=end,
        now=now,
    )
    assert q.direction == PlanChangeDirection.UPGRADE
    assert q.timing == PlanChangeTiming.IMMEDIATE
    assert q.amount_due_now == 50.0


def test_downgrade_deferred_zero_now() -> None:
    start = datetime(2026, 8, 1, tzinfo=UTC)
    end = start + timedelta(days=30)
    q = quote_plan_change(
        old_price=200.0,
        new_price=100.0,
        period_start=start,
        period_end=end,
        downgrade_immediate=False,
        now=start + timedelta(days=10),
    )
    assert q.direction == PlanChangeDirection.DOWNGRADE
    assert q.timing == PlanChangeTiming.PERIOD_END
    assert q.amount_due_now == 0.0


def test_downgrade_immediate_credit() -> None:
    start = datetime(2026, 8, 1, tzinfo=UTC)
    end = start + timedelta(days=30)
    q = quote_plan_change(
        old_price=200.0,
        new_price=100.0,
        period_start=start,
        period_end=end,
        downgrade_immediate=True,
        now=start + timedelta(days=15),
    )
    assert q.timing == PlanChangeTiming.IMMEDIATE
    assert q.amount_due_now == -50.0
