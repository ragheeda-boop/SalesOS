"""SDK interfaces for commercial/revenue cross-domain boundary.

Commercial infrastructure depends on these interfaces instead of
importing directly from the Revenue domain (ISP + DIP).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


# ── Analytics data types ──


@dataclass
class KPIValue:
    """A single KPI measurement."""

    value: float = 0.0
    category: str = "revenue"
    label: str = ""
    trend: str = "stable"


@dataclass
class AnalyticsSnapshot:
    """Immutable analytics measurement snapshot."""

    id: str
    tenant_id: str
    period_start: datetime | None = None
    period_end: datetime | None = None
    kpis: dict[str, KPIValue] = field(default_factory=dict)
    insights: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ── Forecast data types ──


@dataclass
class ForecastExplanation:
    """Explanation for a forecast line."""

    factor: str = ""
    value: float = 0.0
    label: str = ""
    source_id: str = ""
    source_type: str = ""


@dataclass
class ForecastLine:
    """A single forecast prediction line."""

    scenario: str = ""
    expected_revenue: float = 0.0
    confidence: float = 0.0
    risk: float = 0.0
    weighted_revenue: float = 0.0
    explanations: list = field(default_factory=list)
    source_id: str = ""
    source_type: str = ""


@dataclass
class ForecastSnapshot:
    """Immutable forecast snapshot at a point in time."""

    id: str
    tenant_id: str
    title: str = ""
    horizon_months: int = 3
    status: str = "calculated"
    lines: list[ForecastLine] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    finalized_at: datetime | None = None
    version: int = 1
    total_expected_revenue: float = 0.0
    total_weighted_revenue: float = 0.0
    overall_confidence: float = 0.0
    overall_risk: float = 0.0


# ── Repository ABCs ──


class AnalyticsRepository(ABC):
    """Repository contract for analytics snapshots — consumed by commercial infra."""

    @abstractmethod
    async def save(self, snapshot: AnalyticsSnapshot) -> AnalyticsSnapshot:
        ...

    @abstractmethod
    async def get(self, snapshot_id: str) -> Optional[AnalyticsSnapshot]:
        ...

    @abstractmethod
    async def list_by_tenant(
        self, tenant_id: str, limit: int = 20
    ) -> list[AnalyticsSnapshot]:
        ...

    @abstractmethod
    async def get_latest(
        self, tenant_id: str
    ) -> Optional[AnalyticsSnapshot]:
        ...


class ForecastRepository(ABC):
    """Repository contract for forecast snapshots — consumed by commercial infra."""

    @abstractmethod
    async def save(self, snapshot: ForecastSnapshot) -> ForecastSnapshot:
        ...

    @abstractmethod
    async def get(self, snapshot_id: str) -> Optional[ForecastSnapshot]:
        ...

    @abstractmethod
    async def list_by_tenant(
        self, tenant_id: str, limit: int = 10
    ) -> list[ForecastSnapshot]:
        ...

    @abstractmethod
    async def get_latest(
        self, tenant_id: str
    ) -> Optional[ForecastSnapshot]:
        ...

    @abstractmethod
    async def kpis(self, tenant_id: str) -> Any:
        ...
