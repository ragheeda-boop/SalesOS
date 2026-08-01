"""Sprint 04 Story 4.6 (S04-06): Adversarial RLS coverage — remaining high-value tables.

Extends S04-01 (read 7/7) and S04-05 (write 8/8) without re-testing those sampled
tables. Targets Category A tenant tables that already have CREATE TABLE + RLS
(POLICY_COUNT 58 = 47 Category A + B1–B6) but were not in the original sample:

  contacts, company_features, commercial_opportunities, opportunities,
  tasks, tenant_configs, webhook_subscriptions

Does NOT change RLS inventory. Does NOT enable RLS on R-09 / Category B tables.
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.database import engine

RLS_REJECT = "(?i)row-level security"
# 47 Category A + B1–B6 (DEC-112…DEC-118)
POLICY_COUNT = 58


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    yield
    await engine.dispose()


async def _create_tenants(session) -> tuple[str, str]:
    a, b = str(uuid.uuid4()), str(uuid.uuid4())
    await session.execute(
        text("INSERT INTO tenants (id, name, slug) VALUES (:id, :name, :slug)"),
        {"id": a, "name": "S04-06 A", "slug": f"s046a-{a[:8]}"},
    )
    await session.execute(
        text("INSERT INTO tenants (id, name, slug) VALUES (:id, :name, :slug)"),
        {"id": b, "name": "S04-06 B", "slug": f"s046b-{b[:8]}"},
    )
    return a, b


async def _create_company(session, tid: str, cr_suffix: str) -> str:
    """Insert a companies row under tenant context; return company UUID string."""
    cid = str(uuid.uuid4())
    # Prefer f-string UUID literals — avoid `:id::uuid` SQLAlchemy bind cast bug (DEC-020).
    await session.execute(text(f"SET LOCAL app.tenant_id = '{tid}'"))
    await session.execute(
        text(
            f"INSERT INTO companies (id, tenant_id, cr_number, name_ar, name_en) "
            f"VALUES ('{cid}'::uuid, '{tid}'::uuid, "
            f"'C{cr_suffix}-{tid[:8]}', '{cr_suffix}', '{cr_suffix}')"
        )
    )
    return cid


async def _ins(session, tid: str, sql: str, params: dict | None = None):
    await session.execute(text(f"SET LOCAL app.tenant_id = '{tid}'"))
    return await session.execute(text(sql), params or {})


async def _chk(session, tid: str, sql: str, expected: int, label: str):
    await session.execute(text(f"SET LOCAL app.tenant_id = '{tid}'"))
    r = await session.execute(text(sql))
    assert r.scalar() == expected, f"[{label}] exp={expected} got={r.scalar()}"


async def _fc(session, sql: str, label: str):
    await session.execute(text("RESET app.tenant_id"))
    r = await session.execute(text(sql))
    assert r.scalar() == 0, f"[{label}] fail-closed violation: {r.scalar()}"


async def _rw(session, tid: str, sql: str, expected: int, label: str):
    await session.execute(text(f"SET LOCAL app.tenant_id = '{tid}'"))
    r = await session.execute(text(sql))
    assert r.rowcount == expected, f"[{label}] expected {expected} rows, got {r.rowcount}"


# ── Read isolation (S04-01 pattern) ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_contacts_isolation():
    async with engine.begin() as conn:
        ta, tb = await _create_tenants(conn)
        ca = await _create_company(conn, ta, "CA")
        cb = await _create_company(conn, tb, "CB")
        await _ins(
            conn,
            ta,
            f"INSERT INTO contacts (id, tenant_id, company_id, name) VALUES (gen_random_uuid(), '{ta}'::uuid, '{ca}'::uuid, 'ContactA')",  # noqa: E501
        )
        await _ins(
            conn,
            tb,
            f"INSERT INTO contacts (id, tenant_id, company_id, name) VALUES (gen_random_uuid(), '{tb}'::uuid, '{cb}'::uuid, 'ContactB')",  # noqa: E501
        )
        await _chk(
            conn, ta, f"SELECT count(*) FROM contacts WHERE tenant_id='{ta}'::uuid", 1, "own"
        )
        await _chk(
            conn, tb, f"SELECT count(*) FROM contacts WHERE tenant_id='{ta}'::uuid", 0, "cross"
        )
        await _fc(conn, f"SELECT count(*) FROM contacts WHERE tenant_id='{ta}'::uuid", "contacts")
        await conn.rollback()


@pytest.mark.asyncio
async def test_company_features_isolation():
    async with engine.begin() as conn:
        ta, tb = await _create_tenants(conn)
        ca = await _create_company(conn, ta, "FA")
        cb = await _create_company(conn, tb, "FB")
        await _ins(
            conn,
            ta,
            f"INSERT INTO company_features (tenant_id, company_id, feature_name, score, computed_at) VALUES ('{ta}', '{ca}', 'fit_score', 0.8, now())",  # noqa: E501
        )
        await _ins(
            conn,
            tb,
            f"INSERT INTO company_features (tenant_id, company_id, feature_name, score, computed_at) VALUES ('{tb}', '{cb}', 'fit_score', 0.7, now())",  # noqa: E501
        )
        await _chk(
            conn, ta, f"SELECT count(*) FROM company_features WHERE tenant_id='{ta}'", 1, "own"
        )
        await _chk(
            conn, tb, f"SELECT count(*) FROM company_features WHERE tenant_id='{ta}'", 0, "cross"
        )
        await _fc(
            conn,
            f"SELECT count(*) FROM company_features WHERE tenant_id='{ta}'",
            "company_features",
        )
        await conn.rollback()


@pytest.mark.asyncio
async def test_commercial_opportunities_isolation():
    async with engine.begin() as conn:
        ta, tb = await _create_tenants(conn)
        await _ins(
            conn,
            ta,
            f"INSERT INTO commercial_opportunities (id, tenant_id, company_id, name) VALUES ('{uuid.uuid4()}', '{ta}', 'co-a', 'OppA')",  # noqa: E501
        )
        await _ins(
            conn,
            tb,
            f"INSERT INTO commercial_opportunities (id, tenant_id, company_id, name) VALUES ('{uuid.uuid4()}', '{tb}', 'co-b', 'OppB')",  # noqa: E501
        )
        await _chk(
            conn,
            ta,
            f"SELECT count(*) FROM commercial_opportunities WHERE tenant_id='{ta}'",
            1,
            "own",
        )
        await _chk(
            conn,
            tb,
            f"SELECT count(*) FROM commercial_opportunities WHERE tenant_id='{ta}'",
            0,
            "cross",
        )
        await _fc(
            conn,
            f"SELECT count(*) FROM commercial_opportunities WHERE tenant_id='{ta}'",
            "commercial_opportunities",
        )
        await conn.rollback()


@pytest.mark.asyncio
async def test_opportunities_isolation():
    async with engine.begin() as conn:
        ta, tb = await _create_tenants(conn)
        await _ins(
            conn,
            ta,
            f"INSERT INTO opportunities (id, tenant_id, title) VALUES (gen_random_uuid(), '{ta}'::uuid, 'RevA')",  # noqa: E501
        )
        await _ins(
            conn,
            tb,
            f"INSERT INTO opportunities (id, tenant_id, title) VALUES (gen_random_uuid(), '{tb}'::uuid, 'RevB')",  # noqa: E501
        )
        await _chk(
            conn, ta, f"SELECT count(*) FROM opportunities WHERE tenant_id='{ta}'::uuid", 1, "own"
        )
        await _chk(
            conn, tb, f"SELECT count(*) FROM opportunities WHERE tenant_id='{ta}'::uuid", 0, "cross"
        )
        await _fc(
            conn,
            f"SELECT count(*) FROM opportunities WHERE tenant_id='{ta}'::uuid",
            "opportunities",
        )
        await conn.rollback()


@pytest.mark.asyncio
async def test_tasks_isolation():
    async with engine.begin() as conn:
        ta, tb = await _create_tenants(conn)
        await _ins(
            conn,
            ta,
            f"INSERT INTO tasks (id, tenant_id, title) VALUES (gen_random_uuid(), '{ta}'::uuid, 'TaskA')",  # noqa: E501
        )
        await _ins(
            conn,
            tb,
            f"INSERT INTO tasks (id, tenant_id, title) VALUES (gen_random_uuid(), '{tb}'::uuid, 'TaskB')",  # noqa: E501
        )
        await _chk(conn, ta, f"SELECT count(*) FROM tasks WHERE tenant_id='{ta}'::uuid", 1, "own")
        await _chk(conn, tb, f"SELECT count(*) FROM tasks WHERE tenant_id='{ta}'::uuid", 0, "cross")
        await _fc(conn, f"SELECT count(*) FROM tasks WHERE tenant_id='{ta}'::uuid", "tasks")
        await conn.rollback()


@pytest.mark.asyncio
async def test_tenant_configs_isolation():
    async with engine.begin() as conn:
        ta, tb = await _create_tenants(conn)
        await _ins(
            conn,
            ta,
            f"INSERT INTO tenant_configs (tenant_id, key, yaml_content, version) VALUES ('{ta}', 'cfg.a', 'a: 1', 1)",  # noqa: E501
        )
        await _ins(
            conn,
            tb,
            f"INSERT INTO tenant_configs (tenant_id, key, yaml_content, version) VALUES ('{tb}', 'cfg.b', 'b: 1', 1)",  # noqa: E501
        )
        await _chk(
            conn, ta, f"SELECT count(*) FROM tenant_configs WHERE tenant_id='{ta}'", 1, "own"
        )
        await _chk(
            conn, tb, f"SELECT count(*) FROM tenant_configs WHERE tenant_id='{ta}'", 0, "cross"
        )
        await _fc(
            conn, f"SELECT count(*) FROM tenant_configs WHERE tenant_id='{ta}'", "tenant_configs"
        )
        await conn.rollback()


@pytest.mark.asyncio
async def test_webhook_subscriptions_isolation():
    async with engine.begin() as conn:
        ta, tb = await _create_tenants(conn)
        await _ins(
            conn,
            ta,
            f"INSERT INTO webhook_subscriptions (id, tenant_id, url, secret) VALUES ('{uuid.uuid4()}', '{ta}', 'https://a.example/hook', 'sa')",  # noqa: E501
        )
        await _ins(
            conn,
            tb,
            f"INSERT INTO webhook_subscriptions (id, tenant_id, url, secret) VALUES ('{uuid.uuid4()}', '{tb}', 'https://b.example/hook', 'sb')",  # noqa: E501
        )
        await _chk(
            conn, ta, f"SELECT count(*) FROM webhook_subscriptions WHERE tenant_id='{ta}'", 1, "own"
        )
        await _chk(
            conn,
            tb,
            f"SELECT count(*) FROM webhook_subscriptions WHERE tenant_id='{ta}'",
            0,
            "cross",
        )
        await _fc(
            conn,
            f"SELECT count(*) FROM webhook_subscriptions WHERE tenant_id='{ta}'",
            "webhook_subscriptions",
        )
        await conn.rollback()


@pytest.mark.asyncio
async def test_rls_policies_intact_s04_06():
    """Sanity: DEC-044 inventory unchanged (do not reopen STORY-02-01)."""
    async with engine.begin() as conn:
        r = await conn.execute(
            text("SELECT count(*) FROM pg_policies WHERE policyname LIKE 'tenant_isolation_%'")
        )
        assert r.scalar() == POLICY_COUNT, f"policies changed: {r.scalar()}"
        await conn.rollback()


# ── Write fail-closed (S04-05 pattern) ──────────────────────────────────────


@pytest.mark.asyncio
async def test_contacts_write_fail_closed():
    async with engine.begin() as conn:
        ta, tb = await _create_tenants(conn)
        ca = await _create_company(conn, ta, "WA")
        cb = await _create_company(conn, tb, "WB")
        await _ins(
            conn,
            ta,
            f"INSERT INTO contacts (id, tenant_id, company_id, name) VALUES (gen_random_uuid(), '{ta}'::uuid, '{ca}'::uuid, 'ContactA')",  # noqa: E501
        )
        await _ins(
            conn,
            tb,
            f"INSERT INTO contacts (id, tenant_id, company_id, name) VALUES (gen_random_uuid(), '{tb}'::uuid, '{cb}'::uuid, 'ContactB')",  # noqa: E501
        )
        await _rw(
            conn,
            ta,
            f"UPDATE contacts SET name='ContactA2' WHERE tenant_id='{ta}'::uuid",
            1,
            "contacts own update",
        )
        await _rw(
            conn,
            ta,
            f"UPDATE contacts SET name='MUT' WHERE tenant_id='{tb}'::uuid",
            0,
            "contacts cross update",
        )
        await _chk(
            conn,
            tb,
            f"SELECT count(*) FROM contacts WHERE tenant_id='{tb}'::uuid AND name='ContactB'",
            1,
            "contacts B untouched",
        )
        await _rw(
            conn,
            ta,
            f"DELETE FROM contacts WHERE tenant_id='{tb}'::uuid",
            0,
            "contacts cross delete",
        )
        with pytest.raises(DBAPIError, match=RLS_REJECT):
            await _ins(
                conn,
                ta,
                f"INSERT INTO contacts (id, tenant_id, company_id, name) VALUES (gen_random_uuid(), '{tb}'::uuid, '{cb}'::uuid, 'X')",  # noqa: E501
            )
        await conn.rollback()


@pytest.mark.asyncio
async def test_company_features_write_fail_closed():
    async with engine.begin() as conn:
        ta, tb = await _create_tenants(conn)
        ca = await _create_company(conn, ta, "WFA")
        cb = await _create_company(conn, tb, "WFB")
        await _ins(
            conn,
            ta,
            f"INSERT INTO company_features (tenant_id, company_id, feature_name, score, computed_at) VALUES ('{ta}', '{ca}', 'fit_score', 0.8, now())",  # noqa: E501
        )
        await _ins(
            conn,
            tb,
            f"INSERT INTO company_features (tenant_id, company_id, feature_name, score, computed_at) VALUES ('{tb}', '{cb}', 'fit_score', 0.7, now())",  # noqa: E501
        )
        await _rw(
            conn,
            ta,
            f"UPDATE company_features SET score=0.9 WHERE tenant_id='{ta}'",
            1,
            "cf own update",
        )
        await _rw(
            conn,
            ta,
            f"UPDATE company_features SET score=0.1 WHERE tenant_id='{tb}'",
            0,
            "cf cross update",
        )
        await _chk(
            conn,
            tb,
            f"SELECT count(*) FROM company_features WHERE tenant_id='{tb}' AND score=0.7",
            1,
            "cf B untouched",
        )
        await _rw(
            conn, ta, f"DELETE FROM company_features WHERE tenant_id='{tb}'", 0, "cf cross delete"
        )
        with pytest.raises(DBAPIError, match=RLS_REJECT):
            await _ins(
                conn,
                ta,
                f"INSERT INTO company_features (tenant_id, company_id, feature_name, score, computed_at) VALUES ('{tb}', '{cb}', 'leak_score', 0.5, now())",  # noqa: E501
            )
        await conn.rollback()


@pytest.mark.asyncio
async def test_commercial_opportunities_write_fail_closed():
    async with engine.begin() as conn:
        ta, tb = await _create_tenants(conn)
        await _ins(
            conn,
            ta,
            f"INSERT INTO commercial_opportunities (id, tenant_id, company_id, name) VALUES ('{uuid.uuid4()}', '{ta}', 'co-a', 'OppA')",  # noqa: E501
        )
        await _ins(
            conn,
            tb,
            f"INSERT INTO commercial_opportunities (id, tenant_id, company_id, name) VALUES ('{uuid.uuid4()}', '{tb}', 'co-b', 'OppB')",  # noqa: E501
        )
        await _rw(
            conn,
            ta,
            f"UPDATE commercial_opportunities SET name='OppA2' WHERE tenant_id='{ta}'",
            1,
            "coop own update",
        )
        await _rw(
            conn,
            ta,
            f"UPDATE commercial_opportunities SET name='MUT' WHERE tenant_id='{tb}'",
            0,
            "coop cross update",
        )
        await _chk(
            conn,
            tb,
            f"SELECT count(*) FROM commercial_opportunities WHERE tenant_id='{tb}' AND name='OppB'",
            1,
            "coop B untouched",
        )
        await _rw(
            conn,
            ta,
            f"DELETE FROM commercial_opportunities WHERE tenant_id='{tb}'",
            0,
            "coop cross delete",
        )
        with pytest.raises(DBAPIError, match=RLS_REJECT):
            await _ins(
                conn,
                ta,
                f"INSERT INTO commercial_opportunities (id, tenant_id, company_id, name) VALUES ('{uuid.uuid4()}', '{tb}', 'co-x', 'OppX')",  # noqa: E501
            )
        await conn.rollback()


@pytest.mark.asyncio
async def test_opportunities_write_fail_closed():
    async with engine.begin() as conn:
        ta, tb = await _create_tenants(conn)
        await _ins(
            conn,
            ta,
            f"INSERT INTO opportunities (id, tenant_id, title) VALUES (gen_random_uuid(), '{ta}'::uuid, 'RevA')",  # noqa: E501
        )
        await _ins(
            conn,
            tb,
            f"INSERT INTO opportunities (id, tenant_id, title) VALUES (gen_random_uuid(), '{tb}'::uuid, 'RevB')",  # noqa: E501
        )
        await _rw(
            conn,
            ta,
            f"UPDATE opportunities SET title='RevA2' WHERE tenant_id='{ta}'::uuid",
            1,
            "opp own update",
        )
        await _rw(
            conn,
            ta,
            f"UPDATE opportunities SET title='MUT' WHERE tenant_id='{tb}'::uuid",
            0,
            "opp cross update",
        )
        await _chk(
            conn,
            tb,
            f"SELECT count(*) FROM opportunities WHERE tenant_id='{tb}'::uuid AND title='RevB'",
            1,
            "opp B untouched",
        )
        await _rw(
            conn,
            ta,
            f"DELETE FROM opportunities WHERE tenant_id='{tb}'::uuid",
            0,
            "opp cross delete",
        )
        with pytest.raises(DBAPIError, match=RLS_REJECT):
            await _ins(
                conn,
                ta,
                f"INSERT INTO opportunities (id, tenant_id, title) VALUES (gen_random_uuid(), '{tb}'::uuid, 'RevX')",  # noqa: E501
            )
        await conn.rollback()


@pytest.mark.asyncio
async def test_tasks_write_fail_closed():
    async with engine.begin() as conn:
        ta, tb = await _create_tenants(conn)
        await _ins(
            conn,
            ta,
            f"INSERT INTO tasks (id, tenant_id, title) VALUES (gen_random_uuid(), '{ta}'::uuid, 'TaskA')",  # noqa: E501
        )
        await _ins(
            conn,
            tb,
            f"INSERT INTO tasks (id, tenant_id, title) VALUES (gen_random_uuid(), '{tb}'::uuid, 'TaskB')",  # noqa: E501
        )
        await _rw(
            conn,
            ta,
            f"UPDATE tasks SET title='TaskA2' WHERE tenant_id='{ta}'::uuid",
            1,
            "tasks own update",
        )
        await _rw(
            conn,
            ta,
            f"UPDATE tasks SET title='MUT' WHERE tenant_id='{tb}'::uuid",
            0,
            "tasks cross update",
        )
        await _chk(
            conn,
            tb,
            f"SELECT count(*) FROM tasks WHERE tenant_id='{tb}'::uuid AND title='TaskB'",
            1,
            "tasks B untouched",
        )
        await _rw(
            conn, ta, f"DELETE FROM tasks WHERE tenant_id='{tb}'::uuid", 0, "tasks cross delete"
        )
        with pytest.raises(DBAPIError, match=RLS_REJECT):
            await _ins(
                conn,
                ta,
                f"INSERT INTO tasks (id, tenant_id, title) VALUES (gen_random_uuid(), '{tb}'::uuid, 'TaskX')",  # noqa: E501
            )
        await conn.rollback()


@pytest.mark.asyncio
async def test_tenant_configs_write_fail_closed():
    async with engine.begin() as conn:
        ta, tb = await _create_tenants(conn)
        await _ins(
            conn,
            ta,
            f"INSERT INTO tenant_configs (tenant_id, key, yaml_content, version) VALUES ('{ta}', 'cfg.a', 'a: 1', 1)",  # noqa: E501
        )
        await _ins(
            conn,
            tb,
            f"INSERT INTO tenant_configs (tenant_id, key, yaml_content, version) VALUES ('{tb}', 'cfg.b', 'b: 1', 1)",  # noqa: E501
        )
        await _rw(
            conn,
            ta,
            f"UPDATE tenant_configs SET yaml_content='a: 2' WHERE tenant_id='{ta}'",
            1,
            "tc own update",
        )
        await _rw(
            conn,
            ta,
            f"UPDATE tenant_configs SET yaml_content='MUT' WHERE tenant_id='{tb}'",
            0,
            "tc cross update",
        )
        await _chk(
            conn,
            tb,
            f"SELECT count(*) FROM tenant_configs WHERE tenant_id='{tb}' AND yaml_content='b: 1'",
            1,
            "tc B untouched",
        )
        await _rw(
            conn, ta, f"DELETE FROM tenant_configs WHERE tenant_id='{tb}'", 0, "tc cross delete"
        )
        with pytest.raises(DBAPIError, match=RLS_REJECT):
            await _ins(
                conn,
                ta,
                f"INSERT INTO tenant_configs (tenant_id, key, yaml_content, version) VALUES ('{tb}', 'cfg.x', 'x: 1', 1)",  # noqa: E501
            )
        await conn.rollback()


@pytest.mark.asyncio
async def test_webhook_subscriptions_write_fail_closed():
    async with engine.begin() as conn:
        ta, tb = await _create_tenants(conn)
        await _ins(
            conn,
            ta,
            f"INSERT INTO webhook_subscriptions (id, tenant_id, url, secret) VALUES ('{uuid.uuid4()}', '{ta}', 'https://a.example/hook', 'sa')",  # noqa: E501
        )
        await _ins(
            conn,
            tb,
            f"INSERT INTO webhook_subscriptions (id, tenant_id, url, secret) VALUES ('{uuid.uuid4()}', '{tb}', 'https://b.example/hook', 'sb')",  # noqa: E501
        )
        await _rw(
            conn,
            ta,
            (
                "UPDATE webhook_subscriptions SET url='https://a2.example/hook' "
                f"WHERE tenant_id='{ta}'"
            ),
            1,
            "wh own update",
        )
        await _rw(
            conn,
            ta,
            (
                "UPDATE webhook_subscriptions SET url='https://mut.example/hook' "
                f"WHERE tenant_id='{tb}'"
            ),
            0,
            "wh cross update",
        )
        await _chk(
            conn,
            tb,
            f"SELECT count(*) FROM webhook_subscriptions WHERE tenant_id='{tb}' AND url='https://b.example/hook'",  # noqa: E501
            1,
            "wh B untouched",
        )
        await _rw(
            conn,
            ta,
            f"DELETE FROM webhook_subscriptions WHERE tenant_id='{tb}'",
            0,
            "wh cross delete",
        )
        with pytest.raises(DBAPIError, match=RLS_REJECT):
            await _ins(
                conn,
                ta,
                f"INSERT INTO webhook_subscriptions (id, tenant_id, url, secret) VALUES ('{uuid.uuid4()}', '{tb}', 'https://x.example/hook', 'sx')",  # noqa: E501
            )
        await conn.rollback()
