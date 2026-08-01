"""DEC-118 / S04-CATB-06: Adversarial RLS for Category B6 webhook deliveries.

Table: webhook_deliveries — no tenant_id; isolate via
webhook_subscriptions.id (subscription_id). Parent is Category A (DEC-044).
POLICY_COUNT live = 47 Category A + 2 B1 + 2 B2 + 2 B3 + 2 B4 + 2 B5 + 1 B6 = 58.

Does NOT cover B7. Does NOT enable R-09 / DB-05 deferred tables
(including webhook_endpoints).
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
        {"id": a, "name": "B6 A", "slug": f"b6a-{a[:8]}"},
    )
    await session.execute(
        text("INSERT INTO tenants (id, name, slug) VALUES (:id, :name, :slug)"),
        {"id": b, "name": "B6 B", "slug": f"b6b-{b[:8]}"},
    )
    return a, b


async def _create_subscription(session, tid: str, suffix: str) -> str:
    sid = str(uuid.uuid4())
    await session.execute(text(f"SET LOCAL app.tenant_id = '{tid}'"))
    await session.execute(
        text(
            f"INSERT INTO webhook_subscriptions (id, tenant_id, url, secret) "
            f"VALUES ('{sid}', '{tid}', 'https://{suffix}.example/hook', 's{suffix}')"
        )
    )
    return sid


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
async def test_webhook_deliveries_isolation():
    async with engine.begin() as conn:
        ta, tb = await _create_tenants(conn)
        sa = await _create_subscription(conn, ta, "A")
        sb = await _create_subscription(conn, tb, "B")
        await _ins(
            conn,
            ta,
            f"INSERT INTO webhook_deliveries "
            f"(id, subscription_id, event_type, payload, status) "
            f"VALUES ('wd-{ta[:8]}', '{sa}', 'company.created', '{{}}'::jsonb, 'pending')",
        )
        await _ins(
            conn,
            tb,
            f"INSERT INTO webhook_deliveries "
            f"(id, subscription_id, event_type, payload, status) "
            f"VALUES ('wd-{tb[:8]}', '{sb}', 'company.updated', '{{}}'::jsonb, 'pending')",
        )
        await _chk(conn, ta, "SELECT count(*) FROM webhook_deliveries", 1, "own")
        await _chk(conn, tb, "SELECT count(*) FROM webhook_deliveries", 1, "own-b")
        await _chk(
            conn,
            tb,
            f"SELECT count(*) FROM webhook_deliveries WHERE subscription_id = '{sa}'",
            0,
            "cross",
        )
        await _chk(
            conn,
            ta,
            f"SELECT count(*) FROM webhook_deliveries WHERE subscription_id = '{sa}'",
            1,
            "own-sub",
        )
        await _fc(conn, "SELECT count(*) FROM webhook_deliveries", "wd-fc")
        await conn.rollback()


@pytest.mark.asyncio
async def test_rls_policies_intact_after_b6():
    async with engine.begin() as conn:
        r = await conn.execute(
            text("SELECT count(*) FROM pg_policies WHERE policyname LIKE 'tenant_isolation_%'")
        )
        assert r.scalar() == POLICY_COUNT, f"policies changed: {r.scalar()}"
        r2 = await conn.execute(
            text(
                "SELECT count(*) FROM pg_policies "
                "WHERE tablename = 'webhook_deliveries' "
                "AND policyname = 'tenant_isolation_webhook_deliveries'"
            )
        )
        assert r2.scalar() == 1, "missing webhook_deliveries policy"
        # Deferred-8 webhook_endpoints must remain without tenant_isolation policy.
        r3 = await conn.execute(
            text(
                "SELECT count(*) FROM pg_policies "
                "WHERE tablename = 'webhook_endpoints' "
                "AND policyname LIKE 'tenant_isolation_%'"
            )
        )
        assert r3.scalar() == 0, "webhook_endpoints must not gain Category B RLS"
        await conn.rollback()
