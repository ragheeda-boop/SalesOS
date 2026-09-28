"""Phase 4F — research EvidencePack includes company_signals after detection."""

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import async_session
from app.modules.signal_marketplace.models import Signal
from app.modules.signal_marketplace.postgres_repo import (
    PostgresSignalRepository,
    PostgresSignalSubscriptionRepository,
)
from app.modules.signal_marketplace.runtime_bridge import SignalDetectionBridge
from app.modules.signal_marketplace.service import SignalMarketplaceService
from intelligence.agents.research_evidence import build_company_evidence

T_A = "a0000000-0000-4000-a000-000000000001"
CO_A = "25ea3f23-a0a6-4bb5-b91e-59d8e5f402e5"
SIG = "phase4f-evidence-sig"
EVT_TYPE = "construction.contract_awarded"


def _signal() -> Signal:
    return Signal(
        id=SIG,
        name="Evidence Fixture",
        ar_name="دليل",
        description="transient",
        domain="construction",
        category="growth",
        severity="warning",
        source="unit",
        pack_id="unit-pack",
        triggers=["contract"],
    )


async def _pin(db, tenant: str) -> None:
    await db.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant})


async def _cleanup() -> None:
    async with async_session() as db:
        await _pin(db, T_A)
        await db.execute(text("DELETE FROM signal_events WHERE signal_id=:s"), {"s": SIG})
        await db.execute(
            text("DELETE FROM signal_subscriptions WHERE signal_id=:s"), {"s": SIG}
        )
        await db.execute(
            text("DELETE FROM company_signals WHERE signal_type=:s AND tenant_id=CAST(:t AS uuid)"),
            {"s": SIG, "t": T_A},
        )
        # The evidence pack requires a real companies row for (tenant, id);
        # build_company_evidence returns found=False without one. Drop the
        # fixture company so the test never inherits (or leaks) ambient state.
        await db.execute(
            text("DELETE FROM companies WHERE id=CAST(:c AS uuid) AND tenant_id=CAST(:t AS uuid)"),
            {"c": CO_A, "t": T_A},
        )
        await db.commit()
    async with async_session() as db:
        await db.execute(text("DELETE FROM signal_catalog WHERE id=:s"), {"s": SIG})
        await db.commit()


async def _ensure_company() -> None:
    """Seed the companies row the evidence loader needs, if absent.

    Previously this test relied on the pif demo row that a live
    §4F/§19 probe had left behind. Any teardown/truncate elsewhere (or a
    fresh salesos_test) removed it and the test failed on
    company_record_not_found_for_tenant — an environment dependency, not a
    product defect. The fixture now owns the row it depends on.
    """
    async with async_session() as db:
        await _pin(db, T_A)
        # companies.tenant_id is FK-constrained, so the tenant must exist first.
        await db.execute(
            text(
                "INSERT INTO tenants (id, name, slug) "
                "VALUES (CAST(:t AS uuid), :nm, :sl) ON CONFLICT (id) DO NOTHING"
            ),
            {"t": T_A, "nm": "Evidence Fixture Tenant", "sl": "evidence-fixture-tenant"},
        )
        await db.execute(
            text(
                "INSERT INTO companies (id, tenant_id, name_ar, name_en, status) "
                "VALUES (CAST(:c AS uuid), CAST(:t AS uuid), :na, :ne, 'active') "
                "ON CONFLICT (id) DO NOTHING"
            ),
            {"c": CO_A, "t": T_A, "na": "شركة الاختبار", "ne": "Evidence Fixture Co"},
        )
        await db.commit()


@pytest_asyncio.fixture(autouse=True)
async def _fixture():
    await _cleanup()
    async with async_session() as db:
        await PostgresSignalRepository(db).upsert(_signal())
        await db.commit()
    await _ensure_company()
    yield
    await _cleanup()
    from app.database import engine

    await engine.dispose()


@pytest.mark.asyncio
async def test_evidence_pack_includes_signal_after_subscribe_and_bridge():
    async with async_session() as db:
        await _pin(db, T_A)
        svc = SignalMarketplaceService(
            signal_repo=PostgresSignalRepository(db),
            sub_repo=PostgresSignalSubscriptionRepository(db),
        )
        await svc.subscribe(SIG, CO_A, T_A)
        await db.commit()

    bridge = SignalDetectionBridge()
    bridge.refresh()
    await bridge.on_domain_event(
        {
            "event_type": EVT_TYPE,
            "aggregate_id": CO_A,
            "tenant_id": T_A,
            "data": {"license": "MOH-99"},
        }
    )

    pack = await build_company_evidence(async_session, T_A, CO_A)
    assert pack.found is True
    signal_items = [e for e in pack.items if e.source_type == "signal"]
    assert len(signal_items) >= 1
    assert any(SIG in e.field for e in signal_items)
    assert "signals" not in pack.missing_data
