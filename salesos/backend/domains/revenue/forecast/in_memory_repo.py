from __future__ import annotations
from .models import ForecastSnapshot
from .repo import ForecastKPIs, ForecastRepository


class InMemoryForecastRepository(ForecastRepository):
    def __init__(self):
        self._snapshots: list[ForecastSnapshot] = []

    async def save(self, snapshot: ForecastSnapshot) -> ForecastSnapshot:
        for i, s in enumerate(self._snapshots):
            if s.id == snapshot.id:
                self._snapshots[i] = snapshot; return snapshot
        self._snapshots.append(snapshot); return snapshot

    async def get(self, snapshot_id: str) -> ForecastSnapshot | None:
        for s in self._snapshots:
            if s.id == snapshot_id: return s
        return None

    async def list_by_tenant(self, tenant_id: str, limit: int = 10) -> list[ForecastSnapshot]:
        items = [s for s in self._snapshots if s.tenant_id == tenant_id]
        items.sort(key=lambda s: s.created_at, reverse=True)
        return items[:limit]

    async def get_latest(self, tenant_id: str) -> ForecastSnapshot | None:
        items = await self.list_by_tenant(tenant_id, 1)
        return items[0] if items else None

    async def kpis(self, tenant_id: str) -> ForecastKPIs:
        items = await self.list_by_tenant(tenant_id)
        latest = items[0] if items else None
        return ForecastKPIs(
            total_snapshots=len(items),
            latest_expected_revenue=latest.total_expected_revenue if latest else 0.0,
            latest_weighted_revenue=latest.total_weighted_revenue if latest else 0.0,
            latest_confidence=latest.overall_confidence if latest else 0.0,
        )
