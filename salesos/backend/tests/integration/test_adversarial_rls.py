"""Sprint 04 Story 4.1: Adversarial cross-tenant RLS validation suite."""

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
        {"id": a, "name": "S04 A", "slug": f"s04a-{a[:8]}"},
    )
    await session.execute(
        text("INSERT INTO tenants (id, name, slug) VALUES (:id, :name, :slug)"),
        {"id": b, "name": "S04 B", "slug": f"s04b-{b[:8]}"},
    )
    return a, b


async def _ins(session, tid: str, sql: str, params: dict | None = None):
    await session.execute(text(f"SET LOCAL app.tenant_id = '{tid}'"))
    return await session.execute(text(sql), params or {})


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


@pytest.mark.asyncio
async def test_companies_isolation():
    async with engine.begin() as conn:
        ta, tb = await _create_tenants(conn)
        await _ins(
            conn,
            ta,
            f"INSERT INTO companies (tenant_id, cr_number, name_ar, name_en) VALUES ('{ta}'::uuid, 'CA-{ta[:8]}', 'A','A')",  # noqa: E501
        )
        await _ins(
            conn,
            tb,
            f"INSERT INTO companies (tenant_id, cr_number, name_ar, name_en) VALUES ('{tb}'::uuid, 'CB-{tb[:8]}', 'B','B')",  # noqa: E501
        )
        await _chk(
            conn, ta, f"SELECT count(*) FROM companies WHERE tenant_id='{ta}'::uuid", 1, "own"
        )
        await _chk(
            conn, tb, f"SELECT count(*) FROM companies WHERE tenant_id='{ta}'::uuid", 0, "cross"
        )
        await _fc(conn, f"SELECT count(*) FROM companies WHERE tenant_id='{ta}'::uuid", "companies")
        await conn.rollback()


@pytest.mark.asyncio
async def test_users_isolation():
    async with engine.begin() as conn:
        ta, tb = await _create_tenants(conn)
        await _ins(
            conn,
            ta,
            f"INSERT INTO users (id, tenant_id, email, password_hash, full_name, role) VALUES (gen_random_uuid(), '{ta}'::uuid, 'ua-{ta[:8]}@t.l', 'x', 'UA', 'user')",  # noqa: E501
        )
        await _ins(
            conn,
            tb,
            f"INSERT INTO users (id, tenant_id, email, password_hash, full_name, role) VALUES (gen_random_uuid(), '{tb}'::uuid, 'ub-{tb[:8]}@t.l', 'x', 'UB', 'user')",  # noqa: E501
        )
        await _chk(conn, ta, f"SELECT count(*) FROM users WHERE tenant_id='{ta}'::uuid", 1, "own")
        await _chk(conn, tb, f"SELECT count(*) FROM users WHERE tenant_id='{ta}'::uuid", 0, "cross")
        await _fc(conn, f"SELECT count(*) FROM users WHERE tenant_id='{ta}'::uuid", "users")
        await conn.rollback()


@pytest.mark.asyncio
async def test_workflow_definitions_isolation():
    async with engine.begin() as conn:
        ta, tb = await _create_tenants(conn)
        await _ins(
            conn,
            ta,
            f"INSERT INTO workflow_definitions (id, tenant_id, name, description, trigger_type, status, steps) VALUES (gen_random_uuid(), '{ta}', 'WA', '', 'manual', 'active', '[]'::jsonb)",  # noqa: E501
        )
        await _ins(
            conn,
            tb,
            f"INSERT INTO workflow_definitions (id, tenant_id, name, description, trigger_type, status, steps) VALUES (gen_random_uuid(), '{tb}', 'WB', '', 'manual', 'active', '[]'::jsonb)",  # noqa: E501
        )
        await _chk(
            conn, ta, f"SELECT count(*) FROM workflow_definitions WHERE tenant_id='{ta}'", 1, "own"
        )
        await _chk(
            conn,
            tb,
            f"SELECT count(*) FROM workflow_definitions WHERE tenant_id='{ta}'",
            0,
            "cross",
        )
        await _fc(
            conn, f"SELECT count(*) FROM workflow_definitions WHERE tenant_id='{ta}'", "workflow"
        )
        await conn.rollback()


