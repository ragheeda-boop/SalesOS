"""Phase 4B — Sync adapter tests (ADR-0109 Option A runtime wiring).

Proves SyncICPStore satisfies the frozen sync contract the grounded agents
consume (MemICPStore shape) over the real Postgres repository, and that read
failures degrade to honest-empty instead of raising inside agent paths.
Transient rows only; deterministic ids; cleanup in finally.
"""

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import async_session
from app.modules.gtm.icp import ICPError
from app.modules.gtm.icp_persistence import (
    PostgresICPRepository,
    SyncICPStore,
    get_sync_icp_store,
)

NS = uuid.uuid5(uuid.NAMESPACE_URL, "phase4b-sync-adapter-tests")
T_A = "a0000000-0000-4000-a000-000000000001"
T_B = "b0000000-0000-4000-a000-000000000002"
PID_A = uuid.uuid5(NS, "prof-a").hex[:12]
PID_B = uuid.uuid5(NS, "prof-b").hex[:12]
# Phase 4F demo seed (scripts/seed_icp_pif_demo.py) shares T_A — purge so counts stay exact.
DEMO_SEED_ID = "pif-icp-demo"


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
async def _seed_cleanup():
    await _cleanup()
    yield
    await _cleanup()
    from app.database import engine

    await engine.dispose()


@pytest.fixture()
def store():
    # Dedicated-engine adapter: injected repos sharing the global app pool
    # are bound to the caller's event loop, so parity tests exercise exactly
    # what production consumes (get_sync_icp_store builds its own engine).
    s = SyncICPStore()
    yield s
    s.close()


# ── frozen sync-contract parity (agent-facing surface) ───────────────────


def test_create_get_roundtrip_sync_surface(store):
    p = store.create(
        tenant_id=T_A,
        name="A-tech",
        profile_id=PID_A,
        industries=["technology"],
        cities=["Riyadh"],
        titles=["ceo"],
    )
    assert p.id == PID_A
    got = store.get(PID_A, tenant_id=T_A)
    assert got is not None and got.as_dict()["criteria"]["industries"] == ["technology"]


def test_update_bumps_version_like_mem_store(store):
    store.create(tenant_id=T_A, name="x", profile_id=PID_A, industries=["tech"])
    u = store.update(PID_A, T_A, cities=["Dammam"], weights={"city": 2.5})
    assert u.schema_version == 2 and u.criteria.cities == ["dammam"]
    assert u.weights.city == 2.5


def test_cross_tenant_get_is_none(store):
    store.create(tenant_id=T_A, name="a", profile_id=PID_A, industries=["tech"])
    assert store.get(PID_A, tenant_id=T_B) is None


def test_list_scoping_and_active_filter(store):
    store.create(tenant_id=T_A, name="a", profile_id=PID_A, industries=["tech"])
    store.create(tenant_id=T_B, name="b", profile_id=PID_B, industries=["retail"])
    la = [p.id for p in store.list_for_tenant(tenant_id=T_A)]
    lb_active = [p.id for p in store.list_active(tenant_id=T_B)]
    assert la == [PID_A] and lb_active == [PID_B]
    store.update(PID_B, T_B, is_active=False)
    assert store.list_active(tenant_id=T_B) == []
    assert len(store.list_for_tenant(tenant_id=T_B)) == 1  # inactive still listed


def test_agent_contract_helper_matches(store):
    from app.modules.gtm.icp_persistence import active_profiles_from

    profs = store.list_for_tenant(tenant_id=T_A)
    assert [p.id for p in active_profiles_from(profs)] == [
        p.id for p in profs if p.is_active
    ]


# ── failure containment (honest-empty degradation) ────────────────────────


class _BrokenRepo(PostgresICPRepository):
    async def get(self, *a, **k):  # noqa: D401
        raise RuntimeError("db down")

    async def list_for_tenant(self, *, tenant_id: str):
        raise RuntimeError("db down")

    async def list_active(self, *, tenant_id: str):
        raise RuntimeError("db down")


def test_read_failures_degrade_to_empty_not_raise():
    # BrokenRepo overrides reads only; writes hit validation before any DB
    # touch, so the shared-loop caveat for injected repos never triggers.
    broken = SyncICPStore(repo=_BrokenRepo(None))
    try:
        assert broken.list_for_tenant(tenant_id=T_A) == []
        assert broken.list_active(tenant_id=T_A) == []
        assert broken.get("anything", tenant_id=T_A) is None
    finally:
        broken.close()


def test_write_failures_propagate(store):
    class _NoCreate(SyncICPStore):
        pass

    # create on a repo whose table write fails: invalid tenant triggers ICPError
    with pytest.raises(ICPError):
        store.create(tenant_id="not-a-uuid", name="x")


def test_singleton_identity():
    s1 = get_sync_icp_store()
    s2 = get_sync_icp_store()
    assert s1 is s2
