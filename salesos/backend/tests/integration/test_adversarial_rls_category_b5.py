"""DEC-117 / S04-CATB-05: Adversarial RLS for Category B5 identity token children.

Tables: password_reset_tokens, refresh_token_families — no tenant_id;
isolate via users.id (UUID FK). Auth-path careful checks: own-tenant visible
with GUC set; cross-tenant hidden; unset GUC fail-closed (no permissive bypass).
POLICY_COUNT live = 47 Category A (DEC-044) + 2 B1 + 2 B2 + 2 B3 + 2 B4 + 2 B5 + 1 B6 + 1 B7 = 59.

Does NOT cover B6–B7. Does NOT enable R-09 / DB-05 deferred tables.
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import engine

POLICY_COUNT = 59  # 47 Category A + B1 + B2 + B3 + B4 + B5 + B6 + B7 (DEC-119)


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    yield
    await engine.dispose()


async def _create_tenants(session) -> tuple[str, str]:
    a, b = str(uuid.uuid4()), str(uuid.uuid4())
    await session.execute(
        text("INSERT INTO tenants (id, name, slug) VALUES (:id, :name, :slug)"),
        {"id": a, "name": "B5 A", "slug": f"b5a-{a[:8]}"},
    )
    await session.execute(
        text("INSERT INTO tenants (id, name, slug) VALUES (:id, :name, :slug)"),
        {"id": b, "name": "B5 B", "slug": f"b5b-{b[:8]}"},
    )
    return a, b


async def _create_user(session, tid: str, suffix: str) -> str:
    uid = str(uuid.uuid4())
    await session.execute(text(f"SET LOCAL app.tenant_id = '{tid}'"))
    await session.execute(
        text(
            f"INSERT INTO users (id, tenant_id, email, password_hash, full_name, role) "
            f"VALUES ('{uid}'::uuid, '{tid}'::uuid, "
            f"'b5-{suffix}-{tid[:8]}@t.l', 'x', 'B5{suffix}', 'user')"
        )
    )
    return uid


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
async def test_password_reset_tokens_isolation():
    async with engine.begin() as conn:
        ta, tb = await _create_tenants(conn)
        ua = await _create_user(conn, ta, "A")
        ub = await _create_user(conn, tb, "B")
        hash_a = "a" * 64
        hash_b = "b" * 64
        await _ins(
            conn,
            ta,
            f"INSERT INTO password_reset_tokens "
            f"(id, user_id, token_hash, expires_at) "
            f"VALUES ('prt-{ta[:8]}', '{ua}'::uuid, '{hash_a}', NOW() + interval '1 hour')",
        )
        await _ins(
            conn,
            tb,
            f"INSERT INTO password_reset_tokens "
            f"(id, user_id, token_hash, expires_at) "
            f"VALUES ('prt-{tb[:8]}', '{ub}'::uuid, '{hash_b}', NOW() + interval '1 hour')",
        )
        await _chk(conn, ta, "SELECT count(*) FROM password_reset_tokens", 1, "own")
        await _chk(conn, tb, "SELECT count(*) FROM password_reset_tokens", 1, "own-b")
        # Auth-path careful: token_hash lookup under wrong tenant must miss.
        await _chk(
            conn,
            tb,
            f"SELECT count(*) FROM password_reset_tokens WHERE token_hash = '{hash_a}'",
            0,
            "cross-hash",
        )
        await _chk(
            conn,
            ta,
            f"SELECT count(*) FROM password_reset_tokens WHERE token_hash = '{hash_a}'",
            1,
            "own-hash",
        )
        await _fc(conn, "SELECT count(*) FROM password_reset_tokens", "prt-fc")
        # Unset GUC: token_hash lookup also fails closed (no auth bypass).
        await _fc(
            conn,
            f"SELECT count(*) FROM password_reset_tokens WHERE token_hash = '{hash_a}'",
            "prt-hash-fc",
        )
        await conn.rollback()


@pytest.mark.asyncio
async def test_refresh_token_families_isolation():
    async with engine.begin() as conn:
        ta, tb = await _create_tenants(conn)
        ua = await _create_user(conn, ta, "RA")
        ub = await _create_user(conn, tb, "RB")
        hash_a = "c" * 64
        hash_b = "d" * 64
        await _ins(
            conn,
            ta,
            f"INSERT INTO refresh_token_families "
            f"(id, user_id, family_id, token_hash, expires_at, is_compromised) "
            f"VALUES ('rtf-{ta[:8]}', '{ua}'::uuid, 'fam-{ta[:8]}', '{hash_a}', "
            f"NOW() + interval '7 days', false)",
        )
        await _ins(
            conn,
            tb,
            f"INSERT INTO refresh_token_families "
            f"(id, user_id, family_id, token_hash, expires_at, is_compromised) "
            f"VALUES ('rtf-{tb[:8]}', '{ub}'::uuid, 'fam-{tb[:8]}', '{hash_b}', "
            f"NOW() + interval '7 days', false)",
        )
        await _chk(conn, ta, "SELECT count(*) FROM refresh_token_families", 1, "own")
        await _chk(conn, tb, "SELECT count(*) FROM refresh_token_families", 1, "own-b")
        # JWT refresh path sets tenant GUC — own hash visible; cross hidden.
        await _chk(
            conn,
            ta,
            f"SELECT count(*) FROM refresh_token_families WHERE token_hash = '{hash_a}'",
            1,
            "own-hash",
        )
        await _chk(
            conn,
            tb,
            f"SELECT count(*) FROM refresh_token_families WHERE token_hash = '{hash_a}'",
            0,
            "cross-hash",
        )
        await _fc(conn, "SELECT count(*) FROM refresh_token_families", "rtf-fc")
        await conn.rollback()


@pytest.mark.asyncio
async def test_rls_policies_intact_after_b5():
    async with engine.begin() as conn:
        r = await conn.execute(
            text("SELECT count(*) FROM pg_policies WHERE policyname LIKE 'tenant_isolation_%'")
        )
        assert r.scalar() == POLICY_COUNT, f"policies changed: {r.scalar()}"
        await conn.rollback()
