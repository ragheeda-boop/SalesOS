"""Tenant isolation and idempotency proof for persisted account evidence."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.config import settings
from app.modules.identity.models import Tenant
from intelligence.account_evidence import persist_account_insight
from intelligence.account_signals import build_account_signals


@pytest.mark.asyncio
async def test_account_insight_is_idempotent_and_hidden_from_other_tenants() -> None:
    test_url = make_url(settings.app_database_url).set(database="salesos_test")
    engine = create_async_engine(test_url, pool_pre_ping=True, connect_args={"command_timeout": 10})
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
        tenant_a_id = uuid.uuid4()
        tenant_b_id = uuid.uuid4()
        try:
            session.add_all(
                [
                    Tenant(
                        id=tenant_a_id,
                        name="Evidence Tenant A",
                        slug=f"evidence-a-{uuid.uuid4()}",
                    ),
                    Tenant(
                        id=tenant_b_id,
                        name="Evidence Tenant B",
                        slug=f"evidence-b-{uuid.uuid4()}",
                    ),
                ]
            )
            await session.flush()
            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(tenant_a_id)},
            )

            account_signals = build_account_signals(
                total_opportunities=2,
                active_opportunities=1,
                won_deals=0,
                lost_deals=1,
                activity_count=1,
                days_since_activity=120,
            )
            facts = {
                "total_opportunities": 2,
                "active_opportunities": 1,
                "won_deals": 0,
                "lost_deals": 1,
                "activity_count": 1,
                "last_activity_at": "2026-05-01T10:00:00+00:00",
                "account_signals": account_signals,
            }

            first = await persist_account_insight(
                session,
                tenant_id=str(tenant_a_id),
                company_id="company-a",
                company_name="Evidence Company",
                facts=facts,
            )
            await session.flush()
            replay = await persist_account_insight(
                session,
                tenant_id=str(tenant_a_id),
                company_id="company-a",
                company_name="Evidence Company",
                facts=facts,
            )
            await session.flush()

            assert first["created"] is True
            assert replay["created"] is False
            assert replay["insight_id"] == first["insight_id"]
            assert first["evidence_count"] == 3
            evidence_count = await session.scalar(
                text("SELECT COUNT(*) FROM commercial_evidence_items WHERE insight_id = :id"),
                {"id": first["insight_id"]},
            )
            assert evidence_count == first["evidence_count"]

            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(tenant_b_id)},
            )
            assert (
                await session.scalar(
                    text("SELECT COUNT(*) FROM commercial_insights WHERE id = :id"),
                    {"id": first["insight_id"]},
                )
                == 0
            )
            assert (
                await session.scalar(
                    text("SELECT COUNT(*) FROM commercial_evidence_items WHERE insight_id = :id"),
                    {"id": first["insight_id"]},
                )
                == 0
            )
        finally:
            await session.close()
            await outer.rollback()
    await engine.dispose()
