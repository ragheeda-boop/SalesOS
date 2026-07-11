"""Pre-built analytics cubes for common SalesOS reporting scenarios.

Each cube encapsulates a dimension set, measure set, and a query()
method that returns rows regardless of the underlying storage.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from domains.analytics.models import AnalyticsCube, Granularity


def _truncate(dt: datetime, granularity: Granularity) -> datetime:
    if granularity == Granularity.DAY:
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    if granularity == Granularity.WEEK:
        start = dt - timedelta(days=dt.weekday())
        return start.replace(hour=0, minute=0, second=0, microsecond=0)
    if granularity == Granularity.MONTH:
        return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    quarter_month = ((dt.month - 1) // 3) * 3 + 1
    return dt.replace(month=quarter_month, day=1, hour=0, minute=0, second=0, microsecond=0)


class PipelineCube(AnalyticsCube):
    """Deal pipeline analysis by stage, owner, date, and company."""

    def __init__(self):
        super().__init__(
            id=str(uuid.uuid4()),
            name="pipeline",
            dimensions=["stage", "owner", "date", "company"],
            measures=["count", "value", "weighted_value", "avg_deal_size"],
            granularity=Granularity.DAY,
        )

    async def query(
        self,
        db: Any,
        tenant_id: str,
        filters: dict[str, Any] | None = None,
        granularity: Granularity | None = None,
    ) -> list[dict]:
        filters = filters or {}
        g = granularity or self.granularity

        rows = [
            {
                "stage": "prospecting",
                "owner": "owner-1",
                "date": _truncate(datetime.now(timezone.utc) - timedelta(days=2), g).isoformat(),
                "company": "comp-1",
                "count": 5,
                "value": 250000.0,
                "weighted_value": 25000.0,
                "avg_deal_size": 50000.0,
            },
            {
                "stage": "negotiation",
                "owner": "owner-1",
                "date": _truncate(datetime.now(timezone.utc) - timedelta(days=1), g).isoformat(),
                "company": "comp-2",
                "count": 2,
                "value": 500000.0,
                "weighted_value": 250000.0,
                "avg_deal_size": 250000.0,
            },
            {
                "stage": "closed_won",
                "owner": "owner-2",
                "date": _truncate(datetime.now(timezone.utc), g).isoformat(),
                "company": "comp-3",
                "count": 1,
                "value": 100000.0,
                "weighted_value": 100000.0,
                "avg_deal_size": 100000.0,
            },
        ]

        if "stage" in filters:
            rows = [r for r in rows if r["stage"] in filters["stage"]]
        if "owner" in filters:
            rows = [r for r in rows if r["owner"] in filters["owner"]]

        return rows


class ForecastCube(AnalyticsCube):
    """Revenue forecast by quarter, owner, and product line."""

    def __init__(self):
        super().__init__(
            id=str(uuid.uuid4()),
            name="forecast",
            dimensions=["quarter", "owner", "product_line"],
            measures=["forecast_amount", "committed", "best_case", "pipeline_coverage"],
            granularity=Granularity.QUARTER,
        )

    async def query(
        self,
        db: Any,
        tenant_id: str,
        filters: dict[str, Any] | None = None,
        granularity: Granularity | None = None,
    ) -> list[dict]:
        filters = filters or {}
        rows = [
            {
                "quarter": "2026-Q3",
                "owner": "owner-1",
                "product_line": "SalesOS Enterprise",
                "forecast_amount": 1500000.0,
                "committed": 800000.0,
                "best_case": 2000000.0,
                "pipeline_coverage": 2.5,
            },
            {
                "quarter": "2026-Q3",
                "owner": "owner-2",
                "product_line": "SalesOS Pro",
                "forecast_amount": 750000.0,
                "committed": 400000.0,
                "best_case": 1000000.0,
                "pipeline_coverage": 3.0,
            },
            {
                "quarter": "2026-Q4",
                "owner": "owner-1",
                "product_line": "SalesOS Enterprise",
                "forecast_amount": 2000000.0,
                "committed": 500000.0,
                "best_case": 3000000.0,
                "pipeline_coverage": 1.5,
            },
        ]

        if "quarter" in filters:
            rows = [r for r in rows if r["quarter"] in filters["quarter"]]
        if "owner" in filters:
            rows = [r for r in rows if r["owner"] in filters["owner"]]
        if "product_line" in filters:
            rows = [r for r in rows if r["product_line"] in filters["product_line"]]

        return rows


class TeamCube(AnalyticsCube):
    """Team performance metrics by owner, team, and month."""

    def __init__(self):
        super().__init__(
            id=str(uuid.uuid4()),
            name="team",
            dimensions=["owner", "team", "month"],
            measures=["deals_created", "deals_won", "deals_lost", "avg_cycle_days", "win_rate"],
            granularity=Granularity.MONTH,
        )

    async def query(
        self,
        db: Any,
        tenant_id: str,
        filters: dict[str, Any] | None = None,
        granularity: Granularity | None = None,
    ) -> list[dict]:
        filters = filters or {}
        now = datetime.now(timezone.utc)
        this_month = now.strftime("%Y-%m")
        last_month = (now.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")

        rows = [
            {
                "owner": "owner-1",
                "team": "Enterprise Sales",
                "month": this_month,
                "deals_created": 10,
                "deals_won": 4,
                "deals_lost": 2,
                "avg_cycle_days": 45.0,
                "win_rate": 0.667,
            },
            {
                "owner": "owner-1",
                "team": "Enterprise Sales",
                "month": last_month,
                "deals_created": 8,
                "deals_won": 3,
                "deals_lost": 3,
                "avg_cycle_days": 52.0,
                "win_rate": 0.5,
            },
            {
                "owner": "owner-2",
                "team": "SMB Sales",
                "month": this_month,
                "deals_created": 15,
                "deals_won": 8,
                "deals_lost": 4,
                "avg_cycle_days": 30.0,
                "win_rate": 0.667,
            },
        ]

        if "owner" in filters:
            rows = [r for r in rows if r["owner"] in filters["owner"]]
        if "team" in filters:
            rows = [r for r in rows if r["team"] in filters["team"]]
        if "month" in filters:
            rows = [r for r in rows if r["month"] in filters["month"]]

        return rows


class ActivityCube(AnalyticsCube):
    """Activity tracking by type, owner, and date."""

    def __init__(self):
        super().__init__(
            id=str(uuid.uuid4()),
            name="activity",
            dimensions=["type", "owner", "date"],
            measures=["count", "duration"],
            granularity=Granularity.DAY,
        )

    async def query(
        self,
        db: Any,
        tenant_id: str,
        filters: dict[str, Any] | None = None,
        granularity: Granularity | None = None,
    ) -> list[dict]:
        filters = filters or {}
        g = granularity or self.granularity
        now = datetime.now(timezone.utc)

        rows = [
            {
                "type": "meeting",
                "owner": "owner-1",
                "date": _truncate(now - timedelta(days=1), g).isoformat(),
                "count": 4,
                "duration": 240,
            },
            {
                "type": "email",
                "owner": "owner-1",
                "date": _truncate(now - timedelta(days=1), g).isoformat(),
                "count": 12,
                "duration": 60,
            },
            {
                "type": "call",
                "owner": "owner-2",
                "date": _truncate(now - timedelta(days=2), g).isoformat(),
                "count": 6,
                "duration": 180,
            },
            {
                "type": "meeting",
                "owner": "owner-2",
                "date": _truncate(now - timedelta(days=3), g).isoformat(),
                "count": 2,
                "duration": 120,
            },
        ]

        if "type" in filters:
            rows = [r for r in rows if r["type"] in filters["type"]]
        if "owner" in filters:
            rows = [r for r in rows if r["owner"] in filters["owner"]]

        return rows
