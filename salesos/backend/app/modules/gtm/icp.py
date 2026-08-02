"""STORY-11-01 — CAP-095 ICP Engine models (OBJ-350 ICPProfile).

Versioned, reusable ICP profiles (not one-off prompts).
Not Production GO. DEC-085 untouched. No Alembic / FORCE RLS.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class ICPError(ValueError):
    """Invalid ICP profile or score input."""


@dataclass
class ICPCriteria:
    """Firmographic ICP band (aligned to gov-dataset-shaped fields)."""

    industries: list[str] = field(default_factory=list)
    cities: list[str] = field(default_factory=list)
    employees_min: int | None = None
    employees_max: int | None = None
    # Optional free-text persona cues (titles / keywords) — not ML embeddings.
    titles: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "industries": list(self.industries),
            "cities": list(self.cities),
            "employees_min": self.employees_min,
            "employees_max": self.employees_max,
            "titles": list(self.titles),
            "keywords": list(self.keywords),
        }


@dataclass
class ICPWeights:
    """Relative weights for deterministic fit scoring (sum need not be 1)."""

    industry: float = 1.0
    city: float = 1.0
    employees: float = 1.0
    titles: float = 0.5
    keywords: float = 0.5

    def as_dict(self) -> dict[str, Any]:
        return {
            "industry": self.industry,
            "city": self.city,
            "employees": self.employees,
            "titles": self.titles,
            "keywords": self.keywords,
        }


@dataclass
class ICPProfile:
    """Versioned ICP definition reusable across GTM sessions."""

    id: str
    tenant_id: str
    name: str
    criteria: ICPCriteria
    weights: ICPWeights = field(default_factory=ICPWeights)
    description: str = ""
    schema_version: int = 1
    is_active: bool = True
    created_at: str = ""
    updated_at: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "description": self.description,
            "criteria": self.criteria.as_dict(),
            "weights": self.weights.as_dict(),
            "schema_version": self.schema_version,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


def _norm_list(values: list[str] | None) -> list[str]:
    return [str(x).strip().lower() for x in (values or []) if str(x).strip()]


def normalize_criteria(
    *,
    industries: list[str] | None = None,
    cities: list[str] | None = None,
    employees_min: int | None = None,
    employees_max: int | None = None,
    titles: list[str] | None = None,
    keywords: list[str] | None = None,
) -> ICPCriteria:
    emin = employees_min
    emax = employees_max
    if emin is not None and emin < 0:
        raise ICPError("employees_min must be >= 0")
    if emax is not None and emax < 0:
        raise ICPError("employees_max must be >= 0")
    if emin is not None and emax is not None and emin > emax:
        raise ICPError("employees_min must be <= employees_max")
    return ICPCriteria(
        industries=_norm_list(industries),
        cities=_norm_list(cities),
        employees_min=emin,
        employees_max=emax,
        titles=_norm_list(titles),
        keywords=_norm_list(keywords),
    )


def normalize_weights(
    *,
    industry: float | None = None,
    city: float | None = None,
    employees: float | None = None,
    titles: float | None = None,
    keywords: float | None = None,
) -> ICPWeights:
    w = ICPWeights(
        industry=1.0 if industry is None else float(industry),
        city=1.0 if city is None else float(city),
        employees=1.0 if employees is None else float(employees),
        titles=0.5 if titles is None else float(titles),
        keywords=0.5 if keywords is None else float(keywords),
    )
    for label, val in w.as_dict().items():
        if val < 0:
            raise ICPError(f"weight {label} must be >= 0")
    return w
