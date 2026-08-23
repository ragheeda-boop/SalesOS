"""Phase 4F — Signal marketplace API/service E2E over real Postgres.

Proves subscribe → bridge detection → feed contract using the same repos the
HTTP router wires. Cross-tenant and unsubscribed-company silence included.
"""

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import async_session
from app.modules.signal_marketplace.models import Signal
from app.modules.signal_marketplace.postgres_repo import (
    PostgresSignalEventRepository,
    PostgresSignalRepository,
    PostgresSignalSubscriptionRepository,
)
from app.modules.signal_marketplace.runtime_bridge import SignalDetectionBridge
from app.modules.signal_marketplace.service import SignalMarketplaceService

NS = uuid.uuid5(uuid.NAMESPACE_URL, "phase4f-api-e2e-tests")
T_A = "a0000000-0000-4000-a000-000000000001"
T_B = "b0000000-0000-4000-a000-000000000002"
CO_A = "25ea3f23-a0a6-4bb5-b91e-59d8e5f402e5"
CO_OTHER = str(uuid.uuid5(NS, "company-other"))
SIG = "phase4f-api-sig-1"
EVT_TYPE = "construction.contract_awarded"


def _signal() -> Signal:
    return Signal(
        id=SIG,
        name="API E2E Fixture",
        ar_name="اختبار",
        description="transient",
        domain="construction",
        category="growth",
        severity="critical",
        source="unit",
        pack_id="unit-pack",
        priority="high",
        weight=0.9,
        decay_days=30,
        triggers=["contract"],
    )


async def _pin(db, tenant: str) -> None:
    await db.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant})


async def _cleanup() -> None:
    for t in (T_B, T_A):
        async with async_session() as db:
            await _pin(db, t)
            await db.execute(text("DELETE FROM signal_events WHERE signal_id=:s"), {"s": SIG})
            await db.execute(
                text("DELETE FROM signal_subscriptions WHERE signal_id=:s"), {"s": SIG}
            )
            await db.execute(
                text("DELETE FROM company_signals WHERE signal_type=:s"), {"s": SIG}
            )
            await db.commit()
    async with async_session() as db:
        await db.execute(text("DELETE FROM signal_catalog WHERE id=:s"), {"s": SIG})
        await db.commit()


def _service(db) -> SignalMarketplaceService:
    return SignalMarketplaceService(
        signal_repo=PostgresSignalRepository(db),
        sub_repo=PostgresSignalSubscriptionRepository(db),
        event_repo=PostgresSignalEventRepository(db),
    )


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


@pytest.mark.asyncio
async def test_subscribe_bridge_feed_full_loop():
    async with async_session() as db:
        await _pin(db, T_A)
        svc = _service(db)
        sub = await svc.subscribe(SIG, CO_A, T_A)
        assert sub.active is True
        await db.commit()

    bridge = SignalDetectionBridge()
    bridge.refresh()
    n = await bridge.on_domain_event(
        {
            "event_type": EVT_TYPE,
            "aggregate_id": CO_A,
            "tenant_id": T_A,
            "data": {"probe": "phase4f"},
        }
    )
    assert n == 1

    async with async_session() as db:
        await _pin(db, T_A)
        feed = await _service(db).get_feed(T_A)
    assert len(feed) == 1
    assert feed[0].signal_id == SIG
    assert feed[0].company_id == CO_A
    assert feed[0].data.get("probe") == "phase4f"


@pytest.mark.asyncio
async def test_feed_cross_tenant_isolation():
    async with async_session() as db:
        await _pin(db, T_A)
        await _service(db).subscribe(SIG, CO_A, T_A)
        await db.commit()

    bridge = SignalDetectionBridge()
    bridge.refresh()
    await bridge.on_domain_event(
        {"event_type": EVT_TYPE, "aggregate_id": CO_A, "tenant_id": T_A, "data": {}}
    )

    async with async_session() as db:
        await _pin(db, T_B)
        feed_b = await _service(db).get_feed(T_B)
    assert feed_b == []


@pytest.mark.asyncio
async def test_unsubscribed_company_gets_no_event():
    async with async_session() as db:
        await _pin(db, T_A)
        # subscribe CO_A only; fire event for CO_OTHER
        await _service(db).subscribe(SIG, CO_A, T_A)
        await db.commit()

    bridge = SignalDetectionBridge()
    bridge.refresh()
    n = await bridge.on_domain_event(
        {
            "event_type": EVT_TYPE,
            "aggregate_id": CO_OTHER,
            "tenant_id": T_A,
            "data": {},
        }
    )
    assert n == 0

    async with async_session() as db:
        await _pin(db, T_A)
        feed = await _service(db).get_feed(T_A)
    assert feed == []


@pytest.mark.asyncio
async def test_company_feed_scoped():
    async with async_session() as db:
        await _pin(db, T_A)
        svc = _service(db)
        await svc.subscribe(SIG, CO_A, T_A)
        await svc.subscribe(SIG, CO_OTHER, T_A)
        await db.commit()

    bridge = SignalDetectionBridge()
    bridge.refresh()
    await bridge.on_domain_event(
        {"event_type": EVT_TYPE, "aggregate_id": CO_A, "tenant_id": T_A, "data": {"k": 1}}
    )
    await bridge.on_domain_event(
        {"event_type": EVT_TYPE, "aggregate_id": CO_OTHER, "tenant_id": T_A, "data": {"k": 2}}
    )

    async with async_session() as db:
        await _pin(db, T_A)
        company_feed = await _service(db).get_company_feed(CO_A, T_A)
    assert len(company_feed) == 1
    assert company_feed[0].company_id == CO_A


@pytest.mark.asyncio
async def test_no_subscription_bridge_silence():
    bridge = SignalDetectionBridge()
    bridge.refresh()
    n = await bridge.on_domain_event(
        {"event_type": EVT_TYPE, "aggregate_id": CO_A, "tenant_id": T_A, "data": {}}
    )
    assert n == 0
