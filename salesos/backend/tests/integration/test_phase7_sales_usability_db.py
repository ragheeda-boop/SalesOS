"""Phase 7 sales-usability against the restored salesos_test (read-only).

Expected figures come from the Phase 6 run (report 94/96): 5,710 SALES_READY
accounts (all P1) and 37,312 SALES_READY_WITH_REVIEW (all P2). With every
review gate open, none may be treated as sales-usable.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.modules.master_data.phase7.review_queue import ReviewQueueService, _review_engine
from app.modules.master_data.phase7.usability import GATES, Gate, _load, usability_summary


@pytest_asyncio.fixture
async def service():
    svc = ReviewQueueService()
    if await svc._current_db() != "salesos_test":  # raises otherwise
        pytest.skip("salesos_test required")
    count = (await svc.session.execute(text("SELECT count(*) FROM md_identity_classifications"))).scalar()
    if not count:
        pytest.skip("salesos_test has no Phase 6 classifications")
    await svc.session.execute(text("SET TRANSACTION READ ONLY"))
    yield svc
    await svc.session.rollback()
    await svc.session.close()
    await _review_engine.dispose()


@pytest.mark.asyncio
async def test_no_account_is_usable_while_gates_are_open(service):
    s = await service.get_sales_usability_summary()
    assert s["ready_accounts"] == 21_609
    assert s["usable_accounts"] == 0
    assert s["by_readiness"]["SALES_READY"] == {"total": 5_863, "usable": 0}
    assert s["by_readiness"]["SALES_READY_WITH_REVIEW"] == {"total": 15_746, "usable": 0}
    assert s["by_blocker"]["P1_REVIEW_GATE_OPEN"] == 5_863
    assert s["by_blocker"]["P2_STRATUM_NOT_ACCEPTED"] == 15_746


@pytest.mark.asyncio
async def test_closing_priority_gates_still_holds_back_pending_review_accounts(service):
    gates = {k: Gate(k, "CLOSED", "test") if k in ("G4", "G5:SALES_READY_WITH_REVIEW") else g
             for k, g in GATES.items()}
    s = await usability_summary(service.session, gates)
    accounts = await _load(service.session, gates)
    blocked = [a for a in accounts if not a["usable"]]
    pending_only = {"PENDING_P3_FUZZY_PAIR", "PENDING_SHORT_CR_ADJUDICATION", "CR_SUSPICIOUS_MULTI",
                    "NON_COMMERCIAL_SEGMENT", "OUT_OF_MARKET"}
    assert s["usable_accounts"] > 0
    assert s["usable_accounts"] + len(blocked) == s["ready_accounts"]
    assert blocked, "expected some ready accounts to sit in a pending review population"
    assert all(set(a["blockers"]) <= pending_only for a in blocked)


@pytest.mark.asyncio
async def test_account_listing_filters_and_explains(service):
    items, total = await service.list_sales_usability(usable=None, blocker="P1_REVIEW_GATE_OPEN",
                                                      offset=0, limit=5)
    assert total == 5_863
    assert len(items) == 5
    assert all(i["review_priority"] == "P1" and not i["usable"] for i in items)
    assert all(i["slug"].startswith("G-C-") for i in items)
