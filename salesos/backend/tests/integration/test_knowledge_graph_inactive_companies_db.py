"""GET /graph/query/companies-without-activity compared
activity_records.entity_id (varchar) with companies.id (uuid) in three
correlated subqueries: `operator does not exist: character varying = uuid`
on every call. Same bug class as report 72, found by the EXPLAIN sweep
(report 98)."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.database import async_session, engine
from app.dependencies import get_current_tenant_id, get_db_session, verify_token
from runtime.knowledge_graph_runtime.router import router as graph_router


def _pinned(tenant_id: str):
    async def _override():
        async with async_session() as s:
            await s.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id})
            yield s
    return _override


async def _seed(tenant_id: str) -> tuple[str, str]:
    now = datetime.now(timezone.utc)
    async with async_session() as s:
        await s.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id})
        await s.execute(text("INSERT INTO tenants (id, name, slug) VALUES (:id, 'KG Inactive', :slug)"),
                        {"id": tenant_id, "slug": f"kg-inactive-{tenant_id[:8]}"})
        ids = []
        for name, age in (("Stale Co", 60), ("Busy Co", 1)):
            cid = str(uuid.uuid4())
            ids.append(cid)
            await s.execute(text("INSERT INTO companies (id, tenant_id, name_ar, status, is_active) "
                                 "VALUES (:id, :tid, :n, 'active', true)"),
                            {"id": cid, "tid": tenant_id, "n": name})
            await s.execute(text("INSERT INTO activity_records (id, actor, action, entity_type, entity_id, "
                                 "tenant_id, timestamp) VALUES (:id, 'u', 'note', 'company', :eid, :tid, :ts)"),
                            {"id": uuid.uuid4().hex, "eid": cid, "tid": tenant_id,
                             "ts": now - timedelta(days=age)})
        await s.commit()
    return ids[0], ids[1]


def test_returns_only_companies_inactive_past_the_window():
    tenant_id = str(uuid.uuid4())
    stale, busy = asyncio.run(_seed(tenant_id))
    asyncio.run(engine.dispose())

    app = FastAPI()
    app.include_router(graph_router)
    app.dependency_overrides[verify_token] = lambda: {"sub": "u", "tenant_id": tenant_id}
    app.dependency_overrides[get_current_tenant_id] = lambda: tenant_id
    app.dependency_overrides[get_db_session] = _pinned(tenant_id)

    with TestClient(app) as client:
        resp = client.get("/graph/query/companies-without-activity", params={"days": 30},
                          headers={"Authorization": "Bearer x"})
    # TestClient ran on its own loop; drop its pooled connections so later
    # tests do not inherit connections bound to a closed loop.
    asyncio.run(engine.dispose(close=False))
    assert resp.status_code == 200, resp.text
    ids = [str(i.get("id")) for i in resp.json().get("items", resp.json().get("companies", []))]
    assert ids == [stale], resp.json()
