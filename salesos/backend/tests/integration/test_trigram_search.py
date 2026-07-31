"""Integration tests for GIN trigram-powered ILIKE search on companies.

These tests verify that partial search using ILIKE returns correct results
across Arabic, English, exact, and fuzzy queries. The underlying GIN trigram
indexes (migration 0029) enable fast index scans instead of sequential scans.

Requires a running PostgreSQL with pg_trgm extension enabled.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


async def _create_company(db: AsyncSession, tenant_id: str, **kwargs):
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


async def _search_companies(db: AsyncSession, tenant_id: str, q: str, limit: int = 20):
    from app.modules.company.models import Company

    stmt = (
        select(Company)
        .where(Company.tenant_id == uuid.UUID(tenant_id))
        .where(
            Company.name_ar.ilike(f"%{q}%")
            | Company.name_en.ilike(f"%{q}%")
            | Company.cr_number.ilike(f"%{q}%")
            | Company.city.ilike(f"%{q}%")
            | Company.activity_description.ilike(f"%{q}%")
        )
        .limit(limit)
    )
    r = await db.execute(stmt)
    return list(r.scalars().all())


class TestTrigramArabicSearch:
    async def test_exact_arabic_name(self, db_session: AsyncSession, test_tenant: str):
        await _create_company(db_session, test_tenant, name_ar="شركة زامل للمقاولات")
        results = await _search_companies(db_session, test_tenant, "زامل")
        assert len(results) >= 1
        assert results[0].name_ar == "شركة زامل للمقاولات"

    async def test_partial_arabic_middle(self, db_session: AsyncSession, test_tenant: str):
        await _create_company(db_session, test_tenant, name_ar="المجموعة السعودية للاستثمار")
        results = await _search_companies(db_session, test_tenant, "سعودية")
        assert len(results) >= 1

    async def test_partial_arabic_suffix(self, db_session: AsyncSession, test_tenant: str):
        await _create_company(db_session, test_tenant, name_ar="مؤسسة عبدالله بن أحمد التجارية")
        results = await _search_companies(db_session, test_tenant, "تجارية")
        assert len(results) >= 1

    async def test_arabic_prefix_search(self, db_session: AsyncSession, test_tenant: str):
        await _create_company(db_session, test_tenant, name_ar="شركة الاتصالات السعودية")
        results = await _search_companies(db_session, test_tenant, "اتصالات")
        assert len(results) >= 1

    async def test_multiple_arabic_results_ranked(self, db_session: AsyncSession, test_tenant: str):
        for name in [
            "مؤسسة المقاولات الحديثة",
            "شركة المقاولات المتطورة",
            "مكتب مقاولات هندسية",
        ]:
            await _create_company(db_session, test_tenant, name_ar=name)
        results = await _search_companies(db_session, test_tenant, "مقاولات")
        assert len(results) >= 2


class TestTrigramEnglishSearch:
    async def test_exact_english_name(self, db_session: AsyncSession, test_tenant: str):
        await _create_company(db_session, test_tenant, name_en="Saudi Aramco")
        results = await _search_companies(db_session, test_tenant, "Aramco")
        assert len(results) >= 1
        assert results[0].name_en == "Saudi Aramco"

    async def test_partial_english_contains(self, db_session: AsyncSession, test_tenant: str):
        await _create_company(db_session, test_tenant, name_en="Al Rajhi Banking & Investment")
        results = await _search_companies(db_session, test_tenant, "Rajhi")
        assert len(results) >= 1

    async def test_english_prefix(self, db_session: AsyncSession, test_tenant: str):
        await _create_company(db_session, test_tenant, name_en="SABIC Innovative Plastics")
        results = await _search_companies(db_session, test_tenant, "SABIC")
        assert len(results) >= 1


class TestTrigramCrossField:
    async def test_search_by_cr_number_partial(self, db_session: AsyncSession, test_tenant: str):
        cr = "CR-123456"
        await _create_company(db_session, test_tenant, cr_number=cr)
        results = await _search_companies(db_session, test_tenant, "123456")
        assert len(results) >= 1
        assert results[0].cr_number == cr

    async def test_search_by_city(self, db_session: AsyncSession, test_tenant: str):
        await _create_company(db_session, test_tenant, city="جدة")
        results = await _search_companies(db_session, test_tenant, "جدة")
        assert len(results) >= 1

    async def test_search_with_activity_description(
        self, db_session: AsyncSession, test_tenant: str
    ):
        await _create_company(
            db_session,
            test_tenant,
            activity_description="توريد وتركيب أنظمة السلامة",
        )
        results = await _search_companies(db_session, test_tenant, "سلامة")
        assert len(results) >= 1


class TestTrigramEdgeCases:
    async def test_short_query_returns_results(self, db_session: AsyncSession, test_tenant: str):
        await _create_company(db_session, test_tenant, name_ar="بيت التمويل الكويتي")
        results = await _search_companies(db_session, test_tenant, "بيت")
        assert len(results) >= 1

    async def test_no_match_returns_empty(self, db_session: AsyncSession, test_tenant: str):
        results = await _search_companies(db_session, test_tenant, "شركةغيرموجودة")
        assert len(results) == 0

    async def test_multiple_companies_search(self, db_session: AsyncSession, test_tenant: str):
        for i in range(5):
            await _create_company(
                db_session,
                test_tenant,
                name_ar=f"شركة اختبار رقم {i}",
                cr_number=f"CR-MULTI-{i}",
            )
        results = await _search_companies(db_session, test_tenant, "اختبار")
        assert len(results) == 5
