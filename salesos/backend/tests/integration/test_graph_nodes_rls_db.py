"""`graph_nodes` (created in 0004_knowledge_graph.py, kept live under
DEC-130f's "no DROP without a dedicated DEC" register) has a real, NOT NULL,
tenant_id column but RLS was never added for it at creation time, and it was
never registered in `ALL_TENANT_TABLES` -- a pure registry gap (report 132),
unlike DEC-157's 14 orphan-keep tables, which had live callers needing
GUC-pinning fixed first. Exhaustive grep confirmed no application code
anywhere references this table by name -- every `graph_nodes` hit in the
codebase is the unrelated `merge_graph_nodes()` method name on the
knowledge-graph runtime, which never touches this table -- so this test
proves the policy itself is correct under the restricted role directly via
SQL, for whichever caller eventually wires this table up.
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import async_session, engine


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


@pytest.mark.asyncio
async def test_graph_nodes_rls_isolates_tenants_under_the_restricted_role():
    tenant_a = str(uuid.uuid4())
    tenant_b = str(uuid.uuid4())
    node_a = "node-a-" + str(uuid.uuid4())[:8]
    node_b = "node-b-" + str(uuid.uuid4())[:8]

    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_a}
        )
        await session.execute(
            text("INSERT INTO tenants (id, name, slug) VALUES (:id, 'Graph A', :slug)"),
            {"id": tenant_a, "slug": f"graph-a-{tenant_a[:8]}"},
        )
        await session.execute(
            text("INSERT INTO graph_nodes (id, tenant_id, labels) VALUES (:id, :tid, '{COMPANY}')"),
            {"id": node_a, "tid": tenant_a},
        )
        await session.commit()

    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_b}
        )
        await session.execute(
            text("INSERT INTO tenants (id, name, slug) VALUES (:id, 'Graph B', :slug)"),
            {"id": tenant_b, "slug": f"graph-b-{tenant_b[:8]}"},
        )
        await session.execute(
            text("INSERT INTO graph_nodes (id, tenant_id, labels) VALUES (:id, :tid, '{PERSON}')"),
            {"id": node_b, "tid": tenant_b},
        )
        await session.commit()

    # Tenant A's session sees only its own row.
    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_a}
        )
        result = await session.execute(text("SELECT id FROM graph_nodes"))
        ids = {row[0] for row in result.fetchall()}
        assert ids == {node_a}

    # Tenant B's session sees only its own row.
    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_b}
        )
        result = await session.execute(text("SELECT id FROM graph_nodes"))
        ids = {row[0] for row in result.fetchall()}
        assert ids == {node_b}

    # No GUC pinned at all: fail-closed, zero rows (not both tenants' rows).
    async with async_session() as session:
        result = await session.execute(text("SELECT id FROM graph_nodes"))
        ids = {row[0] for row in result.fetchall()}
        assert ids == set()

    # Cross-tenant write attempt is rejected by WITH CHECK.
    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_a}
        )
        with pytest.raises(Exception):
            await session.execute(
                text(
                    "INSERT INTO graph_nodes (id, tenant_id, labels) "
                    "VALUES (:id, :tid, '{COMPANY}')"
                ),
                {"id": "cross-tenant-attempt", "tid": tenant_b},
            )
            await session.commit()
