"""CompanyNameMatcher — fuzzy matching of Arabic company names using Jaro-Winkler distance.

Jaro-Winkler is preferred over Levenshtein for Arabic company names because:
1. It handles short strings well (common in company names)
2. It gives higher scores to strings with matching prefixes
3. It's robust to spelling variations and typos

The matcher normalizes both names through ArabicSearchNormalizer.for_matching()
before comparison, which strips company prefixes/suffixes and normalizes
Arabic characters (Alef, Yeh, Teh Marbuta, etc.).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import ClassVar

from .arabic_normalizer import ArabicSearchNormalizer


# ── Company token stop words (words that add no distinguishing value) ───

COMPANY_STOP_WORDS: set[str] = {
    "شركة", "مؤسسة", "مجموعة", "مصنع", "مكتب",
    "للتجارة", "للتجارۃ", "للصناعة", "للصناعه",
    "للمقاولات", "للمقاوله", "للاستثمار",
    "للخدمات", "للخدمه", "للنقل", "للشحن",
    "المحدودة", "المحدوده", "المساهمة", "المساهمه",
    "السعودية", "السعوديه", "العامة", "العامه",
    "ذات", "مسؤولية", "مسئوليه", "محدودة", "محدوده",
    "مساهمة", "مساهمه",
    "شركة مساهمة سعودية", "شركة ذات مسؤولية محدودة",
    "ال", "و",
}

# Words that indicate the CORE distinguishing part of a company name
# These are used to extract a "head word" for quick pre-filtering
_CORE_INDICATORS: set[str] = {
    "شركة", "شركه", "مؤسسة", "مؤسسه", "موسسه",
    "مجموعة", "مجموعه", "مصنع", "مكتب",
}


def _jaro_distance(s1: str, s2: str) -> float:
    """Compute the Jaro similarity between two strings.

    Returns 0.0 to 1.0 where 1.0 is an exact match.
    """
    if s1 == s2:
        return 1.0

    len1, len2 = len(s1), len(s2)
    if len1 == 0 or len2 == 0:
        return 0.0

    match_window = max(len1, len2) // 2 - 1
    if match_window < 0:
        match_window = 0

    matched_s1: list[bool] = [False] * len1
    matched_s2: list[bool] = [False] * len2

    matches = 0
    for i in range(len1):
        start = max(0, i - match_window)
        end = min(len2, i + match_window + 1)
        for j in range(start, end):
            if matched_s2[j]:
                continue
            if s1[i] != s2[j]:
                continue
            matched_s1[i] = True
            matched_s2[j] = True
            matches += 1
            break

    if matches == 0:
        return 0.0

    transpositions = 0
    j = 0
    for i in range(len1):
        if not matched_s1[i]:
            continue
        while j < len2 and not matched_s2[j]:
            j += 1
        if j < len2 and s1[i] != s2[j]:
            transpositions += 1
        j += 1

    return (
        matches / len1
        + matches / len2
        + (matches - transpositions / 2.0) / matches
    ) / 3.0


def _jaro_winkler_distance(s1: str, s2: str, scaling: float = 0.1) -> float:
    """Compute the Jaro-Winkler similarity, boosting prefix matches.

    Args:
        s1: First string (typically the reference)
        s2: Second string (typically the candidate)
        scaling: Scaling factor for prefix boost (default 0.1)

    Returns:
        Score between 0.0 and 1.0
    """
    jaro = _jaro_distance(s1, s2)

    # Count common prefix (max 4 characters)
    prefix_len = 0
    for i in range(min(len(s1), len(s2), 4)):
        if s1[i] == s2[i]:
            prefix_len += 1
        else:
            break

    return jaro + prefix_len * scaling * (1.0 - jaro)


def _extract_head_word(name: str) -> str | None:
    """Extract the most distinguishing word from a company name.

    After removing company-type words, returns the first remaining
    word as the "head word" for blocking/pre-filtering.

    Example:
        "شركة أرامكو السعودية المحدودة" → "أرامكو"
    """
    words = name.split()
    # Remove company type words from the start
    while words and words[0] in _CORE_INDICATORS:
        words = words[1:]
    # Remove common suffixes
    while words and words[-1] in COMPANY_STOP_WORDS:
        words = words[:-1]
    if not words:
        return None
    # Return the first content word (or last if very short)
    for w in words:
        if len(w) > 2:
            return w
    return words[0] if words else None


@dataclass
class CompanyMatchResult:
    """Result of comparing two company names."""

    score: float
    is_match: bool = False
    normalized_name_a: str = ""
    normalized_name_b: str = ""
    match_type: str = "none"
    reasons: list[str] | None = None

    def to_dict(self) -> dict:
        return {
            "score": round(self.score, 4),
            "is_match": self.is_match,
            "match_type": self.match_type,
            "reasons": self.reasons or [],
        }


class CompanyNameMatcher:
    """Fuzzy matcher for Arabic company names using Jaro-Winkler distance.

    Usage:
        matcher = CompanyNameMatcher()
        result = matcher.match("شركة أرامكو السعودية", "ارامكو السعوديه")
        # result.score ≈ 0.92, result.is_match = True
    """

    DEFAULT_THRESHOLD: ClassVar[float] = 0.85

    def __init__(
        self,
        threshold: float = DEFAULT_THRESHOLD,
        normalizer: ArabicSearchNormalizer | None = None,
    ):
        self.threshold = threshold
        self._normalizer = normalizer or ArabicSearchNormalizer.for_matching()

    @property
    def normalizer(self) -> ArabicSearchNormalizer:
        return self._normalizer

    def match(self, name_a: str, name_b: str) -> CompanyMatchResult:
        """Compare two company names and return a match result.

        The pipeline:
        1. Normalize both names
        2. Compute Jaro-Winkler distance
        3. Apply threshold
        4. Return result with match type and reasons
        """
        if not name_a or not name_b:
            return CompanyMatchResult(
                score=0.0, match_type="empty", reasons=["One or both names are empty"]
            )

        reasons: list[str] = []
        norm_a = self._normalizer.normalize(name_a)
        norm_b = self._normalizer.normalize(name_b)

        # Quick exact match check
        if norm_a == norm_b:
            return CompanyMatchResult(
                score=1.0,
                is_match=True,
                normalized_name_a=norm_a,
                normalized_name_b=norm_b,
                match_type="exact",
                reasons=["Exact match after normalization"],
            )

        # Compute Jaro-Winkler distance
        score = _jaro_winkler_distance(norm_a, norm_b)
        reasons.append(f"Jaro-Winkler: {score:.4f}")

        # Check if one name is a substring of the other
        if norm_a in norm_b or norm_b in norm_a:
            score = max(score, 0.92)
            reasons.append("Substring match")

        is_match = score >= self.threshold
        match_type = "fuzzy" if is_match else "none"

        return CompanyMatchResult(
            score=score,
            is_match=is_match,
            normalized_name_a=norm_a,
            normalized_name_b=norm_b,
            match_type=match_type,
            reasons=reasons,
        )

    def match_with_head_word(
        self, name_a: str, name_b: str
    ) -> CompanyMatchResult:
        """Match using head word pre-filtering for performance.

        This is useful for blocking in entity resolution — it first checks
        if the head words match before computing the full Jaro-Winkler.
        """
        result = self.match(name_a, name_b)
        if result.is_match:
            return result

        # Try head word matching as a fallback
        head_a = _extract_head_word(result.normalized_name_a)
        head_b = _extract_head_word(result.normalized_name_b)

        if head_a and head_b and head_a == head_b:
            result.score = max(result.score, 0.75)
            if result.score >= self.threshold:
                result.is_match = True
                result.match_type = "head_word"
                if result.reasons:
                    result.reasons.append(f"Head word match: '{head_a}'")

        return result

    def compare_multiple(
        self, target: str, candidates: list[str]
    ) -> list[CompanyMatchResult]:
        """Compare a target name against multiple candidates.

        Returns results sorted by score descending.
        """
        results = [self.match(target, c) for c in candidates]
        results.sort(key=lambda r: -r.score)
        return results

    @staticmethod
    def default() -> CompanyNameMatcher:
        return CompanyNameMatcher()
