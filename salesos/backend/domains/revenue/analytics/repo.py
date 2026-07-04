from __future__ import annotations
from abc import ABC, abstractmethod
from .models import AnalyticsSnapshot


class AnalyticsRepository(ABC):
    @abstractmethod
    async def save(self, snapshot: AnalyticsSnapshot) -> AnalyticsSnapshot:
        ...

    @abstractmethod
    async def get(self, snapshot_id: str) -> AnalyticsSnapshot | None:
        ...

    @abstractmethod
    async def list_by_tenant(self, tenant_id: str, limit: int = 20) -> list[AnalyticsSnapshot]:
        ...

    @abstractmethod
    async def get_latest(self, tenant_id: str) -> AnalyticsSnapshot | None:
        ...
