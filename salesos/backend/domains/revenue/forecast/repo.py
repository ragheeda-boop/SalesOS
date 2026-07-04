from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from .models import ForecastSnapshot


@dataclass
class ForecastKPIs:
    total_snapshots: int = 0
    latest_expected_revenue: float = 0.0
    latest_weighted_revenue: float = 0.0
    latest_confidence: float = 0.0
    forecast_accuracy: float = 0.0
    forecast_bias: float = 0.0


class ForecastRepository(ABC):

    @abstractmethod
    async def save(self, snapshot: ForecastSnapshot) -> ForecastSnapshot:
        ...

    @abstractmethod
    async def get(self, snapshot_id: str) -> ForecastSnapshot | None:
        ...

    @abstractmethod
    async def list_by_tenant(self, tenant_id: str, limit: int = 10) -> list[ForecastSnapshot]:
        ...

    @abstractmethod
    async def get_latest(self, tenant_id: str) -> ForecastSnapshot | None:
        ...

    @abstractmethod
    async def kpis(self, tenant_id: str) -> ForecastKPIs:
        ...
