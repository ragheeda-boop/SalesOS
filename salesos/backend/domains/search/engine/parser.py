"""Query parser — parses raw search input into structured tokens.

Handles Arabic and English text, extracts quoted phrases,
and identifies field prefixes (e.g., "cr:1234567890").

Arabic text is normalized through the ArabicSearchNormalizer before
tokenization to ensure consistent matching with indexed content.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class ParsedQuery:
    """Structured representation of a parsed search query."""

    tokens: list[str] = field(default_factory=list)
    phrases: list[str] = field(default_factory=list)
    field_filters: dict[str, str] = field(default_factory=dict)
    raw: str = ""
    normalized_query: str = ""

    @property
    def has_content(self) -> bool:
        return bool(self.tokens or self.phrases or self.field_filters)

    @property
    def full_text(self) -> str:
        parts: list[str] = []
        parts.extend(self.tokens)
        parts.extend(f'"{p}"' for p in self.phrases)
        parts.extend(f"{k}:{v}" for k, v in self.field_filters.items())
        return " ".join(parts)


class QueryParser:
    """Parses raw search strings into structured queries.

    Supports:
    - Free text tokens
    - Quoted phrases ("exact match")
    - Field prefixes (cr:1234567890, city:الرياض)
    - Arabic text normalization (Alef, Yeh, Teh Marbuta, diacritics, stop words)
    - Thesaurus-based query expansion
    """

    FIELD_PREFIX_RE = re.compile(r"^([a-z_]+):(.+)$", re.IGNORECASE)

    def __init__(self, known_fields: set[str] | None = None):
        self._known_fields = known_fields or set()
        self._normalizer = None
        self._thesaurus = None

    @property
    def normalizer(self):
        if self._normalizer is None:
            from ..normalization import ArabicSearchNormalizer
            self._normalizer = ArabicSearchNormalizer.default()
        return self._normalizer

    @property
    def thesaurus(self):
        if self._thesaurus is None:
            from ..normalization import ArabicSearchThesaurus
            self._thesaurus = ArabicSearchThesaurus.default()
        return self._thesaurus

    def parse(self, raw: str) -> ParsedQuery:
        parsed = ParsedQuery(raw=raw)
        raw = raw.strip()

        if not raw:
            return parsed

        # Normalize Arabic text first
        normalized = self.normalizer.normalize_for_query(raw)
        parsed.normalized_query = normalized

        # Parse from normalized text (for consistent field matching)
        parts = re.findall(r'"([^"]*)"|(\S+)', normalized)

        for phrase, token in parts:
            if phrase:
                parsed.phrases.append(self._normalize_phrase(phrase))
            elif token:
                field_match = self.FIELD_PREFIX_RE.match(token)
                if field_match:
                    field_name = field_match.group(1).lower()
                    if not self._known_fields or field_name in self._known_fields:
                        parsed.field_filters[field_name] = field_match.group(2)
                        continue

                parsed.tokens.append(token)

        return parsed

    def _normalize_phrase(self, phrase: str) -> str:
        """Normalize a quoted phrase, preserving word boundaries."""
        return self.normalizer.normalize_for_indexing(phrase)

    @staticmethod
    def default() -> QueryParser:
        return QueryParser(known_fields={"cr", "cr_number", "city", "region", "status", "activity", "phone", "email", "legal_form"})
