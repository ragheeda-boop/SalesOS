"""Persisted contract lifecycle and tenant isolation on the non-bypass app role."""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.config import settings
from app.modules.identity.models import Tenant
from domains.commercial.contract.models import ContractStatus
from domains.commercial.contract.service import ContractService
from domains.commercial.infrastructure.postgres_repositories import PostgresContractRepository


@pytest.mark.asyncio
async def test_contract_lifecycle_is_persisted_and_tenant_scoped() -> None:
    test_url = make_url(settings.app_database_url).set(database="salesos_test")
    engine = create_async_engine(
        test_url, pool_pre_ping=True, connect_args={"command_timeout": 10}
    )
    async with engine.connect() as connection:
        outer = await connection.begin()
        assert await connection.scalar(text("SELECT current_database()")) == "salesos_test"
        role = await connection.execute(
            text("SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user")
        )
        assert role.one() == (False, False)
        session = AsyncSession(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        tenant_a = uuid.uuid4()
        tenant_b = uuid.uuid4()
        try:
            session.add_all(
                [
                    Tenant(id=tenant_a, name="Contracts Tenant A", slug=f"contract-a-{uuid.uuid4()}"),
                    Tenant(id=tenant_b, name="Contracts Tenant B", slug=f"contract-b-{uuid.uuid4()}"),
                ]
            )
            await session.flush()
            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(tenant_a)},
            )
            service = ContractService(PostgresContractRepository(session))
            contract = await service.create_contract(
                str(tenant_a), opportunity_id=str(uuid.uuid4()), quote_id=str(uuid.uuid4())
            )
            contract.title = "Annual service agreement"
            contract.effective_date = date(2026, 9, 22)
            contract.expiry_date = date(2027, 9, 21)
            contract.legal_terms = "Terms retained as contract text"
            contract = await PostgresContractRepository(session).save(contract)

            signed = await service.sign(contract.id, "Provider", "Customer")
            active = await service.activate(contract.id)
            assert signed.status is ContractStatus.SIGNED
            assert active.status is ContractStatus.ACTIVE
            reread = await service.get(contract.id)
            assert reread is not None
            assert reread.title == "Annual service agreement"
            assert reread.effective_date == date(2026, 9, 22)
            assert reread.legal_terms == "Terms retained as contract text"
            assert reread.status is ContractStatus.ACTIVE

            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(tenant_b)},
            )
            assert await service.get(contract.id) is None
            assert await PostgresContractRepository(session).list_by_tenant(str(tenant_a)) == []
        finally:
            await session.close()
            await outer.rollback()
    await engine.dispose()
