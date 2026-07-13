"""Input validation and sanitization utilities for SalesOS.

Provides RFC-compliant email validation, Saudi business format validation
(phone, CR, VAT), injection detection, XSS prevention, and max length enforcement.
"""

import html
import re
from typing import Any

from pydantic import field_validator, model_validator


# ── Regex Patterns ───────────────────────────────────────────────────────────

# RFC 5322 compliant email (practical subset)
EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+"
    r"@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
    r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
)

# Saudi phone: +966XXXXXXXXX (10 digits after +966, first digit 5)
SAUDI_PHONE_RE = re.compile(r"^\+966[5][0-9]{8}$")

# Saudi CR (Commercial Registration): exactly 10 digits
SAUDI_CR_RE = re.compile(r"^\d{10}$")

# Saudi VAT number: exactly 15 digits
SAUDI_VAT_RE = re.compile(r"^\d{15}$")

# Saudi National ID / Iqama: 10 digits
SAUDI_ID_RE = re.compile(r"^\d{10}$")

# ── SQL Injection Patterns ───────────────────────────────────────────────────

SQL_INJECTION_PATTERNS = [
    re.compile(r"(?i)(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|UNION|FETCH|DECLARE|TRUNCATE)\b)"),
    re.compile(r"(?i)(\b(OR|AND)\b\s+[\d\w'\"=]+\s*=\s*[\d\w'\"=]+)"),
    re.compile(r"(?i)(--|/\*|\*/|;\s*(DROP|DELETE|INSERT|UPDATE|SELECT))"),
    re.compile(r"(?i)(CHAR\s*\(|CONCAT\s*\(|0x[0-9a-fA-F]+)"),
    re.compile(r"(?i)(SLEEP\s*\(|BENCHMARK\s*\()"),
    re.compile(r"(?i)(LOAD_FILE\s*\(|INTO\s+(OUTFILE|DUMPFILE))"),
]

# ── XSS Patterns ─────────────────────────────────────────────────────────────

XSS_PATTERNS = [
    re.compile(r"<\s*script[\s>]", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"on\w+\s*=", re.IGNORECASE),
    re.compile(r"<\s*(iframe|object|embed|applet|form|input|button|img|svg|math|link|meta|base|video|audio|source)", re.IGNORECASE),
    re.compile(r"expression\s*\(", re.IGNORECASE),
    re.compile(r"url\s*\(", re.IGNORECASE),
    re.compile(r"data\s*:\s*text/html", re.IGNORECASE),
    re.compile(r"<\s*/?(script|style|iframe)[^>]*>", re.IGNORECASE),
]

# ── Validation Functions ─────────────────────────────────────────────────────


def validate_email(email: str) -> str:
    """Validate email against RFC 5322 practical pattern.

    Args:
        email: Email address to validate.

    Returns:
        Normalized (lowercased, stripped) email.

    Raises:
        ValueError: If email is invalid.
    """
    if not email or not isinstance(email, str):
        raise ValueError("Email is required")
    email = email.strip().lower()
    if len(email) > 254:
        raise ValueError("Email exceeds maximum length of 254 characters")
    local, _, domain = email.rpartition("@")
    if not local or not domain:
        raise ValueError("Invalid email format")
    if len(local) > 64:
        raise ValueError("Email local part exceeds 64 characters")
    if not EMAIL_RE.match(email):
        raise ValueError("Invalid email format")
    return email


def validate_saudi_phone(phone: str) -> str:
    """Validate Saudi phone number format: +966XXXXXXXXX.

    Args:
        phone: Phone number to validate.

    Returns:
        Normalized phone number.

    Raises:
        ValueError: If phone number is invalid.
    """
    if not phone or not isinstance(phone, str):
        raise ValueError("Phone number is required")
    phone = phone.strip()
    # Allow common input formats and normalize
    phone = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if phone.startswith("00966"):
        phone = "+966" + phone[5:]
    elif phone.startswith("966") and not phone.startswith("+"):
        phone = "+" + phone
    elif phone.startswith("0"):
        phone = "+966" + phone[1:]
    if not SAUDI_PHONE_RE.match(phone):
        raise ValueError(
            "Invalid Saudi phone number. Expected format: +966XXXXXXXXX (10 digits starting with 5)"
        )
    return phone


