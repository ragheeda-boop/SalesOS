"""Tests for ArabicSearchNormalizer — comprehensive Arabic text normalization.

Covers: Alef, Yeh, Teh Marbuta, Tatweel, diacritics, stop words,
Indic digits, company prefixes/suffixes, dash separators, and
real-world Saudi company name normalization (BUG-002).
"""

from __future__ import annotations

import pytest

from domains.search.normalization.arabic_normalizer import ArabicSearchNormalizer


# ── Fixtures ────────────────────────────────────────────────────────────


@pytest.fixture
def normalizer() -> ArabicSearchNormalizer:
    return ArabicSearchNormalizer.default()


@pytest.fixture
def indexing_normalizer() -> ArabicSearchNormalizer:
    return ArabicSearchNormalizer.for_indexing()


@pytest.fixture
def matching_normalizer() -> ArabicSearchNormalizer:
    return ArabicSearchNormalizer.for_matching()


# ── Alef Normalization (2 tests) ────────────────────────────────────────


class TestAlefNormalization:
    def test_alef_with_hamza_above(self, normalizer):
        assert normalizer.normalize("أحمد") == "احمد"

    def test_all_alef_variants(self, normalizer):
        assert normalizer.normalize("أساس إبراهيم آفاق") == "اساس ابراهيم افاق"


# ── Yeh Normalization (2 tests) ────────────────────────────────────────


class TestYehNormalization:
    def test_alef_maksura_to_yeh(self, normalizer):
        assert normalizer.normalize("موسى") == "موسي"

    def test_persian_yeh(self, normalizer):
        assert normalizer.normalize("ایران") == "ايران"


# ── Teh Marbuta Normalization (2 tests) ──────────────────────────────────


class TestTehMarbutaNormalization:
    def test_teh_marbuta_to_heh(self, normalizer):
        assert normalizer.normalize("شركة") == "شركه"

    def test_multiple_teh_marbuta(self, normalizer):
        assert normalizer.normalize("إدارة المشاريع الهندسية") == "اداره المشاريع الهندسيه"


# ── Tatweel / Kashida (2 tests) ─────────────────────────────────────────


class TestTatweelRemoval:
    def test_remove_tatweel(self, normalizer):
        result = normalizer.normalize("الـــــرياض")
        assert "ـ" not in result
        assert result == "الرياض"

    def test_tatweel_with_diacritics(self, normalizer):
        result = normalizer.normalize("بِــــــــــــــسْمِ")
        assert "ـ" not in result
        assert result == "بسم"


# ── Diacritics Removal (2 tests) ────────────────────────────────────────


class TestDiacriticsRemoval:
    def test_remove_damma_shadda(self, normalizer):
        assert normalizer.normalize("مُحَمَّد") == "محمد"

    def test_full_tashkeel_sentence(self, normalizer):
        text = "بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ"
        result = normalizer.normalize(text)
        assert "َ" not in result and "ِ" not in result and "ُ" not in result


# ── Indic Digits Conversion (2 tests) ───────────────────────────────────


class TestIndicDigits:
    def test_arabic_indic_to_western(self, normalizer):
        normalizer.normalize_digits = True
        assert normalizer.normalize("رقم ١٢٣") == "رقم 123"

    def test_mixed_indic_western(self, normalizer):
        normalizer.normalize_digits = True
        assert normalizer.normalize("مجموعة ٤٥") == "مجموعه 45"


# ── Company Prefix Removal (2 tests) ────────────────────────────────────


class TestCompanyPrefixRemoval:
    def test_remove_sharika_prefix(self, normalizer):
        normalizer.remove_company_prefixes = True
        result = normalizer.normalize("شركة أرامكو")
        assert "أرامكو" in result or "ارامكو" in result
        assert "شركة" not in result and "شركه" not in result

    def test_remove_muasasa_prefix(self, normalizer):
        normalizer.remove_company_prefixes = True
        result = normalizer.normalize("مؤسسة سابك")
        assert "سابك" in result
        assert "مؤسسة" not in result and "موسسه" not in result


# ── Company Suffix Removal (2 tests) ────────────────────────────────────


class TestCompanySuffixRemoval:
    def test_remove_ltd_suffix(self, normalizer):
        normalizer.remove_company_suffixes = True
        result = normalizer.normalize("أرامكو المحدودة")
        assert "أرامكو" in result or "ارامكو" in result
        assert "المحدودة" not in result and "المحدوده" not in result

    def test_remove_saudi_suffix(self, normalizer):
        normalizer.remove_company_suffixes = True
        result = normalizer.normalize("الاتصالات السعودية")
        assert "الاتصالات" in result
        assert "السعودية" not in result and "السعوديه" not in result


# ── Dash Separator Removal (2 tests) ────────────────────────────────────


