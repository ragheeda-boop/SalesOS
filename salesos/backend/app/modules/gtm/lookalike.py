"""STORY-11-04 — CAP-098 Lookalike Accounts models (OBJ-352 LookalikeModel).

Versioned lookalike model trained on tenant won/lost Opportunity-shaped history.
Not Production GO. DEC-085 untouched. No Alembic / FORCE RLS.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

OutcomeLabel = Literal["won", "lost"]


class LookalikeError(ValueError):
    """Invalid lookalike model or query input."""


@dataclass(frozen=True)
class OpportunityRecord:
    """Minimal Opportunity-shaped row for lookalike training (CI fixture)."""

    id: str
    company_name: str
    industry: str = ""
    city: str = ""
    employees_count: int | None = None
    outcome: str = "won"  # won | lost
    tenant_id: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "company_name": self.company_name,
            "industry": self.industry,
            "city": self.city,
            "employees_count": self.employees_count,
            "outcome": self.outcome,
            "tenant_id": self.tenant_id,
        }


@dataclass
class LookalikeSeed:
    """Seed account to find similar companies for."""

    company_name: str
    industry: str = ""
    city: str = ""
    employees_count: int | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "company_name": self.company_name,
            "industry": self.industry,
            "city": self.city,
            "employees_count": self.employees_count,
        }


@dataclass(frozen=True)
class LookalikeHit:
    company_id: str
    company_name: str
    industry: str = ""
    city: str = ""
    employees_count: int | None = None
    similarity: float = 0.0
    outcome_affinity: str = ""  # won | lost | mixed
    matched_features: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "company_id": self.company_id,
            "company_name": self.company_name,
            "industry": self.industry,
            "city": self.city,
            "employees_count": self.employees_count,
            "similarity": self.similarity,
            "outcome_affinity": self.outcome_affinity,
            "matched_features": list(self.matched_features),
        }


@dataclass
class LookalikeModel:
    """Versioned lookalike model reusable across GTM sessions."""

    id: str
    tenant_id: str
    name: str
    seed: LookalikeSeed
    hits: list[LookalikeHit] = field(default_factory=list)
    trained_on_won: int = 0
    trained_on_lost: int = 0
    schema_version: int = 1
    created_at: str = ""
    updated_at: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "seed": self.seed.as_dict(),
            "hits": [h.as_dict() for h in self.hits],
            "trained_on_won": self.trained_on_won,
            "trained_on_lost": self.trained_on_lost,
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "hit_count": len(self.hits),
        }


def normalize_seed(
    *,
    company_name: str,
    industry: str | None = None,
    city: str | None = None,
    employees_count: int | None = None,
) -> LookalikeSeed:
    name = (company_name or "").strip()
    if not name:
        raise LookalikeError("company_name required")
    emp = employees_count
    if emp is not None and emp < 0:
        raise LookalikeError("employees_count must be >= 0")
    return LookalikeSeed(
        company_name=name,
        industry=(industry or "").strip().lower(),
        city=(city or "").strip().lower(),
        employees_count=emp,
    )
