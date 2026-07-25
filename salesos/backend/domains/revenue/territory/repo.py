from __future__ import annotations
from abc import ABC, abstractmethod

from .models import Territory


class TerritoryRepository(ABC):

    @abstractmethod
    async def save(self, territory: Territory) -> Territory:
        ...

    @abstractmethod
    async def get(self, territory_id: str) -> Territory | None:
        ...

    @abstractmethod
    async def delete(self, territory_id: str) -> bool:
        ...

    @abstractmethod
    async def list_by_tenant(
        self,
        tenant_id: str,
        rep_id: str | None = None,
        region: str | None = None,
        limit: int = 50,
    ) -> list[Territory]:
        ...

    @abstractmethod
    async def list_by_rep(self, tenant_id: str, rep_id: str) -> list[Territory]:
        ...

    @abstractmethod
    async def find_territory_for_account(self, tenant_id: str, account_id: str) -> Territory | None:
        ...
