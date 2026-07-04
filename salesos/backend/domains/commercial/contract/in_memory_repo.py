from __future__ import annotations
from datetime import date, timedelta
from .models import Contract, ContractStatus
from .repo import ContractKPIs, ContractRepository


class InMemoryContractRepository(ContractRepository):
    def __init__(self):
        self._contracts: dict[str, Contract] = {}

    async def save(self, contract: Contract) -> Contract:
        self._contracts[contract.id] = contract; return contract

    async def get(self, contract_id: str) -> Contract | None:
        return self._contracts.get(contract_id)

    async def get_by_opportunity(self, opportunity_id: str) -> list[Contract]:
        return [c for c in self._contracts.values() if c.opportunity_id == opportunity_id]

    async def get_by_quote(self, quote_id: str) -> list[Contract]:
        return [c for c in self._contracts.values() if c.quote_id == quote_id]

    async def list_by_tenant(self, tenant_id: str, status: ContractStatus | None = None) -> list[Contract]:
        items = [c for c in self._contracts.values() if c.tenant_id == tenant_id]
        if status: items = [c for c in items if c.status == status]
        return items

    async def kpis(self, tenant_id: str, quote_values: dict[str, float] | None = None) -> ContractKPIs:
        contracts = [c for c in self._contracts.values() if c.tenant_id == tenant_id]
        total = len(contracts)
        active = sum(1 for c in contracts if c.status == ContractStatus.ACTIVE)
        signed = sum(1 for c in contracts if c.is_signed)
        renewed = sum(1 for c in contracts if c.status == ContractStatus.RENEWED)
        expiring_soon = sum(1 for c in contracts if c.is_signed and c.expiry_date and c.expiry_date <= date.today() + timedelta(days=90))

        total_value = 0.0
        if quote_values:
            for c in contracts:
                total_value += quote_values.get(c.quote_id, 0.0)

        return ContractKPIs(
            total_contracts=total, active_contracts=active,
            signed_rate=round(signed/total, 2) if total > 0 else 0.0,
            renewal_rate=round(renewed/signed, 2) if signed > 0 else 0.0,
            expiring_soon=expiring_soon, total_contract_value=total_value,
        )
