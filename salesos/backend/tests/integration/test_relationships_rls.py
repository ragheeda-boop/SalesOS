"""Database proof for the Commercial Relationship Model (RLS + lifecycle).

Proves real Postgres persistence + RLS + FORCE RLS on
``commercial_relationship_edges`` (migration u1v2w3x4y5z6): per-tenant
writes/reads, cross-tenant isolation for the restricted runtime role,
unpinned-session invisibility (fail-closed), idempotent duplicate create,
and the full observed -> active -> superseded -> re-created lifecycle. Only
test databases via the restricted ``salesos_app`` runtime role.
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import async_session, engine, owner_engine
from app.modules.relationships.store import RelationshipStore
from app.modules.relationships.models import RelationshipError


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    yield
    await engine.dispose()
    await owner_engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def _clean_edges_table():
    async with owner_engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE commercial_relationship_edges"))
    yield


async def _set_tenant(session, tenant_id: str | None) -> None:
    if tenant_id:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": tenant_id},
        )
    else:
        await session.execute(text("RESET app.tenant_id"))


@pytest.mark.asyncio
async def test_edges_persist_and_are_tenant_scoped():
    tenant_a, tenant_b = str(uuid.uuid4()), str(uuid.uuid4())
    store = RelationshipStore()

    edge = await store.create(
        tenant_id=tenant_a,
        edge_type="champion_for",
        source_type="person",
        source_id="p-11111111",
        target_type="company",
        target_id="c-22222222",
        basis="source_assignment",
        confidence=0.9,
        evidence=[{"source": "import", "filename": "org_chart.csv"}],
        created_by="u-qa-1",
    )
    assert edge.tenant_id == tenant_a
    assert edge.edge_type == "champion_for"
    assert edge.confidence == 0.9
    assert edge.superseded_at is None

    fetched = await store.get(edge.id, tenant_id=tenant_a)
    assert fetched is not None
    assert fetched.target_id == "c-22222222"
    assert fetched.evidence == [{"source": "import", "filename": "org_chart.csv"}]

    assert await store.get(edge.id, tenant_id=tenant_b) is None
    visible = await store.list(tenant_id=tenant_a)
    assert [e.id for e in visible] == [edge.id]
    assert await store.list(tenant_id=tenant_b) == []


@pytest.mark.asyncio
async def test_duplicate_active_edge_is_idempotent():
    tenant_a = str(uuid.uuid4())
    store = RelationshipStore()

    first = await store.create(
        tenant_id=tenant_a,
        edge_type="reports_to",
        source_type="person",
        source_id="p-11111111",
        target_type="person",
        target_id="p-22222222",
    )
    second = await store.create(
        tenant_id=tenant_a,
        edge_type="reports_to",
        source_type="person",
        source_id="p-11111111",
        target_type="person",
        target_id="p-22222222",
    )
    # Same active tuple -> same row returned, no duplicate inserted.
    assert second.id == first.id
    assert await store.count_active(tenant_id=tenant_a) == 1


@pytest.mark.asyncio
async def test_force_rls_hides_other_tenant_and_unpinned_edges_from_salesos_app():
    tenant_a, tenant_b = str(uuid.uuid4()), str(uuid.uuid4())
    store = RelationshipStore()
    await store.create(
        tenant_id=tenant_a,
        edge_type="influences",
        source_type="person",
        source_id="p-11111111",
        target_type="person",
        target_id="p-22222222",
    )
    await store.create(
        tenant_id=tenant_b,
        edge_type="blocks",
        source_type="person",
        source_id="p-33333333",
        target_type="person",
        target_id="p-44444444",
    )

    async with async_session() as session:
        await _set_tenant(session, None)
        zero = (
            await session.execute(text("SELECT count(*) AS n FROM commercial_relationship_edges"))
        ).first().n
        assert zero == 0

        await _set_tenant(session, tenant_a)
        a_only = (
            await session.execute(text("SELECT count(*) AS n FROM commercial_relationship_edges"))
        ).first().n
        assert a_only == 1

        await _set_tenant(session, tenant_b)
        b_only = (
            await session.execute(text("SELECT count(*) AS n FROM commercial_relationship_edges"))
        ).first().n
        assert b_only == 1
        await session.rollback()


@pytest.mark.asyncio
async def test_observed_to_superseded_to_recreated_lifecycle():
    tenant_a = str(uuid.uuid4())
    store = RelationshipStore()

    active = await store.create(
        tenant_id=tenant_a,
        edge_type="reports_to",
        source_type="person",
        source_id="p-11111111",
        target_type="person",
        target_id="p-22222222",
        basis="org_structure",
        observed_at="2026-08-01T00:00:00+00:00",
        created_by="u-qa-1",
    )
    assert active.superseded_at is None

    superseded = await store.supersede(active.id, tenant_id=tenant_a)
    assert superseded is not None
    assert superseded.superseded_at is not None
    assert superseded.id == active.id

    # Default list excludes superseded rows.
    assert await store.list(tenant_id=tenant_a) == []
    # Optional filter exposes the history.
    hist = await store.list(tenant_id=tenant_a, include_superseded=True)
    assert [e.id for e in hist] == [active.id]

    # Superseding twice is idempotent (no-op, returns None when already done).
    assert await store.supersede(active.id, tenant_id=tenant_a) is None

    # The same (edge_type, source, target) tuple can be created again AFTER
    # supersession: a fresh ACTIVE row takes the released slot.
    recreated = await store.create(
        tenant_id=tenant_a,
        edge_type="reports_to",
        source_type="person",
        source_id="p-11111111",
        target_type="person",
        target_id="p-22222222",
        basis="source_assignment",
        created_by="u-qa-1",
    )
    assert recreated.id != active.id
    assert recreated.superseded_at is None
    assert await store.count_active(tenant_id=tenant_a) == 1
    # The original committed record is never mutated.
    again = await store.get(active.id, tenant_id=tenant_a)
    assert again is not None
    assert again.superseded_at is not None


@pytest.mark.asyncio
async def test_filtering_and_edge_type_validation():
    tenant_a = str(uuid.uuid4())
    store = RelationshipStore()
    await store.create(
        tenant_id=tenant_a,
        edge_type="reports_to",
        source_type="person",
        source_id="p-a",
        target_type="person",
        target_id="p-b",
    )
    await store.create(
        tenant_id=tenant_a,
        edge_type="introduced_by",
        source_type="person",
        source_id="p-a",
        target_type="person",
        target_id="p-c",
    )
    await store.create(
        tenant_id=tenant_a,
        edge_type="champion_for",
        source_type="person",
        source_id="p-a",
        target_type="company",
        target_id="c-1",
    )

    reports = await store.list(tenant_id=tenant_a, edge_type="reports_to")
    assert len(reports) == 1
    assert reports[0].edge_type == "reports_to"

    sourced = await store.list(tenant_id=tenant_a, source_type="person", source_id="p-a")
    assert len(sourced) == 3

    targeted = await store.list(tenant_id=tenant_a, target_type="company")
    assert len(targeted) == 1

    with pytest.raises(ValueError, match="invalid edge_type"):
        await store.list(tenant_id=tenant_a, edge_type="bogus_type")

    with pytest.raises(ValueError, match="invalid source_type"):
        await store.list(tenant_id=tenant_a, source_type="widget")


@pytest.mark.asyncio
async def test_cross_tenant_duplicate_tuple_is_hidden_not_leaked():
    tenant_a, tenant_b = str(uuid.uuid4()), str(uuid.uuid4())
    store = RelationshipStore()
    await store.create(
        tenant_id=tenant_a,
        edge_type="influences",
        source_type="person",
        source_id="p-11111111",
        target_type="person",
        target_id="p-22222222",
    )
    # Tenant B re-uses the exact same ids; RLS hides A's row so this is a
    # legitimate distinct active edge, not a cross-tenant collision surface.
    b_edge = await store.create(
        tenant_id=tenant_b,
        edge_type="influences",
        source_type="person",
        source_id="p-11111111",
        target_type="person",
        target_id="p-22222222",
    )
    assert await store.count_active(tenant_id=tenant_a) == 1
    assert await store.count_active(tenant_id=tenant_b) == 1
    assert await store.get(b_edge.id, tenant_id=tenant_a) is None

    # count_active is scoped too.
    assert await store.count_active(tenant_id=tenant_a, edge_type="blocks") == 0
    assert await store.count_active(tenant_id=tenant_b, edge_type="influences") == 1


@pytest.mark.asyncio
async def test_model_validation_runs_before_any_write():
    tenant_a = str(uuid.uuid4())
    store = RelationshipStore()
    with pytest.raises(RelationshipError):
        await store.create(
            tenant_id=tenant_a,
            edge_type="reports_into",  # not in taxonomy
            source_type="person",
            source_id="p-1",
            target_type="person",
            target_id="p-2",
        )
    with pytest.raises(RelationshipError):
        await store.create(
            tenant_id=tenant_a,
            edge_type="reports_to",
            source_type="person",
            source_id="p-1",
            target_type="person",
            target_id="p-1",  # self loop
        )