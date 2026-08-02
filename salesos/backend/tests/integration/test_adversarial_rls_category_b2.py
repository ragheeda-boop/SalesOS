"""DEC-114 / S04-CATB-02: Adversarial RLS for Category B2 commercial children.

Tables: commercial_activities, commercial_quote_lines — no tenant_id;
isolate via commercial_activity_sessions / commercial_quotes.
POLICY_COUNT live = 47 Category A (DEC-044) + 2 B1 + 2 B2 + 2 B3 + 2 B4
+ 2 B5 + 1 B6 + 1 B7 = 59 (after DEC-119).

Does NOT cover B3–B7. Does NOT enable R-09 / DB-05 deferred tables.
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import engine

POLICY_COUNT = 70  # 69 prior + STORY-08-05 sync_runs tenant_isolation policy


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    yield
    await engine.dispose()


async def _create_tenants(session) -> tuple[str, str]:
    a, b = str(uuid.uuid4()), str(uuid.uuid4())
    await session.execute(
        text("INSERT INTO tenants (id, name, slug) VALUES (:id, :name, :slug)"),
        {"id": a, "name": "B2 A", "slug": f"b2a-{a[:8]}"},
    )
    await session.execute(
        text("INSERT INTO tenants (id, name, slug) VALUES (:id, :name, :slug)"),
        {"id": b, "name": "B2 B", "slug": f"b2b-{b[:8]}"},
    )
    return a, b


async def _ins(session, tid: str, sql: str):
    await session.execute(text(f"SET LOCAL app.tenant_id = '{tid}'"))
    return await session.execute(text(sql))


async def _chk(session, tid: str, sql: str, expected: int, label: str):
    await session.execute(text(f"SET LOCAL app.tenant_id = '{tid}'"))
    r = await session.execute(text(sql))
    got = r.scalar()
    assert got == expected, f"[{label}] exp={expected} got={got}"


async def _fc(session, sql: str, label: str):
    await session.execute(text("RESET app.tenant_id"))
    r = await session.execute(text(sql))
    got = r.scalar()
    assert got == 0, f"[{label}] fail-closed violation: {got}"


async def _create_session(session, tid: str, suffix: str) -> str:
    sid = str(uuid.uuid4())
    await _ins(
        session,
        tid,
        f"INSERT INTO commercial_activity_sessions "
        f"(id, tenant_id, title, target_id, target_type, status, notes) "
        f"VALUES ('{sid}', '{tid}', 'Sess{suffix}', 'tgt-{suffix}', "
        f"'opportunity', 'scheduled', '')",
    )
    return sid


async def _create_quote(session, tid: str, suffix: str) -> str:
    qid = str(uuid.uuid4())
    await _ins(
        session,
        tid,
        f"INSERT INTO commercial_quotes "
        f"(id, tenant_id, opportunity_id, title, status, total_value, currency, notes) "
        f"VALUES ('{qid}', '{tid}', 'opp-{suffix}', 'Quote{suffix}', "
        f"'draft', 0.0, 'SAR', '')",
    )
    return qid


@pytest.mark.asyncio
async def test_commercial_activities_isolation():
    async with engine.begin() as conn:
        ta, tb = await _create_tenants(conn)
        sa = await _create_session(conn, ta, "A")
        sb = await _create_session(conn, tb, "B")
        await _ins(
            conn,
            ta,
            f"INSERT INTO commercial_activities "
            f"(id, session_id, activity_type, owner_id, status) "
            f"VALUES ('{uuid.uuid4()}', '{sa}', 'call', 'owner-a', 'scheduled')",
        )
        await _ins(
            conn,
            tb,
            f"INSERT INTO commercial_activities "
            f"(id, session_id, activity_type, owner_id, status) "
            f"VALUES ('{uuid.uuid4()}', '{sb}', 'call', 'owner-b', 'scheduled')",
        )
        await _chk(conn, ta, "SELECT count(*) FROM commercial_activities", 1, "own")
        await _chk(conn, tb, "SELECT count(*) FROM commercial_activities", 1, "own-b")
        await _chk(
            conn,
            tb,
            f"SELECT count(*) FROM commercial_activities WHERE session_id = '{sa}'",
            0,
            "cross",
        )
        await _fc(conn, "SELECT count(*) FROM commercial_activities", "activities-fc")
        await conn.rollback()


@pytest.mark.asyncio
async def test_commercial_quote_lines_isolation():
    async with engine.begin() as conn:
        ta, tb = await _create_tenants(conn)
        qa = await _create_quote(conn, ta, "A")
        qb = await _create_quote(conn, tb, "B")
        await _ins(
            conn,
            ta,
            f"INSERT INTO commercial_quote_lines "
            f"(id, quote_id, description, quantity, unit_price, total) "
            f"VALUES ('{uuid.uuid4()}', '{qa}', 'LineA', 1.0, 100.0, 100.0)",
        )
        await _ins(
            conn,
            tb,
            f"INSERT INTO commercial_quote_lines "
            f"(id, quote_id, description, quantity, unit_price, total) "
            f"VALUES ('{uuid.uuid4()}', '{qb}', 'LineB', 1.0, 200.0, 200.0)",
        )
        await _chk(conn, ta, "SELECT count(*) FROM commercial_quote_lines", 1, "own")
        await _chk(conn, tb, "SELECT count(*) FROM commercial_quote_lines", 1, "own-b")
        await _chk(
            conn,
            tb,
            f"SELECT count(*) FROM commercial_quote_lines WHERE quote_id = '{qa}'",
            0,
            "cross",
        )
        await _fc(conn, "SELECT count(*) FROM commercial_quote_lines", "quote-lines-fc")
        await conn.rollback()


@pytest.mark.asyncio
async def test_rls_policies_intact_after_b2():
    async with engine.begin() as conn:
        r = await conn.execute(
            text("SELECT count(*) FROM pg_policies WHERE policyname LIKE 'tenant_isolation_%'")
        )
        count = r.scalar()
        assert count == POLICY_COUNT, f"policies changed: {count}"
        await conn.rollback()
