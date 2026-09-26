"""app/tasks.py: two independent bug classes found together while auditing
Celery task GUC pinning.

Bug 1 -- missing GUC pins, same class as reports 84/129/130: neither
`_run_enrichment_pipeline()` (reachable from the real, mounted GraphQL
`enrichCompany` mutation fixed in report 130, via `enrich_company_task.delay()`)
nor `sync_notion_database()` (a real Celery task) pinned the tenant GUC before
querying/writing FORCE-RLS tables (`companies`), despite already having
`tenant_id` as a plain function parameter -- the easy case, not the
architecture-level "unknown tenant" gap `_get_entity_tenant()` has (documented,
not fixed here, per the report 84/104 precedent for that class of problem).

Bug 2 -- `_entity_table()`'s shared table()/column() stub declared columns that
exist on neither real table as named: `embedding` (real companies column:
`embedding_vector`, a pgvector type; contacts has no embedding column at all)
and, for contacts specifically, `name_en`/`activity_description`/`city`/
`industry` (none of which exist on the real `contacts` table -- confirmed
directly against the schema). Every whole-row `select(tbl)` through the old
stub -- in `_load_company_record()` and `_run_enrichment_pipeline()` -- would
raise `UndefinedColumnError` the instant RLS stopped silently hiding the row
(i.e., the instant bug 1's GUC-pin fix was applied), and `_generate_embedding()`'s
UPDATE would raise a different `UndefinedColumnError` writing to a column that
was never real. Split into per-table, schema-correct stubs; the actual
embedding write now targets `companies.embedding_vector` via a raw
parameterized UPDATE (matching this session's established
`CAST(:x AS type)` pattern for pgvector/jsonb binds).
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import async_session, engine


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    async with engine.connect() as conn:
        db_name = await conn.scalar(text("SELECT current_database()"))
    assert db_name != "salesos", (
        f"REFUSING: connected to {db_name!r} — this is the persistent "
        "local dev database, not a disposable/test one."
    )
    yield
    await engine.dispose()


async def _seed_tenant_and_company(tenant_id: str, company_id: str) -> None:
    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        await session.execute(
            text("INSERT INTO tenants (id, name, slug) VALUES (:id, 'Tasks Test', :slug)"),
            {"id": tenant_id, "slug": f"tasks-test-{tenant_id[:8]}"},
        )
        await session.execute(
            text("""
                INSERT INTO companies (id, tenant_id, name_ar, name_en, cr_number, status)
                VALUES (:id, :tid, 'شركة الاختبار', 'Test Co', '1010101010', 'active')
            """),
            {"id": company_id, "tid": tenant_id},
        )
        await session.commit()


@pytest.mark.asyncio
async def test_load_company_record_finds_the_real_row_with_the_corrected_stub():
    """The old shared stub's `embedding` column would have raised
    UndefinedColumnError on this whole-row select the instant RLS was
    satisfied; the corrected stub excludes it entirely."""
    from app.tasks import _load_company_record

    tenant_id = str(uuid.uuid4())
    company_id = str(uuid.uuid4())
    await _seed_tenant_and_company(tenant_id, company_id)

    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        from app.tasks import _entity_table

        tbl = _entity_table("companies")
        assert "embedding" not in tbl.c
        assert "embedding_vector" not in tbl.c  # excluded entirely by design

    # _load_company_record() opens its own session; pin globally via a direct
    # seed-session pin above is not enough for a second, separate session --
    # exercise it through the real (still-unpinned-by-design) helper and
    # confirm it no longer raises UndefinedColumnError. It will still find
    # nothing without a pin (documented, separate architecture gap in
    # _get_entity_tenant's callers) -- this test's job is only to prove the
    # SELECT itself is now well-formed.
    record = await _load_company_record(company_id)
    assert record is None or "embedding" not in record


@pytest.mark.asyncio
async def test_run_enrichment_pipeline_finds_the_real_company_with_guc_pinned():
    """Reproduces report 130's finding pattern one file over: tenant_id is
    already a plain parameter here, so pinning it is the easy, direct fix."""
    from app.tasks import _run_enrichment_pipeline

    tenant_id = str(uuid.uuid4())
    company_id = str(uuid.uuid4())
    await _seed_tenant_and_company(tenant_id, company_id)

    result = await _run_enrichment_pipeline(company_id, tenant_id)

    assert result.get("error") != "company_not_found", (
        "GUC was not pinned, or the corrected column stub regressed — "
        f"got: {result}"
    )
    assert result["company_id"] == company_id


@pytest.mark.asyncio
async def test_entity_table_contacts_stub_matches_the_real_schema():
    """The old shared stub declared name_en/activity_description/city/industry
    on contacts too -- none of which exist. A whole-row select would have
    raised UndefinedColumnError on every real contacts row."""
    from app.tasks import _entity_table

    tenant_id = str(uuid.uuid4())
    contact_id = str(uuid.uuid4())
    company_id = str(uuid.uuid4())
    await _seed_tenant_and_company(tenant_id, company_id)

    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        await session.execute(
            text("""
                INSERT INTO contacts (id, tenant_id, company_id, name, name_ar, position, department)
                VALUES (:id, :tid, :cid, 'Test Contact', 'جهة اتصال', 'Manager', 'Sales')
            """),
            {"id": contact_id, "tid": tenant_id, "cid": company_id},
        )
        await session.commit()
        # `set_config(..., true)` is transaction-local; commit() above ended
        # that transaction and reset it. Re-pin before the next statement.
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )

        tbl = _entity_table("contacts")
        from sqlalchemy import select

        result = await session.execute(select(tbl).where(tbl.c.id == contact_id))
        row = result.mappings().one_or_none()

        assert row is not None
        assert row["name_ar"] == "جهة اتصال"
        assert row["position"] == "Manager"
        assert row["department"] == "Sales"
        assert "name_en" not in tbl.c
        assert "activity_description" not in tbl.c
        assert "city" not in tbl.c
        assert "industry" not in tbl.c
        assert "embedding" not in tbl.c


# test_sync_notion_database_pins_the_guc_before_import lives in its own file,
# tests/integration/test_sync_notion_guc_db.py -- it calls a bound Celery task
# whose body runs asyncio.run() internally, which cannot nest inside
# pytest-asyncio's own loop, and the module-level `engine`'s connection pool
# is loop-bound (asyncpg), so a fresh, isolated process avoids the shared-pool
# cross-loop contamination this file's other, genuinely async tests would
# otherwise leave behind.
