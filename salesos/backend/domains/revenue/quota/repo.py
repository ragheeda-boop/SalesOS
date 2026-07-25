from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime

from .models import Quota, QuotaSnapshot


class QuotaRepository(ABC):

    @abstractmethod
    async def save(self, quota: Quota) -> Quota:
        ...

    @abstractmethod
    async def get(self, quota_id: str) -> Quota | None:
        ...

    @abstractmethod
    async def delete(self, quota_id: str) -> bool:
        ...

    @abstractmethod
    async def list_by_tenant(
        self,
        tenant_id: str,
        rep_id: str | None = None,
        period: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[Quota]:
        ...

    @abstractmethod
    async def list_by_rep(self, tenant_id: str, rep_id: str) -> list[Quota]:
        ...

    @abstractmethod
    async def get_active_quota(self, tenant_id: str, rep_id: str) -> Quota | None:
        ...

    @abstractmethod
    async def save_snapshot(self, snapshot: QuotaSnapshot) -> QuotaSnapshot:
        ...

    @abstractmethod
    async def list_snapshots(self, tenant_id: str, limit: int = 10) -> list[QuotaSnapshot]:
        ...
