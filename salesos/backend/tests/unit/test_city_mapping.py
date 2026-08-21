"""Tests for entity_resolution.city_mapping — pure normalization logic, no DB."""

from __future__ import annotations

import pytest

from app.modules.entity_resolution.city_mapping import CityRegionNormalizer


@pytest.fixture()
def n() -> CityRegionNormalizer:
    return CityRegionNormalizer()


# ── normalize_city ───────────────────────────────────────────────────────────


class TestNormalizeCityArabicVariants:
    """All Arabic variants map to canonical Arabic name."""

    @pytest.mark.parametrize(
        "variant, expected",
        [
            ("الرياض", "الرياض"),
            ("رياض", "الرياض"),
            ("الرياض منطقة", "الرياض"),
            ("منطقة الرياض", "الرياض"),
            ("جدة", "جدة"),
            ("جده", "جدة"),
            ("جدا", "جدة"),
            ("الدمام", "الدمام"),
            ("دمام", "الدمام"),
            ("مكة المكرمة", "مكة المكرمة"),
            ("مكه المكرمه", "مكة المكرمة"),
            ("مكة", "مكة المكرمة"),
            ("مكه", "مكة المكرمة"),
            ("المدينة المنورة", "المدينة المنورة"),
            ("المدينه المنوره", "المدينة المنورة"),
            ("المدينة", "المدينة المنورة"),
            ("المدينه", "المدينة المنورة"),
            ("طيبة", "المدينة المنورة"),
            ("الخبر", "الخبر"),
            ("خبر", "الخبر"),
            ("الظهران", "الظهران"),
            ("ظهران", "الظهران"),
            ("الجبيل", "الجبيل"),
            ("جبيل", "الجبيل"),
            ("مدينة الجبيل الصناعية", "الجبيل"),
            ("ينبع", "ينبع"),
            ("ينبع الصناعية", "ينبع"),
            ("الطائف", "الطائف"),
            ("طائف", "الطائف"),
            ("تبوك", "تبوك"),
            ("بريدة", "بريدة"),
            ("بريده", "بريدة"),
            ("أبها", "أبها"),
            ("ابها", "أبها"),
            ("حائل", "حائل"),
            ("جازان", "جازان"),
            ("جيزان", "جازان"),
            ("نجران", "نجران"),
            ("الأحساء", "الأحساء"),
            ("الاحساء", "الأحساء"),
            ("حسا", "الأحساء"),
            ("الهفوف", "الأحساء"),
            ("الخرج", "الخرج"),
            ("خرج", "الخرج"),
            ("سيح", "الخرج"),
            ("القصيم", "القصيم"),
            ("منطقة القصيم", "القصيم"),
            ("الحدود الشمالية", "الحدود الشمالية"),
            ("الحدود الشماليه", "الحدود الشمالية"),
            ("عرعر", "الحدود الشمالية"),
            ("الجوف", "الجوف"),
            ("سكاكا", "الجوف"),
            ("الباحة", "الباحة"),
            ("الباحه", "الباحة"),
            ("عسير", "عسير"),
            ("منطقة عسير", "عسير"),
            ("المنطقة الشرقية", "المنطقة الشرقية"),
            ("المنطقه الشرقيه", "المنطقة الشرقية"),
            ("الشرقية", "المنطقة الشرقية"),
            ("الشرقيه", "المنطقة الشرقية"),
        ],
    )
    def test_arabic_variants(self, n: CityRegionNormalizer, variant: str, expected: str):
        assert n.normalize_city(variant) == expected


