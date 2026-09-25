"""PostgresSearchRepository's `"activity"` filter field pointed at a second,
separate, nonexistent `activity` column — the identical bug found and fixed
in the sibling `runtime/search_runtime/__init__.py` (report 79).

Mechanical finding, `domains/search/engine/postgres_repo.py` — this class
is genuinely LIVE and is the actual production search backend: wired at
boot (`app/boot/startup.py`) as `SearchRuntime(..., search_repo=
PostgresSearchRepository(...))`, and `SearchRuntime._fulltext_search()`/
`suggest()` delegate to it whenever `search_repo` is set — which it always
is at boot. Confirmed via grep: zero dedicated tests exercised this class's
real behavior before this session.

The table stub declared both `column("activity", String)` (no such DB
column — confirmed via `\\d companies`) and a correct, separate
`column("activity_description", String)` further down — two declarations
for what should be one field, identical to report 79's finding. Not
reachable from any live router today (no endpoint exposes an "activity"
query filter), so fixed ahead of any future caller. Removed the duplicate
stub and renamed the public `ALLOWED_FILTER_FIELDS` entry from `"activity"`
to `"activity_description"`.
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import async_session, engine
from domains.search.contracts.models import SearchQuery
from domains.search.engine.postgres_repo import PostgresSearchRepository


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    yield
    await engine.dispose()


async def _seed(tenant_id: str, count: int) -> None:
    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        await session.execute(
            text("INSERT INTO tenants (id, name, slug) VALUES (:id, 'Repo Test', :slug)"),
            {"id": tenant_id, "slug": f"repo-test-{tenant_id[:8]}"},
        )
        for i in range(count):
            await session.execute(
                text("""
                    INSERT INTO companies (id, tenant_id, name_ar, name_en, cr_number,
                                            activity_description, is_active)
                    VALUES (:id, :tid, :name_ar, :name_en, :cr, :activity, true)
                """),
                {
                    "id": str(uuid.uuid4()), "tid": tenant_id,
                    "name_ar": "شركة البحث", "name_en": f"Repo Search Co {i:02d}",
                    "cr": f"200000{i:04d}",
                    "activity": "General trade" if i == 0 else "Manufacturing",
                },
            )
        await session.commit()


@pytest.mark.asyncio
async def test_activity_description_filter_field_works_end_to_end():
    tenant_id = str(uuid.uuid4())
    await _seed(tenant_id, count=3)

    repo = PostgresSearchRepository(session_factory=async_session)

    from domains.search.engine.postgres_repo import ALLOWED_FILTER_FIELDS
    assert "activity_description" in ALLOWED_FILTER_FIELDS
    assert "activity" not in ALLOWED_FILTER_FIELDS

    rows, total, _next_cursor = await repo.search_by_filters(
        query="Repo",
        tenant_id=tenant_id,
        filters={"activity_description": "General trade"},
        limit=10,
        offset=0,
    )
    assert total == 1
    assert len(rows) == 1
    assert rows[0]["name_en"] == "Repo Search Co 00"


@pytest.mark.asyncio
async def test_real_keyset_cursor_pagination_advances_correctly():
    tenant_id = str(uuid.uuid4())
    await _seed(tenant_id, count=5)

    repo = PostgresSearchRepository(session_factory=async_session)
    query = SearchQuery(query="Repo", tenant_id=tenant_id, page=1, page_size=3)
    page1 = await repo.search(query)
    assert len(page1.items) == 3
    assert page1.next_cursor is not None

    page2_query = SearchQuery(
        query="Repo", tenant_id=tenant_id, page=1, page_size=3, cursor=page1.next_cursor
    )
    page2 = await repo.search(page2_query)
    assert len(page2.items) == 2

    ids_page1 = {item["id"] for item in page1.items}
    ids_page2 = {item["id"] for item in page2.items}
    assert ids_page1.isdisjoint(ids_page2)
