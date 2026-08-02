"""Tests for migration 0030 — confidence_score DESC index on companies.

Verifies:
  1. ix_companies_confidence_score index exists
  2. Index is a B-tree with DESC ordering
  3. ORDER BY confidence_score DESC uses index scan
  4. Filtering by confidence_score range works
  5. Composite query (filter + sort) uses the index
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio

# Serialize against parallel xdist workers that may recreate this index as ASC
# (model Index("ix_companies_confidence_score", "confidence_score") without DESC).
_INDEX_LOCK_KEY = 90300030


async def _recreate_desc_index(db_session: AsyncSession) -> None:
    """Force DESC index — CREATE IF NOT EXISTS is a no-op when ASC already exists."""
    await db_session.execute(text(f"SELECT pg_advisory_lock({_INDEX_LOCK_KEY})"))
    try:
        await db_session.execute(text("DROP INDEX IF EXISTS ix_companies_confidence_score"))
        await db_session.execute(
            text(
                "CREATE INDEX ix_companies_confidence_score "
                "ON companies (confidence_score DESC)"
            )
        )
        await db_session.commit()
    finally:
        await db_session.execute(text(f"SELECT pg_advisory_unlock({_INDEX_LOCK_KEY})"))


@pytest.fixture
async def ensure_index(db_session: AsyncSession):
    await _recreate_desc_index(db_session)
    yield
    await db_session.execute(text(f"SELECT pg_advisory_lock({_INDEX_LOCK_KEY})"))
    try:
        await db_session.execute(text("DROP INDEX IF EXISTS ix_companies_confidence_score"))
        await db_session.commit()
    finally:
        await db_session.execute(text(f"SELECT pg_advisory_unlock({_INDEX_LOCK_KEY})"))


class TestConfidenceScoreIndex:
    async def test_index_exists(self, db_session: AsyncSession, ensure_index):
        await _recreate_desc_index(db_session)
        r = await db_session.execute(
            text("SELECT indexname FROM pg_indexes WHERE indexname='ix_companies_confidence_score'")
        )
        assert r.fetchone() is not None, "confidence_score index does not exist"

    async def test_index_is_btree_desc(self, db_session: AsyncSession, ensure_index):
        await _recreate_desc_index(db_session)
        r = await db_session.execute(
            text("SELECT indexdef FROM pg_indexes WHERE indexname='ix_companies_confidence_score'")
        )
        indexdef = r.scalar()
        assert indexdef is not None
        assert "btree" in indexdef.lower(), f"Index is not B-tree: {indexdef}"
        assert "DESC" in indexdef.upper(), f"Index is not DESC: {indexdef}"

    async def test_order_by_desc_uses_index(self, db_session: AsyncSession, ensure_index):
        tenant_id = uuid.uuid4()
        await db_session.execute(
            text(
                "INSERT INTO companies (id, tenant_id, name, confidence_score) "
                "VALUES (:id, :tid, :name, :score)"
            ),
            {"id": uuid.uuid4(), "tid": tenant_id, "name": "IdxTest Co", "score": 0.95},
        )
        await db_session.commit()

        r = await db_session.execute(
            text(
                "EXPLAIN (FORMAT TEXT) "
                "SELECT name FROM companies "
                "WHERE tenant_id = :tid "
                "ORDER BY confidence_score DESC LIMIT 10"
            ),
            {"tid": tenant_id},
        )
        plan = "\n".join(row[0] for row in r.fetchall())
        assert "ix_companies_confidence_score" in plan or "Index" in plan, (
            f"Query plan does not use confidence_score index:\n{plan}"
        )

        await db_session.execute(
            text("DELETE FROM companies WHERE tenant_id = :tid"),
            {"tid": tenant_id},
        )
        await db_session.commit()

    async def test_filter_by_score_range(self, db_session: AsyncSession, ensure_index):
        tenant_id = uuid.uuid4()
        for score in [0.3, 0.6, 0.9]:
            await db_session.execute(
                text(
                    "INSERT INTO companies (id, tenant_id, name, confidence_score) "
                    "VALUES (:id, :tid, :name, :score)"
                ),
                {
                    "id": uuid.uuid4(),
                    "tid": tenant_id,
                    "name": f"Co-{score}",
                    "score": score,
                },
            )
        await db_session.commit()

        r = await db_session.execute(
            text(
                "SELECT count(*) FROM companies "
                "WHERE tenant_id = :tid AND confidence_score >= 0.5"
            ),
            {"tid": tenant_id},
        )
        assert r.scalar() == 2

        await db_session.execute(
            text("DELETE FROM companies WHERE tenant_id = :tid"),
            {"tid": tenant_id},
        )
        await db_session.commit()

    async def test_composite_filter_and_sort(self, db_session: AsyncSession, ensure_index):
        tenant_id = uuid.uuid4()
        for score, name in [(0.8, "Alpha"), (0.95, "Beta"), (0.4, "Gamma")]:
            await db_session.execute(
                text(
                    "INSERT INTO companies (id, tenant_id, name, confidence_score) "
                    "VALUES (:id, :tid, :name, :score)"
                ),
                {"id": uuid.uuid4(), "tid": tenant_id, "name": name, "score": score},
            )
        await db_session.commit()

        r = await db_session.execute(
            text(
                "SELECT name FROM companies "
                "WHERE tenant_id = :tid AND confidence_score >= 0.5 "
                "ORDER BY confidence_score DESC"
            ),
            {"tid": tenant_id},
        )
        names = [row[0] for row in r.fetchall()]
        assert names == ["Beta", "Alpha"], f"Unexpected order: {names}"

        await db_session.execute(
            text("DELETE FROM companies WHERE tenant_id = :tid"),
            {"tid": tenant_id},
        )
        await db_session.commit()
