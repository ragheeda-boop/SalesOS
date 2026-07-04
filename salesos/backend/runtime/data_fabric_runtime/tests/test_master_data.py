"""Tests for City/Region Master and Normalizers."""

from __future__ import annotations

from runtime.data_fabric_runtime.master_data import CityLookup
from runtime.data_fabric_runtime.master_data.normalizers import (
    normalize_arabic_text,
    normalize_city,
    normalize_cr,
)


class TestCityLookup:
    def setup_method(self) -> None:
        self.lookup = CityLookup()

    def test_riyadh_normalization(self):
        assert self.lookup.normalize("الرياض") == "الرياض"
        assert self.lookup.normalize("riyadh") == "الرياض"

    def test_jeddah_normalization(self):
        assert self.lookup.normalize("جدة") == "جدة"
        assert self.lookup.normalize("jeddah") == "جدة"

    def test_unknown_city_passthrough(self):
        assert self.lookup.normalize("قرية نائية") == "قرية نائية"

    def test_none_input(self):
        assert self.lookup.normalize(None) is None

    def test_get_region(self):
        assert self.lookup.get_region("الرياض") == "منطقة الرياض"
        assert self.lookup.get_region("جدة") == "منطقة مكة المكرمة"
        assert self.lookup.get_region("الدمام") == "المنطقة الشرقية"

    def test_all_cities_returns_unique(self):
        cities = self.lookup.all_cities()
        names = [c.canonical_ar for c in cities]
        assert len(names) == len(set(names))
        assert "الرياض" in names
        assert "جدة" in names

    def test_get_info(self):
        info = self.lookup.get_info("الرياض")
        assert info is not None
        assert info.region_ar == "منطقة الرياض"
        assert info.canonical_en == "Riyadh"


class TestNormalizers:
    def test_normalize_cr_removes_spaces(self):
        assert normalize_cr("  1234 5678 90  ") == "1234567890"

    def test_normalize_cr_pads_short(self):
        assert normalize_cr("12345") == "0000012345"

    def test_normalize_cr_truncates_long(self):
        long_cr = "123456789012345"
        assert len(normalize_cr(long_cr)) == 10

    def test_normalize_cr_none(self):
        assert normalize_cr(None) is None

    def test_normalize_cr_non_digit_stripped(self):
        assert normalize_cr("CR-12345-6789") == "0123456789"

    def test_normalize_arabic_unify_alef(self):
        result = normalize_arabic_text("أحمد إبراهيم آدم")
        assert "أ" not in result and "إ" not in result

    def test_normalize_arabic_remove_tatweel(self):
        result = normalize_arabic_text("شركـــة")
        assert "ـ" not in result

    def test_normalize_arabic_teh_to_heh(self):
        result = normalize_arabic_text("شركة")
        assert "ة" not in result
        assert "ه" in result

    def test_normalize_city(self):
        assert normalize_city("الرياض") == "الرياض"
        assert normalize_city("riyadh") == "الرياض"
        assert normalize_city(None) is None
