"""Executive revenue and pipeline keep currencies separate in PostgreSQL."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.config import settings
from app.modules.executive.service import ExecutiveService
from app.modules.identity.models import Tenant
from domains.commercial.infrastructure.models import OpportunityModel


@pytest.mark.asyncio
async def test_executive_kpis_never_sum_mixed_currency_opportunities() -> None:
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
        tenant_id = uuid.uuid4()
        try:
            session.add(
                Tenant(id=tenant_id, name="Executive Currency Tenant", slug=f"exec-{uuid.uuid4()}")
            )
            await session.flush()
            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(tenant_id)},
            )
            session.add_all(
                [
                    OpportunityModel(
                        id=str(uuid.uuid4()), tenant_id=str(tenant_id), company_id=str(uuid.uuid4()),
                        name="SAR open", value=1000, currency="SAR", stage="qualification",
                        probability=0.5, owner_id="test", status="open",
                    ),
                    OpportunityModel(
                        id=str(uuid.uuid4()), tenant_id=str(tenant_id), company_id=str(uuid.uuid4()),
                        name="SAR won", value=2000, currency="SAR", stage="closed_won",
                        probability=1.0, owner_id="test", status="won",
                    ),
                    OpportunityModel(
                        id=str(uuid.uuid4()), tenant_id=str(tenant_id), company_id=str(uuid.uuid4()),
                        name="USD open", value=5000, currency="USD", stage="qualification",
                        probability=0.3, owner_id="test", status="open",
                    ),
                ]
            )
            await session.flush()

            service = ExecutiveService(session, str(tenant_id))
            revenue = await service.get_revenue()
            pipeline, _ = await service.get_pipeline()

            assert revenue.currency_consistent is False
            assert revenue.total_booked is None
            assert revenue.total_pipeline is None
            assert [(row.currency, row.total_pipeline) for row in revenue.by_currency] == [
                ("SAR", 3000.0),
                ("USD", 5000.0),
            ]
            assert pipeline.total_deals == 3
            assert pipeline.total_value is None
            assert pipeline.avg_deal_size is None
            assert [(row["currency"], row["total_value"]) for row in pipeline.by_currency] == [
                ("SAR", 3000.0),
                ("USD", 5000.0),
            ]
            assert {(row["stage"], row["currency"]) for row in pipeline.by_stage} == {
                ("qualification", "SAR"),
                ("qualification", "USD"),
            }
        finally:
            await session.close()
            await outer.rollback()
    await engine.dispose()
