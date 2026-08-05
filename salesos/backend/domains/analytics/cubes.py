"""Pre-built analytics cubes for common SalesOS reporting scenarios.

Each cube encapsulates a dimension set, measure set, and a query()
method. Until cubes are wired to real tenant DB queries, query() returns
an empty row set — never fabricated sample metrics for empty tenants.
"""

from __future__ import annotations

import uuid
from typing import Any

from domains.analytics.models import AnalyticsCube, Granularity


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
        # Honest empty: no fabricated sample rows. Wire real SQL when ready.
        _ = (db, tenant_id, filters, granularity)
        return []


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
        _ = (db, tenant_id, filters, granularity)
        return []


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
        _ = (db, tenant_id, filters, granularity)
        return []


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
        _ = (db, tenant_id, filters, granularity)
        return []
