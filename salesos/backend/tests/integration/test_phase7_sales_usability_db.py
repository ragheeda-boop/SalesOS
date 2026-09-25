"""Phase 7 sales-usability against the restored salesos_test (read-only).

Expected figures come from the current active version (report 111, report 112
rec. I/J; PO 2026-09-25): 5,863 SALES_READY (all P1, still fully blocked by G4)
and 15,746 SALES_READY_WITH_REVIEW (all P2). Rec. I closed the registry-
anchored (non-Apollo-only) SRWR gate; Apollo-only SRWR stays open.
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
async def test_p1_fully_blocked_p2_registry_anchored_srwr_accepted(service):
    # rec. I (report 111/112; PO 2026-09-25): the registry-anchored (non-
    # Apollo-only) part of SRWR is accepted; Apollo-only SRWR stays blocked;
    # P1 is untouched (still fully blocked by G4).
    s = await service.get_sales_usability_summary()
    assert s["ready_accounts"] == 21_609
    assert s["usable_accounts"] == 7_768
    assert s["by_readiness"]["SALES_READY"] == {"total": 5_863, "usable": 0}
    assert s["by_readiness"]["SALES_READY_WITH_REVIEW"] == {"total": 15_746, "usable": 7_768}
    assert s["by_blocker"]["P1_REVIEW_GATE_OPEN"] == 5_863
    assert s["by_blocker"]["P2_STRATUM_NOT_ACCEPTED"] == 7_807  # Apollo-only SRWR only
    assert s["by_blocker"]["OUT_OF_MARKET"] == 2_876
    assert s["by_blocker"]["NON_COMMERCIAL_SEGMENT"] == 164
    assert s["by_blocker"]["PLACEHOLDER_ACCOUNT_NAME"] == 22  # rec. J
    assert s["gates"]["G5:SALES_READY_WITH_REVIEW"]["status"] == "CLOSED"
    assert s["gates"]["G5:SALES_READY_WITH_REVIEW:APOLLO_ONLY"]["status"] == "OPEN"


@pytest.mark.asyncio
async def test_closing_remaining_gates_still_holds_back_pending_review_accounts(service):
    # Close G4 and the Apollo-only SRWR gate too (rec. K / a second signal,
    # not yet implemented) — what's left must be genuine pending-review or
    # segment/data-quality holds, never a priority-gate artifact.
    close = {"G4", "G5:SALES_READY_WITH_REVIEW:APOLLO_ONLY"}
    gates = {k: Gate(k, "CLOSED", "test") if k in close else g for k, g in GATES.items()}
    s = await usability_summary(service.session, gates)
    accounts = await _load(service.session, gates)
    blocked = [a for a in accounts if not a["usable"]]
    pending_only = {"PENDING_P3_FUZZY_PAIR", "PENDING_SHORT_CR_ADJUDICATION", "CR_SUSPICIOUS_MULTI",
                    "NON_COMMERCIAL_SEGMENT", "OUT_OF_MARKET", "PLACEHOLDER_ACCOUNT_NAME"}
    assert s["usable_accounts"] > 7_768  # strictly more than rec. I alone unlocks
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
