"""Tests for Quote Domain — commercial agreement draft with revisions."""

from datetime import date, datetime, timedelta, timezone

import pytest

from domains.commercial.quote.contracts.models import (
    ApprovalLevel,
    ApprovalState,
    Quote,
    QuoteLine,
    QuoteRevision,
    QuoteStatus,
)
from domains.commercial.quote.engine.in_memory_repo import InMemoryQuoteRepository
from domains.commercial.quote.engine.service import QuoteService


# ── Models ──

def test_quote_line_totals():
    line = QuoteLine(id="l1", description="Item", quantity=2, unit_price=1000, discount_percent=10, tax_percent=15)
    assert line.line_total == 2000
    assert line.discount_amount == 200
    assert line.net_total == 1800
    assert line.tax_amount == 270
    assert line.grand_total == 2070


def test_quote_computed_totals():
    quote = Quote(id="q1", tenant_id="t1")
    quote.lines = [
        QuoteLine(id="l1", description="A", quantity=1, unit_price=1000, discount_percent=10),
        QuoteLine(id="l2", description="B", quantity=2, unit_price=500),
    ]
    assert quote.subtotal == 2000
    assert quote.total_discount == 100
    assert quote.grand_total == 1900


def test_quote_is_editable():
    draft = Quote(id="q1", tenant_id="t1", status=QuoteStatus.DRAFT)
    sent = Quote(id="q2", tenant_id="t1", status=QuoteStatus.SENT)
    accepted = Quote(id="q3", tenant_id="t1", status=QuoteStatus.ACCEPTED)

    assert draft.is_editable
    assert not sent.is_editable
    assert not accepted.is_editable


def test_quote_is_terminal():
    assert Quote(id="q1", tenant_id="t1", status=QuoteStatus.ACCEPTED).is_terminal
    assert Quote(id="q2", tenant_id="t1", status=QuoteStatus.REJECTED).is_terminal
    assert Quote(id="q3", tenant_id="t1", status=QuoteStatus.EXPIRED).is_terminal
    assert not Quote(id="q4", tenant_id="t1", status=QuoteStatus.DRAFT).is_terminal


def test_quote_has_expired():
    expired = Quote(id="q1", tenant_id="t1", valid_until=date.today() - timedelta(days=1))
    assert expired.has_expired

    valid = Quote(id="q2", tenant_id="t1", valid_until=date.today() + timedelta(days=30))
    assert not valid.has_expired

    no_expiry = Quote(id="q3", tenant_id="t1", valid_until=None)
    assert not no_expiry.has_expired


def test_approval_state():
    state = ApprovalState(level=ApprovalLevel.MANAGER, approved_by="u1", approved_at=datetime.now(timezone.utc))
    assert state.is_approved

    empty = ApprovalState()
    assert not empty.is_approved


# ── Service — Quote Lifecycle ──

@pytest.mark.asyncio
async def test_create_quote():
    repo = InMemoryQuoteRepository()
    service = QuoteService(repo)

    quote = await service.create_quote("t1", opportunity_id="opp-1", title="Q1")
    assert quote.status == QuoteStatus.DRAFT
    assert quote.version == 1
    assert quote.opportunity_id == "opp-1"


@pytest.mark.asyncio
async def test_add_line():
    repo = InMemoryQuoteRepository()
    service = QuoteService(repo)

    quote = await service.create_quote("t1")
    line = await service.add_line(quote.id, "خدمات استشارية", quantity=1, unit_price=5000)

    updated = await service.get(quote.id)
    assert len(updated.lines) == 1
    assert updated.subtotal == 5000


@pytest.mark.asyncio
async def test_cannot_add_line_to_non_draft():
    repo = InMemoryQuoteRepository()
    service = QuoteService(repo)

    quote = await service.create_quote("t1")
    await service.add_line(quote.id, "Item", unit_price=100)
    await service.submit_for_approval(quote.id)

    with pytest.raises(ValueError, match="not editable"):
        await service.add_line(quote.id, "New Item", unit_price=200)


@pytest.mark.asyncio
async def test_submit_empty_quote():
    repo = InMemoryQuoteRepository()
    service = QuoteService(repo)

    quote = await service.create_quote("t1")
    with pytest.raises(ValueError, match="empty"):
        await service.submit_for_approval(quote.id)


