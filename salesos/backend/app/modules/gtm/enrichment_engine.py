"""STORY-11-05 — Enrichment providers + waterfall (CAP-099).

≥2 swappable providers behind Integration Hub-shaped ports.
Not Production GO. DEC-085 untouched.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from app.modules.gtm.enrichment import (
    ENRICHABLE_FIELDS,
    EnrichmentError,
    EnrichmentFieldHit,
    EnrichmentRequest,
)


@runtime_checkable
class EnrichmentProvider(Protocol):
    """Swappable enrichment adapter (Integration Hub commodity port)."""

    @property
    def provider_key(self) -> str:
        """Stable provider id (e.g. ``fake_a``, ``fake_b``) — not a secret."""
        ...

    async def enrich_partial(
        self,
        *,
        request: EnrichmentRequest,
        missing_fields: list[str],
    ) -> dict[str, Any]:
        """Return subset of missing_fields this provider can fill."""
        ...


@dataclass
class MemEnrichmentProvider:
    """In-memory fake provider with a fixed catalog (CI / pilot scaffolding)."""

    key: str
    # domain or company_name (lower) → field → value
    catalog: dict[str, dict[str, Any]] = field(default_factory=dict)
    # Fields this provider is allowed to answer (swap-in commodity surface).
    supported_fields: tuple[str, ...] = ENRICHABLE_FIELDS

    @property
    def provider_key(self) -> str:
        return self.key

    async def enrich_partial(
        self,
        *,
        request: EnrichmentRequest,
        missing_fields: list[str],
    ) -> dict[str, Any]:
        needle = (request.domain or request.company_name or "").strip().lower()
        row = self.catalog.get(needle, {})
        if not row and request.company_name:
            row = self.catalog.get(request.company_name.strip().lower(), {})
        out: dict[str, Any] = {}
        allowed = set(self.supported_fields)
        for f in missing_fields:
            if f not in allowed:
                continue
            if f in row and row[f] is not None and row[f] != "":
                out[f] = row[f]
        return out


def build_default_providers() -> list[EnrichmentProvider]:
    """Two swappable fakes — A covers firmographics, B covers contact."""
    provider_a = MemEnrichmentProvider(
        key="fake_a",
        supported_fields=("industry", "city", "employees_count", "website"),
        catalog={
            "acme.sa": {
                "industry": "technology",
                "city": "riyadh",
                "employees_count": 120,
                "website": "https://acme.sa",
            },
            "acme": {
                "industry": "technology",
                "city": "riyadh",
                "employees_count": 120,
                "website": "https://acme.sa",
            },
        },
    )
    provider_b = MemEnrichmentProvider(
        key="fake_b",
        supported_fields=("phone", "email", "city"),
        catalog={
            "acme.sa": {
                "phone": "+966500000001",
                "email": "hello@acme.sa",
                "city": "jeddah",  # should not override if A already filled city
            },
            "acme": {
                "phone": "+966500000001",
                "email": "hello@acme.sa",
                "city": "jeddah",
            },
        },
    )
    return [provider_a, provider_b]


async def run_waterfall(
    request: EnrichmentRequest,
    providers: list[EnrichmentProvider],
) -> tuple[dict[str, Any], list[EnrichmentFieldHit], list[str], list[str]]:
    """Try providers in order; first non-empty value wins per field."""
    if not isinstance(request, EnrichmentRequest):
        raise EnrichmentError("request required")
    if len(providers) < 2:
        raise EnrichmentError("at least 2 enrichment providers required")

    by_key = {p.provider_key: p for p in providers}
    configured = [p.provider_key for p in providers]
    if request.provider_order:
        ordered: list[EnrichmentProvider] = []
        for key in request.provider_order:
            if key in by_key:
                ordered.append(by_key[key])
        for p in providers:
            if p.provider_key not in {x.provider_key for x in ordered}:
                ordered.append(p)
    else:
        ordered = list(providers)

    filled: dict[str, Any] = {k: v for k, v in request.known.items() if k in ENRICHABLE_FIELDS}
    hits: list[EnrichmentFieldHit] = []
    attempted: list[str] = []

    for provider in ordered:
        missing = [f for f in ENRICHABLE_FIELDS if f not in filled]
        if not missing:
            break
        attempted.append(provider.provider_key)
        partial = await provider.enrich_partial(request=request, missing_fields=missing)
        for field_name, value in partial.items():
            if field_name in filled:
                continue
            if field_name not in ENRICHABLE_FIELDS:
                continue
            if value is None or value == "":
                continue
            filled[field_name] = value
            hits.append(
                EnrichmentFieldHit(
                    field=field_name,
                    value=value,
                    provider_key=provider.provider_key,
                )
            )

    return filled, hits, attempted, configured
