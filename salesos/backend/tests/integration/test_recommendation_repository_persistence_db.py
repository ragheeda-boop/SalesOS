"""PostgresRecommendationRepository crashed on every real call, same
crash class as reports 120-123, 125-126.

Mechanical finding: `RecommendationEvidence` (domains/decision/
recommendation/models.py) has fields `source_layer`/`source_domain`/
`key`/`value`/`narrative` -- `save()` serialized using `factor`/`label`/
`source_id`/`source_type`, none of which exist -- AttributeError on
every call. `Alternative`'s real fields include `expected_outcome`/
`risk`, which `save()` silently dropped (only captured `title`/
`description`/`confidence`) -- data loss, not a crash.
`recommendation.recommendation_type` does not exist on `Recommendation`
at all (real fields are `reasoning`/`risk`/`expected_impact` instead) --
a second, independent AttributeError in `save()`, and `_to_domain()`'s
`recommendation_type=model.recommendation_type` kwarg was also invalid
(Recommendation's constructor has no such parameter).
`recommendation.context_id` is required on the domain (no default) but
was never read/written by `save()`/`_to_domain()` -- `RecommendationModel`
has no `context_id` column at all (no schema home, same category as
report 122's Proposal.sections gap). `_to_domain()` also passed
`applied_at=model.applied_at, dismissed_at=model.dismissed_at` --
`Recommendation` has no such fields either (confirmed via a byte-exact
read of the dataclass) -- a third guaranteed TypeError.

Reachability: `PostgresRecommendationRepository` has zero callers
anywhere in `app/` or `domains/` outside its own definition (confirmed
via grep). `RecommendationEngine.evaluate()` (the only production
producer of a `Recommendation`) never calls any repository's `save()`
at all -- it is a pure computation with no persistence wiring. Fixed
anyway, matching the established practice (reports 121/123/126) of
correcting dead code ahead of any future wiring decision, since the
crash is real and unconditional the moment a caller is added.

Not fixed, disclosed in-source: `recommendation_type` (String(100),
NOT NULL, no column default) is persisted as "" -- no domain
equivalent exists. `applied_at`/`dismissed_at` are left unset on save
and ignored on reload -- no domain equivalent tracks per-transition
timestamps. `context_id`/`reasoning`/`risk`/`expected_impact` are not
persisted at all -- reload uses `context_id=""` as an explicit
placeholder.
"""

from __future__ import annotations

import uuid

import pytest_asyncio
from sqlalchemy import text

from app.database import async_session, engine
from domains.commercial.infrastructure.postgres_repositories import (
    PostgresRecommendationRepository,
)
from domains.decision.recommendation.models import (
    Alternative,
    Recommendation,
    RecommendationEvidence,
    RecommendationStatus,
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
        text("INSERT INTO tenants (id, name, slug) VALUES (:id, 'Recommendation Test', :slug)"),
        {"id": tenant_id, "slug": f"rec-test-{tenant_id[:8]}"},
    )


async def test_save_and_reload_recommendation_with_evidence_and_alternatives():
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

        repo = PostgresRecommendationRepository(session)
        rec = Recommendation(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            context_id=str(uuid.uuid4()),
            title="Schedule executive engagement",
            description="Opportunity stalled 45 days with no activity.",
            reasoning="Stage aging detected: no activity, high risk of stall.",
            confidence=0.87,
            risk="Low — recommendation only, no automated action.",
            expected_impact="Re-engaging decision maker reduces stall risk.",
            status=RecommendationStatus.PROPOSED,
            evidence=[
                RecommendationEvidence(
                    source_layer="fact", source_domain="opportunity", key="stage_aging",
                    value=45, narrative="Stage aging: 45 days in stage",
                )
            ],
            alternatives=[
                Alternative(
                    title="Send follow-up proposal",
                    description="Lower effort, but may not escalate urgency.",
                    expected_outcome="Keeps momentum without escalation.",
                    risk="Low",
                    confidence=0.5,
                )
            ],
            target_id="opp-1", target_type="opportunity",
        )

        saved = await repo.save(rec)
        assert saved.id == rec.id

        reloaded = await repo.get(rec.id)
        assert reloaded is not None
        assert reloaded.title == "Schedule executive engagement"
        assert reloaded.status == RecommendationStatus.PROPOSED
        assert len(reloaded.evidence) == 1
        assert reloaded.evidence[0].source_layer == "fact"
        assert reloaded.evidence[0].source_domain == "opportunity"
        assert reloaded.evidence[0].key == "stage_aging"
        assert reloaded.evidence[0].value == 45
        assert reloaded.evidence[0].narrative == "Stage aging: 45 days in stage"
        assert len(reloaded.alternatives) == 1
        assert reloaded.alternatives[0].title == "Send follow-up proposal"
        assert reloaded.alternatives[0].expected_outcome == "Keeps momentum without escalation."
        assert reloaded.alternatives[0].risk == "Low"
        assert reloaded.alternatives[0].confidence == 0.5

        by_target = await repo.list_by_target("opp-1", "opportunity")
        assert len(by_target) == 1
        assert by_target[0].id == rec.id

        by_tenant = await repo.list_by_tenant(tenant_id)
        assert len(by_tenant) == 1

        row = (
            await session.execute(
                text(
                    "SELECT recommendation_type, applied_at, dismissed_at "
                    "FROM commercial_recommendations WHERE id = :id"
                ),
                {"id": rec.id},
            )
        ).one()
        assert row.recommendation_type == ""
        assert row.applied_at is None
        assert row.dismissed_at is None

        await session.rollback()