@pytest.mark.asyncio
async def test_full_lifecycle():
    repo = InMemoryQuoteRepository()
    service = QuoteService(repo)

    # Create
    quote = await service.create_quote("t1", opportunity_id="opp-1", title="Annual Service")
    await service.add_line(quote.id, "خدمات", quantity=12, unit_price=1000, discount_percent=5)

    # Submit for approval
    quote = await service.submit_for_approval(quote.id)
    assert quote.status == QuoteStatus.SUBMITTED

    # Approve
    quote = await service.approve(quote.id, approved_by="manager-1")
    assert quote.status == QuoteStatus.APPROVED
    assert quote.approval.is_approved

    # Send
    quote = await service.send(quote.id)
    assert quote.status == QuoteStatus.SENT

    # Accept
    quote = await service.accept(quote.id)
    assert quote.status == QuoteStatus.ACCEPTED
    assert quote.is_terminal


@pytest.mark.asyncio
async def test_reject():
    repo = InMemoryQuoteRepository()
    service = QuoteService(repo)

    quote = await service.create_quote("t1")
    await service.add_line(quote.id, "Item", unit_price=100)
    await service.submit_for_approval(quote.id)
    await service.approve(quote.id, "mgr")
    await service.send(quote.id)
    quote = await service.reject(quote.id, reason="Customer chose competitor")

    assert quote.status == QuoteStatus.REJECTED
    assert quote.is_terminal


@pytest.mark.asyncio
async def test_expired_quote():
    repo = InMemoryQuoteRepository()
    service = QuoteService(repo)

    # Create quote with past validity
    quote = await service.create_quote("t1", valid_until=date.today() - timedelta(days=1))
    await service.add_line(quote.id, "Item", unit_price=100)
    await service.submit_for_approval(quote.id)
    await service.approve(quote.id, "mgr")

    with pytest.raises(ValueError, match="expired"):
        await service.send(quote.id)


@pytest.mark.asyncio
async def test_revision():
    repo = InMemoryQuoteRepository()
    service = QuoteService(repo)

    quote = await service.create_quote("t1")
    await service.add_line(quote.id, "Original", unit_price=1000)
    quote = await service.submit_for_approval(quote.id)
    quote = await service.approve(quote.id, "mgr")

    # Revise — creates a new draft version
    quote = await service.revise(quote.id)
    assert quote.status == QuoteStatus.DRAFT
    assert quote.version == 2
    assert len(quote.revisions) == 1


# ── Revenue KPIs ──

@pytest.mark.asyncio
async def test_revenue_kpis():
    repo = InMemoryQuoteRepository()
    service = QuoteService(repo)

    # Accepted quote
    q1 = await service.create_quote("t1", opportunity_id="opp-1")
    await service.add_line(q1.id, "Service A", quantity=1, unit_price=10000)
    await service.submit_for_approval(q1.id)
    await service.approve(q1.id, "mgr")
    await service.send(q1.id)
    await service.accept(q1.id)

    # Rejected quote
    q2 = await service.create_quote("t1", opportunity_id="opp-2")
    await service.add_line(q2.id, "Service B", quantity=1, unit_price=5000)
    await service.submit_for_approval(q2.id)
    await service.approve(q2.id, "mgr")
    await service.send(q2.id)
    await service.reject(q2.id)

    # Open draft
    q3 = await service.create_quote("t1", opportunity_id="opp-3")
    await service.add_line(q3.id, "Service C", quantity=1, unit_price=15000)

    kpis = await service.revenue_kpis("t1")
    assert kpis.total_quotes == 3
    assert kpis.accepted_quotes == 1
    assert kpis.rejected_quotes == 1
    assert kpis.total_quote_value == 30000  # 10000 + 5000 + 15000


@pytest.mark.asyncio
async def test_immutability_after_accept():
    """Accepted quote must not be editable."""
    repo = InMemoryQuoteRepository()
    service = QuoteService(repo)

    quote = await service.create_quote("t1")
    await service.add_line(quote.id, "Item", unit_price=100)
    await service.submit_for_approval(quote.id)
    await service.approve(quote.id, "mgr")
    await service.send(quote.id)
    await service.accept(quote.id)

    with pytest.raises(ValueError, match="not editable"):
        await service.add_line(quote.id, "New", unit_price=200)
