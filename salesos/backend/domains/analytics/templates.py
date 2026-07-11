"""Standard report templates for common SalesOS reporting needs."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from domains.analytics.models import CubeType, ReportDefinition


def weekly_pipeline_summary(tenant_id: str) -> ReportDefinition:
    """Weekly Pipeline Summary — pipeline cube, grouped by stage, last 7 days."""
    return ReportDefinition(
        id="",
        tenant_id=tenant_id,
        name="Weekly Pipeline Summary",
        type=CubeType.PIPELINE,
        config={
            "filters": {},
            "granularity": "week",
            "output_format": "json",
        },
        schedule="0 9 * * 1",
        recipients=[],
    )


def monthly_forecast_report(tenant_id: str) -> ReportDefinition:
    """Monthly Forecast Report — forecast cube, current quarter."""
    return ReportDefinition(
        id="",
        tenant_id=tenant_id,
        name="Monthly Forecast Report",
        type=CubeType.FORECAST,
        config={
            "filters": {},
            "granularity": "quarter",
            "output_format": "json",
        },
        schedule="0 8 1 * *",
        recipients=[],
    )


def team_performance_report(tenant_id: str) -> ReportDefinition:
    """Team Performance — team cube, this month vs last month."""
    return ReportDefinition(
        id="",
        tenant_id=tenant_id,
        name="Team Performance Report",
        type=CubeType.TEAM,
        config={
            "filters": {},
            "granularity": "month",
            "output_format": "json",
        },
        schedule="0 8 * * 1",
        recipients=[],
    )


def activity_report(tenant_id: str) -> ReportDefinition:
    """Activity Report — activity cube, last 30 days per team member."""
    return ReportDefinition(
        id="",
        tenant_id=tenant_id,
        name="Activity Report",
        type=CubeType.ACTIVITY,
        config={
            "filters": {},
            "granularity": "day",
            "output_format": "json",
        },
        schedule="0 7 * * *",
        recipients=[],
    )


STANDARD_TEMPLATES = {
    "weekly_pipeline_summary": weekly_pipeline_summary,
    "monthly_forecast_report": monthly_forecast_report,
    "team_performance_report": team_performance_report,
    "activity_report": activity_report,
}
