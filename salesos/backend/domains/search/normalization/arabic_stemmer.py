"""Arabic Stemmer — lightweight rule-based suffix stripping for search.

Removes common Arabic suffixes to improve search recall by matching
different morphological forms of the same root word.

This is a simple suffix-stripping stemmer (not a full morphological analyzer).
It is intentionally conservative to avoid over-stemming.

Examples:
    "استشارات" → "استشار" (remove ات plural)
    " thương mại" → "تجار" (remove ية feminine)
    "مقاولات" → "مقاول" (remove ات plural)
    " helicoptère" → "هليكوبتر" (no change — not Arabic)
"""

from __future__ import annotations

import re
from typing import ClassVar


class ArabicStemmer:
    """Lightweight Arabic stemmer using suffix stripping.

    Rules are ordered from longest to shortest within each category.
    The stemmer applies the first matching rule and stops.

    Usage:
        stemmer = ArabicStemmer()
        root = stemmer.stem("استشارات")
        # → "استشار"

        root = stemmer.stem("مقاولات")
        # → "مقاول"
    """

    # ── Suffix patterns (order matters — longest first) ───────────

    # Common suffixes grouped by type
    # Each tuple: (compiled_regex, replacement)
    _RULES: ClassVar[list[tuple[re.Pattern, str]]] = [
        # Possessive pronouns (longest first)
        (re.compile(r'هم$'), ''),         # ـهم (their)
        (re.compile(r'هن$'), ''),         # ـهن (their fem.)
        (re.compile(r'كم$'), ''),         # ـكم (your pl.)
        (re.compile(r'كن$'), ''),         # ـكن (your fem. pl.)
        (re.compile(r'كما$'), ''),        # ـكما (your dual)
        (re.compile(r'هما$'), ''),        # ـهما (their dual)
        (re.compile(r'ني$'), ''),         # ـني (me)
        (re.compile(r'ه$'), ''),          # ـه (his/it)
        (re.compile(r'ها$'), ''),         # ـها (her/it fem.)
        (re.compile(r'ي$'), ''),          # ـي (my)

        # Plural suffixes
        (re.compile(r'ات$'), ''),         # ـات (feminine plural)
        (re.compile(r'ون$'), ''),         # ـون (masculine plural)
        (re.compile(r'ين$'), ''),         # ـين (accusative plural)
        (re.compile(r'ان$'), ''),         # ـان (dual / nisba)
        (re.compile(r'ة$'), ''),          # ـة (feminine / teh marbuta — after normalization becomes ه)

        # Common verbal/nominal suffixes
        (re.compile(r'ية$'), ''),         # ـية (feminine nisba)
        (re.compile(r'ي$'), ''),          # ـي (nisba / adjective)

        # Common prefixes (pronominal)
        (re.compile(r'^ال'), ''),         # الـ (definite article)
        (re.compile(r'^وال'), ''),        # والـ (and + definite)
        (re.compile(r'^بال'), ''),        # بالـ (preposition + definite)
        (re.compile(r'^كال'), ''),        # كالـ (like + definite)
        (re.compile(r'^لل'), ''),         # للـ (for + definite)
        (re.compile(r'^سي'), ''),         # سيـ (future marker)
        (re.compile(r'^است'), ''),        # استـ (istaf'ala pattern — often prefix)
    ]

    # Minimum stem length — don't strip if remaining is too short
    _MIN_STEM_LENGTH = 2

    def stem(self, word: str) -> str:
        """Apply suffix/prefix stripping to a single Arabic word.

        Args:
            word: A single normalized Arabic word

        Returns:
            The stemmed (root-like) form of the word
        """
        if not word or len(word) < 3:
            return word

        original = word

        for pattern, replacement in self._RULES:
            new_word = pattern.sub(replacement, word)
            if new_word != word and len(new_word) >= self._MIN_STEM_LENGTH:
                return new_word

        return word

    def stem_query(self, query: str) -> str:
        """Stem all words in a search query.

        Args:
            query: Space-separated words

        Returns:
            Stemmed query string
        """
        if not query or not query.strip():
            return ""

        words = query.split()
        stemmed = [self.stem(w) for w in words]
        return " ".join(stemmed)

    @staticmethod
    def default() -> ArabicStemmer:
        return ArabicStemmer()
