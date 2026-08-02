"""Sprint 04 Story 5: Adversarial cross-tenant WRITE-protection (RLS) suite.

Mirrors tests/integration/test_adversarial_rls.py (read-isolation suite) and
proves the same RLS policies close the WRITE half of the IDOR class:

  - Cross-tenant UPDATE ... WHERE tenant_id='<tenant B>' under tenant A's
    session context affects exactly 0 rows (fail-closed) and never touches
    tenant A's own rows.
  - Cross-tenant DELETE ... WHERE tenant_id='<tenant B>' under A deletes 0 rows.
  - Cross-tenant INSERT carrying tenant_id='<tenant B>' while A's context is
    set is rejected by the policy's WITH CHECK clause (a DBAPI error carrying
    Postgres's "new row violates row-level security policy" is raised).
  - Updating the tenant_id column itself to tenant B under A's context is
    likewise rejected by WITH CHECK.
  - SELECT ... FOR UPDATE (the write-lock path) on tenant B's row under A's
    context returns 0 rows.

The DB schema is authoritative: every policy is `tenant_id::text =
current_setting('app.tenant_id', true)` in both USING and WITH CHECK, and the
application connects as `salesos_app` (non-superuser, NOBYPASSRLS) so RLS is
actually enforced on the app connection.
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.database import engine

RLS_REJECT = "(?i)row-level security"


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    yield
    await engine.dispose()


async def _create_tenants(session) -> tuple[str, str]:
    a, b = str(uuid.uuid4()), str(uuid.uuid4())
    await session.execute(
        text("INSERT INTO tenants (id, name, slug) VALUES (:id, :name, :slug)"),
        {"id": a, "name": "S04 W-A", "slug": f"s04wa-{a[:8]}"},
    )
    await session.execute(
        text("INSERT INTO tenants (id, name, slug) VALUES (:id, :name, :slug)"),
        {"id": b, "name": "S04 W-B", "slug": f"s04wb-{b[:8]}"},
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


async def _rw(session, tid: str, sql: str, expected: int, label: str):
    await session.execute(text(f"SET LOCAL app.tenant_id = '{tid}'"))
    r = await session.execute(text(sql))
    assert r.rowcount == expected, f"[{label}] expected {expected} rows, got {r.rowcount}"


@pytest.mark.asyncio
async def test_companies_write_fail_closed():
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
        await _rw(
            conn,
            ta,
            f"UPDATE companies SET name_en='A2' WHERE tenant_id='{ta}'::uuid",
            1,
            "companies own update",
        )
        await _rw(
            conn,
            ta,
            f"UPDATE companies SET name_en='MUT' WHERE tenant_id='{tb}'::uuid",
            0,
            "companies cross update",
        )
        await _chk(
            conn,
            ta,
            f"SELECT count(*) FROM companies WHERE tenant_id='{ta}'::uuid AND name_en='A2'",
            1,
            "companies own row updated",
        )
        await _chk(
            conn,
            tb,
            f"SELECT count(*) FROM companies WHERE tenant_id='{tb}'::uuid AND name_en='B'",
            1,
            "companies B row untouched by cross update",
        )
        await _rw(
            conn,
            ta,
            f"DELETE FROM companies WHERE tenant_id='{tb}'::uuid",
            0,
            "companies cross delete",
        )
        await _chk(
            conn,
            tb,
            f"SELECT count(*) FROM companies WHERE tenant_id='{tb}'::uuid",
            1,
            "companies B row survives cross delete",
        )
        await _chk(
            conn,
            ta,
            f"SELECT count(*) FROM companies WHERE tenant_id='{ta}'::uuid",
            1,
            "companies A rows intact",
        )
        with pytest.raises(DBAPIError, match=RLS_REJECT):
            await _ins(
                conn,
                ta,
                f"INSERT INTO companies (tenant_id, cr_number, name_ar, name_en) VALUES ('{tb}'::uuid, 'CX-{tb[:8]}', 'X','X')",  # noqa: E501
            )
        await conn.rollback()


@pytest.mark.asyncio
async def test_users_write_fail_closed():
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
        await _rw(
            conn,
            ta,
            f"UPDATE users SET full_name='UA2' WHERE tenant_id='{ta}'::uuid",
            1,
            "users own update",
        )
        await _rw(
            conn,
            ta,
            f"UPDATE users SET full_name='MUT' WHERE tenant_id='{tb}'::uuid",
            0,
            "users cross update",
        )
        await _chk(
            conn,
            ta,
            f"SELECT count(*) FROM users WHERE tenant_id='{ta}'::uuid AND full_name='UA2'",
            1,
            "users own row updated",
        )
        await _chk(
            conn,
            tb,
            f"SELECT count(*) FROM users WHERE tenant_id='{tb}'::uuid AND full_name='UB'",
            1,
            "users B row untouched by cross update",
        )
        await _rw(
            conn,
            ta,
            f"DELETE FROM users WHERE tenant_id='{tb}'::uuid",
            0,
            "users cross delete",
        )
        await _chk(
            conn,
            tb,
            f"SELECT count(*) FROM users WHERE tenant_id='{tb}'::uuid",
            1,
            "users B row survives cross delete",
        )
        await _chk(
            conn,
            ta,
            f"SELECT count(*) FROM users WHERE tenant_id='{ta}'::uuid",
            1,
            "users A rows intact",
        )
        with pytest.raises(DBAPIError, match=RLS_REJECT):
            await _ins(
                conn,
                ta,
                f"INSERT INTO users (id, tenant_id, email, password_hash, full_name, role) VALUES (gen_random_uuid(), '{tb}'::uuid, 'ux-{tb[:8]}@t.l', 'x', 'UX', 'user')",  # noqa: E501
            )
        await conn.rollback()


@pytest.mark.asyncio
async def test_workflow_definitions_write_fail_closed():
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
        await _rw(
            conn,
            ta,
            f"UPDATE workflow_definitions SET name='WA2' WHERE tenant_id='{ta}'",
            1,
            "workflow own update",
        )
        await _rw(
            conn,
            ta,
            f"UPDATE workflow_definitions SET name='MUT' WHERE tenant_id='{tb}'",
            0,
            "workflow cross update",
        )
        await _chk(
            conn,
            ta,
            f"SELECT count(*) FROM workflow_definitions WHERE tenant_id='{ta}' AND name='WA2'",
            1,
            "workflow own row updated",
        )
        await _chk(
            conn,
            tb,
            f"SELECT count(*) FROM workflow_definitions WHERE tenant_id='{tb}' AND name='WB'",
            1,
            "workflow B row untouched by cross update",
        )
        await _rw(
            conn,
            ta,
            f"DELETE FROM workflow_definitions WHERE tenant_id='{tb}'",
            0,
            "workflow cross delete",
        )
        await _chk(
            conn,
            tb,
            f"SELECT count(*) FROM workflow_definitions WHERE tenant_id='{tb}'",
            1,
            "workflow B row survives cross delete",
        )
        await _chk(
            conn,
            ta,
            f"SELECT count(*) FROM workflow_definitions WHERE tenant_id='{ta}'",
            1,
            "workflow A rows intact",
        )
        with pytest.raises(DBAPIError, match=RLS_REJECT):
            await _ins(
                conn,
                ta,
                f"INSERT INTO workflow_definitions (id, tenant_id, name, description, trigger_type, status, steps) VALUES (gen_random_uuid(), '{tb}', 'WX', '', 'manual', 'active', '[]'::jsonb)",  # noqa: E501
            )
        await conn.rollback()


@pytest.mark.asyncio
async def test_golden_records_write_fail_closed():
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
        await _rw(
            conn,
            ta,
            f"UPDATE golden_records SET cr_number='GA2-{ta[:8]}' WHERE tenant_id='{ta}'::uuid",
            1,
            "golden own update",
        )
        await _rw(
            conn,
            ta,
            f"UPDATE golden_records SET cr_number='GMUT-{tb[:8]}' WHERE tenant_id='{tb}'::uuid",
            0,
            "golden cross update",
        )
        await _chk(
            conn,
            ta,
            f"SELECT count(*) FROM golden_records WHERE tenant_id='{ta}'::uuid AND cr_number='GA2-{ta[:8]}'",  # noqa: E501
            1,
            "golden own row updated",
        )
        await _chk(
            conn,
            tb,
            f"SELECT count(*) FROM golden_records WHERE tenant_id='{tb}'::uuid AND cr_number='GB-{tb[:8]}'",  # noqa: E501
            1,
            "golden B row untouched by cross update",
        )
        await _rw(
            conn,
            ta,
            f"DELETE FROM golden_records WHERE tenant_id='{tb}'::uuid",
            0,
            "golden cross delete",
        )
        await _chk(
            conn,
            tb,
            f"SELECT count(*) FROM golden_records WHERE tenant_id='{tb}'::uuid",
            1,
            "golden B row survives cross delete",
        )
        await _chk(
            conn,
            ta,
            f"SELECT count(*) FROM golden_records WHERE tenant_id='{ta}'::uuid",
            1,
            "golden A rows intact",
        )
        with pytest.raises(DBAPIError, match=RLS_REJECT):
            await _ins(
                conn,
                ta,
                f"INSERT INTO golden_records (id, tenant_id, cr_number, data, confidence_score, is_active) VALUES (gen_random_uuid(), '{tb}'::uuid, 'GX-{tb[:8]}', '{{}}'::jsonb, 0.9, true)",  # noqa: E501
            )
        await conn.rollback()


@pytest.mark.asyncio
async def test_notifications_write_fail_closed():
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
        await _rw(
            conn,
            ta,
            f"UPDATE notifications SET title='NA2' WHERE tenant_id='{ta}'",
            1,
            "notif own update",
        )
        await _rw(
            conn,
            ta,
            f"UPDATE notifications SET title='MUT' WHERE tenant_id='{tb}'",
            0,
            "notif cross update",
        )
        await _chk(
            conn,
            ta,
            f"SELECT count(*) FROM notifications WHERE tenant_id='{ta}' AND title='NA2'",
            1,
            "notif own row updated",
        )
        await _chk(
            conn,
            tb,
            f"SELECT count(*) FROM notifications WHERE tenant_id='{tb}' AND title='NB'",
            1,
            "notif B row untouched by cross update",
        )
        await _rw(
            conn,
            ta,
            f"DELETE FROM notifications WHERE tenant_id='{tb}'",
            0,
            "notif cross delete",
        )
        await _chk(
            conn,
            tb,
            f"SELECT count(*) FROM notifications WHERE tenant_id='{tb}'",
            1,
            "notif B row survives cross delete",
        )
        await _chk(
            conn,
            ta,
            f"SELECT count(*) FROM notifications WHERE tenant_id='{ta}'",
            1,
            "notif A rows intact",
        )
        with pytest.raises(DBAPIError, match=RLS_REJECT):
            await _ins(
                conn,
                ta,
                f"INSERT INTO notifications (notification_id, tenant_id, user_id, type, title, body, read) VALUES (gen_random_uuid(), '{tb}', '{uuid.uuid4()}', 'info', 'NX', '', false)",  # noqa: E501
            )
        await conn.rollback()


@pytest.mark.asyncio
async def test_analytics_reports_write_fail_closed():
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
        await _rw(
            conn,
            ta,
            f"UPDATE analytics_reports SET name='RA2' WHERE tenant_id='{ta}'",
            1,
            "analytics own update",
        )
        await _rw(
            conn,
            ta,
            f"UPDATE analytics_reports SET name='MUT' WHERE tenant_id='{tb}'",
            0,
            "analytics cross update",
        )
        await _chk(
            conn,
            ta,
            f"SELECT count(*) FROM analytics_reports WHERE tenant_id='{ta}' AND name='RA2'",
            1,
            "analytics own row updated",
        )
        await _chk(
            conn,
            tb,
            f"SELECT count(*) FROM analytics_reports WHERE tenant_id='{tb}' AND name='RB'",
            1,
            "analytics B row untouched by cross update",
        )
        await _rw(
            conn,
            ta,
            f"DELETE FROM analytics_reports WHERE tenant_id='{tb}'",
            0,
            "analytics cross delete",
        )
        await _chk(
            conn,
            tb,
            f"SELECT count(*) FROM analytics_reports WHERE tenant_id='{tb}'",
            1,
            "analytics B row survives cross delete",
        )
        await _chk(
            conn,
            ta,
            f"SELECT count(*) FROM analytics_reports WHERE tenant_id='{ta}'",
            1,
            "analytics A rows intact",
        )
        with pytest.raises(DBAPIError, match=RLS_REJECT):
            await _ins(
                conn,
                ta,
                f"INSERT INTO analytics_reports (id, tenant_id, name, type, metrics, dimensions, filters, visualization_type, created_by) VALUES ('{uuid.uuid4()}', '{tb}', 'RX', 'search', '[\"count\"]'::jsonb, '[\"day\"]'::jsonb, '{{}}'::jsonb, 'table', '{uuid.uuid4()}')",  # noqa: E501
            )
        await conn.rollback()


@pytest.mark.asyncio
async def test_companies_tenant_column_update_rejected():
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
        with pytest.raises(DBAPIError, match=RLS_REJECT):
            await _ins(
                conn,
                ta,
                f"UPDATE companies SET tenant_id='{tb}'::uuid WHERE tenant_id='{ta}'::uuid",
            )
        await conn.rollback()


@pytest.mark.asyncio
async def test_companies_select_for_update_cross_tenant_fail_closed():
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
        r = await _ins(
            conn, ta, f"SELECT id FROM companies WHERE tenant_id='{ta}'::uuid FOR UPDATE"
        )
        own = r.fetchall()
        assert len(own) == 1, f"[companies for-update own] exp=1 got={len(own)}"
        r = await _ins(
            conn, ta, f"SELECT id FROM companies WHERE tenant_id='{tb}'::uuid FOR UPDATE"
        )
        cross = r.fetchall()
        assert cross == [], f"[companies for-update cross] lock path exposed rows: {cross}"
        await conn.rollback()
