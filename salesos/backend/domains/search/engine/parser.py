"""Query parser — parses raw search input into structured tokens.

Handles Arabic and English text, extracts quoted phrases,
and identifies field prefixes (e.g., "cr:1234567890").
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
    """

    FIELD_PREFIX_RE = re.compile(r"^([a-z_]+):(.+)$", re.IGNORECASE)

    def __init__(self, known_fields: set[str] | None = None):
        self._known_fields = known_fields or set()

    def parse(self, raw: str) -> ParsedQuery:
        parsed = ParsedQuery(raw=raw)
        raw = raw.strip()

        if not raw:
            return parsed

        # Split by spaces, but preserve quoted phrases as single units
        parts = re.findall(r'"([^"]*)"|(\S+)', raw)

        for phrase, token in parts:
            if phrase:
                parsed.phrases.append(phrase)
            elif token:
                field_match = self.FIELD_PREFIX_RE.match(token)
                if field_match:
                    field_name = field_match.group(1).lower()
                    if not self._known_fields or field_name in self._known_fields:
                        parsed.field_filters[field_name] = field_match.group(2)
                        continue

                parsed.tokens.append(token)

        return parsed

    @staticmethod
    def default() -> QueryParser:
        return QueryParser(known_fields={"cr", "cr_number", "city", "region", "status", "activity", "phone", "email", "legal_form"})
