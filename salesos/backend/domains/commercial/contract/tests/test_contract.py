"""Tests for Contract Domain — System of Legal Truth."""

from datetime import date, datetime, timezone

import pytest

from domains.commercial.contract.models import Contract, ContractObligation, ContractParty, ContractStatus, RenewalRule
from domains.commercial.contract.in_memory_repo import InMemoryContractRepository
from domains.commercial.contract.service import ContractService


def test_contract_references_quote():
    c = Contract(id="c1", tenant_id="t1", opportunity_id="opp-1", quote_id="q1", quote_revision=2)
    assert c.quote_id == "q1"; assert c.quote_revision == 2
    assert not hasattr(c, "grand_total"); assert not hasattr(c, "lines")


def test_contract_status_flow():
    assert ContractStatus.DRAFT.value == "draft"
    assert ContractStatus.ACTIVE.value == "active"


def test_is_signed():
    d = Contract(id="c1", tenant_id="t1", status=ContractStatus.DRAFT)
    s = Contract(id="c2", tenant_id="t1", status=ContractStatus.SIGNED)
    a = Contract(id="c3", tenant_id="t1", status=ContractStatus.ACTIVE)
    assert not d.is_signed; assert s.is_signed; assert a.is_signed


@pytest.mark.asyncio
async def test_create_contract():
    repo = InMemoryContractRepository(); svc = ContractService(repo)
    c = await svc.create_contract("t1", opportunity_id="opp-1", quote_id="q1", quote_revision=2)
    assert c.status == ContractStatus.DRAFT; assert c.quote_revision == 2


@pytest.mark.asyncio
async def test_sign_and_activate():
    repo = InMemoryContractRepository(); svc = ContractService(repo)
    c = await svc.create_contract("t1")
    c = await svc.sign(c.id); assert c.status == ContractStatus.SIGNED
    c = await svc.activate(c.id); assert c.status == ContractStatus.ACTIVE


@pytest.mark.asyncio
async def test_complete_and_terminate():
    repo = InMemoryContractRepository(); svc = ContractService(repo)
    c = await svc.create_contract("t1")
    c = await svc.sign(c.id); c = await svc.activate(c.id)
    c = await svc.complete(c.id); assert c.status == ContractStatus.COMPLETED

    c2 = await svc.create_contract("t1")
    c2 = await svc.sign(c2.id); c2 = await svc.activate(c2.id)
    c2 = await svc.terminate(c2.id, "Breach"); assert c2.status == ContractStatus.TERMINATED


@pytest.mark.asyncio
async def test_renewal():
    repo = InMemoryContractRepository(); svc = ContractService(repo)
    c = await svc.create_contract("t1")
    c = await svc.sign(c.id); c = await svc.activate(c.id)
    renewed = await svc.renew(c.id)
    assert renewed.id != c.id; assert renewed.status == ContractStatus.DRAFT
    # Verify original is marked renewed
    original = await svc.get(c.id); assert original.status == ContractStatus.RENEWED


@pytest.mark.asyncio
async def test_expiry():
    repo = InMemoryContractRepository(); svc = ContractService(repo)
    c = Contract(id="c1", tenant_id="t1", expiry_date=date(2020, 1, 1))
    await repo.save(c)
    expiring = await svc.check_expiry("t1")
    assert len(expiring) == 1
    expired = await svc.get("c1"); assert expired.status == ContractStatus.EXPIRED


@pytest.mark.asyncio
async def test_kpis():
    repo = InMemoryContractRepository(); svc = ContractService(repo)
    c1 = await svc.create_contract("t1", quote_id="q1")  # draft
    c2 = await svc.create_contract("t1", quote_id="q2")
    c2 = await svc.sign(c2.id); c2 = await svc.activate(c2.id)  # active
    c3 = await svc.create_contract("t1", quote_id="q3")
    c3 = await svc.sign(c3.id); c3 = await svc.activate(c3.id)
    c3 = await svc.complete(c3.id)  # completed

    kpis = await svc.kpis("t1", quote_values={"q1": 10000, "q2": 50000, "q3": 25000})
    assert kpis.total_contracts == 3
    assert kpis.active_contracts == 1
    assert kpis.total_contract_value == 85000


@pytest.mark.asyncio
async def test_no_pricing_on_contract():
    """Contract must not carry pricing fields — they belong to Quote."""
    c = await ContractService(InMemoryContractRepository()).create_contract("t1", quote_id="q1")
    assert not hasattr(c, "grand_total"); assert not hasattr(c, "subtotal")
    assert not hasattr(c, "total_discount"); assert not hasattr(c, "total_tax")
