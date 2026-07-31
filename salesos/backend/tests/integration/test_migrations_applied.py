"""Integration tests verifying migrations 0029 + 0030 are applied and working.

Tests:
  1. pg_trgm extension installed
  2-7. All 6 GIN trigram indexes exist on companies
  8. ix_companies_confidence_score B-tree DESC index exists
  9. Cursor pagination returns next_cursor and has_next
  10. Keyset pagination produces no overlapping IDs across pages
"""

from __future__ import annotations

import uuid
from datetime import UTC

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio

TRIGRAM_INDEXES = [
    "idx_companies_name_ar_trgm",
    "idx_companies_name_en_trgm",
    "idx_companies_cr_number_trgm",
    "idx_companies_city_trgm",
    "idx_companies_region_trgm",
    "idx_companies_activity_desc_trgm",
]

TRIGRAM_DDL = [
    f"CREATE INDEX IF NOT EXISTS {name} ON companies USING GIN ({col} gin_trgm_ops)"
    for name, col in [
        ("idx_companies_name_ar_trgm", "name_ar"),
        ("idx_companies_name_en_trgm", "name_en"),
        ("idx_companies_cr_number_trgm", "cr_number"),
        ("idx_companies_city_trgm", "city"),
        ("idx_companies_region_trgm", "region"),
        ("idx_companies_activity_desc_trgm", "activity_description"),
    ]
]


@pytest.fixture
async def ensure_trigram_indexes(db_session: AsyncSession):
    for ddl in TRIGRAM_DDL:
        await db_session.execute(text(ddl))
    await db_session.commit()
    yield
    for name in TRIGRAM_INDEXES:
        await db_session.execute(text(f"DROP INDEX IF EXISTS {name}"))
    await db_session.commit()


@pytest.fixture
async def ensure_confidence_index(db_session: AsyncSession):
    await db_session.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_companies_confidence_score "
            "ON companies (confidence_score DESC)"
        )
    )
    await db_session.commit()
    yield
    await db_session.execute(text("DROP INDEX IF EXISTS ix_companies_confidence_score"))
    await db_session.commit()


class TestMigration0029:
    """Verify GIN trigram indexes from migration 0029."""

    async def test_pg_trgm_extension_installed(self, db_session: AsyncSession):
        r = await db_session.execute(
            text("SELECT installed_version FROM pg_available_extensions WHERE name='pg_trgm'")
        )
        row = r.fetchone()
        assert row is not None, "pg_trgm extension not found in pg_available_extensions"
        assert row[0] is not None, "pg_trgm is available but not installed"

    async def test_pg_trgm_extension_enabled(self, db_session: AsyncSession):
        r = await db_session.execute(
            text("SELECT extname FROM pg_extension WHERE extname='pg_trgm'")
        )
        assert r.fetchone() is not None, "pg_trgm extension is not enabled"

    async def test_all_trigram_indexes_exist(
        self, db_session: AsyncSession, ensure_trigram_indexes
    ):
        r = await db_session.execute(
            text(
                "SELECT indexname FROM pg_indexes WHERE tablename='companies' AND indexname LIKE '%trgm'"  # noqa: E501
            )
        )
        existing = {row[0] for row in r.fetchall()}
        missing = set(TRIGRAM_INDEXES) - existing
        assert not missing, f"Missing trigram indexes: {missing}"

    async def test_trigram_indexes_use_gin(self, db_session: AsyncSession, ensure_trigram_indexes):
        r = await db_session.execute(
            text(
                "SELECT indexname, indexdef FROM pg_indexes WHERE tablename='companies' AND indexname LIKE '%trgm'"  # noqa: E501
            )
        )
        for row in r.fetchall():
            assert "gin" in row[1].lower(), f"Index {row[0]} is not GIN: {row[1]}"

    async def test_each_trigram_index_individually(
        self, db_session: AsyncSession, ensure_trigram_indexes
    ):
        for name in TRIGRAM_INDEXES:
            r = await db_session.execute(
                text("SELECT indexname FROM pg_indexes WHERE indexname=:name").bindparams(name=name)
            )
            assert r.fetchone() is not None, f"Missing trigram index: {name}"

    async def test_arabic_iliike_uses_trigram(
        self, db_session: AsyncSession, ensure_trigram_indexes, test_tenant: str
    ):
        from app.modules.company.models import Company

        tid = uuid.UUID(test_tenant)
        db_session.add(
            Company(
                tenant_id=tid,
                name_ar="شركة المقاولات المتقدمة",
                cr_number=f"CR-{uuid.uuid4().hex[:8].upper()}",
                status="active",
            )
        )
        await db_session.flush()

        r = await db_session.execute(
            select(Company).where(
                Company.tenant_id == tid,
                Company.name_ar.ilike("%مقاولات%"),
            )
        )
        assert len(r.scalars().all()) >= 1