def validate_cr_number(cr: str) -> str:
    """Validate Saudi Commercial Registration (CR) number: exactly 10 digits.

    Args:
        cr: CR number to validate.

    Returns:
        Normalized CR number.

    Raises:
        ValueError: If CR number is invalid.
    """
    if not cr or not isinstance(cr, str):
        raise ValueError("CR number is required")
    cr = cr.strip().replace(" ", "")
    if not SAUDI_CR_RE.match(cr):
        raise ValueError("Invalid CR number. Must be exactly 10 digits")
    return cr


def validate_vat_number(vat: str) -> str:
    """Validate Saudi VAT registration number: exactly 15 digits.

    Args:
        vat: VAT number to validate.

    Returns:
        Normalized VAT number.

    Raises:
        ValueError: If VAT number is invalid.
    """
    if not vat or not isinstance(vat, str):
        raise ValueError("VAT number is required")
    vat = vat.strip().replace(" ", "")
    if not SAUDI_VAT_RE.match(vat):
        raise ValueError("Invalid VAT number. Must be exactly 15 digits")
    return vat


def detect_sql_injection(value: str) -> bool:
    """Detect potential SQL injection patterns in a string.

    Args:
        value: Input string to check.

    Returns:
        True if a potential SQL injection pattern is detected.
    """
    if not value or not isinstance(value, str):
        return False
    for pattern in SQL_INJECTION_PATTERNS:
        if pattern.search(value):
            return True
    return False


def detect_xss(value: str) -> bool:
    """Detect potential XSS patterns in a string.

    Args:
        value: Input string to check.

    Returns:
        True if a potential XSS pattern is detected.
    """
    if not value or not isinstance(value, str):
        return False
    for pattern in XSS_PATTERNS:
        if pattern.search(value):
            return True
    return False


def sanitize_html(value: str) -> str:
    """Escape HTML entities in a string to prevent XSS.

    Args:
        value: Input string to sanitize.

    Returns:
        HTML-escaped string.
    """
    if not value or not isinstance(value, str):
        return value
    return html.escape(value, quote=True)


def enforce_max_length(value: str, max_length: int, field_name: str = "Input") -> str:
    """Enforce maximum string length.

    Args:
        value: Input string.
        max_length: Maximum allowed length.
        field_name: Name of the field for error messages.

    Returns:
        Truncated string if within limit.

    Raises:
        ValueError: If string exceeds maximum length.
    """
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if len(value) > max_length:
        raise ValueError(f"{field_name} exceeds maximum length of {max_length} characters")
    return value


def validate_input(
    value: str,
    field_name: str = "input",
    max_length: int = 1000,
    check_sql: bool = True,
    check_xss: bool = True,
) -> str:
    """Comprehensive input validation combining all checks.

    Args:
        value: Input string to validate.
        field_name: Name of the field for error messages.
        max_length: Maximum allowed string length.
        check_sql: Whether to check for SQL injection.
        check_xss: Whether to check for XSS patterns.

    Returns:
        Sanitized and validated string.

    Raises:
        ValueError: If any validation check fails.
    """
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")

    value = value.strip()

    if not value:
        return value

    # Max length check
    enforce_max_length(value, max_length, field_name)

    # SQL injection detection
    if check_sql and detect_sql_injection(value):
        raise ValueError(f"{field_name} contains potentially dangerous content")

    # XSS detection
    if check_xss and detect_xss(value):
        raise ValueError(f"{field_name} contains potentially dangerous content")

    return value


# ── Pydantic Validators ──────────────────────────────────────────────────────

class InputSanitizedModel:
    """Mixin for Pydantic models that sanitizes string inputs against injection."""

    @field_validator("*", mode="before")
    @classmethod
    def sanitize_strings(cls, v: Any) -> Any:
        if isinstance(v, str):
            v = v.strip()
            if detect_sql_injection(v):
                raise ValueError("Input contains potentially dangerous content")
            if detect_xss(v):
                raise ValueError("Input contains potentially dangerous content")
        return v
