"""Pipeline Forecast models — immutable snapshots, breakdowns, and trend tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class ForecastMethod(str, Enum):
    WEIGHTED_PIPELINE = "weighted_pipeline"
    HISTORICAL_VELOCITY = "historical_velocity"
    COMBINED = "combined"


@dataclass
class ForecastBreakdown:
    """Revenue forecast for a specific dimension (rep, region, product)."""

    dimension: str  # "rep", "region", "product", "total"
    label: str
    total_pipeline_value: float = 0.0
    weighted_value: float = 0.0
    historical_velocity_value: float = 0.0
    combined_value: float = 0.0
    opportunity_count: int = 0
    avg_deal_size: float = 0.0
    win_rate: float = 0.0

    @property
    def confidence_interval_lower(self) -> float:
        """Lower bound = combined * (1 - uncertainty)."""
        uncertainty = max(0.0, 1.0 - self.win_rate)
        return self.combined_value * max(0.0, 1.0 - uncertainty * 0.5)

    @property
    def confidence_interval_upper(self) -> float:
        """Upper bound = combined * (1 + upside potential)."""
        upside = self.win_rate * 0.3
        return self.combined_value * (1.0 + upside)


@dataclass
class ForecastSnapshot:
    """An immutable pipeline forecast at a point in time."""

    id: str
    tenant_id: str
    method: ForecastMethod = ForecastMethod.COMBINED
    title: str = ""
    period_start: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    period_end: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    horizon_months: int = 3
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Aggregate values
    total_pipeline_value: float = 0.0
    total_weighted: float = 0.0
    total_velocity: float = 0.0
    total_combined: float = 0.0
    overall_confidence: float = 0.0
    overall_win_rate: float = 0.0

    # Breakdowns
    by_rep: list[ForecastBreakdown] = field(default_factory=list)
    by_region: list[ForecastBreakdown] = field(default_factory=list)
    by_product: list[ForecastBreakdown] = field(default_factory=list)
    total: ForecastBreakdown | None = None

    # Confidence intervals
    ci_lower: float = 0.0
    ci_upper: float = 0.0

    @property
    def forecast_accuracy_range(self) -> str:
        """Human-readable accuracy range."""
        if self.total_combined == 0:
            return "N/A"
        lower_pct = (self.ci_lower / self.total_combined - 1.0) * 100
        upper_pct = (self.ci_upper / self.total_combined - 1.0) * 100
        return f"{lower_pct:+.1f}% to {upper_pct:+.1f}%"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "method": self.method.value,
            "title": self.title,
            "total_pipeline_value": self.total_pipeline_value,
            "total_weighted": self.total_weighted,
            "total_velocity": self.total_velocity,
            "total_combined": self.total_combined,
            "overall_confidence": self.overall_confidence,
            "overall_win_rate": self.overall_win_rate,
            "ci_lower": self.ci_lower,
            "ci_upper": self.ci_upper,
            "accuracy_range": self.forecast_accuracy_range,
            "by_rep": [b.__dict__ for b in self.by_rep],
            "by_region": [b.__dict__ for b in self.by_region],
            "by_product": [b.__dict__ for b in self.by_product],
            "generated_at": self.generated_at.isoformat(),
        }


@dataclass
class PipelineHistoricalPeriod:
    """A completed historical period for velocity calculation."""

    period_label: str  # e.g. "2026-Q1"
    period_start: datetime
    period_end: datetime
    total_deals: int = 0
    closed_won: int = 0
    closed_lost: int = 0
    total_revenue: float = 0.0
    avg_deal_value: float = 0.0
    avg_cycle_days: float = 0.0
    stage_durations: dict[str, float] = field(default_factory=dict)

    @property
    def win_rate(self) -> float:
        closed = self.closed_won + self.closed_lost
        return self.closed_won / closed if closed > 0 else 0.0

    @property
    def velocity(self) -> float:
        """Revenue per period."""
        return self.total_revenue

    @property
    def deals_per_period(self) -> float:
        return float(self.total_deals)
