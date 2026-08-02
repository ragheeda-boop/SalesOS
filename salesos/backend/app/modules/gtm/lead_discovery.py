"""STORY-11-03 — CAP-097 Lead Discovery models.

Government-data-first sourcing with Integration Hub provider fallback.
Not Production GO. DEC-085 untouched. No Alembic / FORCE RLS.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.modules.gtm.market_sizing import GOVERNMENT_DATASET_SCALE_HINT

SOURCE_GOVERNMENT = "government"
SOURCE_PROVIDER_PREFIX = "provider:"


class LeadDiscoveryError(ValueError):
    """Invalid lead discovery query or run input."""


@dataclass
class LeadDiscoveryQuery:
    """Firmographic discovery band (aligned to gov-dataset-shaped fields)."""

    industries: list[str] = field(default_factory=list)
    cities: list[str] = field(default_factory=list)
    employees_min: int | None = None
    employees_max: int | None = None
    limit: int = 25

    def as_dict(self) -> dict[str, Any]:
        return {
            "industries": list(self.industries),
            "cities": list(self.cities),
            "employees_min": self.employees_min,
            "employees_max": self.employees_max,
            "limit": self.limit,
        }


@dataclass(frozen=True)
class DiscoveredLead:
    """Single sourced lead hit (gov or external provider)."""

    id: str
    company_name: str
    industry: str = ""
    city: str = ""
    employees_count: int | None = None
    source: str = SOURCE_GOVERNMENT
    external_id: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "company_name": self.company_name,
            "industry": self.industry,
            "city": self.city,
            "employees_count": self.employees_count,
            "source": self.source,
            "external_id": self.external_id,
        }


@dataclass
class LeadDiscoveryRun:
    """Tenant-scoped discovery run result."""

    id: str
    tenant_id: str
    name: str
    query: LeadDiscoveryQuery
    leads: list[DiscoveredLead] = field(default_factory=list)
    government_hit_count: int = 0
    provider_hit_count: int = 0
    provider_key: str = ""
    dataset_scale_hint: int = GOVERNMENT_DATASET_SCALE_HINT
    schema_version: int = 1
    created_at: str = ""

    @property
    def government_first_ok(self) -> bool:
        """Gov hits precede provider hits in the returned lead list."""
        seen_provider = False
        for lead in self.leads:
            if lead.source.startswith(SOURCE_PROVIDER_PREFIX):
                seen_provider = True
            elif lead.source == SOURCE_GOVERNMENT and seen_provider:
                return False
        return True

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "query": self.query.as_dict(),
            "leads": [lead.as_dict() for lead in self.leads],
            "government_hit_count": self.government_hit_count,
            "provider_hit_count": self.provider_hit_count,
            "provider_key": self.provider_key,
            "dataset_scale_hint": self.dataset_scale_hint,
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "government_first_ok": self.government_first_ok,
            "total_hits": len(self.leads),
        }


def normalize_query(
    *,
    industries: list[str] | None = None,
    cities: list[str] | None = None,
    employees_min: int | None = None,
    employees_max: int | None = None,
    limit: int | None = None,
) -> LeadDiscoveryQuery:
    inds = [str(x).strip().lower() for x in (industries or []) if str(x).strip()]
    cts = [str(x).strip().lower() for x in (cities or []) if str(x).strip()]
    emin = employees_min
    emax = employees_max
    if emin is not None and emin < 0:
        raise LeadDiscoveryError("employees_min must be >= 0")
    if emax is not None and emax < 0:
        raise LeadDiscoveryError("employees_max must be >= 0")
    if emin is not None and emax is not None and emin > emax:
        raise LeadDiscoveryError("employees_min must be <= employees_max")
    lim = 25 if limit is None else int(limit)
    if lim < 1 or lim > 200:
        raise LeadDiscoveryError("limit must be between 1 and 200")
    return LeadDiscoveryQuery(
        industries=inds,
        cities=cts,
        employees_min=emin,
        employees_max=emax,
        limit=lim,
    )


def provider_source_label(provider_key: str) -> str:
    key = (provider_key or "unknown").strip() or "unknown"
    return f"{SOURCE_PROVIDER_PREFIX}{key}"
