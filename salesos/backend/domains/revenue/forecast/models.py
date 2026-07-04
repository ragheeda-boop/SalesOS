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
