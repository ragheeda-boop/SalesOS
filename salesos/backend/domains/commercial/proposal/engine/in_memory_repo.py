"""In-memory Proposal repository for testing and development."""

from __future__ import annotations

from datetime import datetime, timezone

from ..contracts.models import Proposal, ProposalStatus
from ..contracts.repository import ProposalKPIs, ProposalRepository


class InMemoryProposalRepository(ProposalRepository):

    def __init__(self):
        self._proposals: dict[str, Proposal] = {}

    async def save(self, proposal: Proposal) -> Proposal:
        self._proposals[proposal.id] = proposal
        return proposal

    async def get(self, proposal_id: str) -> Proposal | None:
        return self._proposals.get(proposal_id)

    async def get_by_opportunity(self, opportunity_id: str) -> list[Proposal]:
        return [p for p in self._proposals.values() if p.opportunity_id == opportunity_id]

    async def get_by_quote(self, quote_id: str) -> list[Proposal]:
        return [p for p in self._proposals.values() if p.quote_id == quote_id]

    async def list_by_tenant(self, tenant_id: str, status: ProposalStatus | None = None) -> list[Proposal]:
        items = [p for p in self._proposals.values() if p.tenant_id == tenant_id]
        if status:
            items = [p for p in items if p.status == status]
        return items

    async def kpis(self, tenant_id: str) -> ProposalKPIs:
        proposals = [p for p in self._proposals.values() if p.tenant_id == tenant_id]
        total = len(proposals)
        delivered = sum(1 for p in proposals if p.is_delivered)
        accepted = sum(1 for p in proposals if p.status == ProposalStatus.ACCEPTED)

        cycle_hours = 0.0
        cycle_count = 0
        for p in proposals:
            if p.accepted_at and p.created_at:
                diff = (p.accepted_at - p.created_at).total_seconds() / 3600
                cycle_hours += diff
                cycle_count += 1

        return ProposalKPIs(
            total_proposals=total,
            delivery_rate=round(delivered / total, 2) if total > 0 else 0.0,
            acceptance_rate=round(accepted / delivered, 2) if delivered > 0 else 0.0,
            average_cycle_hours=round(cycle_hours / cycle_count, 1) if cycle_count > 0 else 0.0,
            proposal_to_win_conversion=round(accepted / total, 2) if total > 0 else 0.0,
        )
