"""Tests for ArabicSearchNormalizer — comprehensive Arabic text normalization.

Covers: Alef, Yeh, Teh Marbuta, Tatweel, diacritics, stop words, and
real-world Saudi company name normalization.
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


# ── Alef Normalization ─────────────────────────────────────────────────


class TestAlefNormalization:
    """Test normalization of Alef variants (أ, إ, آ, ٱ → ا)."""

    def test_alef_with_hamza_above(self, normalizer):
        assert normalizer.normalize("أحمد") == "احمد"

    def test_alef_with_hamza_below(self, normalizer):
        assert normalizer.normalize("إبراهيم") == "ابراهيم"

    def test_alef_madda(self, normalizer):
        assert normalizer.normalize("آفاق") == "افاق"

    def test_alef_wasla(self, normalizer):
        assert normalizer.normalize("ٱسم") == "اسم"

    def test_all_alef_variants_in_one_string(self, normalizer):
        result = normalizer.normalize("أساس إبراهيم آفاق")
        assert result == "اساس ابراهيم افاق"

    def test_check(self, normalizer):
        result = normalizer.normalize("أساس إبراهيم آفاق")
        assert result == "اساس ابراهيم افاق"


# ── Yeh Normalization ──────────────────────────────────────────────────


class TestYehNormalization:
    """Test normalization of Yeh variants (ى, ئ, ی → ي)."""

    def test_alef_maksura_to_yeh(self, normalizer):
        assert normalizer.normalize("موسى") == "موسي"

    def test_hamza_on_yeh_to_yeh(self, normalizer):
        assert normalizer.normalize("لاجئ") == "لاجي"

    def test_alef_maksura_at_end(self, normalizer):
        assert normalizer.normalize("مستشفى") == "مستشفي"

    def test_persian_yeh(self, normalizer):
        assert normalizer.normalize("ایران") == "ايران"

    def test_yeh_stays_yeh(self, normalizer):
        assert normalizer.normalize("جميل") == "جميل"


# ── Teh Marbuta Normalization ──────────────────────────────────────────


class TestTehMarbutaNormalization:
    """Test normalization of Teh Marbuta (ة → ه)."""

    def test_teh_marbuta_to_heh(self, normalizer):
        assert normalizer.normalize("شركة") == "شركه"

    def test_teh_marbuta_mid_word(self, normalizer):
        assert normalizer.normalize("مؤسسة") == "موسسه"

    def test_teh_marbuta_at_end(self, normalizer):
        assert normalizer.normalize("مدينة") == "مدينه"

    def test_multiple_teh_marbuta(self, normalizer):
        assert normalizer.normalize("إدارة المشاريع الهندسية") == "اداره المشاريع الهندسيه"


# ── Tatweel / Kashida ──────────────────────────────────────────────────


class TestTatweelRemoval:
    """Test removal of Tatweel (kashida) characters."""

    def test_remove_tatweel(self, normalizer):
        text = "الـــــرياض"
        result = normalizer.normalize(text)
        assert "ـ" not in result
        assert result == "الرياض"

    def test_tatweel_with_diacritics(self, normalizer):
        text = "بِــــــــــــــسْمِ"
        result = normalizer.normalize(text)
        assert "ـ" not in result
        assert result == "بسم"


# ── Diacritics Removal ─────────────────────────────────────────────────


class TestDiacriticsRemoval:
    """Test removal of Arabic diacritics (tashkeel)."""

    def test_remove_fatha(self, normalizer):
        assert normalizer.normalize("بَسْمِ") == "بسم"

    def test_remove_damma(self, normalizer):
        assert normalizer.normalize("مُحَمَّد") == "محمد"

    def test_remove_shadda(self, normalizer):
        assert normalizer.normalize("اللّهُ") == "الله"

    def test_remove_sukun(self, normalizer):
        assert normalizer.normalize("مِنْ") == "من"

    def test_full_tashkeel_sentence(self, normalizer):
        text = "بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ"
        result = normalizer.normalize(text)
        assert "َ" not in result
        assert "ِ" not in result
        assert "ُ" not in result
        assert "ّ" not in result
        assert "ْ" not in result


# ── Stop Words Removal ─────────────────────────────────────────────────


class TestStopWordsRemoval:
    """Test removal of Arabic stop words."""

    def test_remove_prepositions(self, normalizer):
        assert "في" not in normalizer.normalize("شركة في الرياض")

    def test_remove_conjunctions(self, normalizer):
        result = normalizer.normalize("شركة و مؤسسة")
        import re
        standalone_waw = re.search(r'(?<!\w)و(?!\w)', result)
        assert standalone_waw is None, f"و still present as standalone word in {result}"

    def test_remove_demonstratives(self, normalizer):
        result = normalizer.normalize("هذه الشركة")
        assert "هذه" not in result

    def test_remove_pronouns(self, normalizer):
        result = normalizer.normalize("هو المدير")
        assert "هو" not in result

    def test_stop_words_not_removed_during_indexing(self, indexing_normalizer):
        text = "شركة في الرياض"
        result = indexing_normalizer.normalize_for_indexing(text)
        assert "في" in result


# ── Real Saudi Company Names ────────────────────────────────────────────


class TestRealCompanyNames:
    """Test normalization of real Saudi company names."""

    def test_company_with_hamza(self, normalizer):
        result = normalizer.normalize("شركة أرامكو السعودية")
        assert result == "شركه ارامكو السعوديه"

    def test_company_with_teh_marbuta(self, normalizer):
        result = normalizer.normalize("شركة الكهرباء السعودية")
        assert result == "شركه الكهرباء السعوديه"

    def test_company_with_multiple_variants(self, normalizer):
        result = normalizer.normalize("مؤسسة سابك للصناعات الأساسية")
        assert result == "موسسه سابك للصناعات الاساسيه"

    def test_engineering_company(self, normalizer):
        result = normalizer.normalize("مكتب استشارات هندسية")
        assert result == "مكتب استشارات هندسيه"

    def test_contracting_company(self, indexing_normalizer):
        result = indexing_normalizer.normalize("شركة مقاولات وإنشاءات")
        assert result == "شركه مقاولات وانشاءات"

    def test_municipality_company(self, normalizer):
        result = normalizer.normalize("أمانة منطقة الرياض")
        assert result == "امانه منطقه الرياض"

    def test_company_with_wasla_and_madda(self, normalizer):
        result = normalizer.normalize("آفاق المستقبل للتجارة")
        assert result == "افاق المستقبل للتجاره"

    def test_defense_company(self, normalizer):
        result = normalizer.normalize("الشركة السعودية للصناعات العسكرية")
        assert result == "الشركه السعوديه للصناعات العسكريه"


# ── Query vs Indexing Normalization ────────────────────────────────────


class TestQueryVsIndexing:
    """Test the difference between query and indexing normalization."""

    def test_query_normalizer_lowercases(self, normalizer):
        saved = normalizer.lower_case
        normalizer.lower_case = True
        result = normalizer.normalize("Saudi Aramco")
        assert result == "saudi aramco"
        normalizer.lower_case = saved

    def test_query_removes_stop_words(self, normalizer):
        result = normalizer.normalize_for_query("شركة في مدينة الرياض")
        assert "في" not in result

    def test_indexing_preserves_all_words(self, indexing_normalizer):
        result = indexing_normalizer.normalize_for_indexing("شركة في مدينة الرياض")
        assert "في" in result

    def test_matching_is_aggressive(self, matching_normalizer):
        result = matching_normalizer.normalize_for_query("شركة مقاولات وإنشاءات")
        import re
        standalone_waw = re.search(r'(?<!\w)و(?!\w)', result)
        assert standalone_waw is None, f"و still present as standalone word in {result}"


# ── Edge Cases ─────────────────────────────────────────────────────────


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_string(self, normalizer):
        assert normalizer.normalize("") == ""

    def test_whitespace_only(self, normalizer):
        assert normalizer.normalize("   ") == ""

    def test_no_arabic_text(self, normalizer):
        assert normalizer.normalize("Hello World") == "Hello World"

    def test_mixed_arabic_english(self, normalizer):
        result = normalizer.normalize("شركة SAP العربية")
        assert "SAP" in result
        assert "العربيه" in result

    def test_numbers_preserved(self, normalizer):
        result = normalizer.normalize("شركة رقم 12345")
        assert "12345" in result

    def test_idempotent(self, normalizer):
        text = "شركة المقاولات الحديثة"
        once = normalizer.normalize(text)
        twice = normalizer.normalize(once)
        assert once == twice

    def test_long_complex_text(self, normalizer):
        text = (
            "شَرِكَةُ الــــمُقَاوَلاَتِ وَالإِنْشَاءَاتِ فِي مِنْطَقَةِ الرِيَاضِ "
            "لِلتِجَارَةِ وَالصِنَاعَةِ ذَاتِ مَسْؤولِيَةٍ مَحْدُودَةٍ"
        )
        result = normalizer.normalize(text)
        assert "ـ" not in result
        assert "َ" not in result
        assert "ِ" not in result
        assert "ُ" not in result
        assert "في" not in result.split()
        assert "و" not in result.split()
