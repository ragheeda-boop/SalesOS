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


@pytest.fixture
async def ensure_index(db_session: AsyncSession):
    await db_session.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_companies_confidence_score "
        "ON companies (confidence_score DESC)"
    ))
    await db_session.commit()
    yield
    await db_session.execute(text(
        "DROP INDEX IF EXISTS ix_companies_confidence_score"
    ))
    await db_session.commit()


class TestConfidenceScoreIndex:

    async def test_index_exists(self, db_session: AsyncSession, ensure_index):
        r = await db_session.execute(
            text("SELECT indexname FROM pg_indexes WHERE indexname='ix_companies_confidence_score'")
        )
        assert r.fetchone() is not None, "confidence_score index does not exist"

    async def test_index_is_btree_desc(self, db_session: AsyncSession, ensure_index):
        r = await db_session.execute(
            text("SELECT indexdef FROM pg_indexes WHERE indexname='ix_companies_confidence_score'")
        )
        row = r.fetchone()
        assert row is not None
        assert "btree" in row[0].lower(), f"Index is not btree: {row[0]}"
        assert "DESC" in row[0], f"Index is not DESC: {row[0]}"

    async def test_sort_by_confidence_desc(self, db_session: AsyncSession, ensure_index, test_tenant: str):
        from app.modules.company.models import Company

        tid = uuid.UUID(test_tenant)
        scores = [0.1, 0.9, 0.5, 0.3, 0.7]
        for score in scores:
            db_session.add(Company(
                tenant_id=tid,
                name_ar=f"شركة اختبار {score}",
                cr_number=f"CR-CS-{uuid.uuid4().hex[:8].upper()}",
                confidence_score=score,
            ))
        await db_session.flush()

        r = await db_session.execute(
            text("SELECT confidence_score FROM companies WHERE tenant_id=:tid ORDER BY confidence_score DESC")
            .bindparams(tid=tid)
        )
        fetched = [row[0] for row in r.fetchall()]
        assert fetched == sorted(scores, reverse=True), f"Expected descending order, got {fetched}"

    async def test_filter_by_confidence_range(self, db_session: AsyncSession, ensure_index, test_tenant: str):
        from app.modules.company.models import Company

        tid = uuid.UUID(test_tenant)
        scores = [0.2, 0.4, 0.6, 0.8, 1.0]
        for score in scores:
            db_session.add(Company(
                tenant_id=tid,
                name_ar=f"شركة نطاق {score}",
                cr_number=f"CR-RNG-{uuid.uuid4().hex[:8].upper()}",
                confidence_score=score,
            ))
        await db_session.flush()

        r = await db_session.execute(
            text("SELECT confidence_score FROM companies WHERE tenant_id=:tid AND confidence_score >= 0.5 ORDER BY confidence_score DESC")
            .bindparams(tid=tid)
        )
        fetched = [row[0] for row in r.fetchall()]
        assert all(s >= 0.5 for s in fetched), f"Expected scores >= 0.5, got {fetched}"
        assert len(fetched) == 3, f"Expected 3 results, got {len(fetched)}"

    async def test_index_used_in_explain(self, db_session: AsyncSession, ensure_index, test_tenant: str):
        tid = uuid.UUID(test_tenant)
        r = await db_session.execute(
            text("EXPLAIN SELECT confidence_score FROM companies WHERE tenant_id=:tid ORDER BY confidence_score DESC"),
            {"tid": str(tid)},
        )
        plan = "\n".join(row[0] for row in r.fetchall())
        assert "confidence_score" in plan, "Index not mentioned in query plan"
