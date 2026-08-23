"""Phase 4E — signal detection bridge tests.

Proves the marketplace contract end-to-end over the real DB (canonical RLS):
matching parity with SignalDetectionEngine, no-subscription silence, active
subscription → isolated signal_event, inactive subscription ignored, and
cross-tenant containment. All rows transient; deterministic ids.
"""

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import async_session
from app.modules.signal_marketplace.engine import SignalDetectionEngine
from app.modules.signal_marketplace.models import Signal
from app.modules.signal_marketplace.postgres_repo import (
    PostgresSignalEventRepository,
    PostgresSignalRepository,
    PostgresSignalSubscriptionRepository,
)
from app.modules.signal_marketplace.runtime_bridge import (
    SignalDetectionBridge,
    get_signal_detection_bridge,
)

NS = uuid.uuid5(uuid.NAMESPACE_URL, "phase4e-bridge-tests")
T_A = "a0000000-0000-4000-a000-000000000001"
T_B = "b0000000-0000-4000-a000-000000000002"
CO_A = "25ea3f23-a0a6-4bb5-b91e-59d8e5f402e5"  # pif, tenant A
SIG = "unit-bridge-sig-1"
EVT_TYPE = "construction.contract_awarded"


def _signal() -> Signal:
    return Signal(
        id=SIG,
        name="Bridge Fixture",
        ar_name="جسر",
        description="transient unit fixture",
        domain="construction",
        category="growth",
        severity="critical",
        source="unit",
        pack_id="unit-bridge-pack",
        priority="high",
        weight=0.9,
        decay_days=30,
        triggers=["contract"],
    )


async def _pin(db, tenant):
    await db.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant})


async def _cleanup():
    for t in (T_B, T_A):
        async with async_session() as db:
            await _pin(db, t)
            await db.execute(
                text("DELETE FROM signal_events WHERE signal_id=:s"), {"s": SIG}
            )
            await db.execute(
                text("DELETE FROM signal_subscriptions WHERE signal_id=:s"),
                {"s": SIG},
            )
            await db.execute(
                text("DELETE FROM company_signals WHERE signal_type=:s"),
                {"s": SIG},
            )
            await db.commit()
    async with async_session() as db:
        # catalog is global-platform: delete without GUC is fine for fixture ids
        await db.execute(
            text("DELETE FROM signal_catalog WHERE id=:s"), {"s": SIG}
        )
        await db.commit()


@pytest_asyncio.fixture(autouse=True)
async def _seed_cleanup():
    await _cleanup()
    async with async_session() as db:
        await PostgresSignalRepository(db).upsert(_signal())
        await db.commit()
    yield
    await _cleanup()
    from app.database import engine

    await engine.dispose()


def _bridge() -> SignalDetectionBridge:
    b = SignalDetectionBridge()
    return b


@pytest.mark.asyncio
async def test_matching_parity_with_engine():
    engine = SignalDetectionEngine(service=None)  # type: ignore[arg-type]
    engine._signal_map = {SIG: _signal()}  # noqa: SLF001
    assert engine.match_signals(EVT_TYPE) == [SIG]
    assert engine.match_signals("crm.note.created") == []  # no trigger/domain hit


@pytest.mark.asyncio
async def test_no_subscription_means_silence():
    bridge = _bridge()
    n = await bridge.on_domain_event(
        {
            "event_type": EVT_TYPE,
            "aggregate_id": CO_A,
            "tenant_id": T_A,
            "data": {"k": 1},
        }
    )
    assert n == 0


@pytest.mark.asyncio
async def test_active_subscription_creates_isolated_event():
    from app.modules.signal_marketplace.models import SignalSubscription

    async with async_session() as db:
        await _pin(db, T_A)
        await PostgresSignalSubscriptionRepository(db).create(
            SignalSubscription(
                id=str(uuid.uuid4()),
                signal_id=SIG,
                company_id=CO_A,
                tenant_id=T_A,
            )
        )
        await db.commit()
    bridge = _bridge()
    n = await bridge.on_domain_event(
        {"event_type": EVT_TYPE, "aggregate_id": CO_A, "tenant_id": T_A, "data": {}}
    )
    assert n == 1
    async with async_session() as db:
        await _pin(db, T_A)
        cnt_a = (
            await db.execute(
                text("SELECT COUNT(*) FROM signal_events WHERE signal_id=:s"),
                {"s": SIG},
            )
        ).scalar()
        await _pin(db, T_B)
        cnt_b = (
            await db.execute(
                text("SELECT COUNT(*) FROM signal_events WHERE signal_id=:s"),
                {"s": SIG},
            )
        ).scalar()
    assert cnt_a == 1 and cnt_b == 0  # RLS-scoped visibility


@pytest.mark.asyncio
async def test_inactive_subscription_ignored():
    from app.modules.signal_marketplace.models import SignalSubscription

    async with async_session() as db:
        await _pin(db, T_A)
        await PostgresSignalSubscriptionRepository(db).create(
            SignalSubscription(
                id=str(uuid.uuid4()),
                signal_id=SIG,
                company_id=CO_A,
                tenant_id=T_A,
                active=False,
            )
        )
        await db.commit()
    n = await _bridge().on_domain_event(
        {"event_type": EVT_TYPE, "aggregate_id": CO_A, "tenant_id": T_A}
    )
    assert n == 0


@pytest.mark.asyncio
async def test_malformed_event_short_circuits():
    assert await _bridge().on_domain_event({"event_type": ""}) == 0
    assert await _bridge().on_domain_event({"aggregate_id": CO_A}) == 0


@pytest.mark.asyncio
async def test_singleton_identity_and_boot_hook():
    assert get_signal_detection_bridge() is get_signal_detection_bridge()
    import inspect

    from app.boot import startup as boot

    src = inspect.getsource(boot.init_startup_services)
    assert "_init_signal_detection_subscriber" in src
