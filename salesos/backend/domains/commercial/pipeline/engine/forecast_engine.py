"""PipelineForecastEngine — weighted pipeline, historical velocity, confidence intervals."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from ..contracts.forecast_models import (
    ForecastBreakdown,
    ForecastMethod,
    ForecastSnapshot,
    PipelineHistoricalPeriod,
)


class PipelineForecastEngine:
    """Generates pipeline forecasts using multiple methods.

    Methods:
    1. Weighted Pipeline: sum(deal_value × probability) per stage
    2. Historical Velocity: deals closed per period × avg deal value
    3. Combined: weighted average of both methods
    """

    def __init__(self):
        self._history: list[PipelineHistoricalPeriod] = []

    def set_history(self, periods: list[PipelineHistoricalPeriod]) -> None:
        self._history = periods

    def forecast(
        self,
        opportunities: list[dict[str, Any]],
        method: ForecastMethod = ForecastMethod.COMBINED,
        horizon_months: int = 3,
        tenant_id: str = "",
        title: str = "",
    ) -> ForecastSnapshot:
        """Generate a forecast snapshot from current pipeline data."""
        weighted = self._compute_weighted_pipeline(opportunities)
        velocity = self._compute_historical_velocity(horizon_months)
        combined = self._combine(weighted, velocity)

        by_rep = self._breakdown_by_key(opportunities, "owner_id", "rep")
        by_region = self._breakdown_by_key(opportunities, "region", "region")
        by_product = self._breakdown_by_key(opportunities, "product", "product")

        total = ForecastBreakdown(
            dimension="total",
            label="Total Pipeline",
            total_pipeline_value=combined["pipeline_value"],
            weighted_value=combined["weighted"],
            historical_velocity_value=combined["velocity"],
            combined_value=combined["combined"],
            opportunity_count=combined["count"],
            avg_deal_size=combined["avg_deal"],
            win_rate=combined["win_rate"],
        )

        ci_lower = total.confidence_interval_lower
        ci_upper = total.confidence_interval_upper
        confidence = self._compute_confidence(opportunities, combined)

        now = datetime.now(timezone.utc)
        snapshot = ForecastSnapshot(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            method=method,
            title=title or f"Pipeline Forecast — {now.strftime('%Y-%m-%d')}",
            period_start=now,
            period_end=now,
            horizon_months=horizon_months,
            generated_at=now,
            total_pipeline_value=total.total_pipeline_value,
            total_weighted=total.weighted_value,
            total_velocity=total.historical_velocity_value,
            total_combined=total.combined_value,
            overall_confidence=confidence,
            overall_win_rate=total.win_rate,
            by_rep=by_rep,
            by_region=by_region,
            by_product=by_product,
            total=total,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
        )
        return snapshot

    def _compute_weighted_pipeline(self, opportunities: list[dict[str, Any]]) -> dict[str, float]:
        """Sum(deal_value × probability) across all open opportunities."""
        total_value = 0.0
        weighted = 0.0
        count = 0
        for opp in opportunities:
            if opp.get("status") in ("won", "lost", "abandoned"):
                continue
            value = opp.get("value", 0.0)
            prob = opp.get("probability", 0.0)
            total_value += value
            weighted += value * prob
            count += 1
        return {
            "pipeline_value": total_value,
            "weighted": weighted,
            "count": count,
        }

    def _compute_historical_velocity(self, horizon_months: int) -> dict[str, float]:
        """Revenue per period × number of periods in horizon."""
        if not self._history:
            return {"velocity": 0.0, "avg_deal": 0.0, "win_rate": 0.0}

        total_revenue = sum(p.total_revenue for p in self._history)
        total_deals = sum(p.total_deals for p in self._history)
        total_won = sum(p.closed_won for p in self._history)
        total_lost = sum(p.closed_lost for p in self._history)
        periods_count = len(self._history)

        avg_revenue_per_period = total_revenue / periods_count if periods_count > 0 else 0.0
        avg_deal = total_revenue / total_deals if total_deals > 0 else 0.0
        win_rate = total_won / (total_won + total_lost) if (total_won + total_lost) > 0 else 0.0

        velocity = avg_revenue_per_period * horizon_months
        return {
            "velocity": velocity,
            "avg_deal": avg_deal,
            "win_rate": win_rate,
            "avg_revenue_per_period": avg_revenue_per_period,
        }

    def _combine(self, weighted: dict[str, float], velocity: dict[str, float]) -> dict[str, float]:
        """Combine weighted pipeline and velocity into a single forecast."""
        w_val = weighted.get("weighted", 0.0)
        v_val = velocity.get("velocity", 0.0)
        count = weighted.get("count", 0)

        # If we have history, give velocity 40% weight; otherwise 100% weighted
        if self._history and v_val > 0:
            combined = w_val * 0.6 + v_val * 0.4
        else:
            combined = w_val

        pipeline_value = weighted.get("pipeline_value", 0.0)
        avg_deal = velocity.get("avg_deal", 0.0)
        win_rate = velocity.get("win_rate", 0.0)

        return {
            "pipeline_value": pipeline_value,
            "weighted": w_val,
            "velocity": v_val,
            "combined": combined,
            "count": count,
            "avg_deal": avg_deal,
            "win_rate": win_rate,
        }

    def _breakdown_by_key(
        self,
        opportunities: list[dict[str, Any]],
        key: str,
        dimension: str,
    ) -> list[ForecastBreakdown]:
        """Group opportunities by a key and compute forecast breakdown."""
        groups: dict[str, list[dict]] = {}
        for opp in opportunities:
            if opp.get("status") in ("won", "lost", "abandoned"):
                continue
            group_key = opp.get(key) or "unassigned"
            groups.setdefault(group_key, []).append(opp)

        breakdowns = []
        for group_key, opps in groups.items():
            pipeline_val = sum(o.get("value", 0) for o in opps)
            weighted_val = sum(o.get("value", 0) * o.get("probability", 0) for o in opps)
            # Historical velocity breakdown uses the overall win rate
            overall_wr = self._compute_win_rate(opportunities)
            velocity_val = pipeline_val * overall_wr * (1 if not self._history else len(self._history) / max(len(self._history), 1))
            combined_val = weighted_val * 0.6 + velocity_val * 0.4 if self._history else weighted_val
            avg_deal = pipeline_val / len(opps) if opps else 0.0

            breakdowns.append(ForecastBreakdown(
                dimension=dimension,
                label=group_key,
                total_pipeline_value=pipeline_val,
                weighted_value=weighted_val,
                historical_velocity_value=velocity_val,
                combined_value=combined_val,
                opportunity_count=len(opps),
                avg_deal_size=avg_deal,
                win_rate=overall_wr,
            ))

        breakdowns.sort(key=lambda b: b.combined_value, reverse=True)
        return breakdowns

    def _compute_win_rate(self, opportunities: list[dict[str, Any]]) -> float:
        """Compute win rate from all closed opportunities."""
        won = sum(1 for o in opportunities if o.get("status") == "won")
        lost = sum(1 for o in opportunities if o.get("status") == "lost")
        closed = won + lost
        return won / closed if closed > 0 else 0.5

    def _compute_confidence(
        self,
        opportunities: list[dict[str, Any]],
        combined: dict[str, float],
    ) -> float:
        """Compute overall confidence based on pipeline consistency and data quality."""
        open_opps = [o for o in opportunities if o.get("status") not in ("won", "lost", "abandoned")]
        if not open_opps:
            return 0.0

        # Factor 1: Number of deals (more = more confident)
        deal_count_factor = min(len(open_opps) / 20.0, 1.0)

        # Factor 2: Pipeline value distribution (concentrated = less confident)
        values = [o.get("value", 0) for o in open_opps]
        total = sum(values) if values else 1
        max_single = max(values) if values else 0
        concentration = max_single / total if total > 0 else 1.0
        diversity_factor = 1.0 - concentration * 0.5

        # Factor 3: Historical data availability
        history_factor = min(len(self._history) / 4.0, 1.0)

        # Factor 4: Win rate consistency
        win_rate = combined.get("win_rate", 0.5)
        wr_factor = 1.0 - abs(win_rate - 0.5) * 0.4

        confidence = (deal_count_factor * 0.3 + diversity_factor * 0.2 +
                      history_factor * 0.25 + wr_factor * 0.25)
        return round(min(max(confidence, 0.0), 1.0), 2)
