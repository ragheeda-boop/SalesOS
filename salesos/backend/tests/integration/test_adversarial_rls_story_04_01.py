"""Phase 1 D3-ready: adversarial RLS after STORY-04-01 tenant Owner Platform columns.

Validates that additive columns on ``tenants``
(plan_id / region / data_residency / provisioning_status / trial_ends_at)
do not weaken Category-A RLS / DEC-085 ``set_config`` isolation.

Requires Alembic head >= ``f6b2e84c1a90`` (non-prod migrate). Skips gracefully
when columns are absent so pre-migrate CI remains green.

Does NOT touch DEC-085. No Production GO.
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import engine

POLICY_COUNT = 69  # 67 prior + STORY-08-02/08-03 tenant_isolation policies


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    yield
    await engine.dispose()


async def _owner_platform_columns_present(session) -> bool:
    r = await session.execute(
        text(
            "SELECT count(*) FROM information_schema.columns "
            "WHERE table_name = 'tenants' AND column_name IN "
            "('plan_id','region','data_residency','provisioning_status','trial_ends_at')"
        )
    )
    return int(r.scalar() or 0) == 5


async def _create_tenants_with_owner_fields(session) -> tuple[str, str]:
    a, b = str(uuid.uuid4()), str(uuid.uuid4())
    await session.execute(
        text(
            "INSERT INTO tenants ("
            "id, name, slug, plan, plan_id, region, data_residency, "
            "provisioning_status, trial_ends_at"
            ") VALUES ("
            f"'{a}'::uuid, 'S04-01 A', 's041a-{a[:8]}', 'starter', "
            f"'plan_starter_v1', 'me-central-1', 'ae', 'active', "
            f"NOW() + interval '14 days'"
            ")"
        )
    )
    await session.execute(
        text(
            "INSERT INTO tenants ("
            "id, name, slug, plan, plan_id, region, data_residency, "
            "provisioning_status, trial_ends_at"
            ") VALUES ("
            f"'{b}'::uuid, 'S04-01 B', 's041b-{b[:8]}', 'growth', "
            f"'plan_growth_v1', 'eu-west-1', 'eu', 'pending', NULL"
            ")"
        )
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


@pytest.mark.asyncio
async def test_story_04_01_owner_fields_persist_and_isolation():
    """New tenant columns persist; child-table RLS isolation still holds."""
    async with engine.begin() as conn:
        if not await _owner_platform_columns_present(conn):
            pytest.skip("STORY-04-01 columns absent — apply f6b2e84c1a90 first")

        ta, tb = await _create_tenants_with_owner_fields(conn)

        # Prove Owner Platform fields round-trip (no GUC required for tenants PK insert).
        r = await conn.execute(
            text(
                f"SELECT plan_id, region, data_residency, provisioning_status "
                f"FROM tenants WHERE id = '{ta}'::uuid"
            )
        )
        row = r.one()
        assert row[0] == "plan_starter_v1"
        assert row[1] == "me-central-1"
        assert row[2] == "ae"
        assert row[3] == "active"

        await _ins(
            conn,
            ta,
            f"INSERT INTO companies (tenant_id, cr_number, name_ar, name_en) "
            f"VALUES ('{ta}'::uuid, 'OA-{ta[:8]}', 'A', 'A')",
        )
        await _ins(
            conn,
            tb,
            f"INSERT INTO companies (tenant_id, cr_number, name_ar, name_en) "
            f"VALUES ('{tb}'::uuid, 'OB-{tb[:8]}', 'B', 'B')",
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
async def test_story_04_01_update_owner_fields_keeps_child_isolation():
    """Updating Owner Platform fields must not open cross-tenant reads."""
    async with engine.begin() as conn:
        if not await _owner_platform_columns_present(conn):
            pytest.skip("STORY-04-01 columns absent — apply f6b2e84c1a90 first")

        ta, tb = await _create_tenants_with_owner_fields(conn)
        await conn.execute(
            text(
                f"UPDATE tenants SET plan_id = 'plan_updated', "
                f"provisioning_status = 'suspended', region = 'me-south-1' "
                f"WHERE id = '{ta}'::uuid"
            )
        )
        r = await conn.execute(
            text(f"SELECT plan_id, provisioning_status FROM tenants WHERE id='{ta}'::uuid")
        )
        plan_id, status = r.one()
        assert plan_id == "plan_updated"
        assert status == "suspended"

        await _ins(
            conn,
            ta,
            f"INSERT INTO companies (tenant_id, cr_number, name_ar, name_en) "
            f"VALUES ('{ta}'::uuid, 'UA-{ta[:8]}', 'A', 'A')",
        )
        await _chk(
            conn, tb, f"SELECT count(*) FROM companies WHERE tenant_id='{ta}'::uuid", 0, "cross"
        )
        await _fc(
            conn, f"SELECT count(*) FROM companies WHERE tenant_id='{ta}'::uuid", "companies-fc"
        )
        await conn.rollback()


@pytest.mark.asyncio
async def test_story_04_01_policy_count_unchanged():
    """Additive columns must not invent/drop RLS policies (POLICY_COUNT pin)."""
    async with engine.begin() as conn:
        if not await _owner_platform_columns_present(conn):
            pytest.skip("STORY-04-01 columns absent — apply f6b2e84c1a90 first")
        r = await conn.execute(text("SELECT count(*) FROM pg_policies"))
        count = int(r.scalar() or 0)
        assert count == POLICY_COUNT, f"POLICY_COUNT drift: expected {POLICY_COUNT} got {count}"
        await conn.rollback()
