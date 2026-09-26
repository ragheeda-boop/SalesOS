"""PostgresPipelineRepository's stage-entry methods used the wrong field
names on both sides of the domain-contract/DB-model boundary, guaranteeing
a crash on every real call.

Mechanical finding: the `StageEntry` domain contract (contracts/models.py)
has `stage_name`/`exit_reason` and no `tenant_id`; the DB model
(`StageEntryModel`, table `commercial_stage_entries`) has `from_stage`/
`to_stage`/`duration_hours` and a required `tenant_id`. save_stage_entry()
read `entry.from_stage`/`entry.to_stage` off the contract (AttributeError:
no such fields) and defaulted `tenant_id=""` (would fail RLS's WITH CHECK
against the real pinned tenant even if the AttributeError didn't fire
first); get_active_stage_entry()/get_stage_history() constructed
StageEntry(from_stage=..., to_stage=..., duration_hours=...) (TypeError:
unexpected keyword arguments -- none of those exist on the contract).
`PostgresPipelineRepository` is wired live via app/routers/commercial.py's
`_get_pipe(db)` factory, so every real call to PipelineService.enter_stage/
exit_stage through that router would have crashed immediately.

A second, independent bug was found while fixing the first: the original
save_stage_entry() always did an unconditional INSERT. `enter_stage()`'s
"close the previous entry" step re-saves the same already-persisted
`prev` object (same primary key) to set exited_at -- an unconditional
INSERT there would raise a primary-key violation on every stage
transition after the first, even with the field names fixed. The fix
upserts by id.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest_asyncio
from sqlalchemy import text

from app.database import async_session, engine
from domains.commercial.infrastructure.postgres_repositories import (
    PostgresPipelineRepository,
)
from domains.commercial.pipeline.engine.service import PipelineService


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    """Report 118 safety net: a bare host-side pytest run of this file that
    exports only DATABASE_URL silently targets the persistent local dev
    Postgres (this repo's checked-in .env sets APP_POSTGRES_PASSWORD, which
    takes precedence over DATABASE_URL for app.database.engine). Run with
    APP_POSTGRES_PASSWORD="" (or APP_DATABASE_URL_OVERRIDE) set to the
    intended disposable database.
    """
    async with engine.connect() as conn:
        db_name = await conn.scalar(text("SELECT current_database()"))
    assert db_name != "salesos", (
        f"REFUSING: connected to {db_name!r} — this is the persistent "
        "local dev database, not a disposable/test one. Set "
        'APP_POSTGRES_PASSWORD="" (or APP_DATABASE_URL_OVERRIDE) to point '
        "app.database.engine at an ephemeral container before running "
        "this file."
    )
    yield
    await engine.dispose()


async def _seed_tenant_company_opportunity_pipeline(session, tenant_id: str) -> tuple[str, str]:
    await session.execute(
        text("INSERT INTO tenants (id, name, slug) VALUES (:id, 'Pipeline Entry Test', :slug)"),
        {"id": tenant_id, "slug": f"pipe-entry-{tenant_id[:8]}"},
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
            "VALUES (:id, :tid, :cid, 'Deal 1', 'prospecting', 50000, 0.1, "
            " 'open', :now, :now)"
        ),
        {"id": opp_id, "tid": tenant_id, "cid": company_id, "now": now},
    )
    pipeline_id = str(uuid.uuid4())
    stages = [
        {"name": "prospecting", "name_ar": "استكشاف", "order": 1, "default_probability": 0.1, "is_terminal": False},
        {"name": "qualification", "name_ar": "تأهيل", "order": 2, "default_probability": 0.25, "is_terminal": False},
    ]
    await session.execute(
        text(
            "INSERT INTO commercial_pipeline_definitions "
            "(id, tenant_id, name, stages, created_at, updated_at) "
            "VALUES (:id, :tid, 'Test Pipeline', CAST(:stages AS jsonb), :now, :now)"
        ),
        {"id": pipeline_id, "tid": tenant_id, "stages": __import__("json").dumps(stages), "now": now},
    )
    return opp_id, pipeline_id


async def test_enter_stage_twice_persists_correct_from_to_stage_and_closes_prior_entry():
    tenant_id = str(uuid.uuid4())

    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        opp_id, pipeline_id = await _seed_tenant_company_opportunity_pipeline(session, tenant_id)
        await session.commit()
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )

        service = PipelineService(PostgresPipelineRepository(session))

        first = await service.enter_stage(opp_id, pipeline_id, to_stage="prospecting")
        assert first.stage_name == "prospecting"
        assert first.from_stage == ""
        assert first.tenant_id == tenant_id
        assert first.exited_at is None

        second = await service.enter_stage(
            opp_id, pipeline_id, to_stage="qualification", from_stage="prospecting"
        )
        assert second.stage_name == "qualification"
        assert second.from_stage == "prospecting"
        assert second.tenant_id == tenant_id

        await session.commit()

        history = await service._repository.get_stage_history(opp_id)
        assert len(history) == 2
        closed, opened = history[0], history[1]
        assert closed.stage_name == "prospecting"
        assert closed.exited_at is not None
        assert opened.stage_name == "qualification"
        assert opened.from_stage == "prospecting"
        assert opened.exited_at is None

        row_count = await session.scalar(
            text("SELECT COUNT(*) FROM commercial_stage_entries WHERE opportunity_id = :oid"),
            {"oid": opp_id},
        )
        assert row_count == 2

        closed_row = (
            await session.execute(
                text(
                    "SELECT to_stage, from_stage, duration_hours, tenant_id "
                    "FROM commercial_stage_entries "
                    "WHERE opportunity_id = :oid AND exited_at IS NOT NULL"
                ),
                {"oid": opp_id},
            )
        ).one()
        assert closed_row.to_stage == "prospecting"
        assert closed_row.from_stage == ""
        assert closed_row.duration_hours is not None
        assert closed_row.tenant_id == tenant_id

        await session.rollback()
