"""Resolver — Stage 2 of the Mapping Pipeline (ADR-012 §6).

Extracts entities from normalized communication data:
- Person name from From/To headers
- Company hints from email domain + signature
- Opportunity ID from subject (e.g., "[OPP-123]")
"""

from __future__ import annotations

import re

from intelligence.activity_intelligence.contracts.models import (
    NormalizedAddress,
    RawEmail,
    ResolvedEntities,
)

_SIGNATURE_PATTERNS = [
    r"^(?:Best|Regards|Sincerely|Cheers|Thanks|Thank you|مع تحياتي|تحياتي)[,\s]*$",
    r"^--\s*$",
    r"^_{3,}$",
]


class EntityResolver:
    """Extract entities (person, company, opportunity) from normalized data."""

    def resolve_from_email(
        self,
        raw: RawEmail,
        from_addr: NormalizedAddress,
    ) -> ResolvedEntities:
        """Resolve entities from a normalized email."""
        person_name = self._extract_person_name(from_addr, raw)
        company_hint = self._extract_company_hint(from_addr, raw)
        opportunity_hint = self._extract_opportunity_hint(raw.subject)

        return ResolvedEntities(
            person_name=person_name,
            person_email=from_addr.email,
            company_hint=company_hint or from_addr.domain,
            domain=from_addr.domain,
            opportunity_hint=opportunity_hint,
        )

    def resolve_domain(self, domain: str) -> ResolvedEntities:
        """Resolve entities from just a domain (for calendar events)."""
        return ResolvedEntities(
            domain=domain,
            company_hint=domain,
        )

    def _extract_person_name(
        self, from_addr: NormalizedAddress, raw: RawEmail
    ) -> str | None:
        """Extract person name from email headers."""
        if from_addr.display_name and len(from_addr.display_name) > 1:
            # Check it's not an email address
            if "@" not in from_addr.display_name:
                return from_addr.display_name

        # Try to derive from email local part
        if from_addr.email and "@" in from_addr.email:
            local = from_addr.email.split("@")[0]
            # Convert dots/underscores to spaces and title-case
            name = local.replace(".", " ").replace("_", " ").title()
            if len(name) > 1 and not name.replace(" ", "").isdigit():
                return name

        return None

    def _extract_company_hint(
        self, from_addr: NormalizedAddress, raw: RawEmail
    ) -> str | None:
        """Extract company hint from domain and signature."""
        # Free email providers don't indicate a company
        free_providers = {"gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com"}
        if from_addr.domain in free_providers:
            # Try to extract from email body signature
            sig = self._extract_from_signature(raw.body_text)
            if sig:
                return sig
            return None

        return from_addr.domain

    @staticmethod
    def _extract_opportunity_hint(subject: str) -> str | None:
        """Extract opportunity ID from subject (e.g., '[OPP-123]', 'Re: [OPP-456]')."""
        patterns = [
            r"\[OPP[_-]?(\d+)\]",
            r"\[OPPORTUNITY[_-]?(\d+)\]",
            r"OPP[_-]?(\d+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, subject, re.IGNORECASE)
            if match:
                return f"OPP-{match.group(1)}"
        return None

    def _extract_from_signature(self, body: str) -> str | None:
        """Extract company name from email body signature."""
        if not body:
            return None

        lines = body.strip().split("\n")
        sig_start = None

        # Find where signature starts
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            for pattern in _SIGNATURE_PATTERNS:
                if re.match(pattern, line_stripped, re.IGNORECASE):
                    sig_start = i
                    break
            if sig_start is not None:
                break

        if sig_start is None or sig_start >= len(lines) - 1:
            return None

        # Extract company-like lines from signature (capitalized, no email-like)
        company_pattern = re.compile(
            r"^(?:[A-Z][a-z]+\s?){1,5}(?:LLC|Ltd|Limited|Inc|Corp|Corporation|Co\.?|"
            r"شركة|مؤسسة|مجموعة|للخدمات|للإستشارات)"
        )
        for line in lines[sig_start + 1:]:
            stripped = line.strip()
            if not stripped or "@" in stripped:
                continue
            if company_pattern.search(stripped):
                return stripped
            # Any line that looks like a company name with at least 2 words
            words = stripped.split()
            if (
                len(words) >= 2
                and not stripped.startswith("http")
                and len(stripped) > 3
                and not stripped[0].islower()
                and "@" not in stripped
            ):
                return stripped

        return None
