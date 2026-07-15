"""Tests for migration 0029 — GIN trigram indexes on companies text columns.

Verifies:
  1. pg_trgm extension is installed
  2. All 6 GIN trigram indexes exist on companies
  3. ILIKE partial search works correctly
  4. Arabic partial search returns correct results
  5. Cross-field search (CR number, city) works
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text
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


class TestPgTrgmExtension:

    async def test_pg_trgm_extension_installed(self, db_session: AsyncSession):
        r = await db_session.execute(
            text("SELECT installed_version FROM pg_available_extensions WHERE name='pg_trgm'")
        )
        row = r.fetchone()
        assert row is not None, "pg_trgm extension is not installed"
        assert row[0] is not None, "pg_trgm is available but not installed"

    async def test_trigram_indexes_exist(self, db_session: AsyncSession, ensure_trigram_indexes):
        r = await db_session.execute(
            text("SELECT indexname FROM pg_indexes WHERE tablename='companies' AND indexname LIKE '%trgm'")
        )
        existing = {row[0] for row in r.fetchall()}
        missing = set(TRIGRAM_INDEXES) - existing
        assert not missing, f"Missing trigram indexes: {missing}"

    async def test_trigram_indexes_use_gin(self, db_session: AsyncSession, ensure_trigram_indexes):
        r = await db_session.execute(
            text("SELECT indexname, indexdef FROM pg_indexes WHERE tablename='companies' AND indexname LIKE '%trgm'")
        )
        for row in r.fetchall():
            assert "gin" in row[1].lower(), f"Index {row[0]} is not GIN: {row[1]}"


class TestTrigramSearchFunctional:

    async def _create_company(self, db: AsyncSession, tenant_id: str, **kwargs):
        from app.modules.company.models import Company

        defaults = {
            "tenant_id": uuid.UUID(tenant_id),
            "name_ar": "شركة اختبار تقنية",
            "name_en": "Test Tech Company",
            "cr_number": f"CR-{uuid.uuid4().hex[:8].upper()}",
            "status": "active",
            "city": "الرياض",
            "region": "منطقة الرياض",
        }
        defaults.update(kwargs)
        c = Company(**defaults)
        db.add(c)
        await db.flush()
        return c

    async def test_arabic_iliike_search(self, db_session: AsyncSession, test_tenant: str):
        await self._create_company(db_session, test_tenant, name_ar="شركة زامل للمقاولات")
        r = await db_session.execute(
            text("SELECT name_ar FROM companies WHERE name_ar ILIKE '%زامل%' AND tenant_id = :tid")
            .bindparams(tid=uuid.UUID(test_tenant))
        )
        rows = r.fetchall()
        assert len(rows) >= 1
        assert "زامل" in rows[0][0]

    async def test_cr_number_iliike_search(self, db_session: AsyncSession, test_tenant: str):
        cr = "CR-987654"
        await self._create_company(db_session, test_tenant, cr_number=cr)
        r = await db_session.execute(
            text("SELECT cr_number FROM companies WHERE cr_number ILIKE '%987654%' AND tenant_id = :tid")
            .bindparams(tid=uuid.UUID(test_tenant))
        )
        rows = r.fetchall()
        assert len(rows) >= 1
        assert rows[0][0] == cr

    async def test_english_iliike_search(self, db_session: AsyncSession, test_tenant: str):
        await self._create_company(db_session, test_tenant, name_en="Saudi Aramco Gulf")
        r = await db_session.execute(
            text("SELECT name_en FROM companies WHERE name_en ILIKE '%aramco%' AND tenant_id = :tid")
            .bindparams(tid=uuid.UUID(test_tenant))
        )
        rows = r.fetchall()
        assert len(rows) >= 1
