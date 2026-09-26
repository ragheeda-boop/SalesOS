"""ContractService.sign() never actually recorded who/whether a contract
was signed, and PostgresContractRepository.kpis() returned fake/wrong
numbers for every metric except the ones that happened to be zero.

Unlike reports 120/121/122 (StageEntry/Quote/Proposal), the Contract
domain contract and DB model are correctly aligned -- save()/get()/
_to_domain() were already correct when checked (report 123). The real
bugs here were found by tracing the service layer, the same way the
Proposal double-fetch bug was found:

- `ContractService.sign()` accepted `signed_by_provider`/
  `signed_by_customer` (strings -- who signed) but only forwarded them
  into the emitted event payload; `Contract.signed_by_provider`/
  `signed_by_customer` (datetime | None -- when signed) were never
  touched at all. Live and reachable at
  `POST /contracts/{contract_id}/sign`, whose own response serializes
  these two fields back to the caller -- every real signing request
  returned null for both, regardless of what was submitted.
- `PostgresContractRepository.kpis()` hardcoded `renewal_rate=0.85` and
  `total_contract_value=0.0` (both fake, ignoring the real
  `quote_values` argument), never set `signed_rate` at all (silently
  always 0.0), and computed `expiring_soon` as the count of
  already-`expired` contracts rather than signed contracts expiring
  within 90 days. Not reachable from any live router endpoint today
  (only a domain-level unit test exercises it), fixed for parity with
  the in-memory reference repository.
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest_asyncio
from sqlalchemy import text

from app.database import async_session, engine
from domains.commercial.contract.models import ContractStatus
from domains.commercial.contract.service import ContractService
from domains.commercial.infrastructure.postgres_repositories import (
    PostgresContractRepository,
)


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    """Report 118/121 safety net."""
    async with engine.connect() as conn:
        db_name = await conn.scalar(text("SELECT current_database()"))
    assert db_name != "salesos", (
        f"REFUSING: connected to {db_name!r} — this is the persistent "
        "local dev database, not a disposable/test one. Set "
        'APP_POSTGRES_PASSWORD="" (or APP_DATABASE_URL_OVERRIDE) to point '
        "app.database.engine at an ephemeral container before running "
        "this file."
    )
    yield
    await engine.dispose()


async def _seed_tenant(session, tenant_id: str) -> None:
    await session.execute(
        text("INSERT INTO tenants (id, name, slug) VALUES (:id, 'Contract Test', :slug)"),
        {"id": tenant_id, "slug": f"contract-test-{tenant_id[:8]}"},
    )


async def test_sign_persists_signed_at_timestamps_and_status():
    tenant_id = str(uuid.uuid4())

    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        await _seed_tenant(session, tenant_id)
        await session.commit()
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )

        service = ContractService(PostgresContractRepository(session))
        contract = await service.create_contract(tenant_id=tenant_id, opportunity_id="opp-1")
        assert contract.status == ContractStatus.DRAFT
        assert contract.signed_by_provider is None
        assert contract.signed_by_customer is None

        signed = await service.sign(contract.id, signed_by_provider="Alice", signed_by_customer="Bob")
        assert signed.status == ContractStatus.SIGNED
        assert signed.signed_by_provider is not None
        assert signed.signed_by_customer is not None

        row = (
            await session.execute(
                text(
                    "SELECT status, signed_by_provider, signed_by_customer "
                    "FROM commercial_contracts WHERE id = :id"
                ),
                {"id": contract.id},
            )
        ).one()
        assert row.status == "signed"
        assert row.signed_by_provider is not None
        assert row.signed_by_customer is not None

        await session.rollback()


async def test_kpis_mirrors_in_memory_reference_formulas():
    tenant_id = str(uuid.uuid4())

    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        await _seed_tenant(session, tenant_id)
        await session.commit()
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )

        service = ContractService(PostgresContractRepository(session))

        # Contract A: signed, expiring in 30 days (must count as expiring_soon).
        a = await service.create_contract(tenant_id=tenant_id, opportunity_id="opp-a", quote_id="quote-a")
        await service.sign(a.id, signed_by_provider="P", signed_by_customer="C")
        a_model = await service._repository.get(a.id)
        a_model.expiry_date = date.today() + timedelta(days=30)
        await service._repository.save(a_model)

        # Contract B: signed then renewed. `is_signed` only covers
        # SIGNED/ACTIVE/COMPLETED, so RENEWED does not count as "signed" --
        # it counts only in renewal_rate's numerator.
        b = await service.create_contract(tenant_id=tenant_id, opportunity_id="opp-b", quote_id="quote-b")
        await service.sign(b.id, signed_by_provider="P", signed_by_customer="C")
        b_signed = await service._repository.get(b.id)
        b_signed.status = ContractStatus.RENEWED
        await service._repository.save(b_signed)

        # Contract C: still draft — must not count toward signed/renewal/expiring_soon.
        await service.create_contract(tenant_id=tenant_id, opportunity_id="opp-c", quote_id="quote-c")

        kpis = await service.kpis(
            tenant_id, quote_values={"quote-a": 1000.0, "quote-b": 2000.0, "quote-c": 5000.0}
        )
        assert kpis.total_contracts == 3
        # Only A counts as `is_signed` (SIGNED/ACTIVE/COMPLETED) -- B moved
        # on to RENEWED, which `is_signed` does not include.
        assert kpis.signed_rate == round(1 / 3, 2)
        # renewed / signed = 1/1 -- B is the renewal of a signed contract.
        assert kpis.renewal_rate == 1.0
        # Only A is signed AND expiring within 90 days.
        assert kpis.expiring_soon == 1
        # Sums every contract's quote value, not just signed/renewed ones.
        assert kpis.total_contract_value == 8000.0

        await session.rollback()
