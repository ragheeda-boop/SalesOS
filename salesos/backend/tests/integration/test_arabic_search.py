"""Integration tests for Arabic search — full search pipeline with Arabic text.

These tests verify the end-to-end search flow using Arabic company names,
covering normalization, fuzzy matching, tokenization, and result ranking.

Requires a running PostgreSQL instance with the SalesOS schema.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from domains.search.normalization.arabic_normalizer import ArabicSearchNormalizer
from domains.search.normalization.company_matcher import CompanyNameMatcher
from domains.search.engine.parser import QueryParser


# ── Helper: create test company ─────────────────────────────────────────


async def _create_test_company(db: AsyncSession, tenant_id: str, **kwargs):
    from app.modules.company.models import Company

    defaults = {
        "tenant_id": uuid.UUID(tenant_id),
        "name_ar": "شركة اختبار",
        "cr_number": f"CR-TEST-{uuid.uuid4().hex[:6].upper()}",
        "status": "active",
        "city": "الرياض",
        "region": "منطقة الرياض",
    }
    defaults.update(kwargs)
    company = Company(**defaults)
    db.add(company)
    await db.flush()
    return company


# ── Normalizer Integration (3 tests) ────────────────────────────────────


class TestNormalizerIntegration:
    """Verify normalizer works end-to-end with different configurations."""

    def test_default_normalizer_pipeline(self):
        normalizer = ArabicSearchNormalizer.default()
        text = "شَرِكَةُ المُقَاوَلَاتِ الحَدِيثَةِ"
        result = normalizer.normalize(text)
        assert "شركه" in result
        assert "المقاولات" in result
        assert "الحديثه" in result
        assert "َ" not in result
        assert "ِ" not in result

    def test_for_matching_pipeline(self):
        normalizer = ArabicSearchNormalizer.for_matching()
        text = "شركة أرامكو السعودية المحدودة - الرياض"
        result = normalizer.normalize(text)
        assert "أرامكو" in result or "ارامكو" in result
        assert "الرياض" in result
        assert "شركة" not in result

    def test_normalizer_idempotent(self):
        normalizer = ArabicSearchNormalizer.for_matching()
        texts = [
            "شركة سابك للصناعات الأساسية",
            "مؤسسة الاتصالات السعودية",
            "مجموعة سامبا المالية",
        ]
        for t in texts:
            once = normalizer.normalize(t)
            twice = normalizer.normalize(once)
            assert once == twice


# ── Company Name Matcher Integration (3 tests) ─────────────────────────


class TestMatcherIntegration:
    """Verify CompanyNameMatcher works with real Saudi business names."""

    def test_saudi_bank_names(self):
        matcher = CompanyNameMatcher.default()
        pairs = [
            ("البنك الأهلي السعودي", "البنك الاهلي السعودي", True),
            ("مصرف الراجحي", "مصرف الراجحي", True),
        ]
        for a, b, expected in pairs:
            result = matcher.match(a, b)
            assert result.is_match == expected, f"Failed: {a} vs {b}"

    def test_contracting_companies(self):
        matcher = CompanyNameMatcher.default()
        result = matcher.match(
            "شركة الزامل للمقاولات",
            "مؤسسة الزامل للمقاولات",
        )
        assert result.is_match

    def test_engineering_firms(self):
        matcher = CompanyNameMatcher.default()
        result = matcher.match(
            "مكتب دراسات هندسية",
            "مكتب دراسات هندسيه",
        )
        assert result.is_match


# ── Query Parser Integration (2 tests) ──────────────────────────────────


class TestQueryParserIntegration:
    """Verify QueryParser handles Arabic text correctly."""

    def test_parse_arabic_query(self):
        parser = QueryParser.default()
        parsed = parser.parse("شركة مقاولات في الرياض")
        assert len(parsed.tokens) > 0
        assert parsed.normalized_query is not None

    def test_parse_arabic_with_field_filters(self):
        parser = QueryParser.default()
        parsed = parser.parse("مقاولات city:الرياض")
        assert len(parsed.tokens) > 0
        assert "city" in parsed.field_filters


# ── Arabic Tokenization (2 tests) ──────────────────────────────────────


class TestArabicTokenization:
    """Verify Arabic text is properly tokenized for search."""

    def test_arabic_words_split_correctly(self):
        parser = QueryParser.default()
        parsed = parser.parse("شركة مقاولات وإنشاءات")
        tokens = [t for t in parsed.tokens if len(t) > 1]
        assert any("مقاولات" in t for t in tokens)
        assert parsed.normalized_query is not None

    def test_arabic_with_numbers(self):
        parser = QueryParser.default()
        parsed = parser.parse("شركة 2024")
        assert any("2024" in t for t in parsed.tokens)


# ── Entity Resolution Integration (2 tests) ────────────────────────────


@pytest.mark.asyncio
async def test_entity_resolution_arabic_name_matching(
    db_session: AsyncSession, test_tenant: str
):
    from app.modules.entity_resolution.service import EntityResolutionService
    from app.modules.company.models import Company

    c1 = Company(
        tenant_id=uuid.UUID(test_tenant),
        name_ar="شركة أرامكو السعودية",
        cr_number="CR-ARAMCO-001",
        status="active",
    )
    db_session.add(c1)
    await db_session.flush()

    service = EntityResolutionService(db_session)
    candidates = await service.find_duplicates(
        tenant_id=test_tenant,
        name="ارامكو السعوديه",
    )

    assert len(candidates) >= 1
    match = next((c for c in candidates if "name_match" in c["match_fields"]), None)
    assert match is not None, "Should find name match for normalized Arabic name"


@pytest.mark.asyncio
async def test_entity_resolution_prefix_variations(
    db_session: AsyncSession, test_tenant: str
):
    from app.modules.entity_resolution.service import EntityResolutionService
    from app.modules.company.models import Company

    c1 = Company(
        tenant_id=uuid.UUID(test_tenant),
        name_ar="مؤسسة سابك للصناعات",
        cr_number="CR-SABIC-001",
        status="active",
    )
    db_session.add(c1)
    await db_session.flush()

    service = EntityResolutionService(db_session)
    duplicates = await service.find_duplicates(
        tenant_id=test_tenant,
        name="شركة سابك للصناعات",
    )

    assert len(duplicates) >= 1
