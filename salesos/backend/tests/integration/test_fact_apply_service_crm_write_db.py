"""FactApplyService is the ONLY code path that ever writes a Phase 7
human-approved fact into the live Company/Contact tables (the "canonical
write boundary" — see docs/adr/0114-canonical-write-boundary.md). The
existing tests/unit/test_fact_apply_service.py exercises it entirely
against a hand-rolled fake session (SimpleNamespace + a fake _Session
class), so it has never actually verified that:

  1. Every field in CRM_APPLY_FIELDS is a real column on the real
     Company/Contact SQLAlchemy models (a class of bug this session has
     found repeatedly elsewhere via exactly this kind of static/dynamic
     mismatch — see reports 142/143 for the two most recent instances).
  2. CanonicalFact.subject_id / Company.id are compatible types under a
     real asyncpg round trip (uuid-vs-varchar comparisons have been a
     recurring live-bug class this session).
  3. The GUC-verification check (`current_setting('app.tenant_id', true)`)
     actually behaves correctly under RLS with a real, GUC-pinned session
     the way get_db_session()'s real dependency chain provides.
  4. The row actually gets updated in the database (not just in an
     in-memory fake), and a FACT_APPLIED audit event is actually
     persisted.

This file exercises the real thing: a real disposable Postgres, real
Company/CanonicalFact rows, a real GUC-pinned session, going through
FactApplyService.apply() exactly as the live router
(app/modules/facts/router.py:372) calls it.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
import pytest_asyncio
from sqlalchemy import select, text

from app.database import apply_tenant_guc, async_session, engine
from app.modules.company.models import Company
from app.modules.facts.apply_service import (
    CRM_APPLY_FIELDS,
    FactApplyRejected,
    FactApplyService,
)
from app.modules.facts.models import CanonicalFact, CanonicalFactEvent
from app.modules.identity.models import Tenant


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    async with engine.connect() as conn:
        db_name = await conn.scalar(text("SELECT current_database()"))
    assert db_name != "salesos", (
        f"REFUSING: connected to {db_name!r} — this is the persistent "
        "local dev database, not a disposable/test one."
    )
    yield
    await engine.dispose()


def test_every_allowlisted_field_is_a_real_company_or_contact_column():
    """Static check: CRM_APPLY_FIELDS must never drift from the real schema."""
    company_cols = {c.name for c in Company.__table__.columns}
    from app.modules.contact.models import Contact

    contact_cols = {c.name for c in Contact.__table__.columns}
    assert CRM_APPLY_FIELDS["company"] <= company_cols
    assert CRM_APPLY_FIELDS["contact"] <= contact_cols


async def _make_tenant(session, tenant_id: uuid.UUID) -> None:
    session.add(Tenant(id=tenant_id, name=f"Test Tenant {tenant_id}", slug=f"test-{tenant_id}"))
    await session.flush()


async def _make_approved_fact(
    session, *, tenant_id: uuid.UUID, subject_id: uuid.UUID, field_name: str, value
) -> CanonicalFact:
    fact = CanonicalFact(
        tenant_id=tenant_id,
        subject_type="company",
        subject_id=subject_id,
        field_name=field_name,
        proposed_value=value,
        value_hash="0" * 64,
        status="APPROVED",
        evidence_band="STRONG",
        score=0.9,
        decision_reason="test fixture — pre-approved for apply-boundary proof",
        idempotency_key=f"test-{uuid.uuid4()}",
        request_fingerprint="a" * 64,
        actor_type="human",
        actor_id="proposer-1",
        reviewer_id="reviewer-1",
        reviewed_at=datetime.now(UTC),
    )
    session.add(fact)
    await session.flush()
    return fact


@pytest.mark.asyncio
async def test_apply_updates_the_real_company_row_and_writes_an_audit_event():
    tenant_id = uuid.uuid4()

    async with async_session() as s:
        await apply_tenant_guc(s, str(tenant_id))
        await _make_tenant(s, tenant_id)
        company = Company(tenant_id=tenant_id, name_ar="شركة تجريبية", city="Jeddah")
        s.add(company)
        await s.flush()
        company_id = company.id
        fact = await _make_approved_fact(
            s, tenant_id=tenant_id, subject_id=company_id, field_name="city", value="Riyadh"
        )
        fact_id = fact.id
        await s.commit()

    async with async_session() as s2:
        await apply_tenant_guc(s2, str(tenant_id))
        result = await FactApplyService(s2).apply(
            tenant_id=tenant_id,
            fact_id=fact_id,
            actor_id="reviewer-1",
            reason="Human review confirmed the correct city.",
        )
        await s2.commit()

    assert result.changed is True
    assert result.status == "APPLIED"
    assert result.previous_value == "Jeddah"
    assert result.applied_value == "Riyadh"

    # Genuinely fresh session/read — no identity-map shortcut available.
    async with async_session() as s3:
        await apply_tenant_guc(s3, str(tenant_id))
        row = (await s3.execute(select(Company).where(Company.id == company_id))).scalar_one()
        assert row.city == "Riyadh"

        fact_row = (
            await s3.execute(select(CanonicalFact).where(CanonicalFact.id == fact_id))
        ).scalar_one()
        assert fact_row.status == "APPLIED"
        assert fact_row.applied_at is not None

        event = (
            await s3.execute(
                select(CanonicalFactEvent).where(CanonicalFactEvent.fact_id == fact_id)
            )
        ).scalar_one()
        assert event.event_type == "FACT_APPLIED"
        assert event.event_data["previous_value"] == "Jeddah"
        assert event.event_data["applied_value"] == "Riyadh"


@pytest.mark.asyncio
async def test_apply_rejects_a_field_not_on_the_allowlist():
    tenant_id = uuid.uuid4()

    async with async_session() as s:
        await apply_tenant_guc(s, str(tenant_id))
        await _make_tenant(s, tenant_id)
        company = Company(tenant_id=tenant_id, name_ar="شركة تجريبية")
        s.add(company)
        await s.flush()
        fact = await _make_approved_fact(
            s, tenant_id=tenant_id, subject_id=company.id, field_name="cr_number", value="1010101010"
        )
        fact_id = fact.id
        await s.commit()

    async with async_session() as s2:
        await apply_tenant_guc(s2, str(tenant_id))
        with pytest.raises(FactApplyRejected, match="not allowlisted"):
            await FactApplyService(s2).apply(
                tenant_id=tenant_id,
                fact_id=fact_id,
                actor_id="reviewer-1",
                reason="cr_number requires the Phase 7 human gate, not this boundary.",
            )


@pytest.mark.asyncio
async def test_apply_is_idempotent_on_an_already_applied_fact():
    tenant_id = uuid.uuid4()

    async with async_session() as s:
        await apply_tenant_guc(s, str(tenant_id))
        await _make_tenant(s, tenant_id)
        company = Company(tenant_id=tenant_id, name_ar="شركة تجريبية", city="Jeddah")
        s.add(company)
        await s.flush()
        company_id = company.id
        fact = await _make_approved_fact(
            s, tenant_id=tenant_id, subject_id=company_id, field_name="city", value="Riyadh"
        )
        fact_id = fact.id
        await s.commit()

    async with async_session() as s2:
        await apply_tenant_guc(s2, str(tenant_id))
        first = await FactApplyService(s2).apply(
            tenant_id=tenant_id, fact_id=fact_id, actor_id="reviewer-1", reason="first apply"
        )
        await s2.commit()
    assert first.changed is True

    async with async_session() as s3:
        await apply_tenant_guc(s3, str(tenant_id))
        second = await FactApplyService(s3).apply(
            tenant_id=tenant_id, fact_id=fact_id, actor_id="reviewer-1", reason="retry, already applied"
        )
    assert second.changed is False
    assert second.status == "APPLIED"

    # Only ONE audit event, despite two apply() calls.
    async with async_session() as s4:
        await apply_tenant_guc(s4, str(tenant_id))
        events = (
            await s4.execute(select(CanonicalFactEvent).where(CanonicalFactEvent.fact_id == fact_id))
        ).scalars().all()
        assert len(events) == 1
