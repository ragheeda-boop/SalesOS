"""FeedbackAnalyticsService.get_dashboard(leaderboard=False) returns only the
caller's own productivity row (PO decision B6, report 99)."""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import async_session, engine
from app.modules.signal_actions.hitl_service import FeedbackAnalyticsService


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    yield
    await engine.dispose()


@pytest.mark.asyncio
async def test_non_manager_sees_only_own_productivity_row():
    tid, a, b = str(uuid.uuid4()), "seller-a", "seller-b"
    async with async_session() as s:
        await s.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tid})
        for seller, n in ((a, 2), (b, 3)):
            for _ in range(n):
                await s.execute(text(
                    "INSERT INTO action_outcomes (tenant_id, action_id, company_name, seller_id, "
                    "outcome_type, occurred_at) VALUES (:t, :a, 'Co', :s, 'connected', now())"),
                    {"t": tid, "a": str(uuid.uuid4()), "s": seller})
        await s.commit()

    svc = FeedbackAnalyticsService(async_session)
    full = await svc.get_dashboard(tid)
    own = await svc.get_dashboard(tid, a, leaderboard=False)

    assert {r["seller_id"] for r in full["seller_productivity"]} == {a, b}
    assert own["seller_productivity"] == [
        {"seller_id": a, "total_outcomes": 2, "converted": 2, "conversion_rate": 1.0}]
    assert own["total_outcomes"] == 2
    with pytest.raises(ValueError):
        await svc.get_dashboard(tid, None, leaderboard=False)
