"""Regression test for a cross-tenant IDOR found and fixed during Sprint 02.

Not one of Sprint 02's assigned stories (STORY-01-04/STORY-03-03/STORY-02-01)
— discovered opportunistically while picking a real-world demonstration
target for the new tests/support/tenant_isolation.py harness (STORY-01-04),
documented in docs/program/RISK_REGISTER.md, and fixed inline per the
Sprint Execution Contract's small-fix carve-out (2-line change, isolated,
no API/schema change, exactly mirrors an already-established pattern used
four times in app/routers/opportunities.py).

Bug: `POST /meetings/{opportunity_id}/brief` (app/routers/meetings.py,
`get_meeting_brief`) fetched the opportunity via
`PostgresOpportunityRepository.get(opportunity_id)` — which has no tenant_id
parameter and applies no tenant filter at all — and never compared the
result's tenant_id against the caller's authenticated tenant before using
it. Any authenticated user of any tenant could request another tenant's
meeting brief (company name, recent signals, contacts, opportunity
value/stage) by opportunity_id alone. Every sibling endpoint in
app/routers/opportunities.py already carries the
`if not opp or getattr(opp, "tenant_id", None) != tenant_id: raise 404`
check; this one caller had been missed.

The underlying repository method is intentionally left unfixed here —
adding a required tenant_id parameter to `PostgresOpportunityRepository.get()`
would touch its abstract interface, the in-memory counterpart, and every
other call site, which is exactly the kind of change the Sprint Execution
Contract's small-fix threshold rules out (isolated, <20 lines, no interface
change). That is out-of-band architecture debt, tracked in the risk
register, not absorbed into this fix.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.routers.meetings import get_meeting_brief
from domains.commercial.infrastructure.postgres_repositories import PostgresOpportunityRepository
from domains.commercial.opportunity.contracts.models import Opportunity
from tests.support.schema import ensure_tables_created
from tests.support.tenant_isolation import assert_cross_tenant_read_blocked

pytestmark = pytest.mark.asyncio


async def _ensure_company_signals_table(db_session: AsyncSession) -> None:
    """`generate_brief()` queries `company_signals` via raw SQL, but no
    SQLAlchemy declarative model registers it — it exists in real deployments
    only via a hand-written Alembic migration. The root conftest.py's
    `setup_database` fixture builds schema from `Base.metadata.create_all()`,
    which therefore can never create this specific table regardless of
    import order (this is a variant of the same root cause as
    docs/program/RISK_REGISTER.md R-11, not a new issue). Creating it here,
    locally, only for this test, rather than touching the shared fixture —
    which would be a materially larger, out-of-scope change to fix properly
    for every test in the suite."""
    await db_session.execute(
        text(
            "CREATE TABLE IF NOT EXISTS company_signals ("
            "id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), "
            "company_id VARCHAR(64), title VARCHAR(255), description TEXT, "
            "created_at TIMESTAMPTZ NOT NULL DEFAULT now())"
        )
    )


async def _create_opportunity_as(tenant_id: str, db_session: AsyncSession) -> str:
    repo = PostgresOpportunityRepository(db_session)
    opp = Opportunity(
        id=uuid.uuid4().hex[:12],
        tenant_id=tenant_id,
        # generate_brief() joins to companies.id and contacts.company_id, both
        # real `uuid` columns (unlike opportunity/workflow-domain ids, which
        # are plain varchar) — must be a syntactically valid UUID even though
        # deliberately not backed by a matching companies row; generate_brief
        # tolerates a missing company gracefully (LEFT-join-shaped queries).
        company_id=str(uuid.uuid4()),
        name="Tenant isolation regression opportunity",
    )
    await repo.save(opp)
    return opp.id


async def _read_brief_as(opportunity_id: str, tenant_id: str, db_session: AsyncSession):
    try:
        return await get_meeting_brief(
            opportunity_id=opportunity_id,
            request=None,  # unused inside the endpoint body; safe for a direct call
            tenant_id=tenant_id,
            db=db_session,
            _rbac=None,
        )
    except HTTPException as exc:
        if exc.status_code == 404:
            return None
        raise


class TestMeetingBriefTenantIsolation:
    async def test_cross_tenant_meeting_brief_blocked(self, db_session: AsyncSession):
        """The actual regression test for the fix — uses the new reusable
        harness (STORY-01-04) rather than hand-writing the create/assert
        pair, and is the harness's first real (not demo) consumer."""
        await ensure_tables_created(db_session)
        await _ensure_company_signals_table(db_session)
        await assert_cross_tenant_read_blocked(
            create_as=lambda tenant_id: _create_opportunity_as(tenant_id, db_session),
            read_as=lambda opportunity_id, tenant_id: _read_brief_as(
                opportunity_id, tenant_id, db_session
            ),
            # generate_brief() also queries contacts.tenant_id, a real `uuid`
            # column (unlike commercial_opportunities.tenant_id, which is
            # varchar) — the harness's plain-string defaults aren't valid
            # UUIDs, so this specific consumer must supply its own.
            tenant_a=str(uuid.uuid4()),
            tenant_b=str(uuid.uuid4()),
        )
