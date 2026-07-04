from __future__ import annotations
from .models import AnalyticsSnapshot
from .repo import AnalyticsRepository


class InMemoryAnalyticsRepository(AnalyticsRepository):
    def __init__(self):
        self._snapshots: dict[str, AnalyticsSnapshot] = {}

    async def save(self, snapshot: AnalyticsSnapshot) -> AnalyticsSnapshot:
        self._snapshots[snapshot.id] = snapshot
        return snapshot

    async def get(self, snapshot_id: str) -> AnalyticsSnapshot | None:
        return self._snapshots.get(snapshot_id)

    async def list_by_tenant(self, tenant_id: str, limit: int = 20) -> list[AnalyticsSnapshot]:
        items = [s for s in self._snapshots.values() if s.tenant_id == tenant_id]
        items.sort(key=lambda s: s.generated_at, reverse=True)
        return items[:limit]

    async def get_latest(self, tenant_id: str) -> AnalyticsSnapshot | None:
        items = await self.list_by_tenant(tenant_id, 1)
        return items[0] if items else None
