"""POST /pipeline/score-deal and /pipeline/score-batch must query the real
`commercial_stage_entries` table, not a non-existent `pipeline_stage_entries`.

Mechanical finding, same class as tests/integration/test_feature_store_licenses_table_db.py:
both endpoints in runtime/pipeline_analytics/router.py issued raw SQL against
`public.pipeline_stage_entries` (a table that does not exist anywhere in the
schema; the real table, created in 0007_commercial_domain.py, is
`commercial_stage_entries`) using nonexistent columns `stage_name` and
`exit_reason` (the real columns are `to_stage`/`from_stage` and
`exited_at`/`entered_at`). Every real call raised an unhandled
UndefinedTableError/UndefinedColumnError, caught only by each endpoint's own
broad `except Exception: raise HTTPException(500)`, so both endpoints always
500ed on every request. Neither endpoint had any prior test coverage — the
only existing suite (tests/unit/test_pipeline_analytics.py) exercises a
different class in the same package (`PipelineAnalytics`, in __init__.py)
which already queries the correct table.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.database import async_session, engine
from app.dependencies import get_current_tenant_id, get_db_session, verify_token
from runtime.pipeline_analytics.router import router as pipeline_router


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    yield
    await engine.dispose()


async def _seed_tenant_company_opportunity_with_stage_history(
    session, tenant_id: str
) -> tuple[str, str]:
    await session.execute(
        text("INSERT INTO tenants (id, name, slug) VALUES (:id, 'Pipeline Test', :slug)"),
        {"id": tenant_id, "slug": f"pipe-test-{tenant_id[:8]}"},
    )
    company_id = str(uuid.uuid4())
    await session.execute(
        text(
            "INSERT INTO companies (id, tenant_id, name_ar, status) "
            "VALUES (:id, :tid, 'شركة اختبار الأنابيب', 'active')"
        ),
        {"id": company_id, "tid": tenant_id},
    )
    opp_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    await session.execute(
        text(
            "INSERT INTO commercial_opportunities "
            "(id, tenant_id, company_id, name, stage, value, probability, "
            " status, created_at, updated_at) "
            "VALUES (:id, :tid, :cid, 'Deal 1', 'negotiation', 100000, 0.6, "
            " 'open', :now, :now)"
        ),
        {"id": opp_id, "tid": tenant_id, "cid": company_id, "now": now},
    )
    # A prior, already-exited stage — must NOT be picked as the current one.
    await session.execute(
        text(
            "INSERT INTO commercial_stage_entries "
            "(id, tenant_id, opportunity_id, pipeline_id, from_stage, to_stage, "
            " entered_at, exited_at) "
            "VALUES (:id, :tid, :oid, :pid, 'qualified', 'proposal', :entered, :exited)"
        ),
        {
            "id": str(uuid.uuid4()),
            "tid": tenant_id,
            "oid": opp_id,
            "pid": str(uuid.uuid4()),
            "entered": now - timedelta(days=10),
            "exited": now - timedelta(days=5),
        },
    )
    # The current, still-open stage the deal is actually sitting in — seeded
    # far beyond any plausible average cycle time (45 days / 4 stages by the
    # scorer's own default) so a working query drives the stage_velocity
    # factor to its worst score, distinguishing "found the real duration"
    # from "found nothing, silently defaulted to 0 days" (the old bug's
    # always-500 behavior would never even reach this factor at all, but a
    # theoretical broken-yet-non-crashing query would default to a suspiciously
    # perfect stage_velocity=1.0 regardless of real data).
    await session.execute(
        text(
            "INSERT INTO commercial_stage_entries "
            "(id, tenant_id, opportunity_id, pipeline_id, from_stage, to_stage, "
            " entered_at, exited_at) "
            "VALUES (:id, :tid, :oid, :pid, 'proposal', 'negotiation', :entered, NULL)"
        ),
        {
            "id": str(uuid.uuid4()),
            "tid": tenant_id,
            "oid": opp_id,
            "pid": str(uuid.uuid4()),
            "entered": now - timedelta(days=60),
        },
    )
    return company_id, opp_id


def _make_app() -> FastAPI:
    app = FastAPI()
    app.include_router(pipeline_router)
    return app


def _tenant_pinned_db_override(tenant_id: str):
    """FastAPI's TestClient bypasses the real ASGI middleware stack that
    normally pins app.tenant_id via set_current_tenant_id() (app/common/middleware.py),
    so a bare override must pin the GUC itself, in the same session/
    transaction the route handler will use, before returning it.
    """

    async def _override():
        session = async_session()
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        return session

    return _override


async def _seed(tenant_id: str) -> str:
    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        _company_id, opp_id = await _seed_tenant_company_opportunity_with_stage_history(
            session, tenant_id
        )
        await session.commit()
    return opp_id


def test_score_deal_reads_real_stage_entries_table(monkeypatch):
    async def _allow(*args, **kwargs):
        return True

    monkeypatch.setattr("app.dependencies.require_permission", _allow)

    tenant_id = str(uuid.uuid4())
    opp_id = asyncio.run(_seed(tenant_id))
    # Starlette's TestClient drives the ASGI app from its own background
    # event loop (an anyio blocking portal) — a different loop than the one
    # asyncio.run() just closed above. The engine's async connection pool is
    # bound to whichever loop first touches it, so it must be disposed here;
    # the next use (inside the TestClient block below) then binds fresh
    # connections to the TestClient's loop instead of raising "attached to a
    # different loop".
    asyncio.run(engine.dispose())

    app = _make_app()
    app.dependency_overrides[verify_token] = lambda: {"sub": "test-user", "tenant_id": tenant_id}
    app.dependency_overrides[get_current_tenant_id] = lambda: tenant_id
    app.dependency_overrides[get_db_session] = _tenant_pinned_db_override(tenant_id)

    with TestClient(app) as client:
        resp = client.post(
            "/pipeline/score-deal",
            params={"deal_id": opp_id},
            headers={"Authorization": "Bearer faketoken"},
        )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    factors = {f["key"]: f["value"] for f in body["factors"]}
    # A deal stuck in its current stage for 60 days (well over the scorer's
    # ~11-day default average) must score stage_velocity at its worst tier
    # (<=0.3). If the query still targeted the non-existent old table/columns
    # and silently found nothing, days_in_stage would default to 0 and this
    # factor would incorrectly read a perfect 1.0 regardless of real data.
    assert factors["stage_velocity"] <= 0.3


def test_score_batch_reads_real_stage_entries_table(monkeypatch):
    async def _allow(*args, **kwargs):
        return True

    monkeypatch.setattr("app.dependencies.require_permission", _allow)

    tenant_id = str(uuid.uuid4())
    asyncio.run(_seed(tenant_id))
    asyncio.run(engine.dispose())

    app = _make_app()
    app.dependency_overrides[verify_token] = lambda: {"sub": "test-user", "tenant_id": tenant_id}
    app.dependency_overrides[get_current_tenant_id] = lambda: tenant_id
    app.dependency_overrides[get_db_session] = _tenant_pinned_db_override(tenant_id)

    with TestClient(app) as client:
        resp = client.post(
            "/pipeline/score-batch",
            headers={"Authorization": "Bearer faketoken"},
        )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total_scored"] == 1