@pytest.mark.asyncio
async def test_golden_records_isolation():
    async with engine.begin() as conn:
        ta, tb = await _create_tenants(conn)
        await _ins(
            conn,
            ta,
            f"INSERT INTO golden_records (id, tenant_id, cr_number, data, confidence_score, is_active) VALUES (gen_random_uuid(), '{ta}'::uuid, 'GA-{ta[:8]}', '{{}}'::jsonb, 0.9, true)",  # noqa: E501
        )
        await _ins(
            conn,
            tb,
            f"INSERT INTO golden_records (id, tenant_id, cr_number, data, confidence_score, is_active) VALUES (gen_random_uuid(), '{tb}'::uuid, 'GB-{tb[:8]}', '{{}}'::jsonb, 0.9, true)",  # noqa: E501
        )
        await _chk(
            conn, ta, f"SELECT count(*) FROM golden_records WHERE tenant_id='{ta}'::uuid", 1, "own"
        )
        await _chk(
            conn,
            tb,
            f"SELECT count(*) FROM golden_records WHERE tenant_id='{ta}'::uuid",
            0,
            "cross",
        )
        await _fc(
            conn, f"SELECT count(*) FROM golden_records WHERE tenant_id='{ta}'::uuid", "golden"
        )
        await conn.rollback()


@pytest.mark.asyncio
async def test_notifications_isolation():
    async with engine.begin() as conn:
        ta, tb = await _create_tenants(conn)
        await _ins(
            conn,
            ta,
            f"INSERT INTO notifications (notification_id, tenant_id, user_id, type, title, body, read) VALUES (gen_random_uuid(), '{ta}', '{uuid.uuid4()}', 'info', 'NA', '', false)",  # noqa: E501
        )
        await _ins(
            conn,
            tb,
            f"INSERT INTO notifications (notification_id, tenant_id, user_id, type, title, body, read) VALUES (gen_random_uuid(), '{tb}', '{uuid.uuid4()}', 'info', 'NB', '', false)",  # noqa: E501
        )
        await _chk(conn, ta, f"SELECT count(*) FROM notifications WHERE tenant_id='{ta}'", 1, "own")
        await _chk(
            conn, tb, f"SELECT count(*) FROM notifications WHERE tenant_id='{ta}'", 0, "cross"
        )
        await _fc(conn, f"SELECT count(*) FROM notifications WHERE tenant_id='{ta}'", "notif")
        await conn.rollback()


@pytest.mark.asyncio
async def test_analytics_reports_isolation():
    async with engine.begin() as conn:
        ta, tb = await _create_tenants(conn)
        await _ins(
            conn,
            ta,
            f"INSERT INTO analytics_reports (id, tenant_id, name, type, metrics, dimensions, filters, visualization_type, created_by) VALUES ('{uuid.uuid4()}', '{ta}', 'RA', 'search', '[\"count\"]'::jsonb, '[\"day\"]'::jsonb, '{{}}'::jsonb, 'table', '{uuid.uuid4()}')",  # noqa: E501
        )
        await _ins(
            conn,
            tb,
            f"INSERT INTO analytics_reports (id, tenant_id, name, type, metrics, dimensions, filters, visualization_type, created_by) VALUES ('{uuid.uuid4()}', '{tb}', 'RB', 'search', '[\"count\"]'::jsonb, '[\"day\"]'::jsonb, '{{}}'::jsonb, 'table', '{uuid.uuid4()}')",  # noqa: E501
        )
        await _chk(
            conn, ta, f"SELECT count(*) FROM analytics_reports WHERE tenant_id='{ta}'", 1, "own"
        )
        await _chk(
            conn, tb, f"SELECT count(*) FROM analytics_reports WHERE tenant_id='{ta}'", 0, "cross"
        )
        await _fc(
            conn, f"SELECT count(*) FROM analytics_reports WHERE tenant_id='{ta}'", "analytics"
        )
        await conn.rollback()


@pytest.mark.asyncio
async def test_rls_policies_intact():
    async with engine.begin() as conn:
        r = await conn.execute(
            text("SELECT count(*) FROM pg_policies WHERE policyname LIKE 'tenant_isolation_%'")
        )
        count = r.scalar()
        assert count == POLICY_COUNT, f"policies changed: {count}"
        await conn.rollback()
