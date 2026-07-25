"""ForecastEngine — consumes commercial truths, produces predictions.

Pipeline stages:
1. Weighted Revenue (from Opportunity probability × value)
2. Activity Signals (recent activity boosts confidence)
3. Pipeline Velocity (stage duration affects risk)
4. Quote Status (approved quotes increase confidence)
5. Contract Status (signed contracts lock revenue)

Also supports:
- Time-series linear regression on historical data
- Combined (weighted average) forecast
- Confidence intervals based on data quality
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .models import (
    CombinedForecast, ForecastBreakdown, ForecastExplanation, ForecastLine,
    ForecastScenario, ForecastSnapshot, ForecastSnapshotStatus,
    TimeSeriesDataPoint, TimeSeriesForecast,
)


@dataclass
class CommercialInput:
    """Consumed facts — Forecast never modifies these."""
    opportunity_id: str = ""
    opportunity_value: float = 0.0
    opportunity_probability: float = 0.0
    opportunity_stage: str = ""
    has_recent_activity: bool = False
    days_in_stage: float = 0.0
    sla_days: int = 30
    quote_approved: bool = False
    quote_value: float = 0.0
    contract_signed: bool = False
    contract_value: float = 0.0
    historical_win_rate: float = 0.0
    rep_id: str = ""
    rep_name: str = ""
    region: str = ""
    product: str = ""


class ForecastEngine:
    """Pipeline of predictors. Each stage adds confidence, risk, or expected revenue."""

    def __init__(self):
        self._stages: list[str] = []

    def predict(self, inputs: list[CommercialInput], horizon_months: int = 3) -> ForecastSnapshot:
        lines: list[ForecastLine] = []

        for inp in inputs:
            explanations: list[ForecastExplanation] = []
            metadata: dict[str, str] = {}
            if inp.rep_id:
                metadata["rep_id"] = inp.rep_id
            if inp.region:
                metadata["region"] = inp.region
            if inp.product:
                metadata["product"] = inp.product

            # Stage 1: Weighted Revenue
            weighted = inp.opportunity_value * inp.opportunity_probability
            explanations.append(ForecastExplanation(
                factor="weighted_revenue", value=weighted,
                label=f"{inp.opportunity_probability:.0%} × {inp.opportunity_value:.0f}",
                source_id=inp.opportunity_id, source_type="opportunity",
            ))

            # Stage 2: Activity Signal
            activity_boost = 1.0
            if inp.has_recent_activity:
                activity_boost = 1.1  # 10% confidence boost
                explanations.append(ForecastExplanation(
                    factor="activity_signal", value=0.1,
                    label="Recent activity detected",
                    source_id=inp.opportunity_id, source_type="activity",
                ))

            # Stage 3: Pipeline Velocity (risk)
            stage_risk = 0.0
            if inp.sla_days > 0 and inp.days_in_stage > inp.sla_days:
                overdue_ratio = (inp.days_in_stage - inp.sla_days) / inp.sla_days
                stage_risk = min(overdue_ratio * 0.2, 0.5)  # up to 50% risk
                explanations.append(ForecastExplanation(
                    factor="stage_overdue", value=stage_risk,
                    label=f"{inp.days_in_stage:.0f}d in stage (SLA: {inp.sla_days}d)",
                    source_id=inp.opportunity_id, source_type="pipeline",
                ))

            # Stage 4: Quote Status
            quote_confidence = 0.0
            if inp.quote_approved:
                quote_confidence = 0.15
                explanations.append(ForecastExplanation(
                    factor="quote_approved", value=quote_confidence,
                    label="Quote approved",
                    source_id=inp.opportunity_id, source_type="quote",
                ))

            # Stage 5: Contract Status
            contract_confidence = 0.0
            if inp.contract_signed:
                contract_confidence = 0.25
                explanations.append(ForecastExplanation(
                    factor="contract_signed", value=contract_confidence,
                    label="Contract signed",
                    source_id=inp.opportunity_id, source_type="contract",
                ))

            # Calculate confidence and risk
            base_confidence = inp.opportunity_probability
            total_confidence = min(base_confidence * activity_boost + quote_confidence + contract_confidence, 1.0)
            total_risk = stage_risk + (1.0 - inp.historical_win_rate) * 0.3

            # Most Likely scenario
            expected = inp.opportunity_value * total_confidence * (1.0 - total_risk)
            lines.append(ForecastLine(
                scenario=ForecastScenario.MOST_LIKELY,
                expected_revenue=expected,
                confidence=round(total_confidence, 2),
                risk=round(min(total_risk, 1.0), 2),
                weighted_revenue=weighted,
                explanations=explanations,
                source_id=inp.opportunity_id, source_type="opportunity",
                metadata=metadata,
            ))

            # Commit scenario (conservative — only what's nearly certain)
            commit_conf = min(inp.opportunity_probability * 0.8, total_confidence)
            commit_expected = inp.opportunity_value * commit_conf
            lines.append(ForecastLine(
                scenario=ForecastScenario.COMMIT,
                expected_revenue=commit_expected,
                confidence=round(commit_conf, 2),
                risk=round(min(total_risk * 0.5, 1.0), 2),
                weighted_revenue=weighted * 0.8,
                source_id=inp.opportunity_id, source_type="opportunity",
                metadata=metadata,
            ))

            # Best Case (optimistic)
            best_conf = min(total_confidence * 1.1, 1.0)
            lines.append(ForecastLine(
                scenario=ForecastScenario.BEST_CASE,
                expected_revenue=inp.opportunity_value * best_conf,
                confidence=round(best_conf, 2),
                risk=round(total_risk * 0.3, 2),
                weighted_revenue=weighted * 1.2,
                source_id=inp.opportunity_id, source_type="opportunity",
                metadata=metadata,
            ))

            # Worst Case (conservative)
            worst_conf = max(inp.opportunity_probability * 0.5, total_confidence * 0.6)
            worst_expected = inp.opportunity_value * worst_conf * (1.0 - total_risk)
            lines.append(ForecastLine(
                scenario=ForecastScenario.WORST_CASE,
                expected_revenue=worst_expected,
                confidence=round(worst_conf, 2),
                risk=round(min(total_risk * 1.5, 1.0), 2),
                weighted_revenue=weighted * 0.5,
                source_id=inp.opportunity_id, source_type="opportunity",
                metadata=metadata,
            ))

        import uuid
        snapshot = ForecastSnapshot(
            id=str(uuid.uuid4()),
            tenant_id="batch",
            title=f"Forecast ({horizon_months}m horizon)",
            horizon_months=horizon_months,
            lines=lines,
            assumptions=[
                "Historical win rate applied",
                "Activity signal: 10% confidence boost",
                "Overdue stage: risk penalty up to 50%",
                "Approved quote: +15% confidence",
                "Signed contract: +25% confidence",
            ],
        )
        return snapshot

    def time_series_forecast(
        self,
        data_points: list[TimeSeriesDataPoint],
        horizon_months: int = 3,
    ) -> TimeSeriesForecast:
        """Simple linear regression on historical revenue data."""
        if len(data_points) < 2:
            return TimeSeriesForecast(data_points_used=len(data_points))

        sorted_data = sorted(data_points, key=lambda d: d.date)
        n = len(sorted_data)

        t0 = sorted_data[0].date
        xs: list[float] = []
        ys: list[float] = []
        for dp in sorted_data:
            days = (dp.date - t0).total_seconds() / 86400.0
            xs.append(days)
            ys.append(dp.value)

        mean_x = sum(xs) / n
        mean_y = sum(ys) / n

        ss_xy = sum((xs[i] - mean_x) * (ys[i] - mean_y) for i in range(n))
        ss_xx = sum((xs[i] - mean_x) ** 2 for i in range(n))

        if ss_xx == 0:
            return TimeSeriesForecast(
                predicted_value=mean_y,
                slope=0.0,
                intercept=mean_y,
                r_squared=0.0,
                confidence_lower=mean_y,
                confidence_upper=mean_y,
                data_points_used=n,
            )

        slope = ss_xy / ss_xx
        intercept = mean_y - slope * mean_x

        ss_res = sum((ys[i] - (slope * xs[i] + intercept)) ** 2 for i in range(n))
        ss_tot = sum((ys[i] - mean_y) ** 2 for i in range(n))
        r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        last_day = xs[-1]
        future_day = last_day + (horizon_months * 30)
        predicted = slope * future_day + intercept

        residuals = [ys[i] - (slope * xs[i] + intercept) for i in range(n)]
        mse = sum(r ** 2 for r in residuals) / max(n - 2, 1)
        std_err = math.sqrt(mse)
        margin = 1.96 * std_err
        if margin == 0.0:
            margin = abs(predicted) * 0.05

        data_confidence = min(n / 12, 1.0) * r_squared

        return TimeSeriesForecast(
            predicted_value=round(predicted, 2),
            slope=round(slope, 4),
            intercept=round(intercept, 2),
            r_squared=round(r_squared, 4),
            confidence_lower=round(predicted - margin, 2),
            confidence_upper=round(predicted + margin, 2),
            data_points_used=n,
        )

    def combined_forecast(
        self,
        inputs: list[CommercialInput],
        historical_data: list[TimeSeriesDataPoint],
        horizon_months: int = 3,
        ts_weight: float = 0.4,
        pipeline_weight: float = 0.6,
    ) -> CombinedForecast:
        """Weighted average of time-series and pipeline-based forecasts."""
        pipeline_snap = self.predict(inputs, horizon_months)
        pipeline_value = pipeline_snap.total_expected_revenue

        ts_result = self.time_series_forecast(historical_data, horizon_months)
        ts_value = ts_result.predicted_value

        combined = (ts_value * ts_weight) + (pipeline_value * pipeline_weight)

        lower = min(
            ts_result.confidence_lower * ts_weight + pipeline_value * pipeline_weight * 0.8,
            combined * 0.7,
        )
        upper = max(
            ts_result.confidence_upper * ts_weight + pipeline_value * pipeline_weight * 1.2,
            combined * 1.3,
        )

        method_confidence = ts_result.r_squared * ts_weight + pipeline_snap.overall_confidence * pipeline_weight

        return CombinedForecast(
            time_series_weight=ts_weight,
            pipeline_weight=pipeline_weight,
            time_series_value=round(ts_value, 2),
            pipeline_value=round(pipeline_value, 2),
            combined_value=round(combined, 2),
            confidence_lower=round(lower, 2),
            confidence_upper=round(upper, 2),
            method_confidence=round(method_confidence, 2),
        )

    def breakdown(
        self,
        snapshot: ForecastSnapshot,
        dimension: str,
    ) -> list[ForecastBreakdown]:
        """Aggregate forecast lines by a dimension (rep_id, region, product)."""
        groups: dict[str, list[ForecastLine]] = {}
        for line in snapshot.lines:
            key = line.metadata.get(dimension, "unknown")
            if key not in groups:
                groups[key] = []
            groups[key].append(line)

        result = []
        for key, lines in groups.items():
            most_likely = [l for l in lines if l.scenario == ForecastScenario.MOST_LIKELY]
            result.append(ForecastBreakdown(
                dimension=dimension,
                value=key,
                expected_revenue=round(sum(l.expected_revenue for l in most_likely), 2),
                weighted_revenue=round(sum(l.weighted_revenue for l in most_likely), 2),
                confidence=round(sum(l.confidence for l in most_likely) / len(most_likely), 2) if most_likely else 0.0,
                line_count=len(most_likely),
            ))
        result.sort(key=lambda b: b.expected_revenue, reverse=True)
        return result