class TestNormalizeCityEnglishVariants:
    """English variants also map to canonical Arabic name."""

    @pytest.mark.parametrize(
        "variant, expected",
        [
            ("riyadh", "الرياض"),
            ("Riyadh", "الرياض"),
            ("riyaadh", "الرياض"),
            ("ar riyad", "الرياض"),
            ("ar-riyad", "الرياض"),
            ("jeddah", "جدة"),
            ("Jeddah", "جدة"),
            ("jedda", "جدة"),
            ("jiddah", "جدة"),
            ("jeddah city", "جدة"),
            ("dammam", "الدمام"),
            ("Damam", "الدمام"),
            ("ad dammam", "الدمام"),
            ("makkah", "مكة المكرمة"),
            ("Makkah", "مكة المكرمة"),
            ("mecca", "مكة المكرمة"),
            ("makka", "مكة المكرمة"),
            ("makkah al mukarramah", "مكة المكرمة"),
            ("madina", "المدينة المنورة"),
            ("Medina", "المدينة المنورة"),
            ("al madinah", "المدينة المنورة"),
            ("khobar", "الخبر"),
            ("al khobar", "الخبر"),
            ("al khubar", "الخبر"),
            ("dhahran", "الظهران"),
            ("zahran", "الظهران"),
            ("jubail", "الجبيل"),
            ("al jubail", "الجبيل"),
            ("jubail industrial city", "الجبيل"),
            ("yanbu", "ينبع"),
            ("yanbu industrial", "ينبع"),
            ("taif", "الطائف"),
            ("at taif", "الطائف"),
            ("tabuk", "تبوك"),
            ("tabouk", "تبوك"),
            ("buraidah", "بريدة"),
            ("buraydah", "بريدة"),
            ("abha", "أبها"),
            ("hail", "حائل"),
            ("ha'il", "حائل"),
            ("jazan", "جازان"),
            ("jizan", "جازان"),
            ("gizan", "جازان"),
            ("najran", "نجران"),
            ("ahsa", "الأحساء"),
            ("al ahsa", "الأحساء"),
            ("hassa", "الأحساء"),
            ("hofuf", "الأحساء"),
            ("kharj", "الخرج"),
            ("al kharj", "الخرج"),
            ("qassim", "القصيم"),
            ("al qassim", "القصيم"),
            ("gassim", "القصيم"),
            ("arar", "الحدود الشمالية"),
            ("jouf", "الجوف"),
            ("al jouf", "الجوف"),
            ("baha", "الباحة"),
            ("al baha", "الباحة"),
            ("asir", "عسير"),
            ("aseer", "عسير"),
            ("eastern province", "المنطقة الشرقية"),
            ("sharqiya", "المنطقة الشرقية"),
            ("ash sharqiyah", "المنطقة الشرقية"),
        ],
    )
    def test_english_variants(self, n: CityRegionNormalizer, variant: str, expected: str):
        assert n.normalize_city(variant) == expected


class TestNormalizeCityEdgeCases:
    def test_empty_string(self, n: CityRegionNormalizer):
        assert n.normalize_city("") == ""

    def test_whitespace_only(self, n: CityRegionNormalizer):
        assert n.normalize_city("   ") == ""

    def test_unknown_city_returns_original(self, n: CityRegionNormalizer):
        assert n.normalize_city("Luton") == "Luton"

    def test_unknown_arabic_returns_original(self, n: CityRegionNormalizer):
        assert n.normalize_city("บางสิ่ง") == "บางสิ่ง"

    def test_none_input(self, n: CityRegionNormalizer):
        assert n.normalize_city(None) == ""

    def test_strip_whitespace(self, n: CityRegionNormalizer):
        assert n.normalize_city("  رياض  ") == "الرياض"


# ── to_english ───────────────────────────────────────────────────────────────


class TestToEnglish:
    def test_riyadh(self, n: CityRegionNormalizer):
        assert n.to_english("الرياض") == "Riyadh"

    def test_jeddah(self, n: CityRegionNormalizer):
        assert n.to_english("جدة") == "Jeddah"

    def test_makkah(self, n: CityRegionNormalizer):
        assert n.to_english("مكة المكرمة") == "Makkah"

    def test_unknown_returns_original(self, n: CityRegionNormalizer):
        assert n.to_english("غير معروف") == "غير معروف"

    def test_empty(self, n: CityRegionNormalizer):
        assert n.to_english("") == ""

    def test_all_24_cities_have_english(self, n: CityRegionNormalizer):
        """Every canonical Arabic city in the map has an English translation."""
        arabic_cities = set(n._CITY_TO_ENGLISH.keys())
        for city in arabic_cities:
            en = n.to_english(city)
            assert en != city, f"No English translation for {city}"


# ── normalize_and_english ────────────────────────────────────────────────────


class TestNormalizeAndEnglish:
    def test_variant_input(self, n: CityRegionNormalizer):
        ar, en = n.normalize_and_english("jeddah")
        assert ar == "جدة"
        assert en == "Jeddah"

    def test_canonical_input(self, n: CityRegionNormalizer):
        ar, en = n.normalize_and_english("الرياض")
        assert ar == "الرياض"
        assert en == "Riyadh"

    def test_unknown(self, n: CityRegionNormalizer):
        ar, en = n.normalize_and_english("Atlantis")
        assert ar == "Atlantis"
        assert en == "Atlantis"


# ── normalize_region ─────────────────────────────────────────────────────────


class TestNormalizeRegion:
    def test_delegates_to_normalize_city(self, n: CityRegionNormalizer):
        assert n.normalize_region("المنطقة الشرقية") == "المنطقة الشرقية"
        assert n.normalize_region("eastern province") == "المنطقة الشرقية"


# ── default() factory ────────────────────────────────────────────────────────


class TestDefault:
    def test_returns_instance(self):
        n = CityRegionNormalizer.default()
        assert isinstance(n, CityRegionNormalizer)