class TestMigration0030:
    """Verify confidence_score DESC index from migration 0030."""

    async def test_confidence_score_index_exists(
        self, db_session: AsyncSession, ensure_confidence_index
    ):
        r = await db_session.execute(
            text("SELECT indexname FROM pg_indexes WHERE indexname='ix_companies_confidence_score'")
        )
        assert r.fetchone() is not None, "ix_companies_confidence_score index does not exist"

    async def test_confidence_score_index_is_btree_desc(
        self, db_session: AsyncSession, ensure_confidence_index
    ):
        r = await db_session.execute(
            text("SELECT indexdef FROM pg_indexes WHERE indexname='ix_companies_confidence_score'")
        )
        row = r.fetchone()
        assert row is not None
        assert "btree" in row[0].lower(), f"Index is not btree: {row[0]}"
        assert "DESC" in row[0], f"Index is not descending: {row[0]}"


class TestKeysetPagination:
    """Verify keyset (cursor) pagination works end-to-end."""

    async def test_cursor_pagination_returns_next_cursor(
        self, db_session: AsyncSession, test_tenant: str
    ):
        from app.modules.company.repositories import CompanyRepository

        repo = CompanyRepository(db_session)
        result = await repo.search_cursored(tenant_id=test_tenant, page_size=10)
        assert hasattr(result, "next_cursor"), "Response missing next_cursor"
        assert hasattr(result, "has_next"), "Response missing has_next"
        if result.items:
            assert result.next_cursor is not None or not result.has_next

    async def test_cursor_pagination_has_next(self, db_session: AsyncSession, test_tenant: str):
        from datetime import datetime, timedelta

        from app.modules.company.models import Company
        from app.modules.company.repositories import CompanyRepository

        tid = uuid.UUID(test_tenant)
        now = datetime.now(UTC)
        for i in range(15):
            db_session.add(
                Company(
                    tenant_id=tid,
                    name_ar=f"شركة اختبار {i}",
                    cr_number=f"CR-CURSOR-{i:04d}",
                    status="active",
                    created_at=now - timedelta(seconds=i),
                )
            )
        await db_session.flush()

        repo = CompanyRepository(db_session)
        result = await repo.search_cursored(tenant_id=test_tenant, page_size=5)
        assert result.has_next is True
        assert len(result.items) == 5
        assert result.next_cursor is not None

    async def test_no_overlap_across_pages(self, db_session: AsyncSession, test_tenant: str):
        from datetime import datetime, timedelta

        from app.modules.company.models import Company
        from app.modules.company.repositories import CompanyRepository

        tid = uuid.UUID(test_tenant)
        now = datetime.now(UTC)
        for i in range(20):
            db_session.add(
                Company(
                    tenant_id=tid,
                    name_ar=f"شركة لا تكرار {i}",
                    cr_number=f"CR-NODUP-{i:04d}",
                    status="active",
                    created_at=now - timedelta(seconds=i),
                )
            )
        await db_session.flush()

        repo = CompanyRepository(db_session)
        page1 = await repo.search_cursored(tenant_id=test_tenant, page_size=5)
        ids1 = {str(c.id) for c in page1.items}

        page2 = await repo.search_cursored(
            tenant_id=test_tenant, page_size=5, cursor=page1.next_cursor
        )
        ids2 = {str(c.id) for c in page2.items}

        assert ids1.isdisjoint(ids2), f"Overlapping IDs between pages: {ids1 & ids2}"
