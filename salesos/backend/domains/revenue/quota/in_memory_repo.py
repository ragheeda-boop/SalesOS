from __future__ import annotations
from datetime import timezone
from typing import Any

from .models import Quota, QuotaSnapshot
from .repo import QuotaRepository


class InMemoryQuotaRepository(QuotaRepository):
    def __init__(self):
        self._quotas: dict[str, Quota] = {}
        self._snapshots: list[QuotaSnapshot] = []

    async def save(self, quota: Quota) -> Quota:
        self._quotas[quota.id] = quota
        return quota

    async def get(self, quota_id: str) -> Quota | None:
        return self._quotas.get(quota_id)

    async def delete(self, quota_id: str) -> bool:
        if quota_id in self._quotas:
            del self._quotas[quota_id]
            return True
        return False

    async def list_by_tenant(
        self,
        tenant_id: str,
        rep_id: str | None = None,
        period: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[Quota]:
        items = [q for q in self._quotas.values() if q.tenant_id == tenant_id]
        if rep_id:
            items = [q for q in items if q.rep_id == rep_id]
        if period:
            items = [q for q in items if q.period.value == period]
        if status:
            items = [q for q in items if q.status.value == status]
        items.sort(key=lambda q: q.created_at, reverse=True)
        return items[:limit]

    async def list_by_rep(self, tenant_id: str, rep_id: str) -> list[Quota]:
        return await self.list_by_tenant(tenant_id, rep_id=rep_id)

    async def get_active_quota(self, tenant_id: str, rep_id: str) -> Quota | None:
        from .models import QuotaStatus
        now = __import__("datetime").datetime.now(timezone.utc)
        items = [
            q for q in self._quotas.values()
            if q.tenant_id == tenant_id
            and q.rep_id == rep_id
            and q.status == QuotaStatus.ACTIVE
            and q.start_date <= now <= q.end_date
        ]
        return items[0] if items else None

    async def save_snapshot(self, snapshot: QuotaSnapshot) -> QuotaSnapshot:
        self._snapshots.append(snapshot)
        return snapshot

    async def list_snapshots(self, tenant_id: str, limit: int = 10) -> list[QuotaSnapshot]:
        items = [s for s in self._snapshots if s.tenant_id == tenant_id]
        items.sort(key=lambda s: s.created_at, reverse=True)
        return items[:limit]
