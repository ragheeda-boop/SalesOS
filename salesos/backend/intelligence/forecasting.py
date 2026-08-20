"""Forecasting Intelligence — Commit/Best Case/Pipeline/Risk from durable data.

P2-5: Reads from Product Core facts (opportunities, pipeline) and produces
forecast categories with confidence levels. No LLM dependency.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ForecastCategory:
    """A single forecast category with evidence."""
    category: str               # commit / best_case / pipeline / risk
    amount: float
    deal_count: int
    confidence: float           # 0.0 - 1.0
    evidence: list[str] = field(default_factory=list)


@dataclass
class ForecastSummary:
    """Complete forecast summary with all categories."""
    commit: ForecastCategory
    best_case: ForecastCategory
    pipeline: ForecastCategory
    risk: ForecastCategory
    total_pipeline: float = 0.0
    coverage_ratio: float = 0.0
    weighted_average: float = 0.0


class ForecastingService:
    """Produces Commit/Best Case/Pipeline/Risk forecasts from durable Product Core data."""

    def __init__(self):
        pass

    def compute_forecast(
        self,
        opportunities: list[dict],
        target_amount: float = 0.0,
    ) -> ForecastSummary:
        """Compute forecast categories from opportunity data."""
        total = sum(o.get("value", 0.0) for o in opportunities)
        weighted = sum(o.get("value", 0.0) * o.get("probability", 0.0) for o in opportunities)

        # Commit: deals with probability >= 0.8 or status won
        commit_deals = [o for o in opportunities if o.get("probability", 0) >= 0.8 or o.get("status") == "won"]
        commit_amount = sum(o.get("value", 0.0) for o in commit_deals)

        # Best case: deals with probability >= 0.5
        best_deals = [o for o in opportunities if o.get("probability", 0) >= 0.5]
        best_amount = sum(o.get("value", 0.0) for o in best_deals)

        # Pipeline: all open deals
        pipeline_deals = [o for o in opportunities if o.get("status") not in ("won", "lost")]
        pipeline_amount = sum(o.get("value", 0.0) for o in pipeline_deals)

        # Risk: deals with probability < 0.3 or stalled > 30 days
        risk_deals = [o for o in opportunities if o.get("probability", 0) < 0.3 or o.get("days_in_stage", 0) > 30]
        risk_amount = sum(o.get("value", 0.0) for o in risk_deals)

        coverage = pipeline_amount / max(commit_amount, 1.0)

        commit = ForecastCategory(
            category="commit", amount=commit_amount,
            deal_count=len(commit_deals),
            confidence=min(1.0, 0.7 + len(commit_deals) * 0.05),
            evidence=[f"{len(commit_deals)} deals with probability >= 80%"],
        )
        best_case = ForecastCategory(
            category="best_case", amount=best_amount,
            deal_count=len(best_deals),
            confidence=min(1.0, 0.5 + len(best_deals) * 0.05),
            evidence=[f"{len(best_deals)} deals with probability >= 50%"],
        )
        pipeline = ForecastCategory(
            category="pipeline", amount=pipeline_amount,
            deal_count=len(pipeline_deals),
            confidence=min(1.0, 0.3 + len(pipeline_deals) * 0.03),
            evidence=[f"{len(pipeline_deals)} open deals in pipeline"],
        )
        risk = ForecastCategory(
            category="risk", amount=risk_amount,
            deal_count=len(risk_deals),
            confidence=min(1.0, 0.6 + len(risk_deals) * 0.05),
            evidence=[f"{len(risk_deals)} deals at risk (low probability or stalled)"],
        )

        return ForecastSummary(
            commit=commit,
            best_case=best_case,
            pipeline=pipeline,
            risk=risk,
            total_pipeline=total,
            coverage_ratio=coverage,
            weighted_average=weighted,
        )
