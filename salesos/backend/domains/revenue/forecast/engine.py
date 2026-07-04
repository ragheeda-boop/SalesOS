"""ForecastEngine — consumes commercial truths, produces predictions.

Pipeline stages:
1. Weighted Revenue (from Opportunity probability × value)
2. Activity Signals (recent activity boosts confidence)
3. Pipeline Velocity (stage duration affects risk)
4. Quote Status (approved quotes increase confidence)
5. Contract Status (signed contracts lock revenue)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .models import (
    ForecastExplanation, ForecastLine, ForecastScenario,
    ForecastSnapshot, ForecastSnapshotStatus,
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


class ForecastEngine:
    """Pipeline of predictors. Each stage adds confidence, risk, or expected revenue."""

    def __init__(self):
        self._stages: list[str] = []

    def predict(self, inputs: list[CommercialInput], horizon_months: int = 3) -> ForecastSnapshot:
        lines: list[ForecastLine] = []

        for inp in inputs:
            explanations: list[ForecastExplanation] = []

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
