"""ProposalService — communication layer lifecycle.

Proposal references Quote revisions. It never duplicates commercial data.
Acceptance is an event the Rule Engine consumes — Proposal doesn't close opportunities.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from ..contracts.models import Proposal, ProposalSection, ProposalStatus, ProposalTemplate
from ..contracts.repository import ProposalKPIs, ProposalRepository


class ProposalService:

    def __init__(self, repository: ProposalRepository, event_bus: Any = None):
        self._repository = repository
        self._event_bus = event_bus

    async def _emit(self, event_type: str, tenant_id: str, data: dict[str, Any]) -> None:
        if not self._event_bus:
            return
        from sdk.events.base import DomainEvent
        event = DomainEvent(event_type=event_type, tenant_id=tenant_id,
                            aggregate_id=data.get("proposal_id", ""), data=data)
        event.event_type = event_type
        await self._event_bus.publish(event)

    async def create_proposal(
        self,
        tenant_id: str,
        opportunity_id: str,
        quote_id: str,
        quote_revision: int = 1,
        title: str = "",
        template: ProposalTemplate | None = None,
        created_by: str = "",
    ) -> Proposal:
        tpl = template or ProposalTemplate.default()
        proposal = Proposal(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            opportunity_id=opportunity_id,
            quote_id=quote_id,
            quote_revision=quote_revision,
            title=title or f"Proposal for {opportunity_id}",
            sections=[ProposalSection(**s.__dict__) for s in tpl.sections],
            template_id=tpl.id,
            created_by=created_by,
        )
        result = await self._repository.save(proposal)
        await self._emit("proposal.generated", tenant_id, {
            "proposal_id": proposal.id, "opportunity_id": opportunity_id,
            "quote_id": quote_id, "quote_revision": quote_revision,
        })
        return result

    async def update_section(self, proposal_id: str, section_index: int, content: str, content_ar: str = "") -> Proposal:
        proposal = await self._repository.get(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal {proposal_id} not found")
        if not proposal.is_editable:
            raise ValueError(f"Proposal {proposal_id} is not editable")

        if section_index < 0 or section_index >= len(proposal.sections):
            raise ValueError(f"Section index {section_index} out of range")
        proposal.sections[section_index].content = content
        proposal.sections[section_index].content_ar = content_ar
        proposal.updated_at = datetime.now(timezone.utc)
        return await self._repository.save(proposal)

    async def approve(self, proposal_id: str, approved_by: str) -> Proposal:
        return await self._transition(proposal_id, ProposalStatus.APPROVED, "proposal.approved", {
            "approved_by": approved_by,
        })

    async def deliver(self, proposal_id: str, method: str = "email", url: str = "") -> Proposal:
        proposal = await self._repository.get(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal {proposal_id} not found")
        if proposal.status != ProposalStatus.APPROVED:
            raise ValueError(f"Cannot deliver proposal in status: {proposal.status.value}")

        proposal.delivery_method = method
        proposal.delivery_url = url
        return await self._transition(proposal_id, ProposalStatus.DELIVERED, "proposal.delivered", {
            "method": method, "url": url,
        })

    async def mark_viewed(self, proposal_id: str) -> Proposal:
        proposal = await self._repository.get(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal {proposal_id} not found")

        proposal.viewed_at = datetime.now(timezone.utc)
        return await self._transition(proposal_id, ProposalStatus.VIEWED, "proposal.viewed")

    async def accept(self, proposal_id: str) -> Proposal:
        """Accept a proposal. This generates an event — Rule Engine should consume it."""
        proposal = await self._repository.get(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal {proposal_id} not found")
        if proposal.status not in (ProposalStatus.DELIVERED, ProposalStatus.VIEWED):
            raise ValueError(f"Cannot accept proposal in status: {proposal.status.value}")

        proposal.accepted_at = datetime.now(timezone.utc)
        result = await self._transition(proposal_id, ProposalStatus.ACCEPTED, "proposal.accepted", {
            "opportunity_id": proposal.opportunity_id,
            "quote_id": proposal.quote_id,
            "quote_revision": proposal.quote_revision,
        })
        return result

    async def reject(self, proposal_id: str, reason: str = "") -> Proposal:
        return await self._transition(proposal_id, ProposalStatus.REJECTED, "proposal.rejected", {
            "reason": reason,
        })

    async def expire(self, proposal_id: str) -> Proposal:
        return await self._transition(proposal_id, ProposalStatus.EXPIRED, "proposal.expired")

    async def _transition(self, proposal_id: str, to_status: ProposalStatus, event_type: str, extra: dict | None = None) -> Proposal:
        proposal = await self._repository.get(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal {proposal_id} not found")
        proposal.status = to_status
        proposal.updated_at = datetime.now(timezone.utc)
        result = await self._repository.save(proposal)
        data = {"proposal_id": proposal_id, "status": to_status.value, **(extra or {})}
        await self._emit(event_type, proposal.tenant_id, data)
        return result

    async def get(self, proposal_id: str) -> Proposal | None:
        return await self._repository.get(proposal_id)

    async def get_by_opportunity(self, opportunity_id: str) -> list[Proposal]:
        return await self._repository.get_by_opportunity(opportunity_id)

    async def kpis(self, tenant_id: str) -> ProposalKPIs:
        return await self._repository.kpis(tenant_id)
