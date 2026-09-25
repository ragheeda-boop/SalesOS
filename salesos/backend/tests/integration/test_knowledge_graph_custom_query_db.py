"""GET /graph/query/custom was broken for every supported entity_type.

Two independent mechanical findings in `custom_graph_query()`
(runtime/knowledge_graph_runtime/router.py), zero prior test coverage for
this endpoint:

1. The `opportunity`/`contract` branches never assign a local `items`
   variable (only `result["items"]`), yet both read `len(items)` — an
   undefined local. Every real call with `entity_type=opportunity` or
   `entity_type=contract` raised `UnboundLocalError: cannot access local
   variable 'items' where it is not associated with a value`, an unhandled
   500 (the route has no try/except at all).
2. The `company` branch's correlated subquery
   `(SELECT COUNT(*) FROM commercial_opportunities WHERE company_id = c.id)`
   compares `commercial_opportunities.company_id` (`varchar(36)`) directly
   against `companies.id` (`uuid`) with no cast — Postgres/asyncpg reject
   this outright: `UndefinedFunctionError: operator does not exist:
   character varying = uuid`. This was reproduced in complete isolation
   (a bare script, no test framework) against a fresh ephemeral database
   before being attributed to the router, ruling out a test-harness
   artifact. The sibling `contacts.company_id` column is `uuid` and needed
   no change.

Net effect: every one of the 3 entity_types this endpoint supports
(`company`, `opportunity`, `contract`) was broken, each for a different
underlying reason.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.database import async_session, engine
from app.dependencies import get_current_tenant_id, get_db_session, verify_token
from runtime.knowledge_graph_runtime.router import router as graph_router


def _make_app() -> FastAPI:
    app = FastAPI()
    app.include_router(graph_router)
    return app


def _tenant_pinned_db_override(tenant_id: str):
    async def _override():
        session = async_session()
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        return session

    return _override


async def _seed(tenant_id: str) -> None:
    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        await session.execute(
            text("INSERT INTO tenants (id, name, slug) VALUES (:id, 'KG Test', :slug)"),
            {"id": tenant_id, "slug": f"kg-test-{tenant_id[:8]}"},
        )
        company_id = str(uuid.uuid4())
        await session.execute(
            text(
                "INSERT INTO companies (id, tenant_id, name_ar, status) "
                "VALUES (:id, :tid, 'شركة اختبار الرسم البياني', 'active')"
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
                "VALUES (:id, :tid, :cid, 'Deal 1', 'prospecting', 50000, 0.2, "
                " 'open', :now, :now)"
            ),
            {"id": opp_id, "tid": tenant_id, "cid": company_id, "now": now},
        )
        await session.execute(
            text(
                "INSERT INTO commercial_contracts "
                "(id, tenant_id, opportunity_id, quote_id, title, status, "
                " created_at, updated_at) "
                "VALUES (:id, :tid, :oid, :qid, 'Contract 1', 'draft', :now, :now)"
            ),
            {
                "id": str(uuid.uuid4()),
                "tid": tenant_id,
                "oid": opp_id,
                "qid": str(uuid.uuid4()),
                "now": now,
            },
        )
        await session.commit()


def test_custom_graph_query_opportunity_does_not_crash():
    tenant_id = str(uuid.uuid4())
    asyncio.run(_seed(tenant_id))
    asyncio.run(engine.dispose())

    app = _make_app()
    app.dependency_overrides[verify_token] = lambda: {"sub": "test-user", "tenant_id": tenant_id}
    app.dependency_overrides[get_current_tenant_id] = lambda: tenant_id
    app.dependency_overrides[get_db_session] = _tenant_pinned_db_override(tenant_id)

    with TestClient(app) as client:
        resp = client.get(
            "/graph/query/custom",
            params={"entity_type": "opportunity"},
            headers={"Authorization": "Bearer faketoken"},
        )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1


def test_custom_graph_query_contract_does_not_crash():
    tenant_id = str(uuid.uuid4())
    asyncio.run(_seed(tenant_id))
    asyncio.run(engine.dispose())

    app = _make_app()
    app.dependency_overrides[verify_token] = lambda: {"sub": "test-user", "tenant_id": tenant_id}
    app.dependency_overrides[get_current_tenant_id] = lambda: tenant_id
    app.dependency_overrides[get_db_session] = _tenant_pinned_db_override(tenant_id)

    with TestClient(app) as client:
        resp = client.get(
            "/graph/query/custom",
            params={"entity_type": "contract"},
            headers={"Authorization": "Bearer faketoken"},
        )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1


def test_custom_graph_query_company_still_works():
    tenant_id = str(uuid.uuid4())
    asyncio.run(_seed(tenant_id))
    asyncio.run(engine.dispose())

    app = _make_app()
    app.dependency_overrides[verify_token] = lambda: {"sub": "test-user", "tenant_id": tenant_id}
    app.dependency_overrides[get_current_tenant_id] = lambda: tenant_id
    app.dependency_overrides[get_db_session] = _tenant_pinned_db_override(tenant_id)

    with TestClient(app) as client:
        resp = client.get(
            "/graph/query/custom",
            params={"entity_type": "company"},
            headers={"Authorization": "Bearer faketoken"},
        )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 1
