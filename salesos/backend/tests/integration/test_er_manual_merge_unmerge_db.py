"""Manual ER merge -> unmerge round trip (POST /er/merge, /er/unmerge).

Both handlers bound a Python list and dict straight into the jsonb columns of
md_entity_merge_history (asyncpg's jsonb encoder expects str), and unmerge
compared md_source_rows.id (uuid) with md_entity_matches.source_a_id
(varchar since migration q9r0s1t2u3v4). Every manual merge and unmerge
therefore failed and rolled back.

These are human-invoked operations (entity-resolution:CREATE); nothing here
is an automatic merge.
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import async_session, engine
from app.modules.entity_resolution.er_router import merge_entities, unmerge_entities
from app.modules.entity_resolution.er_schemas import MergeRequest, UnmergeRequest


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    yield
    await engine.dispose()


async def _company(s, name: str) -> str:
    cid = str(uuid.uuid4())
    await s.execute(
        text("INSERT INTO md_global_companies (id, slug, canonical_name) VALUES (:id, :slug, :n)"),
        {"id": cid, "slug": f"G-C-{cid[:8].upper()}", "n": name},
    )
    return cid


@pytest.mark.asyncio
async def test_manual_merge_then_unmerge_round_trip():
    performer = str(uuid.uuid4())
    async with async_session() as s:
        target = await _company(s, "Target Co")
        source = await _company(s, "Source Co")
        await s.commit()

    async with async_session() as s:
        merged = await merge_entities(
            MergeRequest(target_entity_id=target, source_entity_id=source, performed_by=performer), s)
        await s.commit()
    history_id = merged["merge_history_id"]

    async with async_session() as s:
        status = (await s.execute(text("SELECT status FROM md_global_companies WHERE id=:i"),
                                  {"i": source})).scalar_one()
        h = (await s.execute(text("SELECT source_entity_ids, details, rollback_available "
                                  "FROM md_entity_merge_history WHERE id=:i"),
                             {"i": history_id})).mappings().one()
    assert status == "merged"
    assert h["source_entity_ids"] == [source]
    assert h["details"] == {"reason": "manual_merge"}
    assert h["rollback_available"] is True

    async with async_session() as s:
        undone = await unmerge_entities(UnmergeRequest(merge_history_id=history_id, performed_by=performer), s)
        await s.commit()

    async with async_session() as s:
        status = (await s.execute(text("SELECT status FROM md_global_companies WHERE id=:i"),
                                  {"i": source})).scalar_one()
        original = (await s.execute(text("SELECT rollback_available FROM md_entity_merge_history WHERE id=:i"),
                                    {"i": history_id})).scalar_one()
        u = (await s.execute(text("SELECT operation, details FROM md_entity_merge_history WHERE id=:i"),
                             {"i": undone["unmerge_history_id"]})).mappings().one()
    assert status == "active"
    assert original is False
    assert u["operation"] == "unmerge"
    assert u["details"] == {"rollback_of": history_id}
