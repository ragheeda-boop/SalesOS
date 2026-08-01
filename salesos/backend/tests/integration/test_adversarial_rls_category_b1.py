"""DEC-112 / S04-CATB-01: Adversarial RLS for Category B1 company children.

Tables: branches, licenses — no tenant_id; isolate via companies.company_id.
POLICY_COUNT live = 47 Category A (DEC-044) + 2 B1 + 2 B2 + 2 B3 + 2 B4 + 2 B5 + 1 B6 = 58 (after DEC-118).

Does NOT cover B2–B7. Does NOT enable R-09 / DB-05 deferred tables.
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import engine

POLICY_COUNT = 58  # 47 Category A + B1 + B2 + B3 + B4 + B5 + B6 (DEC-118)


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    yield
    await engine.dispose()


async def _create_tenants(session) -> tuple[str, str]:
    a, b = str(uuid.uuid4()), str(uuid.uuid4())
    await session.execute(
        text("INSERT INTO tenants (id, name, slug) VALUES (:id, :name, :slug)"),
        {"id": a, "name": "B1 A", "slug": f"b1a-{a[:8]}"},
    )
    await session.execute(
        text("INSERT INTO tenants (id, name, slug) VALUES (:id, :name, :slug)"),
        {"id": b, "name": "B1 B", "slug": f"b1b-{b[:8]}"},
    )
    return a, b


async def _create_company(session, tid: str, cr_suffix: str) -> str:
    cid = str(uuid.uuid4())
    await session.execute(text(f"SET LOCAL app.tenant_id = '{tid}'"))
    await session.execute(
        text(
            f"INSERT INTO companies (id, tenant_id, cr_number, name_ar, name_en) "
            f"VALUES ('{cid}'::uuid, '{tid}'::uuid, "
            f"'B1{cr_suffix}-{tid[:8]}', '{cr_suffix}', '{cr_suffix}')"
        )
    )
    return cid


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
async def test_branches_isolation():
    async with engine.begin() as conn:
        ta, tb = await _create_tenants(conn)
        ca = await _create_company(conn, ta, "BA")
        cb = await _create_company(conn, tb, "BB")
        await _ins(
            conn,
            ta,
            f"INSERT INTO branches (id, company_id, name_ar) "
            f"VALUES (gen_random_uuid(), '{ca}'::uuid, 'BranchA')",
        )
        await _ins(
            conn,
            tb,
            f"INSERT INTO branches (id, company_id, name_ar) "
            f"VALUES (gen_random_uuid(), '{cb}'::uuid, 'BranchB')",
        )
        await _chk(conn, ta, "SELECT count(*) FROM branches", 1, "own")
        await _chk(conn, tb, "SELECT count(*) FROM branches", 1, "own-b")
        await _chk(
            conn,
            tb,
            f"SELECT count(*) FROM branches WHERE company_id = '{ca}'::uuid",
            0,
            "cross",
        )
        await _fc(conn, "SELECT count(*) FROM branches", "branches-fc")
        await conn.rollback()


@pytest.mark.asyncio
async def test_licenses_isolation():
    async with engine.begin() as conn:
        ta, tb = await _create_tenants(conn)
        ca = await _create_company(conn, ta, "LA")
        cb = await _create_company(conn, tb, "LB")
        await _ins(
            conn,
            ta,
            f"INSERT INTO licenses (id, company_id, license_number, license_type) "
            f"VALUES (gen_random_uuid(), '{ca}'::uuid, 'LIC-A-{ta[:8]}', 'commercial')",
        )
        await _ins(
            conn,
            tb,
            f"INSERT INTO licenses (id, company_id, license_number, license_type) "
            f"VALUES (gen_random_uuid(), '{cb}'::uuid, 'LIC-B-{tb[:8]}', 'commercial')",
        )
        await _chk(conn, ta, "SELECT count(*) FROM licenses", 1, "own")
        await _chk(conn, tb, "SELECT count(*) FROM licenses", 1, "own-b")
        await _chk(
            conn,
            tb,
            f"SELECT count(*) FROM licenses WHERE company_id = '{ca}'::uuid",
            0,
            "cross",
        )
        await _fc(conn, "SELECT count(*) FROM licenses", "licenses-fc")
        await conn.rollback()


@pytest.mark.asyncio
async def test_rls_policies_intact_after_b1():
    async with engine.begin() as conn:
        r = await conn.execute(
            text("SELECT count(*) FROM pg_policies WHERE policyname LIKE 'tenant_isolation_%'")
        )
        assert r.scalar() == POLICY_COUNT, f"policies changed: {r.scalar()}"
        await conn.rollback()
