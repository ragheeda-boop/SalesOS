from __future__ import annotations

from .models import Territory
from .repo import TerritoryRepository


class InMemoryTerritoryRepository(TerritoryRepository):
    def __init__(self):
        self._territories: dict[str, Territory] = {}

    async def save(self, territory: Territory) -> Territory:
        self._territories[territory.id] = territory
        return territory

    async def get(self, territory_id: str) -> Territory | None:
        return self._territories.get(territory_id)

    async def delete(self, territory_id: str) -> bool:
        if territory_id in self._territories:
            del self._territories[territory_id]
            return True
        return False

    async def list_by_tenant(
        self,
        tenant_id: str,
        rep_id: str | None = None,
        region: str | None = None,
        limit: int = 50,
    ) -> list[Territory]:
        items = [t for t in self._territories.values() if t.tenant_id == tenant_id]
        if rep_id:
            items = [t for t in items if t.rep_id == rep_id]
        if region:
            items = [t for t in items if t.region == region]
        items.sort(key=lambda t: t.created_at, reverse=True)
        return items[:limit]

    async def list_by_rep(self, tenant_id: str, rep_id: str) -> list[Territory]:
        return await self.list_by_tenant(tenant_id, rep_id=rep_id)

    async def find_territory_for_account(self, tenant_id: str, account_id: str) -> Territory | None:
        for t in self._territories.values():
            if t.tenant_id == tenant_id and account_id in t.account_ids:
                return t
        return None
