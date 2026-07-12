"""SDK interfaces for company/commercial cross-domain boundary.

The Company module depends on this interface instead of importing
directly from the Commercial domain (ISP + DIP).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CompanyOpportunityQuery:
    """Structured query for company-scoped opportunities."""

    tenant_id: str = ""
    company_id: str = ""
    page: int = 1
    page_size: int = 20


class CompanyOpportunityService(ABC):
    """Interface for querying opportunities scoped to a company."""

    @abstractmethod
    async def query_opportunities(
        self, query: CompanyOpportunityQuery
    ) -> Any:
        ...
