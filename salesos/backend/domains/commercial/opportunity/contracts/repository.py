"""OpportunityRepository — persistence and query interface for opportunities."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from .models import Opportunity, OpportunityStatus


@dataclass
class OpportunityQuery:
    """Structured query for filtering opportunities."""

    tenant_id: str = ""
    company_id: str = ""
    owner_id: str = ""
    stage: str = ""
    status: OpportunityStatus | None = None
    min_value: float | None = None
    max_value: float | None = None
    from_date: date | None = None
    to_date: date | None = None
    search: str = ""
    page: int = 1
    page_size: int = 20
    sort_by: str = "updated_at"
    sort_order: str = "desc"


@dataclass
class OpportunityResult:
    items: list[Opportunity] = field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20

    @property
    def total_weighted_value(self) -> float:
        return sum(o.weighted_value for o in self.items)

    @property
    def total_value(self) -> float:
        return sum(o.value for o in self.items)


class OpportunityRepository(ABC):

    @abstractmethod
    async def save(self, opportunity: Opportunity) -> Opportunity: ...

    @abstractmethod
    async def get(self, opportunity_id: str) -> Opportunity | None: ...

    @abstractmethod
    async def query(self, query: OpportunityQuery) -> OpportunityResult: ...

    @abstractmethod
    async def delete(self, opportunity_id: str) -> None: ...

    @abstractmethod
    async def count_by_stage(self, tenant_id: str) -> dict[str, int]: ...

    @abstractmethod
    async def total_value_by_stage(self, tenant_id: str) -> dict[str, float]: ...

    @abstractmethod
    async def win_rate(self, tenant_id: str) -> float:
        """Return win rate as 0.0-1.0 based on historical opportunities."""
