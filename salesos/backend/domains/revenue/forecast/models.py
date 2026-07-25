from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ForecastScenario(Enum):
    COMMIT = "commit"
    BEST_CASE = "best_case"
    MOST_LIKELY = "most_likely"
    WORST_CASE = "worst_case"


class ForecastSnapshotStatus(Enum):
    CALCULATED = "calculated"
    FINALIZED = "finalized"


@dataclass
class ForecastExplanation:
    """Why a particular prediction has its value."""

    factor: str                    # "win_rate", "stage", "quote_status", "activity_signal"
    value: float = 0.0             # numerical contribution
    label: str = ""                # human-readable description
    source_id: str = ""            # which opportunity/quote/contract contributed
    source_type: str = ""          # "opportunity", "quote", "contract"


@dataclass
class ForecastLine:
    """A single prediction for a specific scope."""

    scenario: ForecastScenario
    expected_revenue: float = 0.0
    confidence: float = 0.0        # 0.0 - 1.0
    risk: float = 0.0              # 0.0 - 1.0
    weighted_revenue: float = 0.0
    explanations: list[ForecastExplanation] = field(default_factory=list)
    source_id: str = ""            # opportunity/quote/contract ID
    source_type: str = ""          # "opportunity", "quote", "contract"
    metadata: dict[str, str] = field(default_factory=dict)  # rep_id, region, product


@dataclass
class ForecastSnapshot:
    """An immutable forecast at a point in time."""

    id: str
    tenant_id: str
    title: str = ""
    horizon_months: int = 3
    status: ForecastSnapshotStatus = ForecastSnapshotStatus.CALCULATED
    lines: list[ForecastLine] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    finalized_at: datetime | None = None
    version: int = 1

    # ── Rollups ──

    @property
    def total_expected_revenue(self) -> float:
        return sum(l.expected_revenue for l in self.lines)

    @property
    def total_weighted_revenue(self) -> float:
        return sum(l.weighted_revenue for l in self.lines)

    @property
    def overall_confidence(self) -> float:
        if not self.lines:
            return 0.0
        return sum(l.confidence for l in self.lines) / len(self.lines)

    @property
    def overall_risk(self) -> float:
        if not self.lines:
            return 0.0
        return sum(l.risk for l in self.lines) / len(self.lines)

    def by_scenario(self, scenario: ForecastScenario) -> list[ForecastLine]:
        return [l for l in self.lines if l.scenario == scenario]

    def by_dimension(self, dimension: str, value: str) -> list[ForecastLine]:
        return [l for l in self.lines if l.metadata.get(dimension) == value]


@dataclass
class TimeSeriesDataPoint:
    """A single historical revenue data point for time-series forecasting."""

    date: datetime
    value: float
    rep_id: str = ""
    region: str = ""
    product: str = ""


@dataclass
class TimeSeriesForecast:
    """Result of a time-series linear regression forecast."""

    predicted_value: float = 0.0
    slope: float = 0.0
    intercept: float = 0.0
    r_squared: float = 0.0
    confidence_lower: float = 0.0
    confidence_upper: float = 0.0
    data_points_used: int = 0


@dataclass
class CombinedForecast:
    """Weighted combination of time-series and pipeline-based forecasts."""

    time_series_weight: float = 0.4
    pipeline_weight: float = 0.6
    time_series_value: float = 0.0
    pipeline_value: float = 0.0
    combined_value: float = 0.0
    confidence_lower: float = 0.0
    confidence_upper: float = 0.0
    method_confidence: float = 0.0


@dataclass
class ForecastBreakdown:
    """Revenue breakdown by a specific dimension (rep, region, product)."""

    dimension: str = ""         # "rep", "region", "product"
    value: str = ""             # the actual rep_id / region name / product name
    expected_revenue: float = 0.0
    weighted_revenue: float = 0.0
    confidence: float = 0.0
    line_count: int = 0
