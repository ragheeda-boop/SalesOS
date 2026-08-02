"""STORY-11-02 — Company universe port + TAM/SAM/SOM compute.

Counts against a pluggable universe (mem fixture in CI; Postgres adapter later).
Invariant: SOM ≤ SAM ≤ TAM ≤ universe_size.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from app.modules.gtm.market_sizing import (
    CompanyRecord,
    MarketSizingCriteria,
    MarketSizingError,
)


class CompanyUniversePort(Protocol):
    def universe_size(self, *, tenant_id: str | None = None) -> int: ...

    def count(
        self,
        *,
        tenant_id: str | None = None,
        industries: list[str] | None = None,
        cities: list[str] | None = None,
        employees_min: int | None = None,
        employees_max: int | None = None,
    ) -> int: ...


def _norm(value: str) -> str:
    return (value or "").strip().lower()


def _match_record(
    row: CompanyRecord,
    *,
    industries: list[str] | None,
    cities: list[str] | None,
    employees_min: int | None,
    employees_max: int | None,
) -> bool:
    if industries:
        if _norm(row.industry) not in industries:
            return False
    if cities:
        if _norm(row.city) not in cities:
            return False
    if employees_min is not None or employees_max is not None:
        emp = row.employees_count
        if emp is None:
            return False
        if employees_min is not None and emp < employees_min:
            return False
        if employees_max is not None and emp > employees_max:
            return False
    return True


@dataclass
class MemCompanyUniverse:
    """In-memory government-dataset-shaped universe for CAP-096 tests/CI."""

    records: list[CompanyRecord] = field(default_factory=list)

    def universe_size(self, *, tenant_id: str | None = None) -> int:
        if tenant_id:
            return sum(1 for r in self.records if not r.tenant_id or r.tenant_id == tenant_id)
        return len(self.records)

    def count(
        self,
        *,
        tenant_id: str | None = None,
        industries: list[str] | None = None,
        cities: list[str] | None = None,
        employees_min: int | None = None,
        employees_max: int | None = None,
    ) -> int:
        inds = [_norm(x) for x in (industries or []) if str(x).strip()]
        cts = [_norm(x) for x in (cities or []) if str(x).strip()]
        n = 0
        for row in self.records:
            if tenant_id and row.tenant_id and row.tenant_id != tenant_id:
                continue
            if _match_record(
                row,
                industries=inds or None,
                cities=cts or None,
                employees_min=employees_min,
                employees_max=employees_max,
            ):
                n += 1
        return n


@dataclass(frozen=True)
class MarketSizingResult:
    tam: int
    sam: int
    som: int
    universe_size: int

    @property
    def invariant_ok(self) -> bool:
        return self.som <= self.sam <= self.tam <= self.universe_size


def compute_tam_sam_som(
    criteria: MarketSizingCriteria,
    universe: CompanyUniversePort,
    *,
    tenant_id: str | None = None,
) -> MarketSizingResult:
    """Compute TAM ⊇ SAM ⊇ SOM counts against company universe."""
    if not isinstance(criteria, MarketSizingCriteria):
        raise MarketSizingError("criteria required")

    universe_size = int(universe.universe_size(tenant_id=tenant_id))

    # TAM: industry band (or full universe when industries empty)
    tam = int(
        universe.count(
            tenant_id=tenant_id,
            industries=list(criteria.industries) or None,
        )
    )

    # SAM: TAM ∩ cities (if cities empty, SAM == TAM)
    sam = int(
        universe.count(
            tenant_id=tenant_id,
            industries=list(criteria.industries) or None,
            cities=list(criteria.cities) or None,
        )
    )

    # SOM: SAM ∩ employee fit
    som = int(
        universe.count(
            tenant_id=tenant_id,
            industries=list(criteria.industries) or None,
            cities=list(criteria.cities) or None,
            employees_min=criteria.employees_min,
            employees_max=criteria.employees_max,
        )
    )

    result = MarketSizingResult(tam=tam, sam=sam, som=som, universe_size=universe_size)
    if not result.invariant_ok:
        raise MarketSizingError(
            f"invariant broken: SOM={som} SAM={sam} TAM={tam} universe={universe_size}"
        )
    return result
