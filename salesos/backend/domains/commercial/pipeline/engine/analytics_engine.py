"""PipelineAnalyticsEngine — computes conversion rates, velocity, stage duration, win/loss rates."""

from __future__ import annotations

from typing import Any

from ..contracts.analytics_models import (
    ConversionRate,
    PipelineAnalyticsResult,
    PipelineValueOverTime,
    StageDuration,
    VelocityMetrics,
    WinLossMetrics,
)
from ..contracts.forecast_models import PipelineHistoricalPeriod


class PipelineAnalyticsEngine:
    """Computes comprehensive pipeline analytics from opportunity data."""

    STAGE_ORDER = ["prospecting", "qualification", "proposal", "negotiation", "closed_won", "closed_lost"]

    def __init__(self):
        self._history: list[PipelineHistoricalPeriod] = []

    def set_history(self, periods: list[PipelineHistoricalPeriod]) -> None:
        self._history = periods

    def compute(
        self,
        opportunities: list[dict[str, Any]],
        stage_entries: list[dict[str, Any]] | None = None,
        tenant_id: str = "",
    ) -> PipelineAnalyticsResult:
        """Compute full pipeline analytics from opportunity data."""
        stage_entries = stage_entries or []

        conversion_rates = self._compute_conversion_rates(opportunities, stage_entries)
        velocity = self._compute_velocity(opportunities, stage_entries)
        stage_durations = self._compute_stage_durations(stage_entries)
        value_over_time = self._compute_value_over_time(opportunities)
        win_loss = self._compute_win_loss(opportunities)

        active = [o for o in opportunities if o.get("status") not in ("won", "lost", "abandoned")]
        total_value = sum(o.get("value", 0) for o in active)
        weighted = sum(o.get("value", 0) * o.get("probability", 0) for o in active)

        overall_conv = 0.0
        if conversion_rates:
            # Overall = prospecting → closed_won
            for cr in conversion_rates:
                if cr.from_stage == "prospecting" and cr.to_stage == "closed_won":
                    overall_conv = cr.rate
                    break

        return PipelineAnalyticsResult(
            tenant_id=tenant_id,
            conversion_rates=conversion_rates,
            overall_conversion_rate=overall_conv,
            velocity=velocity,
            stage_durations=stage_durations,
            value_over_time=value_over_time,
            win_loss=win_loss,
            total_pipeline_value=total_value,
            total_weighted_value=weighted,
            active_deals=len(active),
        )

    def _compute_conversion_rates(
        self,
        opportunities: list[dict[str, Any]],
        stage_entries: list[dict[str, Any]],
    ) -> list[ConversionRate]:
        """Compute conversion rate between each consecutive pair of stages."""
        rates = []
        stage_order = self.STAGE_ORDER[:-1]  # exclude terminal stages

        # Method 1: From stage entries (more accurate)
        if stage_entries:
            for i in range(len(stage_order) - 1):
                from_stage = stage_order[i]
                to_stage = stage_order[i + 1]
                entered_from = sum(1 for e in stage_entries if e.get("stage") == from_stage)
                advanced_to = sum(
                    1 for e in stage_entries
                    if e.get("stage") == from_stage and e.get("next_stage") == to_stage
                )
                rate = advanced_to / entered_from if entered_from > 0 else 0.0
                rates.append(ConversionRate(
                    from_stage=from_stage, to_stage=to_stage,
                    rate=round(rate, 3), count=advanced_to, total=entered_from,
                ))
        else:
            # Method 2: From opportunity current stage (approximation)
            stage_counts = {}
            for opp in opportunities:
                stage = opp.get("stage", "unknown")
                stage_counts[stage] = stage_counts.get(stage, 0) + 1

            for i in range(len(stage_order) - 1):
                from_stage = stage_order[i]
                to_stage = stage_order[i + 1]
                from_count = stage_counts.get(from_stage, 0)
                to_count = stage_counts.get(to_stage, 0)
                # Approximate: assume deals at to_stage came from from_stage
                rate = to_count / from_count if from_count > 0 else 0.0
                rates.append(ConversionRate(
                    from_stage=from_stage, to_stage=to_stage,
                    rate=round(min(rate, 1.0), 3), count=to_count, total=from_count,
                ))

        return rates

    def _compute_velocity(
        self,
        opportunities: list[dict[str, Any]],
        stage_entries: list[dict[str, Any]],
    ) -> VelocityMetrics:
        """Compute velocity metrics from historical data and entries."""
        avg_days_per_stage: dict[str, float] = {}

        if stage_entries:
            for stage in self.STAGE_ORDER:
                durations = [
                    e.get("duration_days", 0)
                    for e in stage_entries
                    if e.get("stage") == stage and e.get("duration_days", 0) > 0
                ]
                if durations:
                    avg_days_per_stage[stage] = round(sum(durations) / len(durations), 1)

        # Overall cycle time from closed deals
        cycle_times = []
        for opp in opportunities:
            if opp.get("status") in ("won", "lost"):
                created = opp.get("created_at")
                closed = opp.get("closed_at") or opp.get("updated_at")
                if created and closed:
                    try:
                        from datetime import datetime
                        if isinstance(created, str):
                            created = datetime.fromisoformat(created.replace("Z", "+00:00"))
                        if isinstance(closed, str):
                            closed = datetime.fromisoformat(closed.replace("Z", "+00:00"))
                        days = (closed - created).total_seconds() / 86400
                        if days > 0:
                            cycle_times.append(days)
                    except (ValueError, TypeError):
                        pass

        avg_cycle = sum(cycle_times) / len(cycle_times) if cycle_times else 0.0
        fastest = min(cycle_times) if cycle_times else 0.0
        slowest = max(cycle_times) if cycle_times else 0.0

        # Supplement from history
        if self._history and not avg_days_per_stage:
            for period in self._history:
                for stage, days in period.stage_durations.items():
                    if stage not in avg_days_per_stage:
                        avg_days_per_stage[stage] = days

        return VelocityMetrics(
            avg_cycle_days=round(avg_cycle, 1),
            avg_days_per_stage=avg_days_per_stage,
            overall_cycle_time=round(avg_cycle, 1),
            fastest_close_days=round(fastest, 1),
            slowest_close_days=round(slowest, 1),
        )

    def _compute_stage_durations(self, stage_entries: list[dict[str, Any]]) -> list[StageDuration]:
        """Compute detailed stage duration statistics."""
        durations_by_stage: dict[str, list[float]] = {}
        for entry in stage_entries:
            stage = entry.get("stage", "")
            duration = entry.get("duration_days", 0)
            if stage and duration > 0:
                durations_by_stage.setdefault(stage, []).append(duration)

        results = []
        for stage in self.STAGE_ORDER:
            durations = durations_by_stage.get(stage, [])
            if not durations:
                continue
            sorted_d = sorted(durations)
            median_idx = len(sorted_d) // 2
            median = sorted_d[median_idx] if sorted_d else 0.0
            results.append(StageDuration(
                stage=stage,
                avg_days=round(sum(durations) / len(durations), 1),
                median_days=round(median, 1),
                min_days=round(min(durations), 1),
                max_days=round(max(durations), 1),
                sample_count=len(durations),
            ))
        return results

    def _compute_value_over_time(self, opportunities: list[dict[str, Any]]) -> list[PipelineValueOverTime]:
        """Compute monthly pipeline value snapshots."""
        monthly: dict[str, dict] = {}
        for opp in opportunities:
            created = opp.get("created_at", "")
            if isinstance(created, str) and len(created) >= 7:
                month = created[:7]  # "2026-01"
            else:
                month = "unknown"
            if month not in monthly:
                monthly[month] = {"value": 0, "weighted": 0, "count": 0, "new": 0, "closed": 0}
            entry = monthly[month]
            entry["count"] += 1
            entry["value"] += opp.get("value", 0)
            entry["weighted"] += opp.get("value", 0) * opp.get("probability", 0)
            if opp.get("status") in ("won", "lost"):
                entry["closed"] += 1
            else:
                entry["new"] += 1

        result = []
        for month in sorted(monthly.keys()):
            data = monthly[month]
            result.append(PipelineValueOverTime(
                month=month,
                total_value=data["value"],
                weighted_value=data["weighted"],
                deal_count=data["count"],
                new_deals=data["new"],
                closed_deals=data["closed"],
            ))
        return result

    def _compute_win_loss(self, opportunities: list[dict[str, Any]]) -> WinLossMetrics:
        """Compute win rate, loss rate, and stagnation rate."""
        won = sum(1 for o in opportunities if o.get("status") == "won")
        lost = sum(1 for o in opportunities if o.get("status") == "lost")
        active = [o for o in opportunities if o.get("status") not in ("won", "lost", "abandoned")]

        # Stagnation: active deals with no activity in 14+ days
        stagnant = 0
        for o in active:
            days_inactive = o.get("days_inactive", 0)
            if days_inactive >= 14:
                stagnant += 1

        total_closed = won + lost
        total_evaluated = total_closed + len(active)

        win_rate = won / total_closed if total_closed > 0 else 0.0
        loss_rate = lost / total_closed if total_closed > 0 else 0.0
        stagnation_rate = stagnant / len(active) if active else 0.0

        return WinLossMetrics(
            win_rate=round(win_rate, 3),
            loss_rate=round(loss_rate, 3),
            stagnation_rate=round(stagnation_rate, 3),
            total_won=won,
            total_lost=lost,
            total_stagnant=stagnant,
            total_active=len(active),
        )
