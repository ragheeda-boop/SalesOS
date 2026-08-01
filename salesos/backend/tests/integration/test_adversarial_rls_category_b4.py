"""DEC-116 / S04-CATB-04: Adversarial RLS for Category B4 decision-center children.

Tables: decision_center_audits, decision_center_feedback — no tenant_id;
isolate via decision_center_decisions (parent id UUID; child decision_id varchar).
POLICY_COUNT live = 47 Category A (DEC-044) + 2 B1 + 2 B2 + 2 B3 + 2 B4 + 2 B5 + 1 B6 + 1 B7 = 59 (after DEC-119).

Does NOT cover B6–B7. Does NOT enable R-09 / DB-05 deferred tables.
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import engine

POLICY_COUNT = 67  # 59 prior (DEC-119) + 8 deferred-8 (DEC-123)


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    yield
    await engine.dispose()


async def _create_tenants(session) -> tuple[str, str]:
    a, b = str(uuid.uuid4()), str(uuid.uuid4())
    await session.execute(
        text("INSERT INTO tenants (id, name, slug) VALUES (:id, :name, :slug)"),
        {"id": a, "name": "B4 A", "slug": f"b4a-{a[:8]}"},
    )
    await session.execute(
        text("INSERT INTO tenants (id, name, slug) VALUES (:id, :name, :slug)"),
        {"id": b, "name": "B4 B", "slug": f"b4b-{b[:8]}"},
    )
    return a, b


async def _ins(session, tid: str, sql: str):
    await session.execute(text(f"SET LOCAL app.tenant_id = '{tid}'"))
    return await session.execute(text(sql))


async def _chk(session, tid: str, sql: str, expected: int, label: str):
    await session.execute(text(f"SET LOCAL app.tenant_id = '{tid}'"))
    r = await session.execute(text(sql))
    assert r.scalar() == expected, f"[{label}] exp={expected} got={r.scalar()}"


async def _fc(session, sql: str, label: str):
    await session.execute(text("RESET app.tenant_id"))
    r = await session.execute(text(sql))
    assert r.scalar() == 0, f"[{label}] fail-closed violation: {r.scalar()}"


async def _create_decision(session, tid: str, suffix: str) -> str:
    did = str(uuid.uuid4())
    await _ins(
        session,
        tid,
        f"INSERT INTO decision_center_decisions "
        f"(id, tenant_id, domain, decision_type, entity_id, entity_type, "
        f"decision, confidence, provider, status, timestamp) "
        f"VALUES ('{did}', '{tid}', 'sales', 'score', 'ent-{suffix}', "
        f"'opportunity', 'approve', 0.9, 'test', 'active', NOW())",
    )
    return did


@pytest.mark.asyncio
async def test_decision_center_audits_isolation():
    async with engine.begin() as conn:
        ta, tb = await _create_tenants(conn)
        da = await _create_decision(conn, ta, "A")
        db = await _create_decision(conn, tb, "B")
        await _ins(
            conn,
            ta,
            f"INSERT INTO decision_center_audits "
            f"(decision_id, provider_used, timestamp) "
            f"VALUES ('{da}', 'test', NOW())",
        )
        await _ins(
            conn,
            tb,
            f"INSERT INTO decision_center_audits "
            f"(decision_id, provider_used, timestamp) "
            f"VALUES ('{db}', 'test', NOW())",
        )
        await _chk(conn, ta, "SELECT count(*) FROM decision_center_audits", 1, "own")
        await _chk(conn, tb, "SELECT count(*) FROM decision_center_audits", 1, "own-b")
        await _chk(
            conn,
            tb,
            f"SELECT count(*) FROM decision_center_audits WHERE decision_id = '{da}'",
            0,
            "cross",
        )
        await _fc(conn, "SELECT count(*) FROM decision_center_audits", "audits-fc")
        await conn.rollback()


@pytest.mark.asyncio
async def test_decision_center_feedback_isolation():
    async with engine.begin() as conn:
        ta, tb = await _create_tenants(conn)
        da = await _create_decision(conn, ta, "A")
        db = await _create_decision(conn, tb, "B")
        await _ins(
            conn,
            ta,
            f"INSERT INTO decision_center_feedback "
            f"(id, decision_id, rating, created_at) "
            f"VALUES ('{uuid.uuid4()}', '{da}', 'up', NOW())",
        )
        await _ins(
            conn,
            tb,
            f"INSERT INTO decision_center_feedback "
            f"(id, decision_id, rating, created_at) "
            f"VALUES ('{uuid.uuid4()}', '{db}', 'down', NOW())",
        )
        await _chk(conn, ta, "SELECT count(*) FROM decision_center_feedback", 1, "own")
        await _chk(conn, tb, "SELECT count(*) FROM decision_center_feedback", 1, "own-b")
        await _chk(
            conn,
            tb,
            f"SELECT count(*) FROM decision_center_feedback WHERE decision_id = '{da}'",
            0,
            "cross",
        )
        await _fc(conn, "SELECT count(*) FROM decision_center_feedback", "feedback-fc")
        await conn.rollback()


@pytest.mark.asyncio
async def test_rls_policies_intact_after_b4():
    async with engine.begin() as conn:
        r = await conn.execute(
            text("SELECT count(*) FROM pg_policies WHERE policyname LIKE 'tenant_isolation_%'")
        )
        assert r.scalar() == POLICY_COUNT, f"policies changed: {r.scalar()}"
        await conn.rollback()
