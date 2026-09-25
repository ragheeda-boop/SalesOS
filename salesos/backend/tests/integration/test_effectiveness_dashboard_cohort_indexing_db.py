"""get_dashboard()'s per-cohort breakdown reported the wrong column as
avg_time_to_action_hours.

Mechanical finding, `app/modules/effectiveness/__init__.py::
EffectivenessService.get_dashboard()` — genuinely LIVE: called from
`app/modules/effectiveness/router.py` (mounted at boot) and
`app/modules/signal_actions/hitl_router.py`.

The per-cohort SQL SELECTs 12 columns ending
`..., nba_acc, nba_over, avg_tta` (indices 9, 10, 11), but the Python code
building each cohort's dict read `row[10]` (nba_over — a count of
overridden NBA recommendations) for `avg_time_to_action_hours` instead of
`row[11]` (the actual average-hours figure) — a plain off-by-one indexing
bug, invisible to every existing test since `test_effectiveness.py` only
exercises this module's pure helper functions, never `get_dashboard()`'s
real SQL/row-indexing path. Confirmed directly: seeding one account with a
real >0 nba_over count and a real, different avg_time_to_action_hours value
showed the cohort's reported `avg_time_to_action_hours` was exactly the
`nba_over` count, not the real hours figure. Fixed to `row[11]`.
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import async_session, engine
from app.modules.effectiveness import EffectivenessService


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    yield
    await engine.dispose()


@pytest.mark.asyncio
async def test_cohort_avg_time_to_action_hours_is_not_the_override_count():
    tenant_id = str(uuid.uuid4())
    account_id = str(uuid.uuid4())

    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        await session.execute(
            text("INSERT INTO tenants (id, name, slug) VALUES (:id, 'Eff Dashboard Test', :slug)"),
            {"id": tenant_id, "slug": f"eff-test-{tenant_id[:8]}"},
        )
        # A distinctive, deliberately different value from nba_rejected+nba_modified
        # (3), so the bug (row[10] instead of row[11]) is unmistakable: the
        # buggy code would report 3.0 instead of 42.5.
        await session.execute(
            text("""
                INSERT INTO account_funnel
                    (id, tenant_id, company_name, seller_id, intent_score, intent_level, cohort,
                     nba_accepted, nba_rejected, nba_modified,
                     total_actions, total_outcomes, connected_outcomes, meeting_outcomes,
                     time_to_first_action_hours)
                VALUES
                    (:id, :tid, 'Cohort Test Co', 'seller-1', 90, 'high', 'critical',
                     1, 2, 1,
                     0, 0, 0, 0,
                     42.5)
            """),
            {"id": account_id, "tid": tenant_id},
        )
        await session.commit()

    svc = EffectivenessService(async_session)
    dashboard = await svc.get_dashboard(tenant_id)

    critical = dashboard["cohorts"]["critical"]
    # nba_over = nba_rejected(2) + nba_modified(1) = 3 — the buggy value.
    assert critical["nba_overridden"] == 3
    # The real fix: avg_time_to_action_hours must be the actual hours figure,
    # not the override count.
    assert critical["avg_time_to_action_hours"] == 42.5
