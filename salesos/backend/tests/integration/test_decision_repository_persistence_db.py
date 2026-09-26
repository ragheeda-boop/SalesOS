"""PostgresDecisionRepository crashed on every real call to build a
decision context, and its Policy methods used a completely different
(and apparently stale) field shape from the current domain contract.

Mechanical finding, same crash class as reports 120-122: `DecisionContext`
(contracts/models.py) has `factors: list[DecisionFactor]`, `policies:
list[Policy]`, `generated_at` -- there is no top-level `confidence` at
all. `DecisionContextModel` (table `commercial_decision_contexts`, FORCE
RLS) has a flat `confidence: float` column and treats `factors` as a
plain JSON dict, not a list of typed objects. `save_context()`/
`save_contexts()` read `context.confidence`/`ctx.confidence` directly --
AttributeError on every call, confirmed as the actual crash below.
`get_context()`/`get_latest_for_target()` constructed
`DecisionContext(..., confidence=model.confidence)` -- an unexpected
keyword argument.

`PostgresDecisionRepository` is wired live via
app/routers/commercial.py's `_get_context(db)` factory --
`DecisionService.build_context()`/`build_contexts()` (used by real
decision/recommendation endpoints) would have crashed on their first
`save_context()`/`save_contexts()` call.

A second, unreached (zero live callers, confirmed via grep) but equally
broken pair: `save_policy()`/`list_policies()` used `policy.rules`/
`policy.outcome`/`policy.priority`/`policy.enabled` -- none of which
exist on `Policy` (`description`/`rule`[singular]/`category`), and
`policy.tenant_id`, which also didn't exist despite `PolicyModel.
tenant_id` being required on this FORCE-RLS table (mirroring the
StageEntry/Proposal tenant_id gap). `PolicyModel`'s shape
(`rules`/`outcome`/`priority`/`enabled`) matches no other domain class
found in this codebase -- most likely a stale schema from an earlier
policy-engine design, not a simple rename. Fixed with a documented,
best-effort, lossy mapping (`rule` <-> single-element `rules`; `category`
stands in for `outcome`, which has no domain equivalent at all).

Not fixed, disclosed: `DecisionContext.policies` has no column on
`DecisionContextModel` at all -- not persisted, same category as report
122's Proposal.sections gap.
"""

from __future__ import annotations

import uuid

import pytest_asyncio
from sqlalchemy import text

from app.database import async_session, engine
from domains.commercial.infrastructure.postgres_repositories import (
    PostgresDecisionRepository,
)
from domains.decision.context.models import DecisionFactor, Policy
from domains.decision.context.service import DecisionService


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
        text("INSERT INTO tenants (id, name, slug) VALUES (:id, 'Decision Test', :slug)"),
        {"id": tenant_id, "slug": f"decision-test-{tenant_id[:8]}"},
    )


async def test_build_context_persists_and_reloads_factors_correctly():
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

        service = DecisionService(PostgresDecisionRepository(session))
        factor = DecisionFactor(
            source_layer="fact", source_domain="opportunity", key="stage_aging",
            value=45, label="45 days in stage", severity="critical",
        )
        context = await service.build_context(
            tenant_id=tenant_id, target_id="opp-1", target_type="opportunity", factors=[factor],
        )
        assert context.factors
        assert context.has_critical()

        reloaded = await service.get_context(context.id)
        assert reloaded is not None
        assert len(reloaded.factors) == 1
        assert reloaded.factors[0].key == "stage_aging"
        assert reloaded.factors[0].value == 45
        assert reloaded.factors[0].severity == "critical"
        assert reloaded.has_critical()

        latest = await service.get_latest_context("opp-1", "opportunity")
        assert latest is not None
        assert latest.id == context.id

        await session.rollback()


async def test_add_policy_persists_and_reloads_with_lossy_mapping():
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

        service = DecisionService(PostgresDecisionRepository(session))
        policy = Policy(
            id=str(uuid.uuid4()), name="Discount Approval",
            rule="if discount > 30% then requires executive approval",
            category="approval",
        )
        saved = await service.add_policy(tenant_id, policy)
        assert saved.tenant_id == tenant_id

        policies = await service.list_policies(tenant_id)
        assert len(policies) == 1
        assert policies[0].name == "Discount Approval"
        assert policies[0].rule == "if discount > 30% then requires executive approval"
        assert policies[0].category == "approval"
        assert policies[0].tenant_id == tenant_id

        row = (
            await session.execute(
                text("SELECT rules, outcome, priority, enabled FROM commercial_policies WHERE id = :id"),
                {"id": policy.id},
            )
        ).one()
        assert row.rules == ["if discount > 30% then requires executive approval"]
        assert row.outcome == "approval"
        assert row.priority == 0
        assert row.enabled is True

        await session.rollback()
