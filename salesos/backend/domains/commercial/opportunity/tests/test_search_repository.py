from __future__ import annotations

import pytest

from domains.commercial.opportunity.contracts.models import Opportunity, OpportunityStatus
from domains.commercial.opportunity.contracts.repository import OpportunityResult
from domains.commercial.opportunity.engine.search_repository import OpportunitySearchRepository
from domains.search.contracts.models import SearchQuery


class FakeOpportunityRepository:
    def __init__(self, items: list[Opportunity]):
        self.items = items
        self.last_query = None

    async def query(self, query):
        self.last_query = query
        return OpportunityResult(items=self.items, total=len(self.items))


def _opportunity(**overrides) -> Opportunity:
    defaults = {
        "id": "opp-1",
        "tenant_id": "tenant-a",
        "company_id": "company-a",
        "name": "Riyadh renewal",
        "stage": "proposal",
        "owner_id": "seller-a",
        "status": OpportunityStatus.OPEN,
    }
    return Opportunity(**(defaults | overrides))


@pytest.mark.asyncio
async def test_suggest_returns_unique_prefix_matches_from_tenant_query():
    repo = FakeOpportunityRepository(
        [
            _opportunity(id="1", name="Riyadh renewal"),
            _opportunity(id="2", name="riyadh renewal"),
            _opportunity(id="3", name="Jeddah expansion"),
        ]
    )
    adapter = OpportunitySearchRepository(repo)

    values = await adapter.suggest(SearchQuery(tenant_id="tenant-a"), "name", "riy", limit=10)

    assert values == ["Riyadh renewal"]
    assert repo.last_query.tenant_id == "tenant-a"
    assert repo.last_query.search == ""


@pytest.mark.asyncio
async def test_suggest_supports_stage_and_rejects_unknown_fields():
    repo = FakeOpportunityRepository(
        [
            _opportunity(id="1", stage="proposal"),
            _opportunity(id="2", stage="prospecting"),
        ]
    )
    adapter = OpportunitySearchRepository(repo)
    query = SearchQuery(tenant_id="tenant-a")

    assert await adapter.suggest(query, "stage", "pro", limit=1) == ["proposal"]
    assert await adapter.suggest(query, "metadata", "", limit=10) == []
    assert await adapter.suggest(query, "name", "", limit=0) == []
