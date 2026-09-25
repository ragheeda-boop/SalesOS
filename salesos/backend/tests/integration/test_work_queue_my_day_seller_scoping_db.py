"""WorkQueueService.get_my_day()'s pending-actions query leaked every
seller's pending actions to every other seller in the same tenant.

Mechanical finding, `app/modules/signal_actions/hitl_service.py::
WorkQueueService.get_my_day()` — genuinely LIVE: called from
`GET /work-queue/my-day` (`get_my_day_for_current_user`, mounted at boot)
with the caller's own authenticated user id as `seller_id`.

`agent_sales_actions.user_id` is the seller-owner column (populated at
INSERT time in `signal_actions/actions.py`) — but the pending-actions
query in `get_my_day()` filtered only on `tenant_id` and `status`, never
on `user_id`. This is a "mine-only" read model per its own docstring; the
sibling queries in the same method (`sales_followups`, `action_outcomes`)
already correctly filter by `seller_id`. Confirmed directly: seeding two
sellers' pending actions in the same tenant and calling `get_my_day()` for
seller A returned seller B's pending action too. Fixed by adding
`AND user_id = :s` to the pending-actions query, matching the pattern
already used by the two sibling queries.
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import async_session, engine
from app.modules.signal_actions.hitl_service import WorkQueueService


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    yield
    await engine.dispose()


@pytest.mark.asyncio
async def test_my_day_only_shows_the_calling_sellers_own_pending_actions():
    tenant_id = str(uuid.uuid4())
    seller_a, seller_b = str(uuid.uuid4()), str(uuid.uuid4())

    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        await session.execute(
            text("INSERT INTO tenants (id, name, slug) VALUES (:id, 'My Day Test', :slug)"),
            {"id": tenant_id, "slug": f"myday-test-{tenant_id[:8]}"},
        )
        await session.execute(
            text("""
                INSERT INTO agent_sales_actions
                    (id, tenant_id, company_name, user_id, action_type, status)
                VALUES (gen_random_uuid(), :tid, 'Seller A Co', :uid, 'call', 'pending')
            """),
            {"tid": tenant_id, "uid": seller_a},
        )
        await session.execute(
            text("""
                INSERT INTO agent_sales_actions
                    (id, tenant_id, company_name, user_id, action_type, status)
                VALUES (gen_random_uuid(), :tid, 'Seller B Co', :uid, 'call', 'pending')
            """),
            {"tid": tenant_id, "uid": seller_b},
        )
        await session.commit()

    svc = WorkQueueService(async_session)
    day_a = await svc.get_my_day(tenant_id, seller_a)

    company_names = {a["company_name"] for a in day_a["pending_actions"]}
    assert company_names == {"Seller A Co"}
    assert "Seller B Co" not in company_names
