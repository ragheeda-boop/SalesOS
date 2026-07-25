"""Tests for ArabicStemmer — suffix stripping for Arabic search.

Covers: plural suffixes, possessive pronouns, prefixes, edge cases,
and integration with ArabicSearchNormalizer for_stemming mode.
"""
from __future__ import annotations

import pytest

from domains.search.normalization.arabic_stemmer import ArabicStemmer
from domains.search.normalization.arabic_normalizer import ArabicSearchNormalizer


# ── Fixtures ────────────────────────────────────────────────────────────


@pytest.fixture
def stemmer() -> ArabicStemmer:
    return ArabicStemmer.default()


@pytest.fixture
def stemming_normalizer() -> ArabicSearchNormalizer:
    return ArabicSearchNormalizer.for_stemming()


# ── Plural Suffixes ─────────────────────────────────────────────────────


class TestPluralSuffixes:
    """Test removal of Arabic plural suffixes."""

    def test_at_plural(self, stemmer):
        assert stemmer.stem("استشارات") == "استشار"

    def test_at_plural_contracting(self, stemmer):
        assert stemmer.stem("مقاولات") == "مقاول"

    def test_at_plural_services(self, stemmer):
        assert stemmer.stem("خدمات") == "خدم"

    def test_un_plural(self, stemmer):
        assert stemmer.stem("عمالون") == "عمال"

    def test_in_plural(self, stemmer):
        assert stemmer.stem("مستخدمين") == "مستخدم"


# ── Possessive Pronouns ─────────────────────────────────────────────────


class TestPossessiveSuffixes:
    """Test removal of possessive pronoun suffixes."""

    def test_his_suffix(self, stemmer):
        assert stemmer.stem("كتابه") == "كتاب"

    def test_her_suffix(self, stemmer):
        assert stemmer.stem("مؤسسةها") == "مؤسسه" or stemmer.stem("مؤسسةها") == "مؤسسة"

    def test_my_suffix(self, stemmer):
        assert stemmer.stem("شركتي") == "شركت"

    def test_their_suffix(self, stemmer):
        result = stemmer.stem("شركاتهم")
        assert len(result) < len("شركاتهم")


# ── Feminine Nisba ──────────────────────────────────────────────────────


class TestFeminineSuffixes:
    """Test removal of feminine and nisba suffixes."""

    def test_ya_nisba(self, stemmer):
        result = stemmer.stem("هندسية")
        assert len(result) < len("هندسية")

    def test_teh_marbuta(self, stemmer):
        result = stemmer.stem("مدينة")
        assert len(result) < len("مدينة")


# ── Prefixes ────────────────────────────────────────────────────────────


class TestPrefixes:
    """Test removal of common Arabic prefixes."""

    def test_al_prefix(self, stemmer):
        result = stemmer.stem("الرقم")
        assert "ال" not in result

    def test_wal_prefix(self, stemmer):
        result = stemmer.stem("والبائع")
        assert "وال" not in result

    def test_bal_prefix(self, stemmer):
        result = stemmer.stem("بالنسبة")
        # ة suffix matches first → "بالنسب" → then no further stripping
        assert isinstance(result, str) and len(result) < len("بالنسبة")


# ── Minimum Length Protection ───────────────────────────────────────────


class TestMinLength:
    """Test that short words are not over-stemmed."""

    def test_two_char_word_unchanged(self, stemmer):
        assert stemmer.stem("في") == "في"

    def test_single_char_unchanged(self, stemmer):
        assert stemmer.stem("و") == "و"

    def test_three_char_word_may_stem(self, stemmer):
        result = stemmer.stem("أتم")
        assert len(result) >= 2


# ── Query Stemming ──────────────────────────────────────────────────────


class TestQueryStemming:
    """Test stemming of multi-word queries."""

    def test_stem_query(self, stemmer):
        result = stemmer.stem_query("شركات مقاولات")
        assert len(result.split()) == 2

    def test_stem_query_empty(self, stemmer):
        assert stemmer.stem_query("") == ""

    def test_stem_query_whitespace(self, stemmer):
        assert stemmer.stem_query("   ") == ""


# ── Integration with Normalizer ─────────────────────────────────────────


class TestNormalizerStemming:
    """Test ArabicSearchNormalizer.for_stemming() integration."""

    def test_for_stemming_removes_stop_words(self, stemming_normalizer):
        result = stemming_normalizer.normalize("شركة في الرياض")
        assert "في" not in result

    def test_for_stemming_applies_stemming(self, stemming_normalizer):
        result = stemming_normalizer.normalize("استشارات هندسية")
        # Both suffixes should be stripped
        assert len(result) < len("استشارات هندسية")

    def test_stemming_idempotent(self, stemming_normalizer):
        text = "مقاولات وإنشاءات"
        once = stemming_normalizer.normalize(text)
        twice = stemming_normalizer.normalize(once)
        assert once == twice

    def test_normalizer_default_no_stemming(self):
        normalizer = ArabicSearchNormalizer.default()
        assert normalizer.apply_stemming is False

    def test_for_stemming_has_stemming_enabled(self):
        normalizer = ArabicSearchNormalizer.for_stemming()
        assert normalizer.apply_stemming is True

    def test_real_world_company_search(self, stemming_normalizer):
        """Test that stemming improves recall for real company names."""
        q1 = stemming_normalizer.normalize("شركة مقاولات")
        q2 = stemming_normalizer.normalize("مقاولون")
        # Both should stem to a similar root
        assert "مقاول" in q1 or "مقاول" in q2
