"""PostgresProposalRepository crashed on every real call: same bug class
as reports 120/121 (StageEntry, Quote). A second, distinct bug was found
tracing the service layer: `_transition()` always re-fetched its own
independent copy of the proposal, silently discarding whatever the caller
had already mutated on its own copy (delivery_method/url, viewed_at,
accepted_at, rejection_reason all affected).

Mechanical finding: `Proposal` (contracts/models.py) has no top-level
`sent_at`/`rejected_at`/`rejection_reason` at all (it does have
`viewed_at`/`accepted_at`, which do exist and are correctly persisted
already). `ProposalModel` (table `commercial_proposals`, FORCE RLS) has
flat `sent_at`/`rejected_at`/`rejection_reason` columns with no domain
equivalent. `save()` read `proposal.sent_at`/`rejected_at`/
`rejection_reason` directly -- `AttributeError` on every call, confirmed
below. `_to_domain()`/`kpis()` had the same class of mismatch
(`ProposalKPIs`'s real fields are `total_proposals`/`delivery_rate`/
`average_cycle_hours`/`proposal_to_win_conversion`, not `total_sent`/
`accepted_count`/`avg_days_to_decision`).

`PostgresProposalRepository` is wired live via app/routers/commercial.py's
`_get_proposal(db)` factory -- every real call to `ProposalService.
create_proposal()`/`approve()`/`deliver()`/`mark_viewed()`/`accept()`/
`reject()`/`expire()` would have crashed on its first `save()`.

Not fixed, disclosed: `proposal.sections` (the proposal's actual content)
has no persistence column at all on ProposalModel -- update_section()'s
mutations do not round-trip through this schema. A genuine, separate,
deeper gap (no existing table/column to reuse, unlike Quote's lines);
would need a new migration to close.
"""

from __future__ import annotations

import uuid

import pytest_asyncio
from sqlalchemy import text

from app.database import async_session, engine
from domains.commercial.infrastructure.postgres_repositories import (
    PostgresProposalRepository,
)
from domains.commercial.proposal.contracts.models import ProposalStatus
from domains.commercial.proposal.engine.service import ProposalService


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    """Report 118/121 safety net -- see those reports for the incident this
    guards against."""
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
        text("INSERT INTO tenants (id, name, slug) VALUES (:id, 'Proposal Test', :slug)"),
        {"id": tenant_id, "slug": f"proposal-test-{tenant_id[:8]}"},
    )


async def test_proposal_full_lifecycle_persists_mutations_at_each_transition():
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

        service = ProposalService(PostgresProposalRepository(session))

        proposal = await service.create_proposal(
            tenant_id=tenant_id, opportunity_id="opp-1", quote_id="quote-1", title="Test Proposal"
        )
        assert proposal.status == ProposalStatus.DRAFT

        await service.approve(proposal.id, approved_by="manager-1")

        delivered = await service.deliver(proposal.id, method="portal", url="https://example.test/p")
        # Proves the double-fetch-discards-mutation bug is fixed: deliver()'s
        # own local mutations must be the ones actually persisted.
        assert delivered.delivery_method == "portal"
        assert delivered.delivery_url == "https://example.test/p"
        sent_row = (
            await session.execute(
                text("SELECT sent_at, delivery_method FROM commercial_proposals WHERE id = :id"),
                {"id": proposal.id},
            )
        ).one()
        assert sent_row.sent_at is not None
        assert sent_row.delivery_method == "portal"

        viewed = await service.mark_viewed(proposal.id)
        assert viewed.viewed_at is not None
        assert viewed.status == ProposalStatus.VIEWED

        accepted = await service.accept(proposal.id)
        assert accepted.accepted_at is not None
        assert accepted.status == ProposalStatus.ACCEPTED

        kpis = await service.kpis(tenant_id)
        assert kpis.total_proposals == 1
        assert kpis.delivery_rate == 1.0
        assert kpis.acceptance_rate == 1.0

        await session.rollback()


async def test_proposal_reject_persists_reason_via_fixed_double_fetch():
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

        service = ProposalService(PostgresProposalRepository(session))
        proposal = await service.create_proposal(
            tenant_id=tenant_id, opportunity_id="opp-2", quote_id="quote-2", title="Reject Me"
        )

        rejected = await service.reject(proposal.id, reason="budget cut")
        assert rejected.rejection_reason == "budget cut"
        assert rejected.status == ProposalStatus.REJECTED

        row = (
            await session.execute(
                text(
                    "SELECT rejected_at, rejection_reason, status "
                    "FROM commercial_proposals WHERE id = :id"
                ),
                {"id": proposal.id},
            )
        ).one()
        assert row.rejected_at is not None
        assert row.rejection_reason == "budget cut"
        assert row.status == "rejected"

        await session.rollback()
