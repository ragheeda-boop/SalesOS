"""ProposalRepository — persistence for proposals and their KPIs."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from .models import Proposal, ProposalStatus


@dataclass
class ProposalKPIs:
    total_proposals: int = 0
    delivery_rate: float = 0.0
    acceptance_rate: float = 0.0
    average_cycle_hours: float = 0.0
    proposal_to_win_conversion: float = 0.0


class ProposalRepository(ABC):

    @abstractmethod
    async def save(self, proposal: Proposal) -> Proposal: ...

    @abstractmethod
    async def get(self, proposal_id: str) -> Proposal | None: ...

    @abstractmethod
    async def get_by_opportunity(self, opportunity_id: str) -> list[Proposal]: ...

    @abstractmethod
    async def get_by_quote(self, quote_id: str) -> list[Proposal]: ...

    @abstractmethod
    async def list_by_tenant(self, tenant_id: str, status: ProposalStatus | None = None) -> list[Proposal]: ...

    @abstractmethod
    async def kpis(self, tenant_id: str) -> ProposalKPIs: ...
