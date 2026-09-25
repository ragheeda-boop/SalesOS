"""Explainable account signals derived from persisted CRM activity and deals."""

from __future__ import annotations

from typing import Any, Literal

Polarity = Literal["positive", "attention", "neutral"]


def build_account_signals(
    *,
    total_opportunities: int,
    active_opportunities: int,
    won_deals: int,
    lost_deals: int,
    activity_count: int,
    days_since_activity: int | None,
) -> dict[str, Any]:
    """Return rule-based CRM observations; never infer an opaque health score."""
    signals: list[dict[str, str]] = []
    recommendations: list[str] = []

    if total_opportunities == 0:
        signals.append(
            {
                "code": "NO_OPPORTUNITY_HISTORY",
                "polarity": "neutral",
                "title": "No opportunity history",
                "detail": "No opportunities are linked to this account in the tenant CRM.",
                "source": "commercial_opportunities",
            }
        )

    if activity_count == 0:
        signals.append(
            {
                "code": "NO_ACTIVITY_HISTORY",
                "polarity": "neutral",
                "title": "No activity recorded",
                "detail": "No company activity is recorded in the tenant CRM.",
                "source": "activity_records",
            }
        )
    elif days_since_activity is not None and days_since_activity > 90:
        signals.append(
            {
                "code": "STALE_ACTIVITY",
                "polarity": "attention",
                "title": "No recent activity",
                "detail": f"The last recorded company activity was {days_since_activity} days ago.",
                "source": "activity_records",
            }
        )

    if active_opportunities > 0 and (
        activity_count == 0 or days_since_activity is None or days_since_activity > 90
    ):
        signals.append(
            {
                "code": "OPEN_DEALS_WITHOUT_RECENT_ACTIVITY",
                "polarity": "attention",
                "title": "Open opportunities need follow-up",
                "detail": (
                    f"{active_opportunities} open opportunities have no activity recorded "
                    "within the last 90 days."
                ),
                "source": "commercial_opportunities+activity_records",
            }
        )
        recommendations.append("Review the open opportunities and record the next customer action.")

    if total_opportunities >= 2 and lost_deals > won_deals:
        signals.append(
            {
                "code": "LOSSES_OUTWEIGH_WINS",
                "polarity": "attention",
                "title": "More opportunities lost than won",
                "detail": f"CRM history shows {lost_deals} lost and {won_deals} won opportunities.",
                "source": "commercial_opportunities",
            }
        )
        recommendations.append(
            "Review recent loss reasons before prioritizing another opportunity."
        )

    if activity_count > 0 and days_since_activity is not None and days_since_activity <= 30:
        signals.append(
            {
                "code": "RECENT_ACTIVITY",
                "polarity": "positive",
                "title": "Recent account engagement",
                "detail": f"A company activity was recorded {days_since_activity} days ago.",
                "source": "activity_records",
            }
        )

    if total_opportunities == 0 and activity_count == 0:
        status = "insufficient_data"
    elif any(signal["polarity"] == "attention" for signal in signals):
        status = "needs_attention"
    elif any(signal["polarity"] == "positive" for signal in signals):
        status = "engaged"
    else:
        status = "no_current_risk_signal"

    return {"status": status, "signals": signals, "recommendations": recommendations}


def build_engagement_trend(*, recent_90_days: int, previous_90_days: int) -> dict[str, Any]:
    """Compare CRM activity volume across two adjacent 90-day windows."""
    recent = max(0, int(recent_90_days))
    previous = max(0, int(previous_90_days))
    if recent == 0 and previous == 0:
        trend = "insufficient_data"
        change_percent = None
    elif previous == 0:
        trend = "improving"
        change_percent = None
    else:
        change_percent = round(((recent - previous) / previous) * 100, 1)
        if recent >= previous * 1.2:
            trend = "improving"
        elif recent <= previous * 0.8:
            trend = "declining"
        else:
            trend = "stable"

    return {
        "trend": trend,
        "recent_90_days": recent,
        "previous_90_days": previous,
        "change_percent": change_percent,
        "method": "activity_count_90d_comparison_v1",
        "interpretation": "Activity volume only; it does not measure customer sentiment or deal quality.",
    }
