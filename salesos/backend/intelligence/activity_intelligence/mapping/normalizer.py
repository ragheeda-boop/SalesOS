"""Normalizer — Stage 1 of the Mapping Pipeline (ADR-012 §6).

Cleans raw communication data:
- Lower-case email addresses
- Trim whitespace
- Remove "Re:" and "Fwd:" prefixes
- Decode MIME-encoded subjects
- Normalize domains (remove subdomains for common providers)
"""

from __future__ import annotations

import re
from email.header import decode_header

from intelligence.activity_intelligence.contracts.models import (
    NormalizedAddress,
    NormalizedDomain,
    NormalizedSubject,
    RawCalendarEvent,
    RawEmail,
    ResolvedEntities,
)

_FREE_PROVIDERS = {
    "gmail.com", "googlemail.com", "yahoo.com", "ymail.com",
    "outlook.com", "hotmail.com", "live.com", "msn.com",
    "icloud.com", "me.com", "mac.com",
    "protonmail.com", "proton.me", "pm.me",
    "aol.com", "mail.com", "gmx.com", "zoho.com",
}

_RE_PREFIX = re.compile(r"^(Re|Fwd|رد|FW|إعادة)\s*:\s*", re.IGNORECASE)
_RE_WHITESPACE = re.compile(r"\s+")


def _decode_mime(value: str) -> str:
    """Decode MIME-encoded header values."""
    try:
        parts = decode_header(value)
        result = ""
        for part, charset in parts:
            if isinstance(part, bytes):
                charset = charset or "utf-8"
                result += part.decode(charset, errors="replace")
            else:
                result += str(part)
        return result.strip()
    except Exception:
        return value


def _extract_domain(email: str) -> str:
    """Extract domain from an email address."""
    if "@" in email:
        return email.rsplit("@", 1)[-1].strip().lower()
    return ""


def _normalize_domain(raw_domain: str) -> str:
    """Normalize domain: remove subdomains for free providers."""
    domain = raw_domain.lower().strip()
    parts = domain.split(".")
    if len(parts) > 2 and ".".join(parts[-2:]) in _FREE_PROVIDERS:
        return ".".join(parts[-2:])
    return domain


class Normalizer:
    """Clean and normalize raw communication data."""

    def normalize_email(self, raw: RawEmail) -> tuple[NormalizedAddress, NormalizedAddress | None, NormalizedSubject]:
        """Normalize email headers. Returns (from_address, reply_to, subject)."""
        from_addr = self._normalize_address(raw.from_address)
        reply_to_raw = raw.headers.get("Reply-To", "")
        reply_to = self._normalize_address(reply_to_raw) if reply_to_raw else None
        subject = self._normalize_subject(raw.subject)
        return from_addr, reply_to, subject

    def normalize_calendar(self, raw: RawCalendarEvent) -> list[NormalizedAddress]:
        """Normalize calendar attendee addresses."""
        addresses: list[NormalizedAddress] = []
        for attendee in raw.attendees:
            email_addr = attendee.get("email", "")
            if email_addr:
                addresses.append(self._normalize_address(email_addr))
        return addresses

    def normalize_domain(self, raw_domain: str) -> NormalizedDomain:
        """Normalize a raw domain string."""
        domain = _normalize_domain(raw_domain)
        return NormalizedDomain(
            raw=raw_domain,
            normalized=domain,
            is_free_provider=domain in _FREE_PROVIDERS,
        )

    def extract_hints(self, raw: RawEmail) -> ResolvedEntities:
        """Extract entity hints from raw email for the Resolver stage."""
        from_addr = self._normalize_address(raw.from_address)
        from_name = from_addr.display_name or from_addr.email
        from_domain = from_addr.domain

        # Extract host from References/In-Reply-To headers
        references = raw.references or raw.in_reply_to or ""

        # Check subject for opportunity hints like [OPP-123]
        opp_match = re.search(r"\[OPP[_-]?(\d+)\]", raw.subject, re.IGNORECASE)
        opportunity_hint = f"OPP-{opp_match.group(1)}" if opp_match else None

        return ResolvedEntities(
            person_name=from_name,
            person_email=from_addr.email,
            domain=from_domain,
            company_hint=from_domain,
            opportunity_hint=opportunity_hint,
        )

    def _normalize_address(self, raw: str) -> NormalizedAddress:
        """Parse and normalize an email address."""
        raw = raw.strip()
        display_name = ""
        email = raw

        match = re.match(r'(.*?)\s*<(.+?)>', raw)
        if match:
            display_name = match.group(1).strip().strip('"').strip("'")
            email = match.group(2).strip()

        email = email.lower().strip()
        domain = _extract_domain(email)

        return NormalizedAddress(
            raw=raw,
            display_name=display_name,
            email=email,
            domain=domain,
        )

    @staticmethod
    def _normalize_subject(raw: str) -> NormalizedSubject:
        """Clean and decode an email subject."""
        decoded = _decode_mime(raw)

        # Strip ALL Re:/Fwd: prefixes (e.g., "Re: Re: Re: Final" → "Final")
        cleaned = decoded
        has_re = False
        has_fwd = False
        prefix = ""
        while True:
            match = _RE_PREFIX.match(cleaned)
            if not match:
                break
            prefix_val = match.group(1).lower()
            if prefix_val in ("re", "رد", "إعادة"):
                has_re = True
            elif prefix_val in ("fwd", "fw"):
                has_fwd = True
            prefix = prefix_val
            cleaned = cleaned[match.end():].strip()

        cleaned = _RE_WHITESPACE.sub(" ", cleaned)

        return NormalizedSubject(
            raw=decoded,
            cleaned=cleaned,
            has_re=has_re,
            has_fwd=has_fwd,
            prefix=prefix.lower() if prefix else "",
        )
