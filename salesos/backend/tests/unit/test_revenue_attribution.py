from datetime import UTC, datetime, timedelta
from decimal import Decimal

from domains.commercial.revenue.attribution import Touchpoint, first_touch_attribution


def test_first_touch_attribution_is_windowed_and_cost_aware():
    close = datetime(2026, 9, 22, tzinfo=UTC)
    result = first_touch_attribution(
        opportunity_id="opp-1",
        revenue=Decimal("1000.00"),
        closed_at=close,
        touchpoints=[
            Touchpoint("late", "opp-1", "email", close - timedelta(days=10), Decimal("2")),
            Touchpoint("first", "opp-1", "event", close - timedelta(days=20), Decimal("5")),
            Touchpoint("out", "opp-1", "old", close - timedelta(days=91), Decimal("50")),
        ],
    )
    assert result.touchpoint_id == "first"
    assert result.attributed_source == "event"
    assert result.revenue == Decimal("1000.00")
    assert result.source_cost == Decimal("5")


def test_attribution_keeps_unattributed_revenue_explicit():
    close = datetime(2026, 9, 22, tzinfo=UTC)
    result = first_touch_attribution(
        opportunity_id="opp-2",
        revenue=Decimal("20"),
        closed_at=close,
        touchpoints=[],
    )
    assert result.method == "unattributed"
    assert result.attributed_source is None
