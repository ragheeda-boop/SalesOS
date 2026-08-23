"""Phase 4A Part F — ICP persistence layer tests (Postgres, canonical RLS).

Transient records only: every profile created here uses a deterministic id,
is asserted against, and is deleted in finally. No business ICP profiles are
seeded — production/local counts stay ZERO outside the test run.
"""

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import async_session
from app.modules.gtm.icp import ICPError
from app.modules.gtm.icp_persistence import (
    PostgresICPRepository,
    active_profiles_from,
)

NS = uuid.uuid5(uuid.NAMESPACE_URL, "phase4a-icp-persistence-tests")

T_A = "a0000000-0000-4000-a000-000000000001"
T_B = "b0000000-0000-4000-a000-000000000002"
PID_A = uuid.uuid5(NS, "prof-a").hex[:12]
PID_B = uuid.uuid5(NS, "prof-b").hex[:12]
# Phase 4F demo seed (scripts/seed_icp_pif_demo.py) shares T_A — purge so counts stay exact.
DEMO_SEED_ID = "pif-icp-demo"

REPO = PostgresICPRepository(None)


def _crit_kwargs():
    return dict(
        industries=["technology"],
        cities=["Riyadh"],
        employees_min=10,
        employees_max=500,
        titles=["ceo"],
        keywords=["erp"],
    )


async def _pin(db, tenant):
    await db.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant})


async def _cleanup():
    for t in (T_B, T_A):
        async with async_session() as db:
            await _pin(db, t)
            for pid in (PID_A, PID_B, DEMO_SEED_ID):
                await db.execute(
                    text("DELETE FROM icp_profiles WHERE id=:i"), {"i": pid}
                )
            await db.commit()


@pytest_asyncio.fixture(autouse=True)
async def _icp_seed_cleanup():
    await _cleanup()
    await REPO.create(
        tenant_id=T_A,
        name="A-tech",
        description="tenant A profile",
        weights={"industry": 2.0, "city": 1.0},
        profile_id=PID_A,
        **_crit_kwargs(),
    )
    await REPO.create(
        tenant_id=T_B,
        name="B-retail",
        profile_id=PID_B,
        industries=["retail"],
        cities=["Jeddah"],
        titles=["owner"],
    )
    yield
    await _cleanup()
    from app.database import engine

    await engine.dispose()


# ── isolation ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_is_tenant_scoped_cross_tenant_returns_none():
    assert await REPO.get(PID_A, tenant_id=T_A) is not None
    assert await REPO.get(PID_A, tenant_id=T_B) is None
    assert await REPO.get(PID_B, tenant_id=T_B) is not None
    assert await REPO.get(PID_B, tenant_id=T_A) is None


@pytest.mark.asyncio
async def test_no_guc_sees_zero_rows():
    async with async_session() as db:
        await db.execute(text("SELECT set_config('app.tenant_id', '', false)"))
        n = (await db.execute(text("SELECT COUNT(*) FROM icp_profiles"))).scalar()
    assert n == 0


@pytest.mark.asyncio
async def test_list_for_tenant_only_own_rows():
    la = {p.id for p in await REPO.list_for_tenant(tenant_id=T_A)}
    lb = {p.id for p in await REPO.list_for_tenant(tenant_id=T_B)}
    assert la == {PID_A} and lb == {PID_B}


# ── lifecycle / semantics parity with MemICPStore ────────────────────────


@pytest.mark.asyncio
async def test_create_roundtrip_preserves_normalized_payload():
    p = await REPO.get(PID_A, tenant_id=T_A)
    d = p.as_dict()
    assert d["criteria"]["industries"] == ["technology"]
    assert d["criteria"]["employees_min"] == 10
    assert d["weights"]["industry"] == 2.0
    assert p.schema_version == 1 and p.is_active is True


@pytest.mark.asyncio
async def test_update_bumps_version_and_merges_weights():
    u = await REPO.update(
        PID_A, tenant_id=T_A, cities=["Riyadh", "Dammam"], weights={"city": 3.0}
    )
    assert u.schema_version == 2
    assert u.criteria.cities == ["riyadh", "dammam"]
    # industry weight preserved from v1, city overridden — mem-store merge shape
    assert u.weights.industry == 2.0 and u.weights.city == 3.0


@pytest.mark.asyncio
async def test_update_bump_version_false_keeps_version():
    u = await REPO.update(PID_A, tenant_id=T_A, description="tuned", bump_version=False)
    assert u.schema_version == 1 and u.description == "tuned"


@pytest.mark.asyncio
async def test_inactive_excluded_from_active_listing_only():
    await REPO.update(PID_A, tenant_id=T_A, is_active=False)
    all_a = {p.id for p in await REPO.list_for_tenant(tenant_id=T_A)}
    act_a = {p.id for p in await REPO.list_active(tenant_id=T_A)}
    assert all_a == {PID_A} and act_a == set()
    await REPO.update(PID_A, tenant_id=T_A, is_active=True)  # restore for cleanup symmetry


@pytest.mark.asyncio
async def test_agent_contract_filter_mirrors_runtime():
    """active_profiles_from must equal the grounded agents' _active_profiles
    filter so the future runtime swap changes nothing for the 13 agents."""
    profs = await REPO.list_for_tenant(tenant_id=T_B)
    via_helper = [p.id for p in active_profiles_from(profs)]
    via_agent_rule = [
        p.id for p in profs if getattr(p, "is_active", False)
    ]
    assert via_helper == via_agent_rule == [PID_B]


@pytest.mark.asyncio
async def test_update_missing_profile_raises_keyerror_tenant_safely():
    with pytest.raises(KeyError):
        await REPO.update("doesnotexist", tenant_id=T_A, description="x")


@pytest.mark.asyncio
async def test_invalid_uuid_tenant_fails_safe():
    with pytest.raises(ICPError):
        await REPO.create(tenant_id="not-a-uuid", name="x")


@pytest.mark.asyncio
async def test_validation_rejects_empty_name_and_bad_weights():
    with pytest.raises(ICPError):
        await REPO.create(tenant_id=T_A, name="   ")
    with pytest.raises(ICPError):
        await REPO.create(
            tenant_id=T_A, name="badw", industries=[], weights={"industry": -1.0}
        )


@pytest.mark.asyncio
async def test_malformed_stored_criteria_fails_safe_not_garbage():
    """Corrupt the jsonb behind RLS (as the owning tenant), then prove the
    repository raises ICPError instead of returning a half-valid profile."""
    async with async_session() as db:
        await _pin(db, T_A)
        await db.execute(
            text(
                "UPDATE icp_profiles SET criteria=CAST(:c AS jsonb) WHERE id=:i"
            ),
            {"c": '{"industries": "should-have-been-a-list"}', "i": PID_A},
        )
        await db.commit()
    with pytest.raises(ICPError):
        await REPO.get(PID_A, tenant_id=T_A)
