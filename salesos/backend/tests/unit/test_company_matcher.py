"""Tests for CompanyNameMatcher — fuzzy matching of Arabic company names.

Covers: Jaro-Winkler distance, exact matching, prefix normalization,
suffix normalization, threshold behavior, head word matching, and
real-world Saudi company name matching scenarios.
"""

from __future__ import annotations

import pytest

from domains.search.normalization.company_matcher import (
    CompanyMatchResult,
    CompanyNameMatcher,
    _jaro_distance,
    _jaro_winkler_distance,
    _extract_head_word,
)


# ── Fixtures ────────────────────────────────────────────────────────────


@pytest.fixture
def matcher() -> CompanyNameMatcher:
    return CompanyNameMatcher.default()


# ── Jaro-Winkler Distance (3 tests) ─────────────────────────────────────


class TestJaroWinkler:
    def test_exact_match(self):
        assert _jaro_winkler_distance("أرامكو", "أرامكو") == 1.0

    def test_no_match(self):
        assert _jaro_winkler_distance("abc", "xyz") < 0.3

    def test_partial_match(self):
        score = _jaro_winkler_distance("أرامكو", "أرامكو السعودية")
        assert 0.5 < score < 1.0


# ── Jaro Distance (2 tests) ────────────────────────────────────────────


class TestJaro:
    def test_empty_first(self):
        assert _jaro_distance("", "test") == 0.0

    def test_empty_second(self):
        assert _jaro_distance("test", "") == 0.0


# ── Head Word Extraction (2 tests) ──────────────────────────────────────


class TestHeadWord:
    def test_extract_from_company(self):
        assert _extract_head_word("شركة أرامكو السعودية المحدودة") == "أرامكو"

    def test_extract_short_name(self):
        assert _extract_head_word("مؤسسة سابك") == "سابك"


# ── Basic Matching (3 tests) ────────────────────────────────────────────


class TestBasicMatching:
    def test_exact_match_after_normalization(self, matcher):
        result = matcher.match("شركة أرامكو السعودية", "شركة أرامكو السعودية")
        assert result.is_match
        assert result.score == 1.0
        assert result.match_type == "exact"

    def test_exact_match_with_teh_marbuta(self, matcher):
        result = matcher.match("شركة", "شركه")
        assert result.is_match
        assert result.score == 1.0

    def test_fuzzy_match_similar_names(self, matcher):
        result = matcher.match("أرامكو السعودية", "ارامكو السعوديه")
        assert result.is_match
        assert result.score >= 0.85


# ── Threshold & Scoring (3 tests) ──────────────────────────────────────


class TestThreshold:
    def test_above_threshold(self):
        matcher = CompanyNameMatcher(threshold=0.7)
        result = matcher.match("شركة أرامكو", "أرامكو السعودية")
        assert result.is_match

    def test_below_threshold(self):
        matcher = CompanyNameMatcher(threshold=0.95)
        # Mismatched names should still be below high threshold
        result = matcher.match("شركة تطوير التعليم", "مؤسسة سابك")
        assert not result.is_match
        assert result.score < 0.95

    def test_custom_threshold_constructor(self):
        matcher = CompanyNameMatcher(threshold=0.5)
        assert matcher.threshold == 0.5


# ── Company Type Prefix Handling (3 tests) ──────────────────────────────


class TestCompanyPrefixHandling:
    def test_sharika_vs_muasasa(self, matcher):
        result = matcher.match_with_head_word("شركة سابك", "مؤسسة سابك")
        assert result.is_match, f"SABIC match should be >= 0.85, got {result.score}"

    def test_group_prefix(self, matcher):
        result = matcher.match("مجموعة سامبا المالية", "سامبا")
        assert result.is_match

    def test_prefix_removed_correctly(self, matcher):
        result = matcher.match("شركة أرامكو", "أرامكو")
        assert result.is_match


# ── Stop Words & Legal Suffixes (3 tests) ───────────────────────────────


class TestStopWords:
    def test_ltd_suffix_variations(self, matcher):
        # Both normalize to same core after prefix/suffix removal
        result = matcher.match_with_head_word(
            "شركة أرامكو المحدودة",
            "ارامكو ذات مسئوليه محدوده",
        )
        assert result.is_match

    def test_saudi_suffix_handling(self, matcher):
        result = matcher.match(
            "الاتصالات السعودية",
            "شركة الاتصالات السعوديه",
        )
        assert result.is_match

    def test_suffix_does_not_hurt_good_match(self, matcher):
        result = matcher.match(
            "مؤسسة سابك للصناعات الأساسية",
            "سابك للصناعات الاساسيه",
        )
        assert result.is_match


# ── Persian Character Handling (2 tests) ────────────────────────────────


class TestPersianChars:
    def test_persian_yeh_match(self, matcher):
        result = matcher.match("ایران خودرو", "ايران خودرو")
        assert result.is_match

    def test_persian_kaf_match(self, matcher):
        result = matcher.match("شرکت دانش بنیان", "شركة دانش بنيان")
        assert result.is_match


# ── Edge Cases (3 tests) ────────────────────────────────────────────────


class TestMatcherEdgeCases:
    def test_empty_first_name(self, matcher):
        result = matcher.match("", "شركة")
        assert not result.is_match
        assert result.match_type == "empty"

    def test_empty_second_name(self, matcher):
        result = matcher.match("شركة", "")
        assert not result.is_match

    def test_both_empty(self, matcher):
        result = matcher.match("", "")
        assert not result.is_match


# ── Multiple Candidates (2 tests) ──────────────────────────────────────


class TestMultipleCandidates:
    def test_compare_multiple_returns_sorted(self, matcher):
        results = matcher.compare_multiple(
            "أرامكو السعودية",
            [
                "شركة سابك",
                "أرامكو السعودية المحدودة",
                "الاتصالات السعودية",
            ],
        )
        assert len(results) == 3
        assert results[0].score >= results[1].score

    def test_best_match_first(self, matcher):
        results = matcher.compare_multiple(
            "أرامكو",
            ["شركة سابك", "أرامكو السعودية", "الاتصالات"],
        )
        assert results[0].score >= results[1].score


# ── Head Word Matching (2 tests) ────────────────────────────────────────


class TestHeadWordMatching:
    def test_head_word_fallback(self, matcher):
        # Both have "أرامكو" as head word (after prefix removal), should boost score
        result = matcher.match_with_head_word(
            "شركة أرامكو السعودية",
            "مؤسسة ارامكو",
        )
        assert result.score >= 0.7

    def test_head_word_precision(self, matcher):
        result = matcher.match_with_head_word(
            "شركة أرامكو",
            "مؤسسة سابك",
        )
        # Different head words (أرامكو vs سابك), no boost
        assert result.score < 0.7


# ── Result Data Class (2 tests) ─────────────────────────────────────────


class TestResultData:
    def test_to_dict_returns_fields(self, matcher):
        result = matcher.match("شركة", "شركه")
        d = result.to_dict()
        assert "score" in d
        assert "is_match" in d
        assert "reasons" in d

    def test_reasons_populated(self, matcher):
        result = matcher.match("أرامكو", "ارامكو")
        assert result.reasons is not None
        assert len(result.reasons) >= 1
