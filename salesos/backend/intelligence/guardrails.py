"""Prompt injection protection, PII scrubbing (AI-GR-001), and output validation."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from html import unescape
from typing import Any

SPECIAL_TOKENS = [
    "{{",
    "}}",
    "{%",
    "%}",
    "<|",
    "|>",
    "<s>",
    "</s>",
    "[INST]",
    "[/INST]",
    "<<SYS>>",
    "<</SYS>>",
]

HARMFUL_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|above|below)\s+instructions",
    r"forget\s+(all\s+)?(previous|above|below)",
    r"disregard\s+(all\s+)?(previous|above|below)",
    r"system\s+prompt",
    r"you\s+are\s+(now|not\s+an?\s+ai|a\s+free)",
    r"act\s+as\s+(if|though)",
    r"pretend\s+(to\s+be|that)",
    r"role[-\s]*play",
    r"do\s+(not\s+)?(follow|obey)",
    r"output\s+(raw|json|the\s+following)",
    r"print\s+(the\s+)?(secret|password|key|token)",
    r"leak\s+(the\s+)?(secret|password|key|token)",
    r"bypass\s+(the\s+)?(safety|filter|guardrail|restriction|rule)",
    r"jailbreak",
    r"dan\b(\s*$|\s*\d)",
]


def sanitize_input(user_input: str) -> str:
    """AI-GR-001 — Strip special tokens, escape sequences, and control characters."""
    sanitized = user_input
    for token in SPECIAL_TOKENS:
        sanitized = sanitized.replace(token, "")
    sanitized = re.sub(r"\\u[0-9a-fA-F]{4}", "", sanitized)
    sanitized = re.sub(r"\\x[0-9a-fA-F]{2}", "", sanitized)
    sanitized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", sanitized)
    return sanitized.strip()


# --- AI-GR-001 PII scrub (InteractionNote / RAG path; STORY-09-03) ---------------

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",
    re.IGNORECASE,
)
# Saudi mobiles + international with optional separators.
_PHONE_RE = re.compile(
    r"(?<!\d)(?:\+?966[\s\-.]*)?0?5\d(?:[\s\-.]*\d){7}"
    r"|(?<!\d)\+\d{1,3}(?:[\s\-.]*\d){7,12}(?!\d)"
)
# Saudi national ID / Iqama: 10 digits starting with 1 or 2.
_NATIONAL_ID_RE = re.compile(r"(?<!\d)[12]\d{9}(?!\d)")
_IBAN_RE = re.compile(r"\bSA[0-9A-Z]{22}\b", re.IGNORECASE)
_CARD_RE = re.compile(r"(?<!\d)(?:\d[ \-]*){13,19}(?!\d)")
_LABELED_NAME_RE = re.compile(
    r"(?i)(?:\bname\b|\bcontact\b|\bfull\s*name\b|\bالاسم\b|\bاسم\b)\s*[:：]\s*"
    r"([A-Za-z\u0600-\u06FF][A-Za-z\u0600-\u06FF\s\-'.]{0,60})"
)

_PLACEHOLDERS = {
    "email": "[EMAIL]",
    "phone": "[PHONE]",
    "national_id": "[NATIONAL_ID]",
    "iban": "[IBAN]",
    "card": "[CARD]",
    "name": "[NAME]",
}


@dataclass(frozen=True)
class PiiScrubResult:
    """AI-GR-001 scrub output — raw must never be used for RAG."""

    text: str
    redactions: dict[str, int] = field(default_factory=dict)

    @property
    def redaction_count(self) -> int:
        return sum(self.redactions.values())


def scrub_pii_for_rag(text: str | None) -> PiiScrubResult:
    """AI-GR-001 — redact PII before any note content reaches RAG.

    Covers phones, emails, Saudi national ID/Iqama, IBAN, card-like digit
    runs, and labeled name fields. Not Production GO by itself — live ≥100
    sample ops audit remains a residual before RAG Production GO.
    """
    if text is None:
        return PiiScrubResult(text="", redactions={})
    # HTML first so tags do not split phone/email tokens.
    working = _HTML_TAG_RE.sub(" ", unescape(str(text)))
    counts: dict[str, int] = {}

    def _sub(pattern: re.Pattern[str], kind: str, body: str) -> str:
        hits = 0

        def _repl(_m: re.Match[str]) -> str:
            nonlocal hits
            hits += 1
            return _PLACEHOLDERS[kind]

        out = pattern.sub(_repl, body)
        if hits:
            counts[kind] = counts.get(kind, 0) + hits
        return out

    working = _sub(_EMAIL_RE, "email", working)
    working = _sub(_IBAN_RE, "iban", working)
    working = _sub(_PHONE_RE, "phone", working)
    working = _sub(_NATIONAL_ID_RE, "national_id", working)
    working = _sub(_CARD_RE, "card", working)

    def _name_repl(m: re.Match[str]) -> str:
        counts["name"] = counts.get("name", 0) + 1
        return m.group(0)[: m.start(1) - m.start(0)] + _PLACEHOLDERS["name"]

    working = _LABELED_NAME_RE.sub(_name_repl, working)
    cleaned = re.sub(r"[ \t]{2,}", " ", working)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return PiiScrubResult(text=cleaned, redactions=dict(counts))


def detect_pii_leakage(text: str) -> list[str]:
    """Return kinds of PII still present (empty = pass for fixture audit)."""
    leaks: list[str] = []
    if _EMAIL_RE.search(text):
        leaks.append("email")
    if _PHONE_RE.search(text):
        leaks.append("phone")
    if _NATIONAL_ID_RE.search(text):
        leaks.append("national_id")
    if _IBAN_RE.search(text):
        leaks.append("iban")
    if _CARD_RE.search(text):
        # Avoid flagging scrubbed placeholders / short numbers.
        for m in _CARD_RE.finditer(text):
            digits = re.sub(r"\D", "", m.group(0))
            if len(digits) >= 13:
                leaks.append("card")
                break
    if _LABELED_NAME_RE.search(text):
        for m in _LABELED_NAME_RE.finditer(text):
            if m.group(1).strip() not in {_PLACEHOLDERS["name"], "[NAME]"}:
                leaks.append("name")
                break
    return leaks


def add_input_moderation(text: str) -> bool:
    """Check for harmful content. Returns True if text is harmful."""
    lower = text.lower()
    for pattern in HARMFUL_PATTERNS:
        if re.search(pattern, lower):
            return True
    return False


def validate_output(llm_output: str, schema: dict[str, Any]) -> bool:
    """Validate LLM output against expected JSON schema."""
    content = llm_output.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return False
    if not isinstance(parsed, dict):
        return False
    if "analysis" not in parsed and "proposal" not in parsed and "summary" not in parsed:
        return False
    # Require non-optional keys declared in the schema (e.g. proposal when listed)
    optional_keys = {"confidence", "evidence", "sources"}
    for key in schema:
        if key in optional_keys:
            continue
        if key not in parsed:
            return False
    if "confidence" in schema and "confidence" in parsed:
        c = parsed["confidence"]
        if not isinstance(c, (int, float)) or not (0 <= c <= 1):
            return False
    return True


def extract_json_from_llm_output(output: str) -> dict[str, Any] | None:
    """Extract JSON dict from LLM output, handling markdown fences."""
    content = output.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*\n?", "", content)
        content = re.sub(r"\n?\s*```$", "", content)
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return None
