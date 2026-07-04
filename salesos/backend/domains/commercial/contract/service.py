from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any

from .models import Contract, ContractObligation, ContractParty, ContractStatus, RenewalRule
from .repo import ContractKPIs, ContractRepository


class ContractService:
    def __init__(self, repository: ContractRepository, event_bus: Any = None):
        self._repository = repository; self._event_bus = event_bus

    async def _emit(self, event_type: str, tenant_id: str, data: dict[str, Any]) -> None:
        if not self._event_bus: return
        from sdk.events.base import DomainEvent
        event = DomainEvent(event_type=event_type, tenant_id=tenant_id, aggregate_id=data.get("contract_id", ""), data=data)
        event.event_type = event_type; await self._event_bus.publish(event)

    async def create_contract(self, tenant_id: str, opportunity_id: str = "", quote_id: str = "", quote_revision: int = 1) -> Contract:
        c = Contract(id=str(uuid.uuid4()), tenant_id=tenant_id, opportunity_id=opportunity_id, quote_id=quote_id, quote_revision=quote_revision)
        result = await self._repository.save(c)
        await self._emit("contract.created", tenant_id, {"contract_id": c.id, "opportunity_id": opportunity_id, "quote_id": quote_id})
        return result

    async def sign(self, contract_id: str, signed_by_provider: str = "", signed_by_customer: str = "") -> Contract:
        return await self._transition(contract_id, ContractStatus.SIGNED, "contract.signed", {"provider": signed_by_provider, "customer": signed_by_customer})

    async def activate(self, contract_id: str) -> Contract:
        return await self._transition(contract_id, ContractStatus.ACTIVE, "contract.activated")

    async def complete(self, contract_id: str) -> Contract:
        return await self._transition(contract_id, ContractStatus.COMPLETED, "contract.completed")

    async def terminate(self, contract_id: str, reason: str = "") -> Contract:
        return await self._transition(contract_id, ContractStatus.TERMINATED, "contract.terminated", {"reason": reason})

    async def renew(self, contract_id: str) -> Contract:
        c = await self._repository.get(contract_id)
        if not c: raise ValueError(f"Contract {contract_id} not found")
        if not c.renewal.auto_renew and c.renewal.max_renewals > 0:
            pass
        c.status = ContractStatus.RENEWED
        c.updated_at = datetime.now(timezone.utc)
        result = await self._repository.save(c)
        await self._emit("contract.renewed", c.tenant_id, {"contract_id": contract_id, "version": c.version})
        # Create new contract as renewal
        new_c = Contract(id=str(uuid.uuid4()), tenant_id=c.tenant_id, opportunity_id=c.opportunity_id,
                         quote_id=c.quote_id, quote_revision=c.quote_revision, title=c.title,
                         parties=list(c.parties), renewal=c.renewal, legal_terms=c.legal_terms,
                         governing_law=c.governing_law, effective_date=c.expiry_date,
                         notes=f"Renewal of {contract_id}")
        return await self._repository.save(new_c)

    async def check_expiry(self, tenant_id: str) -> list[dict]:
        contracts = await self._repository.list_by_tenant(tenant_id)
        expiring = []
        for c in contracts:
            if c.is_expired and not c.is_terminal:
                c.status = ContractStatus.EXPIRED
                await self._repository.save(c)
                await self._emit("contract.expired", tenant_id, {"contract_id": c.id})
                expiring.append({"contract_id": c.id, "expiry_date": str(c.expiry_date)})
        return expiring

    async def _transition(self, contract_id: str, to: ContractStatus, event: str, extra: dict | None = None) -> Contract:
        c = await self._repository.get(contract_id)
        if not c: raise ValueError(f"Contract {contract_id} not found")
        c.status = to; c.updated_at = datetime.now(timezone.utc)
        result = await self._repository.save(c)
        await self._emit(event, c.tenant_id, {"contract_id": contract_id, **(extra or {})})
        return result

    async def get(self, contract_id: str) -> Contract | None:
        return await self._repository.get(contract_id)

    async def kpis(self, tenant_id: str, quote_values: dict[str, float] | None = None) -> ContractKPIs:
        return await self._repository.kpis(tenant_id, quote_values)
