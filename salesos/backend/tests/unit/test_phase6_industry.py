"""Unit tests for Phase 6 industry normalization module."""

import pytest

from app.modules.master_data.phase6.industry import IndustryResult, normalize_industry


class TestNormalizeIndustry:
    """Test industry normalization to canonical buckets.

    Actual behavior:
    - Returns UPPERCASE bucket labels (e.g., "CONSTRUCTION", "ICT_TECHNOLOGY")
    - Code is the same as the bucket label
    - Arabic keywords mapped to English bucket labels (exact keyword match)
    - Multi-value: first match wins
    - Empty/None returns empty strings, not None
    """

    def test_construction_arabic(self):
        # Use keyword that exists in mapping: "مقاولات"
        res = normalize_industry("مقاولات")
        assert res.normalized_industry == "CONSTRUCTION"
        assert res.industry_code == "CONSTRUCTION"
        assert res.normalization_method == "MAPPED"

    def test_construction_english(self):
        res = normalize_industry("Construction")
        assert res.normalized_industry == "CONSTRUCTION"
        assert res.industry_code == "CONSTRUCTION"

    def test_manufacturing(self):
        # "industrial" is in MANUFACTURING mapping
        res = normalize_industry("industrial")
        assert res.normalized_industry == "MANUFACTURING"
        assert res.industry_code == "MANUFACTURING"

    def test_healthcare(self):
        res = normalize_industry("Healthcare")
        assert res.normalized_industry == "HEALTHCARE"
        assert res.industry_code == "HEALTHCARE"

    def test_financial_services(self):
        res = normalize_industry("Financial Services")
        assert res.normalized_industry == "FINANCIAL_SERVICES"
        assert res.industry_code == "FINANCIAL_SERVICES"

    def test_technology(self):
        res = normalize_industry("Technology")
        assert res.normalized_industry == "ICT_TECHNOLOGY"
        assert res.industry_code == "ICT_TECHNOLOGY"

    def test_multi_value_semicolon(self):
        # First match wins
        res = normalize_industry("مقاولات; industrial")
        assert res.normalized_industry == "CONSTRUCTION"
        assert res.industry_code == "CONSTRUCTION"
        assert res.normalization_method == "MAPPED"

    def test_multi_value_pipe(self):
        res = normalize_industry("Construction | Technology")
        assert res.normalized_industry == "CONSTRUCTION"
        assert res.industry_code == "CONSTRUCTION"

    def test_unknown_industry(self):
        res = normalize_industry("Unknown Sector XYZ")
        # Falls back to cleaned raw
        assert res.normalized_industry == "unknown sector xyz"
        assert res.industry_code is None
        assert res.normalization_method == "CLEANED"

    def test_empty_input(self):
        res = normalize_industry("")
        assert res.normalized_industry == ""
        assert res.industry_code is None
        assert res.normalization_method == "CLEANED"

    def test_none_input(self):
        res = normalize_industry(None)
        assert res.normalized_industry == ""
        assert res.industry_code is None
        assert res.normalization_method == "CLEANED"

    def test_case_insensitive(self):
        res = normalize_industry("CONSTRUCTION")
        assert res.normalized_industry == "CONSTRUCTION"

    def test_whitespace_handling(self):
        res = normalize_industry("  Construction  ")
        assert res.normalized_industry == "CONSTRUCTION"

    def test_arabic_variants(self):
        for variant in ["مقاولات", "بناء", "تشييد"]:
            res = normalize_industry(variant)
            assert res.normalized_industry == "CONSTRUCTION"
            assert res.industry_code == "CONSTRUCTION"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])