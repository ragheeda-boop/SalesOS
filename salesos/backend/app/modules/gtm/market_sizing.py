"""STORY-11-02 — CAP-096 Market Sizing (TAM/SAM/SOM) models.

Filters aligned to government company dataset fields (industry/city/employees).
Not Production GO. DEC-085 untouched. No Alembic / FORCE RLS.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Documented scale of Muhide government company universe (prod evidence / board AC).
# Runtime counts come from CompanyUniversePort — do not invent live DB numbers in CI.
GOVERNMENT_DATASET_SCALE_HINT = 141_221


class MarketSizingError(ValueError):
    """Invalid market sizing criteria or compute input."""


@dataclass(frozen=True)
class CompanyRecord:
    """Minimal firmographic row for universe counting (gov dataset shape)."""

    id: str
    industry: str = ""
    city: str = ""
    employees_count: int | None = None
    tenant_id: str = ""


@dataclass
class MarketSizingCriteria:
    """TAM/SAM/SOM filter bands (tenant market definition)."""

    # TAM band — industries (empty = all industries in universe)
    industries: list[str] = field(default_factory=list)
    # SAM band — geography within TAM
    cities: list[str] = field(default_factory=list)
    # SOM band — size fit within SAM
    employees_min: int | None = None
    employees_max: int | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "industries": list(self.industries),
            "cities": list(self.cities),
            "employees_min": self.employees_min,
            "employees_max": self.employees_max,
        }


@dataclass
class MarketSizingSnapshot:
    id: str
    tenant_id: str
    name: str
    criteria: MarketSizingCriteria
    tam: int
    sam: int
    som: int
    universe_size: int
    dataset_scale_hint: int = GOVERNMENT_DATASET_SCALE_HINT
    schema_version: int = 1
    created_at: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "criteria": self.criteria.as_dict(),
            "tam": self.tam,
            "sam": self.sam,
            "som": self.som,
            "universe_size": self.universe_size,
            "dataset_scale_hint": self.dataset_scale_hint,
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            # Honesty: invariant proven; live 141221 requires DB universe adapter.
            "invariant_ok": self.som <= self.sam <= self.tam <= self.universe_size,
        }


def normalize_criteria(
    *,
    industries: list[str] | None = None,
    cities: list[str] | None = None,
    employees_min: int | None = None,
    employees_max: int | None = None,
) -> MarketSizingCriteria:
    inds = [str(x).strip().lower() for x in (industries or []) if str(x).strip()]
    cts = [str(x).strip().lower() for x in (cities or []) if str(x).strip()]
    emin = employees_min
    emax = employees_max
    if emin is not None and emin < 0:
        raise MarketSizingError("employees_min must be >= 0")
    if emax is not None and emax < 0:
        raise MarketSizingError("employees_max must be >= 0")
    if emin is not None and emax is not None and emin > emax:
        raise MarketSizingError("employees_min must be <= employees_max")
    return MarketSizingCriteria(
        industries=inds,
        cities=cts,
        employees_min=emin,
        employees_max=emax,
    )
