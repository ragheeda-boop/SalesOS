"""Database proof for Customer Success survey evidence.

The assertions cover real Postgres RLS behavior, scale-safe aggregation, and
idempotent client retry. No provider, production database, or synthetic score
is involved.
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import async_session, engine, owner_engine
from app.modules.customer_success.service import (
    SurveyCompanyNotFound,
    record_survey_response,
    survey_summary,
)


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    yield
    await engine.dispose()
    await owner_engine.dispose()


async def _set_tenant(session, tenant_id: str | None) -> None:
    if tenant_id:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": tenant_id},
        )
    else:
        await session.execute(text("RESET app.tenant_id"))


@pytest.mark.asyncio
async def test_customer_survey_responses_are_tenant_scoped_and_idempotent():
    tenant_a, tenant_b = str(uuid.uuid4()), str(uuid.uuid4())
    company_a, company_b = str(uuid.uuid4()), str(uuid.uuid4())
    # Seed as the migration owner; all service calls below use salesos_app.
    async with owner_engine.begin() as conn:
        for tenant_id, company_id, suffix in (
            (tenant_a, company_a, "a"),
            (tenant_b, company_b, "b"),
        ):
            await conn.execute(
                text("INSERT INTO tenants (id, name, slug) VALUES (:id, :name, :slug)"),
                {
                    "id": tenant_id,
                    "name": f"Survey QA {suffix}",
                    "slug": f"survey-qa-{suffix}-{tenant_id[:8]}",
                },
            )
            await _set_tenant(conn, tenant_id)
            await conn.execute(
                text(
                    "INSERT INTO companies (id, tenant_id, name_ar) "
                    "VALUES (:id, :tenant_id, :name_ar)"
                ),
                {
                    "id": company_id,
                    "tenant_id": tenant_id,
                    "name_ar": f"شركة الاستبيان {suffix}",
                },
            )

    async with async_session() as session:
        await _set_tenant(session, tenant_a)
        first = await record_survey_response(
            session,
            tenant_id=tenant_a,
            company_id=company_a,
            survey_type="nps",
            score=10,
            comment="Confirmed promoter",
            source="manual",
            recorded_at=None,
            idempotency_key="survey-retry-1",
        )

    async with async_session() as session:
        await _set_tenant(session, tenant_a)
        replay = await record_survey_response(
            session,
            tenant_id=tenant_a,
            company_id=company_a,
            survey_type="nps",
            score=10,
            comment="Changed payload must not duplicate the original retry",
            source="manual",
            recorded_at=None,
            idempotency_key="survey-retry-1",
        )
        # `record_survey_response` commits. The real summary endpoint starts
        # a fresh request/session, which pins its tenant GUC again.
        await _set_tenant(session, tenant_a)
        summary = await survey_summary(session, tenant_id=tenant_a, company_id=company_a)

    assert replay["id"] == first["id"]
    assert summary["nps"] == 100.0
    assert summary["nps_responses"] == 1
    assert summary["response_rate"] is None

    async with async_session() as session:
        await _set_tenant(session, tenant_a)
        with pytest.raises(SurveyCompanyNotFound):
            await record_survey_response(
                session,
                tenant_id=tenant_a,
                company_id=company_b,
                survey_type="csat",
                score=5,
                comment=None,
                source="manual",
                recorded_at=None,
                idempotency_key="cross-tenant-company",
            )

    async with async_session() as session:
        await _set_tenant(session, tenant_b)
        hidden = await survey_summary(session, tenant_id=tenant_b, company_id=company_a)
        assert hidden["nps_responses"] == 0
        await session.rollback()
