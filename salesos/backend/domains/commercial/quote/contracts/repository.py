"""QuoteRepository — persistence for quotes, revisions, and revenue KPIs."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from .models import Quote, QuoteStatus


@dataclass
class QuoteRevenueKPIs:
    total_quote_value: float = 0.0
    total_discount_amount: float = 0.0
    average_discount_percent: float = 0.0
    approval_rate: float = 0.0
    acceptance_rate: float = 0.0
    quote_to_win_conversion: float = 0.0
    open_pipeline_value: float = 0.0
    total_quotes: int = 0
    accepted_quotes: int = 0
    rejected_quotes: int = 0
    expired_quotes: int = 0


class QuoteRepository(ABC):

    @abstractmethod
    async def save(self, quote: Quote) -> Quote: ...

    @abstractmethod
    async def get(self, quote_id: str) -> Quote | None: ...

    @abstractmethod
    async def get_by_opportunity(self, opportunity_id: str) -> list[Quote]: ...

    @abstractmethod
    async def list_by_tenant(self, tenant_id: str, status: QuoteStatus | None = None) -> list[Quote]: ...

    @abstractmethod
    async def count_by_status(self, tenant_id: str) -> dict[str, int]: ...

    @abstractmethod
    async def revenue_kpis(self, tenant_id: str) -> QuoteRevenueKPIs: ...
