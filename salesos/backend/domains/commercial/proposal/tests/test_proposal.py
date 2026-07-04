"""Tests for Proposal Domain — communication layer, not commercial truth."""

from datetime import datetime, timezone

import pytest

from domains.commercial.proposal.contracts.models import (
    Proposal,
    ProposalSection,
    ProposalStatus,
    ProposalTemplate,
)
from domains.commercial.proposal.engine.in_memory_repo import (
    InMemoryProposalRepository,
)
from domains.commercial.proposal.engine.service import ProposalService


def test_proposal_template_default():
    tpl = ProposalTemplate.default()
    assert len(tpl.sections) == 5
    assert tpl.sections[2].type == "pricing_ref"


def test_proposal_quote_reference():
    """Proposal references Quote, never duplicates it."""
    p = Proposal(id="p1", tenant_id="t1", opportunity_id="opp-1", quote_id="q1", quote_revision=2)
    assert p.quote_id == "q1"
    assert p.quote_revision == 2


def test_proposal_is_editable():
    draft = Proposal(id="p1", tenant_id="t1", status=ProposalStatus.DRAFT)
    delivered = Proposal(id="p2", tenant_id="t1", status=ProposalStatus.DELIVERED)
    assert draft.is_editable
    assert not delivered.is_editable


def test_proposal_is_delivered():
    assert Proposal(id="p1", tenant_id="t1", status=ProposalStatus.DELIVERED).is_delivered
    assert Proposal(id="p2", tenant_id="t1", status=ProposalStatus.VIEWED).is_delivered
    assert not Proposal(id="p3", tenant_id="t1", status=ProposalStatus.DRAFT).is_delivered


@pytest.mark.asyncio
async def test_create_proposal():
    repo = InMemoryProposalRepository()
    service = ProposalService(repo)

    p = await service.create_proposal("t1", "opp-1", "q1", quote_revision=2, title="Annual Service Proposal")
    assert p.status == ProposalStatus.DRAFT
    assert p.quote_id == "q1"
    assert p.quote_revision == 2
    assert len(p.sections) == 5


@pytest.mark.asyncio
async def test_update_section():
    repo = InMemoryProposalRepository()
    service = ProposalService(repo)

    p = await service.create_proposal("t1", "opp-1", "q1")
    p = await service.update_section(p.id, 0, "We propose to deliver...", "نقترح تقديم...")
    assert p.sections[0].content == "We propose to deliver..."
    assert p.sections[0].content_ar == "نقترح تقديم..."


@pytest.mark.asyncio
async def test_full_lifecycle():
    repo = InMemoryProposalRepository()
    service = ProposalService(repo)

    # Create
    p = await service.create_proposal("t1", "opp-1", "q1")
    assert p.status == ProposalStatus.DRAFT

    # Update section
    p = await service.update_section(p.id, 1, "Deliverable A, B, C")

    # Approve
    p = await service.approve(p.id, "mgr-1")
    assert p.status == ProposalStatus.APPROVED

    # Deliver
    p = await service.deliver(p.id, method="email", url="https://salesos.io/p/123")
    assert p.status == ProposalStatus.DELIVERED
    assert p.delivery_url == "https://salesos.io/p/123"

    # Viewed
    p = await service.mark_viewed(p.id)
    assert p.status == ProposalStatus.VIEWED
    assert p.viewed_at is not None

    # Accept — this generates an event for the Rule Engine
    p = await service.accept(p.id)
    assert p.status == ProposalStatus.ACCEPTED
    assert p.accepted_at is not None


@pytest.mark.asyncio
async def test_reject():
    repo = InMemoryProposalRepository()
    service = ProposalService(repo)

    p = await service.create_proposal("t1", "opp-1", "q1")
    p = await service.approve(p.id, "mgr")
    p = await service.deliver(p.id)
    p = await service.reject(p.id, reason="Budget not approved")

    assert p.status == ProposalStatus.REJECTED
    assert p.is_terminal


@pytest.mark.asyncio
async def test_cannot_accept_before_delivery():
    repo = InMemoryProposalRepository()
    service = ProposalService(repo)

    p = await service.create_proposal("t1", "opp-1", "q1")
    with pytest.raises(ValueError, match="accept"):
        await service.accept(p.id)


@pytest.mark.asyncio
async def test_kpis():
    repo = InMemoryProposalRepository()
    service = ProposalService(repo)

    # Accepted proposal
    p1 = await service.create_proposal("t1", "opp-1", "q1")
    p1 = await service.approve(p1.id, "mgr")
    p1 = await service.deliver(p1.id)
    p1 = await service.mark_viewed(p1.id)
    p1 = await service.accept(p1.id)

    # Delivered but not accepted
    p2 = await service.create_proposal("t1", "opp-2", "q2")
    p2 = await service.approve(p2.id, "mgr")
    p2 = await service.deliver(p2.id)

    # Draft (not delivered)
    p3 = await service.create_proposal("t1", "opp-3", "q3")

    kpis = await service.kpis("t1")
    assert kpis.total_proposals == 3
    assert round(kpis.delivery_rate, 2) == 0.67
    assert kpis.acceptance_rate == 0.5
    assert round(kpis.proposal_to_win_conversion, 2) == 0.33


@pytest.mark.asyncio
async def test_proposal_references_quote_not_price():
    """Proposal should never contain pricing data directly."""
    p = await ProposalService(InMemoryProposalRepository()).create_proposal("t1", "opp-1", "q1")
    # No pricing fields on Proposal
    assert not hasattr(p, "grand_total")
    assert not hasattr(p, "subtotal")
    assert not hasattr(p, "lines")
