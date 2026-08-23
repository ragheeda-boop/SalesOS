#!/usr/bin/env python3
"""Runtime probes via agent layer (bypasses HTTP CSRF secure-cookie on localhost)."""
from __future__ import annotations

import asyncio
import json
import sys

from app.database import async_session
from app.modules.gtm.icp_persistence import get_sync_icp_store
from intelligence.agents.icp import NO_PROFILE_REASON, evaluate_icp
from intelligence.agents.research_evidence import build_company_evidence

T_A = "a0000000-0000-4000-a000-000000000001"
T_B = "b0000000-0000-4000-b000-000000000002"
CO_PIF = "25ea3f23-a0a6-4bb5-b91e-59d8e5f402e5"


async def probe_a() -> dict:
    pack = await build_company_evidence(async_session, T_A, CO_PIF)
    result = evaluate_icp(pack, get_sync_icp_store(), T_A)
    fit = result.get("fit", "UNKNOWN")
    return {
        "status": "PASS" if fit not in ("UNKNOWN",) else "PARTIAL",
        "fit": fit,
        "criteria_n": len(result.get("criteria", [])),
        "reason": (result.get("reason") or "")[:200],
    }


async def probe_b() -> dict:
    """Cross-tenant: tenant B store must not see tenant A profile."""
    store = get_sync_icp_store()
    profiles_b = store.list_for_tenant(tenant_id=T_B)
    pack = await build_company_evidence(async_session, T_A, CO_PIF)
    result = evaluate_icp(pack, store, T_B)
    fit = result.get("fit", "UNKNOWN")
    no_profile = NO_PROFILE_REASON in (result.get("reason") or "")
    return {
        "status": "PASS" if no_profile and len(profiles_b) == 0 else "WARN",
        "tenant_b_profiles": len(profiles_b),
        "fit_under_wrong_tenant": fit,
        "no_profile_honest": no_profile,
    }


async def probe_c() -> dict:
    from sqlalchemy import text

    from app.modules.signal_marketplace.postgres_repo import (
        PostgresSignalEventRepository,
        PostgresSignalRepository,
        PostgresSignalSubscriptionRepository,
    )
    from app.modules.signal_marketplace.runtime_bridge import SignalDetectionBridge
    from app.modules.signal_marketplace.service import SignalMarketplaceService

    SIG = "SIG-CN-001"
    EVT = "capacity_change"
    async with async_session() as db:
        await db.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": T_A}
        )
        svc = SignalMarketplaceService(
            signal_repo=PostgresSignalRepository(db),
            sub_repo=PostgresSignalSubscriptionRepository(db),
            event_repo=PostgresSignalEventRepository(db),
        )
        await svc.subscribe(SIG, CO_PIF, T_A)
        await db.commit()
    bridge = SignalDetectionBridge()
    n_created = await bridge.on_domain_event(
        {
            "event_type": EVT,
            "aggregate_id": CO_PIF,
            "tenant_id": T_A,
            "data": {"contract_value": 1_000_000},
        }
    )
    async with async_session() as db:
        await db.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": T_A}
        )
        cnt = (
            await db.execute(
                text("SELECT COUNT(*) FROM signal_events WHERE company_id=:c AND signal_id=:s"),
                {"c": CO_PIF, "s": SIG},
            )
        ).scalar()
        await db.execute(
            text("DELETE FROM signal_events WHERE company_id=:c AND signal_id=:s"),
            {"c": CO_PIF, "s": SIG},
        )
        await db.execute(
            text(
                "DELETE FROM signal_subscriptions WHERE company_id=:c AND signal_id=:s"
            ),
            {"c": CO_PIF, "s": SIG},
        )
        await db.commit()
    return {
        "status": "PASS" if n_created >= 1 and cnt >= 1 else "FAIL",
        "bridge_created": n_created,
        "feed_events": cnt,
        "signal_id": SIG,
    }


async def main() -> int:
    out = {
        "probe_a": await probe_a(),
        "probe_b": await probe_b(),
        "probe_c": await probe_c(),
    }
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
