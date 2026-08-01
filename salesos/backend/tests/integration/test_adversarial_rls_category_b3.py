"""DEC-115 / S04-CATB-03: Adversarial RLS for Category B3 analytics children.

Tables: analytics_report_executions, analytics_report_shares — no tenant_id;
isolate via analytics_reports.
POLICY_COUNT live = 47 Category A (DEC-044) + 2 B1 + 2 B2 + 2 B3 + 2 B4 + 2 B5 + 1 B6 + 1 B7 = 59 (after DEC-119).

Does NOT cover B4–B7. Does NOT enable R-09 / DB-05 deferred tables.
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
        {"id": a, "name": "B3 A", "slug": f"b3a-{a[:8]}"},
    )
    await session.execute(
        text("INSERT INTO tenants (id, name, slug) VALUES (:id, :name, :slug)"),
        {"id": b, "name": "B3 B", "slug": f"b3b-{b[:8]}"},
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


async def _create_report(session, tid: str, suffix: str) -> str:
    rid = str(uuid.uuid4())
    await _ins(
        session,
        tid,
        f"INSERT INTO analytics_reports "
        f"(id, tenant_id, name, type, metrics, dimensions, filters, "
        f"visualization_type, created_by) "
        f"VALUES ('{rid}', '{tid}', 'R{suffix}', 'search', "
        f"'[\"count\"]'::jsonb, '[\"day\"]'::jsonb, '{{}}'::jsonb, "
        f"'table', '{uuid.uuid4()}')",
    )
    return rid


@pytest.mark.asyncio
async def test_analytics_report_executions_isolation():
    async with engine.begin() as conn:
        ta, tb = await _create_tenants(conn)
        ra = await _create_report(conn, ta, "A")
        rb = await _create_report(conn, tb, "B")
        await _ins(
            conn,
            ta,
            f"INSERT INTO analytics_report_executions "
            f"(id, report_id, status, output_format) "
            f"VALUES ('{uuid.uuid4()}', '{ra}', 'pending', 'json')",
        )
        await _ins(
            conn,
            tb,
            f"INSERT INTO analytics_report_executions "
            f"(id, report_id, status, output_format) "
            f"VALUES ('{uuid.uuid4()}', '{rb}', 'pending', 'json')",
        )
        await _chk(conn, ta, "SELECT count(*) FROM analytics_report_executions", 1, "own")
        await _chk(conn, tb, "SELECT count(*) FROM analytics_report_executions", 1, "own-b")
        await _chk(
            conn,
            tb,
            f"SELECT count(*) FROM analytics_report_executions WHERE report_id = '{ra}'",
            0,
            "cross",
        )
        await _fc(conn, "SELECT count(*) FROM analytics_report_executions", "executions-fc")
        await conn.rollback()


@pytest.mark.asyncio
async def test_analytics_report_shares_isolation():
    async with engine.begin() as conn:
        ta, tb = await _create_tenants(conn)
        ra = await _create_report(conn, ta, "A")
        rb = await _create_report(conn, tb, "B")
        await _ins(
            conn,
            ta,
            f"INSERT INTO analytics_report_shares "
            f"(id, report_id, user_id, permission, shared_by) "
            f"VALUES ('{uuid.uuid4()}', '{ra}', 'user-a', 'view', 'sharer-a')",
        )
        await _ins(
            conn,
            tb,
            f"INSERT INTO analytics_report_shares "
            f"(id, report_id, user_id, permission, shared_by) "
            f"VALUES ('{uuid.uuid4()}', '{rb}', 'user-b', 'view', 'sharer-b')",
        )
        await _chk(conn, ta, "SELECT count(*) FROM analytics_report_shares", 1, "own")
        await _chk(conn, tb, "SELECT count(*) FROM analytics_report_shares", 1, "own-b")
        await _chk(
            conn,
            tb,
            f"SELECT count(*) FROM analytics_report_shares WHERE report_id = '{ra}'",
            0,
            "cross",
        )
        await _fc(conn, "SELECT count(*) FROM analytics_report_shares", "shares-fc")
        await conn.rollback()


@pytest.mark.asyncio
async def test_rls_policies_intact_after_b3():
    async with engine.begin() as conn:
        r = await conn.execute(
            text("SELECT count(*) FROM pg_policies WHERE policyname LIKE 'tenant_isolation_%'")
        )
        assert r.scalar() == POLICY_COUNT, f"policies changed: {r.scalar()}"
        await conn.rollback()
