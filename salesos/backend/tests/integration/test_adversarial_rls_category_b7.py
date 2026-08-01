"""DEC-119 / S04-CATB-07: Adversarial RLS for Category B7 admin_role_permissions.

Table: admin_role_permissions — no tenant_id; isolate via admin_roles.id (role_id).
Parent is Category A with nullable tenant_id (DEC-044 / DEC-110).
POLICY_COUNT live = 47 Category A + 2 B1 + 2 B2 + 2 B3 + 2 B4 + 2 B5 + 1 B6 + 1 B7 = 59.

Nullable semantics: join uses fail-closed parent tenant equality only — no
permissive OR IS NULL. Tests exercise tenant-scoped roles (tenant_id set).

Does NOT enable R-09 / DB-05 deferred-8 admin billing tables.
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
        {"id": a, "name": "B7 A", "slug": f"b7a-{a[:8]}"},
    )
    await session.execute(
        text("INSERT INTO tenants (id, name, slug) VALUES (:id, :name, :slug)"),
        {"id": b, "name": "B7 B", "slug": f"b7b-{b[:8]}"},
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


@pytest.mark.asyncio
async def test_admin_role_permissions_isolation():
    async with engine.begin() as conn:
        ta, tb = await _create_tenants(conn)
        perm_a = f"perm_b7a_{ta[:8]}"
        perm_b = f"perm_b7b_{tb[:8]}"
        role_a = f"role_b7a_{ta[:8]}"
        role_b = f"role_b7b_{tb[:8]}"

        # admin_permissions is global (not Category B / no tenant RLS).
        await conn.execute(
            text(
                'INSERT INTO admin_permissions (id, key, name, description, "group") '
                f"VALUES ('{perm_a}', 'b7a.{ta[:8]}', 'B7 A', '', 'test')"
            )
        )
        await conn.execute(
            text(
                'INSERT INTO admin_permissions (id, key, name, description, "group") '
                f"VALUES ('{perm_b}', 'b7b.{tb[:8]}', 'B7 B', '', 'test')"
            )
        )

        await _ins(
            conn,
            ta,
            f"INSERT INTO admin_roles (id, name, description, is_system, tenant_id) "
            f"VALUES ('{role_a}', 'B7 Role A', '', false, '{ta}')",
        )
        await _ins(
            conn,
            tb,
            f"INSERT INTO admin_roles (id, name, description, is_system, tenant_id) "
            f"VALUES ('{role_b}', 'B7 Role B', '', false, '{tb}')",
        )
        await _ins(
            conn,
            ta,
            f"INSERT INTO admin_role_permissions (role_id, permission_id) "
            f"VALUES ('{role_a}', '{perm_a}')",
        )
        await _ins(
            conn,
            tb,
            f"INSERT INTO admin_role_permissions (role_id, permission_id) "
            f"VALUES ('{role_b}', '{perm_b}')",
        )

        await _chk(conn, ta, "SELECT count(*) FROM admin_role_permissions", 1, "own")
        await _chk(conn, tb, "SELECT count(*) FROM admin_role_permissions", 1, "own-b")
        await _chk(
            conn,
            tb,
            f"SELECT count(*) FROM admin_role_permissions WHERE role_id = '{role_a}'",
            0,
            "cross",
        )
        await _chk(
            conn,
            ta,
            f"SELECT count(*) FROM admin_role_permissions WHERE role_id = '{role_a}'",
            1,
            "own-role",
        )
        await _fc(conn, "SELECT count(*) FROM admin_role_permissions", "arp-fc")
        await conn.rollback()


@pytest.mark.asyncio
async def test_rls_policies_intact_after_b7():
    async with engine.begin() as conn:
        r = await conn.execute(
            text("SELECT count(*) FROM pg_policies WHERE policyname LIKE 'tenant_isolation_%'")
        )
        assert r.scalar() == POLICY_COUNT, f"policies changed: {r.scalar()}"
        r2 = await conn.execute(
            text(
                "SELECT count(*) FROM pg_policies "
                "WHERE tablename = 'admin_role_permissions' "
                "AND policyname = 'tenant_isolation_admin_role_permissions'"
            )
        )
        assert r2.scalar() == 1, "missing admin_role_permissions policy"
        # Deferred-8 admin billing RLS is owned by DB-05 Slice 4 (DEC-123 / 7.5).
        for tbl in (
            "admin_licenses",
            "admin_invoices",
            "admin_transactions",
            "admin_ai_costs",
            "admin_jobs",
        ):
            r3 = await conn.execute(
                text(
                    "SELECT count(*) FROM pg_policies "
                    f"WHERE tablename = '{tbl}' "
                    f"AND policyname = 'tenant_isolation_{tbl}'"
                )
            )
            assert r3.scalar() == 1, f"{tbl} missing deferred-8 RLS (DEC-123)"
        await conn.rollback()
