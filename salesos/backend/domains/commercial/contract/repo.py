from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from .models import Contract, ContractStatus


@dataclass
class ContractKPIs:
    total_contracts: int = 0
    active_contracts: int = 0
    signed_rate: float = 0.0
    renewal_rate: float = 0.0
    expiring_soon: int = 0
    total_contract_value: float = 0.0


class ContractRepository(ABC):

    @abstractmethod
    async def save(self, contract: Contract) -> Contract:
        ...

    @abstractmethod
    async def get(self, contract_id: str) -> Contract | None:
        ...

    @abstractmethod
    async def get_by_opportunity(self, opportunity_id: str) -> list[Contract]:
        ...

    @abstractmethod
    async def get_by_quote(self, quote_id: str) -> list[Contract]:
        ...

    @abstractmethod
    async def list_by_tenant(self, tenant_id: str, status: ContractStatus | None = None) -> list[Contract]:
        ...

    @abstractmethod
    async def kpis(self, tenant_id: str, quote_values: dict[str, float] | None = None) -> ContractKPIs:
        ...
