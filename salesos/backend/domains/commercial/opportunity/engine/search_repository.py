"""OpportunitySearchRepository — implements SearchRepository[Opportunity].

Reuses the Search Domain. Zero changes to SearchQuery, SearchResult, SearchPlanner.
"""

from __future__ import annotations

from typing import Any

from domains.search.contracts.models import SearchQuery, SearchResult, SearchSort
from domains.search.contracts.repository import SearchRepository
from ..contracts.models import Opportunity, OpportunityStatus
from ..contracts.repository import OpportunityQuery, OpportunityRepository


class OpportunitySearchRepository(SearchRepository[Any]):

    def __init__(self, opportunity_repo: OpportunityRepository):
        self._repo = opportunity_repo

    async def search(self, query: SearchQuery) -> SearchResult[Any]:
        field = query.sort.field if query.sort else "updated_at"
        direction = query.sort.direction if query.sort else "desc"

        opp_query = OpportunityQuery(
            tenant_id=query.tenant_id,
            search=query.query,
            page=query.page,
            page_size=query.page_size,
            sort_by=field,
            sort_order=direction,
        )

        # Map field filters from SearchQuery
        if "company_id" in query.filters:
            opp_query.company_id = query.filters["company_id"]
        if "stage" in query.filters:
            opp_query.stage = query.filters["stage"]
        if "owner_id" in query.filters:
            opp_query.owner_id = query.filters["owner_id"]
        if "status" in query.filters:
            status_map = {"open": OpportunityStatus.OPEN, "won": OpportunityStatus.WON, "lost": OpportunityStatus.LOST}
            opp_query.status = status_map.get(query.filters["status"])

        result = await self._repo.query(opp_query)

        return SearchResult(
            items=result.items,
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            query=query.query,
            strategy="in_memory",
        )

    async def count(self, query: SearchQuery) -> int:
        result = await self.search(query)
        return result.total

    async def facets(self, query: SearchQuery, fields: list[str]) -> dict[str, dict[str, int]]:
        opp_result = await self._repo.query(OpportunityQuery(tenant_id=query.tenant_id, page_size=1))
        all_opps = opp_result.total
        return {"total_opportunities": {"all": all_opps}}

    async def suggest(self, query: SearchQuery, field: str, prefix: str, limit: int = 10) -> list[str]:
        return []
