"""ADR-030: Tenant isolation tests for opportunity_contacts."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

from domains.commercial.infrastructure.models import OpportunityContactModel


@pytest.mark.asyncio
class TestOpportunityContactTenantIsolation:

    async def test_cross_tenant_read_blocked(self, db_session):
        tenant_a = uuid.uuid4()
        tenant_b = uuid.uuid4()

        oc = OpportunityContactModel(
            id=str(uuid.uuid4()),
            tenant_id=str(tenant_a),
            opportunity_id=str(uuid.uuid4()),
            contact_id=str(uuid.uuid4()),
        )
        db_session.add(oc)
        await db_session.flush()

        stmt_a = select(OpportunityContactModel).where(
            OpportunityContactModel.id == oc.id,
            OpportunityContactModel.tenant_id == str(tenant_a),
        )
        result_a = await db_session.execute(stmt_a)
        assert result_a.scalar_one_or_none() is not None

        stmt_b = select(OpportunityContactModel).where(
            OpportunityContactModel.id == oc.id,
            OpportunityContactModel.tenant_id == str(tenant_b),
        )
        result_b = await db_session.execute(stmt_b)
        assert result_b.scalar_one_or_none() is None

    async def test_cross_tenant_listing_excludes(self, db_session):
        tenant_a = uuid.uuid4()
        tenant_b = uuid.uuid4()

        oc_a = OpportunityContactModel(
            id=str(uuid.uuid4()),
            tenant_id=str(tenant_a),
            opportunity_id="opp-shared",
            contact_id=str(uuid.uuid4()),
        )
        oc_b = OpportunityContactModel(
            id=str(uuid.uuid4()),
            tenant_id=str(tenant_b),
            opportunity_id="opp-shared",
            contact_id=str(uuid.uuid4()),
        )
        db_session.add_all([oc_a, oc_b])
        await db_session.flush()

        stmt = select(OpportunityContactModel).where(
            OpportunityContactModel.tenant_id == str(tenant_a),
        )
        result = await db_session.execute(stmt)
        rows = result.scalars().all()
        ids = {r.id for r in rows}

        assert oc_a.id in ids
        assert oc_b.id not in ids

    async def test_uniqueness_violation_prevented(self, db_session):
        tenant_id = str(uuid.uuid4())
        opportunity_id = str(uuid.uuid4())
        contact_id = str(uuid.uuid4())

        oc1 = OpportunityContactModel(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            opportunity_id=opportunity_id,
            contact_id=contact_id,
        )
        db_session.add(oc1)
        await db_session.flush()

        oc2 = OpportunityContactModel(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            opportunity_id=opportunity_id,
            contact_id=contact_id,
        )
        db_session.add(oc2)

        from sqlalchemy.exc import IntegrityError
        with pytest.raises(IntegrityError):
            await db_session.flush()
        await db_session.rollback()

    async def test_same_contact_different_opportunities(self, db_session):
        tenant_id = str(uuid.uuid4())
        contact_id = str(uuid.uuid4())
        opp_id_1 = str(uuid.uuid4())
        opp_id_2 = str(uuid.uuid4())

        oc1 = OpportunityContactModel(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            opportunity_id=opp_id_1,
            contact_id=contact_id,
        )
        oc2 = OpportunityContactModel(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            opportunity_id=opp_id_2,
            contact_id=contact_id,
        )
        db_session.add_all([oc1, oc2])
        await db_session.flush()

        stmt = select(OpportunityContactModel).where(
            OpportunityContactModel.tenant_id == tenant_id,
            OpportunityContactModel.contact_id == contact_id,
        )
        result = await db_session.execute(stmt)
        rows = result.scalars().all()
        assert len(rows) == 2

    async def test_same_opportunity_different_contacts(self, db_session):
        tenant_id = str(uuid.uuid4())
        opportunity_id = str(uuid.uuid4())

        oc1 = OpportunityContactModel(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            opportunity_id=opportunity_id,
            contact_id=str(uuid.uuid4()),
        )
        oc2 = OpportunityContactModel(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            opportunity_id=opportunity_id,
            contact_id=str(uuid.uuid4()),
        )
        db_session.add_all([oc1, oc2])
        await db_session.flush()

        stmt = select(OpportunityContactModel).where(
            OpportunityContactModel.tenant_id == tenant_id,
            OpportunityContactModel.opportunity_id == opportunity_id,
        )
        result = await db_session.execute(stmt)
        rows = result.scalars().all()
        assert len(rows) == 2
