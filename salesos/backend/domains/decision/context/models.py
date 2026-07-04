from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class DecisionFactor:
    """A single factor contributing to a decision context."""

    source_layer: str  # "fact", "knowledge", "measurement", "policy"
    source_domain: str  # "opportunity", "forecast", "analytics", "pipeline"
    key: str  # "stage_aging", "forecast_drop", "revenue_variance"
    value: Any = None
    label: str = ""
    severity: str = "info"  # "info", "warning", "critical"


@dataclass
class Policy:
    """A business policy that constrains or guides decisions."""

    id: str
    name: str
    description: str = ""
    rule: str = ""  # e.g. "if discount > 30% then requires executive approval"
    category: str = "approval"


@dataclass
class DecisionContext:
    """A snapshot of all relevant factors for making a decision at a point in time."""

    id: str
    tenant_id: str
    target_id: str  # opportunity_id, company_id, etc.
    target_type: str  # "opportunity", "company", "pipeline"
    factors: list[DecisionFactor] = field(default_factory=list)
    policies: list[Policy] = field(default_factory=list)
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def critical_factors(self) -> list[DecisionFactor]:
        return [f for f in self.factors if f.severity == "critical"]

    @property
    def warnings(self) -> list[DecisionFactor]:
        return [f for f in self.factors if f.severity == "warning"]

    @property
    def info(self) -> list[DecisionFactor]:
        return [f for f in self.factors if f.severity == "info"]

    def has_critical(self) -> bool:
        return len(self.critical_factors) > 0