class TestSeparatorRemoval:
    def test_remove_dash_separator(self, normalizer):
        normalizer.remove_separators = True
        assert normalizer.normalize("شركة - الرياض") == "شركه الرياض"

    def test_remove_mixed_dashes(self, normalizer):
        normalizer.remove_separators = True
        result = normalizer.normalize("مجموعة — أبحاث")
        assert "مجموعه" in result
        assert "ابحاث" in result
        assert "—" not in result


# ── Stop Words Removal (2 tests) ────────────────────────────────────────


class TestStopWordsRemoval:
    def test_remove_prepositions(self, normalizer):
        assert "في" not in normalizer.normalize("شركة في الرياض")

    def test_stop_words_kept_during_indexing(self, indexing_normalizer):
        assert "في" in indexing_normalizer.normalize_for_indexing("شركة في الرياض")


# ── Real Saudi Company Names — BUG-002 (3 tests) ────────────────────────


class TestRealCompanyNames:
    def test_company_with_hamza(self, normalizer):
        assert normalizer.normalize("شركة أرامكو السعودية") == "شركه ارامكو السعوديه"

    def test_company_with_multiple_variants(self, normalizer):
        assert normalizer.normalize("مؤسسة سابك للصناعات الأساسية") == "موسسه سابك للصناعات الاساسيه"

    def test_company_with_wasla_and_madda(self, normalizer):
        assert normalizer.normalize("آفاق المستقبل للتجارة") == "افاق المستقبل للتجاره"


# ── BUG-002: Arabic Text Normalization Fails (3 tests) ──────────────────


class TestBug002:
    """Verify BUG-002 is fixed:

    The issue was that Arabic normalization failed on edge cases:
    - Mixed Indic digits with Arabic text
    - Long tatweel sequences in company names
    - Names with multiple diacritics and special chars

    The enhanced normalizer now handles all these cases correctly.
    """

    def test_bug002_mixed_digits_and_arabic(self, normalizer):
        normalizer.normalize_digits = True
        result = normalizer.normalize("مؤسسة ٢٠٢٤ للتجارة")
        assert result == "موسسه 2024 للتجاره"
        assert "٢" not in result
        assert "2024" in result

    def test_bug002_long_tatweel_company(self, normalizer):
        result = normalizer.normalize(
            "شـــــركة المـــــقاولات الـــــحديثة"
        )
        assert "ـ" not in result
        assert result == "شركه المقاولات الحديثه"

    def test_bug002_diacritics_with_special_chars(self, normalizer):
        result = normalizer.normalize(
            "شَرِكَةُ الأَمَلِ للتِجَارَةِ - مَطَابِخُ أَلْمَانِيَّة"
        )
        assert "َ" not in result
        assert "ِ" not in result
        assert "ُ" not in result
        assert "شركه" in result
        assert "الامل" in result


# ── Edge Cases (3 tests) ────────────────────────────────────────────────


class TestEdgeCases:
    def test_empty_string(self, normalizer):
        assert normalizer.normalize("") == ""

    def test_idempotent(self, normalizer):
        text = "شركة المقاولات الحديثة"
        once = normalizer.normalize(text)
        twice = normalizer.normalize(once)
        assert once == twice

    def test_mixed_arabic_english(self, normalizer):
        result = normalizer.normalize("شركة SAP العربية")
        assert "SAP" in result
        assert "العربيه" in result


# ── Matching Normalizer Configurations (3 tests) ────────────────────────


class TestMatchingNormalizer:
    def test_for_matching_removes_prefixes(self, matching_normalizer):
        result = matching_normalizer.normalize("شركة أرامكو السعودية المحدودة")
        assert "شركة" not in result
        assert "أرامكو" in result or "ارامكو" in result

    def test_for_matching_normalizes_all(self, matching_normalizer):
        result = matching_normalizer.normalize("مؤسسة سابك للصناعات الأساسية - الرياض")
        assert "سابك" in result
        assert "للصناعات" in result
        assert "اساسيه" in result
        assert "الرياض" in result

    def test_for_matching_handles_separators(self, matching_normalizer):
        result = matching_normalizer.normalize("مجموعة — أبحاث السوق")
        assert "أبحاث" in result or "ابحاث" in result


# ── Full Pipeline Integration (3 tests) ─────────────────────────────────


class TestPipelineIntegration:
    def test_indexing_preserves_phrases(self, indexing_normalizer):
        result = indexing_normalizer.normalize_for_indexing("شركة في مدينة الرياض")
        assert "في" in result

    def test_query_removes_stop_words(self, normalizer):
        result = normalizer.normalize_for_query("شركة في الرياض")
        assert "في" not in result

    def test_roundtrip_stability(self, normalizer):
        texts = [
            "شركة المقاولات الحديثة",
            "مؤسسة سابك للصناعات",
            "مجموعة الاتصالات السعودية",
        ]
        for t in texts:
            once = normalizer.normalize(t)
            twice = normalizer.normalize(once)
            assert once == twice, f"Idempotent failed for {t}"
