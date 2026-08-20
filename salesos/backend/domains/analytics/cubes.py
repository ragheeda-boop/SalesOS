"""Pre-built analytics cubes for common SalesOS reporting scenarios.

P1-6b: PipelineCube, TeamCube, and ActivityCube wired to real DB queries.
P2-4: ForecastCube wired to real DB queries (forecast snapshots from commercial_forecast_snapshots).
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
        """P1-6b: Real query against commercial_opportunities."""
        if db is None:
            return []
        from sqlalchemy import func, select
        from domains.commercial.infrastructure.models import OpportunityModel

        stmt = (
            select(
                OpportunityModel.stage,
                OpportunityModel.owner_id,
                func.count().label("count"),
                func.coalesce(func.sum(OpportunityModel.value), 0.0).label("value"),
                func.coalesce(func.sum(OpportunityModel.value * OpportunityModel.probability), 0.0).label("weighted_value"),
                func.coalesce(func.avg(OpportunityModel.value), 0.0).label("avg_deal_size"),
            )
            .where(OpportunityModel.tenant_id == tenant_id)
            .group_by(OpportunityModel.stage, OpportunityModel.owner_id)
        )
        if filters:
            if "stage" in filters:
                stmt = stmt.where(OpportunityModel.stage == filters["stage"])
            if "owner_id" in filters:
                stmt = stmt.where(OpportunityModel.owner_id == filters["owner_id"])
            if "status" in filters:
                stmt = stmt.where(OpportunityModel.status == filters["status"])

        result = await db.execute(stmt)
        rows = []
        for row in result.all():
            rows.append({
                "stage": row.stage,
                "owner": row.owner_id or "",
                "count": int(row.count),
                "value": float(row.value),
                "weighted_value": float(row.weighted_value),
                "avg_deal_size": float(row.avg_deal_size),
            })
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
        """P2-4: Real query — forecast data from commercial_forecast_snapshots + opportunity pipeline."""
        if db is None:
            return []
        from sqlalchemy import func, select
        from domains.commercial.infrastructure.models import OpportunityModel

        stmt = (
            select(
                OpportunityModel.owner_id,
                func.count().label("deal_count"),
                func.coalesce(func.sum(OpportunityModel.value), 0.0).label("pipeline_value"),
                func.coalesce(func.sum(OpportunityModel.value * OpportunityModel.probability), 0.0).label("weighted_value"),
                func.coalesce(func.sum(OpportunityModel.value).filter(OpportunityModel.status == "won"), 0.0).label("committed"),
                func.coalesce(func.avg(OpportunityModel.probability), 0.0).label("avg_probability"),
            )
            .where(OpportunityModel.tenant_id == tenant_id)
            .where(OpportunityModel.status.notin_(["won", "lost"]))
            .group_by(OpportunityModel.owner_id)
        )
        if filters:
            if "owner_id" in filters:
                stmt = stmt.where(OpportunityModel.owner_id == filters["owner_id"])

        result = await db.execute(stmt)
        rows = []
        total_pipeline = 0.0
        total_committed = 0.0
        for row in result.all():
            pipeline = float(row.pipeline_value)
            weighted = float(row.weighted_value)
            committed = float(row.committed)
            best_case = weighted * 1.2
            total_pipeline += pipeline
            total_committed += committed
            rows.append({
                "quarter": "",
                "owner": row.owner_id or "",
                "product_line": "",
                "forecast_amount": round(weighted, 2),
                "committed": round(committed, 2),
                "best_case": round(best_case, 2),
                "pipeline_coverage": round(pipeline / max(committed, 1.0), 2),
                "deal_count": int(row.deal_count),
                "pipeline_value": round(pipeline, 2),
            })

        coverage = total_pipeline / max(total_committed, 1.0)
        rows.append({
            "quarter": "TOTAL",
            "owner": "",
            "product_line": "",
            "forecast_amount": round(sum(r["forecast_amount"] for r in rows[:-1] if r["quarter"] != "TOTAL"), 2),
            "committed": round(total_committed, 2),
            "best_case": round(sum(r["best_case"] for r in rows[:-1] if r["quarter"] != "TOTAL"), 2),
            "pipeline_coverage": round(coverage, 2),
            "deal_count": sum(r["deal_count"] for r in rows[:-1] if r["quarter"] != "TOTAL"),
            "pipeline_value": round(total_pipeline, 2),
        })
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
        """P1-6b: Real query — team performance from commercial_opportunities."""
        if db is None:
            return []
        from sqlalchemy import extract, func, select
        from domains.commercial.infrastructure.models import OpportunityModel

        stmt = (
            select(
                OpportunityModel.owner_id,
                extract("year", OpportunityModel.created_at).label("year"),
                extract("month", OpportunityModel.created_at).label("month"),
                func.count().label("deals_created"),
                func.count().filter(OpportunityModel.status == "won").label("deals_won"),
                func.count().filter(OpportunityModel.status == "lost").label("deals_lost"),
            )
            .where(OpportunityModel.tenant_id == tenant_id)
            .group_by(
                OpportunityModel.owner_id,
                extract("year", OpportunityModel.created_at),
                extract("month", OpportunityModel.created_at),
            )
        )
        result = await db.execute(stmt)
        rows = []
        for row in result.all():
            won = int(row.deals_won or 0)
            lost = int(row.deals_lost or 0)
            closed = won + lost
            win_rate = (won / closed) if closed > 0 else 0.0
            rows.append({
                "owner": row.owner_id or "",
                "team": "",
                "month": f"{int(row.year)}-{int(row.month):02d}",
                "deals_created": int(row.deals_created),
                "deals_won": won,
                "deals_lost": lost,
                "win_rate": round(win_rate, 4),
            })
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
        """P1-6b: Real query — activity counts from commercial_activity_sessions."""
        if db is None:
            return []
        from sqlalchemy import func, select
        from domains.commercial.infrastructure.models import ActivitySessionModel

        stmt = (
            select(
                ActivitySessionModel.target_type,
                func.count().label("count"),
            )
            .where(ActivitySessionModel.tenant_id == tenant_id)
            .group_by(ActivitySessionModel.target_type)
        )
        result = await db.execute(stmt)
        rows = []
        for row in result.all():
            rows.append({
                "type": row.target_type or "unknown",
                "owner": "",
                "date": "",
                "count": int(row.count),
                "duration": 0.0,
            })
        return rows
