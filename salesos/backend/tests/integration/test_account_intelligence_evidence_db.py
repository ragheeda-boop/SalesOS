"""CRM-grounded account signals and idempotent evidence snapshots on PostgreSQL."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.config import settings
from app.modules.company.models import Company
from app.modules.gtm.account_intelligence_router import (
    get_account_intelligence,
    record_account_intelligence_evidence,
)
from app.modules.gtm.evidence_router import list_evidence_insights
from app.modules.identity.models import Tenant
from domains.commercial.infrastructure.models import OpportunityModel


@pytest.mark.asyncio
async def test_account_snapshot_uses_tenant_crm_facts_and_persists_idempotent_evidence() -> None:
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
        other_tenant_id = uuid.uuid4()
        company_id = uuid.uuid4()
        now = datetime.now(UTC)
        try:
            session.add_all(
                [
                    Tenant(
                        id=tenant_id,
                        name="Account Intel Tenant",
                        slug=f"account-intel-{uuid.uuid4()}",
                    ),
                    Tenant(
                        id=other_tenant_id,
                        name="Other Account Tenant",
                        slug=f"other-account-{uuid.uuid4()}",
                    ),
                ]
            )
            await session.flush()
            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(tenant_id)},
            )
            session.add(
                Company(
                    id=company_id,
                    tenant_id=tenant_id,
                    name_ar="شركة اختبارية",
                    name_en="Test Account",
                    industry="technology",
                    city="Riyadh",
                    cr_number=None,
                    status="active",
                )
            )
            session.add_all(
                [
                    OpportunityModel(
                        id=str(uuid.uuid4()),
                        tenant_id=str(tenant_id),
                        company_id=str(company_id),
                        name="Open opportunity",
                        value=20000,
                        currency="SAR",
                        stage="qualification",
                        probability=0.4,
                        owner_id="test-owner",
                        status="open",
                    ),
                    OpportunityModel(
                        id=str(uuid.uuid4()),
                        tenant_id=str(tenant_id),
                        company_id=str(company_id),
                        name="Won opportunity",
                        value=10000,
                        won_amount=10000,
                        currency="SAR",
                        stage="closed_won",
                        probability=1.0,
                        owner_id="test-owner",
                        status="won",
                    ),
                ]
            )
            for days_ago in (5, 30, 120):
                await session.execute(
                    text(
                        "INSERT INTO activity_records "
                        "(id, actor, action, entity_type, entity_id, tenant_id, timestamp) "
                        "VALUES (:id, 'test', 'meeting_completed', 'company', :company_id, "
                        ":tenant_id, :timestamp)"
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "company_id": str(company_id),
                        "tenant_id": str(tenant_id),
                        "timestamp": now - timedelta(days=days_ago),
                    },
                )
            await session.flush()

            snapshot = await get_account_intelligence(
                str(company_id), tenant_id=str(tenant_id), db=session, _rbac=None
            )
            assert snapshot["company_name"] == "Test Account"
            assert snapshot["total_opportunities"] == 2
            assert snapshot["active_opportunities"] == 1
            assert snapshot["won_deals"] == 1
            assert snapshot["activity_count"] == 3
            assert snapshot["engagement_trend"]["trend"] == "improving"
            assert snapshot["method"] == "persisted_crm_records_with_explainable_rules"
            assert "health_score" not in snapshot
            assert snapshot["mutated_crm"] is False

            first = await record_account_intelligence_evidence(
                str(company_id), tenant_id=str(tenant_id), db=session, _rbac=None
            )
            second = await record_account_intelligence_evidence(
                str(company_id), tenant_id=str(tenant_id), db=session, _rbac=None
            )
            assert first["created"] is True
            assert second["created"] is False
            assert first["insight_id"] == second["insight_id"]
            assert first["evidence_count"] > 0

            read_back = await list_evidence_insights(
                page=1,
                page_size=25,
                target_type="company",
                target_id=str(company_id),
                category="account_health",
                tenant_id=str(tenant_id),
                db=session,
                _rbac=None,
            )
            assert read_back["total"] == 1
            assert len(read_back["items"][0]["evidence_items"]) == first["evidence_count"]
            assert read_back["items"][0]["evidence_items"][0]["source_domain"]

            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(other_tenant_id)},
            )
            other_tenant_read = await list_evidence_insights(
                page=1,
                page_size=25,
                target_type="company",
                target_id=str(company_id),
                category="account_health",
                tenant_id=str(other_tenant_id),
                db=session,
                _rbac=None,
            )
            assert other_tenant_read["total"] == 0

            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(tenant_id)},
            )
            counts = await session.execute(
                text(
                    "SELECT (SELECT COUNT(*) FROM commercial_insights WHERE tenant_id = :tenant_id), "
                    "(SELECT COUNT(*) FROM commercial_evidence_items WHERE tenant_id = :tenant_id)"
                ),
                {"tenant_id": str(tenant_id)},
            )
            insight_count, evidence_count = counts.one()
            assert insight_count == 1
            assert evidence_count == first["evidence_count"]
            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(tenant_id)},
            )
            unchanged = await session.scalar(
                text("SELECT name_en FROM companies WHERE id = :company_id"),
                {"company_id": company_id},
            )
            assert unchanged == "Test Account"
        finally:
            await session.close()
            await outer.rollback()
    await engine.dispose()
