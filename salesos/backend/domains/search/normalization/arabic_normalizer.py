"""ArabicSearchNormalizer — comprehensive Arabic text normalization for search.

Normalization pipeline:
1. Diacritics removal (tashkeel)
2. Tatweel (kashida) removal
3. Alef normalization (أ إ آ → ا)
4. Yeh normalization (ي ى ئ → unified)
5. Teh Marbuta normalization (ة → ه)
6. Arabic punctuation normalization
7. Whitespace normalization
8. Stop word removal (optional)

This ensures that "شركة", "شَرِكَة", "شركه", and "شــركة" all match the same index.
"""

from __future__ import annotations

import re
from typing import ClassVar


class ArabicSearchNormalizer:
    """Comprehensive Arabic text normalizer for search and matching.

    Usage:
        normalizer = ArabicSearchNormalizer()
        normalized = normalizer.normalize("شَرِكَةُ الأَمَلِ للتّجارة")
        # → "شركة الامل للتجارة"

        with_stop_words = normalizer.normalize("شَرِكَةُ فِي الرِياض")
        # → "شركة الرياض"

    All normalization rules are applied in a deterministic order to ensure
    consistent indexing and querying.
    """

    # ── Unicode character classes ─────────────────────────────────────

    # Arabic diacritics (tashkeel): fatha, damma, kasra, sukun, shadda, etc.
    _DIACRITICS_PATTERN: ClassVar[re.Pattern] = re.compile(
        r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E4'
        r'\u06E7\u06E8\u06EA-\u06ED]'
    )

    # Tatweel / Kashida (stretching character)
    _TATWEEL = '\u0640'

    # Arabic punctuation to normalize
    _ARABIC_PUNCTUATION_MAP: ClassVar[dict[str, str]] = {
        '\u060C': ',',   # Arabic comma
        '\u061B': ';',   # Arabic semicolon
        '\u061F': '?',   # Arabic question mark
        '،': ',',
        '؛': ';',
        '؟': '?',
    }

    # Multiple whitespace
    _WHITESPACE_RE: ClassVar[re.Pattern] = re.compile(r'\s+')

    # ── Alef normalizations ───────────────────────────────────────────

    # Alef with hamza above (أ), below (إ), and Alef madda (آ) → plain Alef (ا)
    _ALEF_NORMALIZATION_TABLE: ClassVar[dict[int, str]] = {
        ord('\u0622'): '\u0627',  # آ (alef madda) → ا
        ord('\u0623'): '\u0627',  # أ (alef with hamza above) → ا
        ord('\u0625'): '\u0627',  # إ (alef with hamza below) → ا
        ord('\u0671'): '\u0627',  # ٱ (alef wasla) → ا
        ord('\u0672'): '\u0627',  # ٲ
        ord('\u0673'): '\u0627',  # ٳ
        ord('\u0675'): '\u0627',  # ٵ
    }

    # ── Yeh normalizations ────────────────────────────────────────────

    # Yeh (ي) and Alif Maksura (ى) → dotless Yeh (ى)
    # Note: this maps Persian Yeh too
    _YEH_NORMALIZATION_TABLE: ClassVar[dict[int, str]] = {
        ord('\u0649'): '\u064A',  # ى (alef maksura) → ي
        ord('\u064A'): '\u064A',  # ي stays ي (no change, baseline)
        ord('\u06CC'): '\u064A',  # ی (Persian yeh) → ي
        ord('\u06D0'): '\u064A',  # ې → ي
        ord('\u06CD'): '\u064A',  # ۍ → ي
        ord('\u06CE'): '\u064A',  # ێ → ي
        ord('\u0777'): '\u064A',  # ݷ → ي
        ord('\u06D1'): '\u064A',  # ۑ → ي
    }

    # Hamza on Yeh (ئ) → plain Yeh (ي)
    _HAMZA_YEH_TABLE: ClassVar[dict[int, str]] = {
        ord('\u0626'): '\u064A',  # ئ → ي
    }

    # ── Teh Marbuta normalization ─────────────────────────────────────

    # Teh Marbuta (ة) → Heh (ه) for search normalization
    _TEH_MARBUTA_TABLE: ClassVar[dict[int, str]] = {
        ord('\u0629'): '\u0647',  # ة → ه
    }

    # ── Other normalizations ──────────────────────────────────────────

    # Waw with hamza (ؤ) → plain Waw (و)
    _WAW_HAMZA_TABLE: ClassVar[dict[int, str]] = {
        ord('\u0624'): '\u0648',  # ؤ → و
    }

    # Arabic-Indic digits → Western digits
    _DIGIT_NORMALIZATION_TABLE: ClassVar[dict[int, str]] = {
        ord('\u0660'): '0', ord('\u0661'): '1', ord('\u0662'): '2',
        ord('\u0663'): '3', ord('\u0664'): '4', ord('\u0665'): '5',
        ord('\u0666'): '6', ord('\u0667'): '7', ord('\u0668'): '8',
        ord('\u0669'): '9',
    }

    def __init__(
        self,
        remove_diacritics: bool = True,
        remove_tatweel: bool = True,
        normalize_alef: bool = True,
        normalize_yeh: bool = True,
        normalize_teh_marbuta: bool = True,
        normalize_hamza_on_waw: bool = True,
        normalize_digits: bool = False,
        normalize_punctuation: bool = True,
        remove_stop_words: bool = True,
        lower_case: bool = False,
    ):
        self.remove_diacritics = remove_diacritics
        self.remove_tatweel = remove_tatweel
        self.normalize_alef = normalize_alef
        self.normalize_yeh = normalize_yeh
        self.normalize_teh_marbuta = normalize_teh_marbuta
        self.normalize_hamza_on_waw = normalize_hamza_on_waw
        self.normalize_digits = normalize_digits
        self.normalize_punctuation = normalize_punctuation
        self.remove_stop_words = remove_stop_words
        self.lower_case = lower_case

    def normalize(self, text: str) -> str:
        """Apply the full normalization pipeline to the given text.

        Args:
            text: Raw Arabic (or mixed) text to normalize

        Returns:
            Normalized text string
        """
        if not text or not text.strip():
            return ""

        text = text.strip()

        # 1. Remove diacritics (tashkeel)
        if self.remove_diacritics:
            text = self._DIACRITICS_PATTERN.sub('', text)

        # 2. Remove tatweel / kashida
        if self.remove_tatweel:
            text = text.replace(self._TATWEEL, '')

        # 3. Normalize Alef variants (أ إ آ → ا)
        if self.normalize_alef:
            text = text.translate(self._ALEF_NORMALIZATION_TABLE)

        # 4. Normalize Yeh variants (ى ئ → ي)
        if self.normalize_yeh:
            text = text.translate(self._YEH_NORMALIZATION_TABLE)
            text = text.translate(self._HAMZA_YEH_TABLE)

        # 5. Normalize Teh Marbuta (ة → ه)
        if self.normalize_teh_marbuta:
            text = text.translate(self._TEH_MARBUTA_TABLE)

        # 6. Normalize Waw with hamza (ؤ → و)
        if self.normalize_hamza_on_waw:
            text = text.translate(self._WAW_HAMZA_TABLE)

        # 7. Normalize Arabic-Indic digits to Western
        if self.normalize_digits:
            text = text.translate(self._DIGIT_NORMALIZATION_TABLE)

        # 8. Normalize Arabic punctuation
        if self.normalize_punctuation:
            for arabic_char, latin_char in self._ARABIC_PUNCTUATION_MAP.items():
                text = text.replace(arabic_char, latin_char)

        # 9. Normalize whitespace
        text = self._WHITESPACE_RE.sub(' ', text).strip()

        # 10. Lowercase for English characters
        if self.lower_case:
            text = text.lower()

        # 11. Remove Arabic stop words
        if self.remove_stop_words:
            text = self._remove_stop_words(text)

        return text

    def normalize_for_indexing(self, text: str) -> str:
        """Normalize text for database indexing (preserves more information).

        Unlike search query normalization, indexing preserves word boundaries
        and keeps all words (no stop word removal) to support phrase matching.
        """
        saved = self.remove_stop_words
        self.remove_stop_words = False
        result = self.normalize(text)
        self.remove_stop_words = saved
        return result

    def normalize_for_query(self, text: str) -> str:
        """Normalize a search query (aggressive normalization).

        Removes stop words, normalizes all characters, lowercases.
        """
        saved_lower = self.lower_case
        self.lower_case = True
        result = self.normalize(text)
        self.lower_case = saved_lower
        return result

    def _remove_stop_words(self, text: str) -> str:
        """Remove Arabic stop words from the text."""
        from .stop_words import STOP_WORDS_RE
        text = STOP_WORDS_RE.sub('', text).strip()
        text = self._WHITESPACE_RE.sub(' ', text).strip()
        return text

    @staticmethod
    def default() -> ArabicSearchNormalizer:
        """Create a normalizer with default settings for search."""
        return ArabicSearchNormalizer()

    @staticmethod
    def for_indexing() -> ArabicSearchNormalizer:
        """Create a normalizer optimized for database indexing."""
        return ArabicSearchNormalizer(
            remove_stop_words=False,
            normalize_digits=False,
        )

    @staticmethod
    def for_matching() -> ArabicSearchNormalizer:
        """Create an aggressive normalizer for entity matching."""
        return ArabicSearchNormalizer(
            remove_stop_words=True,
            normalize_teh_marbuta=True,
            normalize_digits=True,
        )
