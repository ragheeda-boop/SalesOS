"""Phase 4C — ICP admin API unit tests (handler-level).

Handlers are exercised directly with explicit tenant identity (the same
dependency value auth would inject). Persistence is the real Postgres
repository behind canonical RLS; rows are transient with deterministic ids.
"""

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import async_session
from app.modules.gtm.icp import ICPError
from app.modules.gtm.icp_admin_router import (
    ICPCriteriaIn,
    ICPProfileCreate,
    ICPProfilePatch,
    ICPWeightsIn,
    create_icp_profile,
    get_icp_profile,
    list_icp_profiles,
    update_icp_profile,
)

NS = uuid.uuid5(uuid.NAMESPACE_URL, "phase4c-icp-admin-tests")
T_A = "a0000000-0000-4000-a000-000000000001"
T_B = "b0000000-0000-4000-a000-000000000002"


async def _pin(db, tenant):
    await db.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant})


async def _cleanup():
    async with async_session() as db:
        for t in (T_B, T_A):
            await _pin(db, t)
            await db.execute(
                text(
                    "DELETE FROM icp_profiles WHERE name LIKE 'phase4c-%' "
                    "OR tenant_id=CAST(:t AS uuid)"
                ),
                {"t": t},
            )
        await db.commit()


@pytest_asyncio.fixture(autouse=True)
async def _cleanup_fixture():
    await _cleanup()
    yield
    await _cleanup()
    from app.database import engine

    await engine.dispose()


def _create_payload(name="phase4c-tech", **crit):
    return ICPProfileCreate(
        name=name,
        description="unit fixture",
        criteria=ICPCriteriaIn(**{"industries": ["technology"], **crit}),
        weights=ICPWeightsIn(industry=2.0),
    )


@pytest.mark.asyncio
async def test_create_returns_201_shape_and_persists():
    out = await create_icp_profile(_create_payload(), tenant_id=T_A)
    assert out["tenant_id"] == T_A and out["is_active"] is True
    assert out["criteria"]["industries"] == ["technology"]
    got = await get_icp_profile(out["id"], tenant_id=T_A)
    assert got["name"] == "phase4c-tech"


@pytest.mark.asyncio
async def test_get_cross_tenant_404():
    from fastapi import HTTPException

    out = await create_icp_profile(_create_payload(), tenant_id=T_A)
    with pytest.raises(HTTPException) as ei:
        await get_icp_profile(out["id"], tenant_id=T_B)
    assert ei.value.status_code == 404


@pytest.mark.asyncio
async def test_list_is_tenant_scoped():
    a = await create_icp_profile(_create_payload("phase4c-a"), tenant_id=T_A)
    b = await create_icp_profile(_create_payload("phase4c-b"), tenant_id=T_B)
    la = (await list_icp_profiles(tenant_id=T_A))["profiles"]
    ids_a = {p["id"] for p in la}
    assert a["id"] in ids_a and b["id"] not in ids_a


@pytest.mark.asyncio
async def test_active_only_filter():
    p = await create_icp_profile(_create_payload("phase4c-inactive"), tenant_id=T_A)
    await update_icp_profile(
        p["id"], ICPProfilePatch(is_active=False), tenant_id=T_A
    )
    all_rows = (await list_icp_profiles(tenant_id=T_A, active_only=False))["profiles"]
    act = (await list_icp_profiles(tenant_id=T_A, active_only=True))["profiles"]
    assert p["id"] in {r["id"] for r in all_rows}
    assert p["id"] not in {r["id"] for r in act}


@pytest.mark.asyncio
async def test_patch_bumps_version_and_updates_criteria():
    p = await create_icp_profile(_create_payload(), tenant_id=T_A)
    out = await update_icp_profile(
        p["id"],
        ICPProfilePatch(criteria=ICPCriteriaIn(industries=["fintech"], cities=["Jeddah"])),
        tenant_id=T_A,
    )
    assert out["schema_version"] == 2
    assert out["criteria"]["industries"] == ["fintech"]
    assert out["weights"]["industry"] == 2.0  # untouched weights preserved


@pytest.mark.asyncio
async def test_patch_missing_profile_404_and_invalid_tenant_422():
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as e404:
        await update_icp_profile("nope", ICPProfilePatch(name="x"), tenant_id=T_A)
    assert e404.value.status_code == 404
    # invalid tenant identity never reaches persistence: handler maps
    # ICPError → 422 (auth-injected tenants are valid in production)
    with pytest.raises(HTTPException) as e422:
        await create_icp_profile(_create_payload(), tenant_id="definitely-not-a-uuid-xx")
    assert e422.value.status_code == 422


@pytest.mark.asyncio
async def test_router_registered_under_auth():
    from app.boot.routers import register_routers
    from app.main import app  # noqa: F401  (imports boot wiring transitively)
    import inspect

    src = inspect.getsource(register_routers)
    assert "icp_admin_router" in src
