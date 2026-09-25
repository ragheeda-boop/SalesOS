"""Pipeline Analytics — velocity, conversion, health, and forecast."""

from __future__ import annotations

from typing import Any

from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession


class PipelineAnalytics:
    """Computes pipeline metrics: velocity, win rate, conversion, health, forecast."""

    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    async def velocity(self) -> dict[str, Any]:
        """Average days per stage for won opportunities."""
        rows = await self.db.execute(
            sa_text("""
                SELECT se.to_stage as stage_name,
                       AVG(EXTRACT(EPOCH FROM (se.exited_at - se.entered_at)) / 86400) as avg_days,
                       COUNT(*) as entry_count
                FROM commercial_stage_entries se
                JOIN commercial_opportunities o ON o.id = se.opportunity_id
                WHERE o.tenant_id = :tid AND se.exited_at IS NOT NULL
                GROUP BY se.to_stage
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
        """Health status for all open opportunities.

        Missing probability stays unknown; it is never replaced by a guessed score.
        """
        rows = await self.db.execute(
            sa_text("""
                SELECT o.id, o.name, o.stage, o.value, o.currency, o.owner_id,
                       o.probability as health_score
                FROM commercial_opportunities o
                WHERE o.tenant_id = :tid AND o.status = 'open'
                ORDER BY o.probability ASC NULLS LAST
            """),
            {"tid": self.tenant_id},
        )
        results = []
        for r in rows.mappings().all():
            raw_score = r["health_score"]
            score = float(raw_score) if raw_score is not None else None
            if score is None:
                health = "unknown"
            elif score >= 0.7:
                health = "healthy"
            elif score >= 0.4:
                health = "at_risk"
            else:
                health = "critical"
            results.append(
                {
                    "opportunity_id": r["id"],
                    "name": r["name"],
                    "stage": r["stage"],
                    "value": float(r["value"]),
                    "currency": str(r.get("currency") or "UNKNOWN"),
                    "health": health,
                    "health_score": score,
                    "owner": r["owner_id"] or "",
                }
            )
        return results

    async def forecast(self) -> dict[str, Any]:
        """Best case, commit, and pipeline forecasts, never summing currencies."""
        rows = await self.db.execute(
            sa_text("""
                SELECT
                    COALESCE(NULLIF(UPPER(TRIM(currency)), ''), 'UNKNOWN') AS currency,
                    COUNT(*) as total_count,
                    COALESCE(SUM(value), 0) as total_value,
                    COALESCE(SUM(value * probability), 0) as weighted_value,
                    COALESCE(AVG(probability), 0) as avg_probability
                FROM commercial_opportunities
                WHERE tenant_id = :tid AND status = 'open'
                GROUP BY COALESCE(NULLIF(UPPER(TRIM(currency)), ''), 'UNKNOWN')
                ORDER BY currency
            """),
            {"tid": self.tenant_id},
        )
        by_currency = []
        for row in rows.mappings().all():
            total = float(row["total_value"] or 0)
            weighted = float(row["weighted_value"] or 0)
            by_currency.append(
                {
                    "currency": str(row.get("currency") or "UNKNOWN"),
                    "best_case": round(total, 2),
                    "commit": round(weighted, 2),
                    "pipeline": round(total, 2),
                    "gap": round(total - weighted, 2),
                    "avg_probability": round(float(row["avg_probability"] or 0), 2),
                    "total_deals": int(row["total_count"] or 0),
                }
            )

        total_deals = sum(row["total_deals"] for row in by_currency)
        avg_probability = (
            sum(float(row["avg_probability"]) * row["total_deals"] for row in by_currency)
            / total_deals
            if total_deals
            else 0.0
        )
        single_currency = by_currency[0] if len(by_currency) == 1 else None

        # Top-level money values are present only when a single currency exists.
        # Consumers must use by_currency when the tenant has mixed-currency deals.
        return {
            "currency": single_currency["currency"] if single_currency else None,
            "best_case": single_currency["best_case"] if single_currency else None,
            "commit": single_currency["commit"] if single_currency else None,
            "pipeline": single_currency["pipeline"] if single_currency else None,
            "gap": single_currency["gap"] if single_currency else None,
            "avg_probability": round(avg_probability, 2),
            "total_deals": total_deals,
            "by_currency": by_currency,
        }

    async def summary(self) -> dict[str, Any]:
        """Combined pipeline summary (sequential — one asyncpg connection)."""
        velocity = await self.velocity()
        conversion = await self.conversion_rates()
        health = await self.health_map()
        forecast = await self.forecast()

        healthy_count = sum(1 for h in health if h["health"] == "healthy")
        at_risk_count = sum(1 for h in health if h["health"] == "at_risk")
        critical_count = sum(1 for h in health if h["health"] == "critical")
        unknown_count = sum(1 for h in health if h["health"] == "unknown")

        return {
            "velocity": velocity,
            "conversion_rates": conversion,
            "health_map": {
                "healthy": healthy_count,
                "at_risk": at_risk_count,
                "critical": critical_count,
                "unknown": unknown_count,
                "opportunities": health,
            },
            "forecast": forecast,
            "total_open_deals": len(health),
        }
