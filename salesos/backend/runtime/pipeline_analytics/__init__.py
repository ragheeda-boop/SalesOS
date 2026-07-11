"""Pipeline Analytics — velocity, conversion, health, and forecast."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text as sa_text


class PipelineAnalytics:
    """Computes pipeline metrics: velocity, win rate, conversion, health, forecast."""

    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    async def velocity(self) -> dict[str, Any]:
        """Average days per stage for won opportunities."""
        rows = await self.db.execute(
            sa_text("""
                SELECT se.stage_name,
                       AVG(EXTRACT(EPOCH FROM (se.exited_at - se.entered_at)) / 86400) as avg_days,
                       COUNT(*) as entry_count
                FROM commercial_stage_entries se
                JOIN commercial_opportunities o ON o.id = se.opportunity_id
                WHERE o.tenant_id = :tid AND se.exited_at IS NOT NULL
                GROUP BY se.stage_name
                ORDER BY MIN(se.entered_at)
            """),
            {"tid": self.tenant_id},
        )
        return {
            r["stage_name"]: {
                "avg_days": round(float(r["avg_days"]), 1) if r["avg_days"] else 0,
                "entries": r["entry_count"],
            }
            for r in rows.mappings().all()
        }

    async def conversion_rates(self) -> dict[str, Any]:
        """Conversion rate between consecutive stages."""
        rows = await self.db.execute(
            sa_text("""
                WITH stage_counts AS (
                    SELECT stage, COUNT(*) as cnt
                    FROM commercial_opportunities
                    WHERE tenant_id = :tid
                    GROUP BY stage
                )
                SELECT stage, cnt FROM stage_counts ORDER BY stage
            """),
            {"tid": self.tenant_id},
        )
        stages = [(r["stage"], r["cnt"]) for r in rows.mappings().all()]
        rates = {}
        for i in range(len(stages) - 1):
            from_stage, from_count = stages[i]
            to_stage, to_count = stages[i + 1]
            if from_count > 0:
                rates[f"{from_stage}→{to_stage}"] = round(to_count / from_count, 3)
        return rates

    async def health_map(self) -> list[dict[str, Any]]:
        """Health status for all open opportunities."""
        rows = await self.db.execute(
            sa_text("""
                SELECT o.id, o.name, o.stage, o.value,
                       COALESCE(cf.score, 0.5) as health_score,
                       o.owner_id
                FROM commercial_opportunities o
                LEFT JOIN company_features cf ON cf.company_id = o.id::text
                    AND cf.tenant_id = :tid AND cf.feature_name = 'deal_health'
                WHERE o.tenant_id = :tid AND o.status = 'open'
                ORDER BY cf.score ASC NULLS LAST
            """),
            {"tid": self.tenant_id},
        )
        results = []
        for r in rows.mappings().all():
            score = float(r["health_score"])
            if score >= 0.7:
                health = "healthy"
            elif score >= 0.4:
                health = "at_risk"
            else:
                health = "critical"
            results.append({
                "opportunity_id": r["id"],
                "name": r["name"],
                "stage": r["stage"],
                "value": float(r["value"]),
                "health": health,
                "health_score": score,
                "owner": r["owner_id"] or "",
            })
        return results

    async def forecast(self) -> dict[str, Any]:
        """Best case, commit, and pipeline forecasts."""
        rows = await self.db.execute(
            sa_text("""
                SELECT
                    COUNT(*) as total_count,
                    COALESCE(SUM(value), 0) as total_value,
                    COALESCE(SUM(value * probability), 0) as weighted_value,
                    COALESCE(AVG(probability), 0) as avg_probability
                FROM commercial_opportunities
                WHERE tenant_id = :tid AND status = 'open'
            """),
            {"tid": self.tenant_id},
        )
        r = rows.mappings().one()
        total = float(r["total_value"])
        weighted = float(r["weighted_value"])
        avg_prob = float(r["avg_probability"])

        # Best case: all deals close at full value
        # Commit: weighted value (probability-adjusted)
        # Pipeline: total value of all open deals
        return {
            "best_case": round(total, 2),
            "commit": round(weighted, 2),
            "pipeline": round(total, 2),
            "gap": round(total - weighted, 2),
            "avg_probability": round(avg_prob, 2),
            "total_deals": r["total_count"],
        }

    async def summary(self) -> dict[str, Any]:
        """Combined pipeline summary."""
        velocity = await self.velocity()
        conversion = await self.conversion_rates()
        health = await self.health_map()
        forecast = await self.forecast()

        healthy_count = sum(1 for h in health if h["health"] == "healthy")
        at_risk_count = sum(1 for h in health if h["health"] == "at_risk")
        critical_count = sum(1 for h in health if h["health"] == "critical")

        return {
            "velocity": velocity,
            "conversion_rates": conversion,
            "health_map": {
                "healthy": healthy_count,
                "at_risk": at_risk_count,
                "critical": critical_count,
                "opportunities": health,
            },
            "forecast": forecast,
            "total_open_deals": len(health),
        }
