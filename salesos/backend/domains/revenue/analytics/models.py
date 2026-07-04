from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class MetricCategory(Enum):
    REVENUE = "revenue"
    PIPELINE = "pipeline"
    COMMERCIAL = "commercial"
    CUSTOMER = "customer"
    FORECAST = "forecast"
    OPERATIONAL = "operational"


@dataclass
class KPI:
    """Definition of a key performance indicator."""

    id: str
    name: str
    name_ar: str
    category: MetricCategory
    formula: str                    # e.g. "forecast_revenue / actual_revenue"
    description: str = ""
    unit: str = ""                  # "currency", "percent", "days", "count"
    higher_is_better: bool = True
    source_domains: list[str] = field(default_factory=list)


@dataclass
class KPIValue:
    """A single measured KPI value in a snapshot."""

    kpi_id: str
    value: float = 0.0
    previous_value: float = 0.0     # for trend comparison
    change: float = 0.0             # absolute change
    change_percent: float = 0.0     # relative change
    dimension: str = ""             # e.g. "monthly", "by_region", "by_rep"
    note: str = ""


@dataclass
class AnalyticsSnapshot:
    """An immutable measurement snapshot at a point in time."""

    id: str
    tenant_id: str
    period_start: datetime
    period_end: datetime
    values: list[KPIValue] = field(default_factory=list)
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: int = 1

    @property
    def by_category(self) -> dict[MetricCategory, list[KPIValue]]:
        from collections import defaultdict
        result: dict[MetricCategory, list[KPIValue]] = defaultdict(list)
        for v in self.values:
            # KPI metadata would need registry lookup
            result[MetricCategory.REVENUE].append(v)
        return result

    @property
    def total_kpis(self) -> int:
        return len(self.values)

    def get_value(self, kpi_id: str) -> KPIValue | None:
        for v in self.values:
            if v.kpi_id == kpi_id:
                return v
        return None
