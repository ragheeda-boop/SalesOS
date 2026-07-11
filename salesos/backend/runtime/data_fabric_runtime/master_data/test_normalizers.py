"""Tests for Arabic text, CR, and city normalization."""
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
        assert normalize_arabic_text("آل") == "ال"
        assert normalize_arabic_text("ٱسم") == "اسم"

    def test_alef_maqsura_to_yaa(self):
        assert normalize_arabic_text("مستشفى") == "مستشفي"
        assert normalize_arabic_text("محامى") == "محامي"

    def test_teh_marbuta_to_heh(self):
        assert normalize_arabic_text("شركة") == "شركه"
        assert normalize_arabic_text("مؤسسة") == "مؤسسه"

    def test_tashkeel_removal(self):
        assert normalize_arabic_text("شَرِكَة") == "شركه"
        assert normalize_arabic_text("الْمُهَنْدِس") == "المهندس"

    def test_tatweel_removal(self):
        assert normalize_arabic_text("الـريـاض") == "الرياض"

    def test_yeh_hamza_to_yaa(self):
        assert normalize_arabic_text("مسائل") == "مسايل"

    def test_unicode_normalization(self):
        result = normalize_arabic_text("شَرِكَةُ الأَمَل")
        assert "شركه الامل" in result

    def test_whitespace_normalization(self):
        result = normalize_arabic_text("   شركة    الأمل   ")
        assert result == "شركه الامل"


class TestNormalizeCr:
    def test_none_and_empty(self):
        assert normalize_cr(None) is None
        assert normalize_cr("") is None

    def test_ascii_cr(self):
        assert normalize_cr("1234567890") == "1234567890"

    def test_short_cr_pads_to_10(self):
        assert normalize_cr("123") == "0000000123"

    def test_arabic_indic_digits(self):
        result = normalize_cr("١٢٣٤٥٦٧٨٩٠")
        assert result == "1234567890"

    def test_extended_arabic_digits(self):
        result = normalize_cr("۰۱۲۳۴۵۶۷۸۹")
        assert result == "0123456789"

    def test_truncates_long_cr(self):
        assert normalize_cr("123456789012345") == "1234567890"

    def test_strips_non_digits(self):
        assert normalize_cr("CR-123-456") == "0000123456"

    def test_mixed_arabic_indic_and_ascii(self):
        result = normalize_cr("١23٤٥6")
        assert result == "0000123456"


class TestNormalizeCity:
    def test_none_and_empty(self):
        assert normalize_city(None) is None
        assert normalize_city("") is None

    def test_known_city_returns_canonical(self):
        result = normalize_city("الرياض")
        assert result is not None

    def test_city_with_tatweel_is_normalized(self):
        result = normalize_city("الـريـاض")
        assert result == "الرياض"
