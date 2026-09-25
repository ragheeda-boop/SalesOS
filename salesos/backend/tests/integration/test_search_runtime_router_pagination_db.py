"""GET /search's cursor-based pagination was completely non-functional.

Mechanical finding, `runtime/search_runtime/router.py::search()` — this
route is genuinely live (mounted at boot, no test coverage previously
existed for this router at all):

`decode_cursor` was imported but never called anywhere in the function.
`offset` passed to `SearchRuntime.search()` was hardcoded to `0`
regardless of the `cursor` query parameter, so following a response's own
`next_cursor` value always returned page 1 again — pagination beyond the
first page was silently broken for every caller. A second, compounding bug:
the cursor's sort-value component was built from
`getattr(last, "created_at", None)`, but `SearchResultItem` has no
`created_at` attribute at all, so that value was always the fabricated
"now" timestamp rather than anything meaningful.

`SearchRuntime.search()` only ever supported a plain numeric offset (no
keyset `WHERE` clause exists in any of its fulltext/semantic/hybrid query
paths) — genuinely different from `sdk.pagination`'s id+sort_value keyset
cursor used correctly elsewhere in this codebase. Reusing that generic
codec here for a capability it never had was the root mismatch. Fixed with
a small local offset cursor (`_encode_offset_cursor`/`_decode_offset_cursor`)
that matches what this API can actually do, rather than either bolting a
real keyset condition onto `SearchRuntime` (a larger, separate change) or
leaving the parameter silently inert.
"""

from __future__ import annotations

import asyncio
import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.database import async_session, engine
from app.dependencies import get_current_tenant_id, verify_token
from runtime.search_runtime import SearchRuntime
from runtime.search_runtime.router import router as search_router


def _make_app(tenant_id: str) -> FastAPI:
    app = FastAPI()
    app.include_router(search_router)
    app.state.search_runtime = SearchRuntime(session_factory=async_session)
    app.dependency_overrides[verify_token] = lambda: {"sub": "test-user", "tenant_id": tenant_id}
    app.dependency_overrides[get_current_tenant_id] = lambda: tenant_id
    return app


async def _seed(tenant_id: str, count: int) -> None:
    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        await session.execute(
            text("INSERT INTO tenants (id, name, slug) VALUES (:id, 'Pagination Test', :slug)"),
            {"id": tenant_id, "slug": f"pg-test-{tenant_id[:8]}"},
        )
        for i in range(count):
            await session.execute(
                text("""
                    INSERT INTO companies (id, tenant_id, name_ar, name_en, cr_number, is_active)
                    VALUES (:id, :tid, :name_ar, :name_en, :cr, true)
                """),
                {
                    "id": str(uuid.uuid4()), "tid": tenant_id,
                    "name_ar": "شركة الاختبار", "name_en": f"Pagination Co {i:02d}",
                    "cr": f"100000{i:04d}",
                },
            )
        await session.commit()


def test_next_cursor_actually_advances_to_a_different_page():
    tenant_id = str(uuid.uuid4())
    asyncio.run(_seed(tenant_id, count=7))
    asyncio.run(engine.dispose())

    app = _make_app(tenant_id)
    with TestClient(app) as client:
        page1 = client.get(
            "/search", params={"q": "Pagination", "strategy": "fulltext", "limit": 5},
            headers={"Authorization": "Bearer faketoken"},
        )
        assert page1.status_code == 200, page1.text
        body1 = page1.json()
        assert body1["has_next"] is True
        assert body1["next_cursor"] is not None
        assert len(body1["items"]) == 5

        page2 = client.get(
            "/search",
            params={"q": "Pagination", "strategy": "fulltext", "limit": 5, "cursor": body1["next_cursor"]},
            headers={"Authorization": "Bearer faketoken"},
        )
        assert page2.status_code == 200, page2.text
        body2 = page2.json()
        assert body2["has_next"] is False
        assert len(body2["items"]) == 2

        # The whole point of the fix: page 2 must be genuinely different
        # rows from page 1, not the same first page again.
        ids_page1 = {item["id"] for item in body1["items"]}
        ids_page2 = {item["id"] for item in body2["items"]}
        assert ids_page1.isdisjoint(ids_page2)

    asyncio.run(engine.dispose())


def test_invalid_cursor_is_rejected_not_silently_ignored():
    tenant_id = str(uuid.uuid4())
    asyncio.run(_seed(tenant_id, count=1))
    asyncio.run(engine.dispose())

    app = _make_app(tenant_id)
    with TestClient(app) as client:
        resp = client.get(
            "/search",
            params={"q": "Pagination", "cursor": "not-valid-base64!!!"},
            headers={"Authorization": "Bearer faketoken"},
        )
    assert resp.status_code == 422

    asyncio.run(engine.dispose())
