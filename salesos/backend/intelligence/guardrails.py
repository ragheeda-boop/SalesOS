"""Prompt injection protection and output validation."""

import json
import re
from typing import Any

SPECIAL_TOKENS = [
    "{{", "}}", "{%", "%}",
    "<|", "|>",
    "<s>", "</s>",
    "[INST]", "[/INST]",
    "<<SYS>>", "<</SYS>>",
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
    """Strip special tokens, escape sequences, and control characters."""
    sanitized = user_input
    for token in SPECIAL_TOKENS:
        sanitized = sanitized.replace(token, "")
    sanitized = re.sub(r"\\u[0-9a-fA-F]{4}", "", sanitized)
    sanitized = re.sub(r"\\x[0-9a-fA-F]{2}", "", sanitized)
    sanitized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", sanitized)
    return sanitized.strip()


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
