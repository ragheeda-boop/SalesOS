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


class TestNormalizeCity:
    def test_none_and_empty(self):
        assert normalize_city(None) is None
        assert normalize_city("") is None

    def test_known_city(self):
        assert normalize_city("الرياض") is not None
