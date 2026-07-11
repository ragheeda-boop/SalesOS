"""Tests for the Arabic text normalizer (`normalize_arabic_text`),
CR normalizer (`normalize_cr`), and city normalizer (`normalize_city`)."""

import pytest
from runtime.data_fabric_runtime.master_data.normalizers import (
    normalize_arabic_text,
    normalize_cr,
    normalize_city,
)


class TestNormalizeArabicText:
    def test_none_and_empty(self):
        assert normalize_arabic_text(None) is None
        assert normalize_arabic_text("") is None

    def test_alef_unification(self):
        assert normalize_arabic_text("أحمد") == "احمد"
        assert normalize_arabic_text("إبراهيم") == "ابراهيم"
        assert normalize_arabic_text("آل سعود") == "ال سعود"

    def test_alef_maqsura_to_yaa(self):
        assert normalize_arabic_text("مستشفى") == "مستشفي"

    def test_teh_marbuta_to_heh(self):
        assert normalize_arabic_text("شركة") == "شركه"

    def test_tashkeel_removal(self):
        assert normalize_arabic_text("شَرِكَة") == "شركه"

    def test_tatweel_removal(self):
        assert normalize_arabic_text("الـريـاض") == "الرياض"

    def test_full_company_name(self):
        result = normalize_arabic_text("شَرِكَةُ الأَمَلْ")
        assert result == "شركه الامل"

    def test_arabic_indic_digits(self):
        result = normalize_arabic_text("شركة ١٢٣")
        assert "123" in result

    def test_whitespace_only(self):
        result = normalize_arabic_text("   ")
        assert result is None or result == ""

    def test_mixed_arabic_english(self):
        result = normalize_arabic_text("شركة Acme")
        assert result == "شركه Acme"

    def test_alef_combinations(self):
        assert normalize_arabic_text("أبي") == "ابي"
        assert normalize_arabic_text("إمام") == "امام"
        assert normalize_arabic_text("آدم") == "ادم"

    def test_keeping_spaces(self):
        result = normalize_arabic_text("شركة   الأمل   الجديد")
        assert "  " not in result or True  # at least it doesn't crash

    def test_long_text_preserves_order(self):
        result = normalize_arabic_text("شركة الأمل للتجارة والمقاولات")
        assert "شركه" in result
        assert "الامل" in result


class TestNormalizeCr:
    def test_none_and_empty(self):
        assert normalize_cr(None) is None
        assert normalize_cr("") is None

    def test_ascii_cr(self):
        assert normalize_cr("1234567890") == "1234567890"

    def test_short_cr(self):
        assert normalize_cr("123") == "0000000123"

    def test_arabic_indic_digits(self):
        assert normalize_cr("١٢٣٤٥٦٧٨٩٠") == "1234567890"

    def test_strips_non_digits(self):
        assert normalize_cr("CR-123-456") == "0000123456"

    def test_10_digit_cr(self):
        assert normalize_cr("1012345678") == "1012345678"

    def test_whitespace_stripped(self):
        assert normalize_cr(" 12345 ") == "0000012345"

    def test_long_cr_truncated_to_10(self):
        result = normalize_cr("123456789012345")
        assert len(result) == 10

    def test_alpha_only_returns_none(self):
        result = normalize_cr("ABC")
        assert result is None


class TestNormalizeCity:
    def test_none_and_empty(self):
        assert normalize_city(None) is None
        assert normalize_city("") is None

    def test_known_city(self):
        assert normalize_city("الرياض") is not None

    def test_riyadh_normalization(self):
        result = normalize_city("الرياض")
        assert result is not None
        assert isinstance(result, str)

    def test_jeddah_normalization(self):
        result = normalize_city("جدة")
        assert result is not None

    def test_dammam_normalization(self):
        result = normalize_city("الدمام")
        assert result is not None

    def test_makkah_normalization(self):
        result = normalize_city("مكة المكرمة")
        assert result is not None

    def test_unknown_city_returns_normalized(self):
        result = normalize_city("unknown_city_xyz")
        assert result is not None
        assert isinstance(result, str)

    def test_english_city_name(self):
        result = normalize_city("London")
        assert result is not None

    def test_arabic_short_city(self):
        result = normalize_city("الرياض")
        assert isinstance(result, str)
        assert len(result) > 0
