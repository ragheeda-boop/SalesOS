"""STORY-11-05 — CAP-099 Enrichment Waterfall models.

Multi-provider orchestration with swappable Integration Hub providers.
Not Production GO. DEC-085 untouched. No Alembic / FORCE RLS.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class EnrichmentError(ValueError):
    """Invalid enrichment request or waterfall input."""


# Fields the waterfall may fill (commodity firmographic + contact cues).
ENRICHABLE_FIELDS: tuple[str, ...] = (
    "industry",
    "city",
    "employees_count",
    "website",
    "phone",
    "email",
)


@dataclass
class EnrichmentRequest:
    """Input seed for waterfall enrichment."""

    company_name: str
    domain: str = ""
    external_id: str = ""
    # Known values — waterfall only fills blanks.
    known: dict[str, Any] = field(default_factory=dict)
    # Optional provider priority override (provider_key list).
    provider_order: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "company_name": self.company_name,
            "domain": self.domain,
            "external_id": self.external_id,
            "known": dict(self.known),
            "provider_order": list(self.provider_order),
        }


@dataclass(frozen=True)
class EnrichmentFieldHit:
    field: str
    value: Any
    provider_key: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "field": self.field,
            "value": self.value,
            "provider_key": self.provider_key,
        }


@dataclass
class EnrichmentResult:
    """Waterfall outcome for one enrichment run."""

    id: str
    tenant_id: str
    request: EnrichmentRequest
    filled: dict[str, Any] = field(default_factory=dict)
    hits: list[EnrichmentFieldHit] = field(default_factory=list)
    providers_attempted: list[str] = field(default_factory=list)
    providers_configured: list[str] = field(default_factory=list)
    missing_fields: list[str] = field(default_factory=list)
    schema_version: int = 1
    created_at: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "request": self.request.as_dict(),
            "filled": dict(self.filled),
            "hits": [h.as_dict() for h in self.hits],
            "providers_attempted": list(self.providers_attempted),
            "providers_configured": list(self.providers_configured),
            "missing_fields": list(self.missing_fields),
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "complete": len(self.missing_fields) == 0,
        }


def normalize_request(
    *,
    company_name: str,
    domain: str | None = None,
    external_id: str | None = None,
    known: dict[str, Any] | None = None,
    provider_order: list[str] | None = None,
) -> EnrichmentRequest:
    name = (company_name or "").strip()
    if not name:
        raise EnrichmentError("company_name required")
    known_clean: dict[str, Any] = {}
    for key, val in (known or {}).items():
        k = str(key).strip()
        if k not in ENRICHABLE_FIELDS:
            continue
        if val is None or val == "":
            continue
        known_clean[k] = val
    order = [str(x).strip() for x in (provider_order or []) if str(x).strip()]
    return EnrichmentRequest(
        company_name=name,
        domain=(domain or "").strip().lower(),
        external_id=(external_id or "").strip(),
        known=known_clean,
        provider_order=order,
    )
