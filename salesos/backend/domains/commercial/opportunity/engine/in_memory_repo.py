"""In-memory opportunity repository for testing and development."""

from __future__ import annotations

from datetime import date

from ..contracts.models import Opportunity, OpportunityStatus
from ..contracts.repository import OpportunityQuery, OpportunityRepository, OpportunityResult


class InMemoryOpportunityRepository(OpportunityRepository):

    def __init__(self):
        self._opportunities: dict[str, Opportunity] = {}

    async def save(self, opportunity: Opportunity) -> Opportunity:
        self._opportunities[opportunity.id] = opportunity
        return opportunity

    async def get(self, opportunity_id: str) -> Opportunity | None:
        return self._opportunities.get(opportunity_id)

    async def query(self, query: OpportunityQuery) -> OpportunityResult:
        items = list(self._opportunities.values())

        if query.tenant_id:
            items = [o for o in items if o.tenant_id == query.tenant_id]
        if query.company_id:
            items = [o for o in items if o.company_id == query.company_id]
        if query.owner_id:
            items = [o for o in items if o.owner_id == query.owner_id]
        if query.stage:
            items = [o for o in items if o.stage == query.stage]
        if query.status:
            items = [o for o in items if o.status == query.status]
        if query.min_value is not None:
            items = [o for o in items if o.value >= query.min_value]
        if query.max_value is not None:
            items = [o for o in items if o.value <= query.max_value]
        if query.search:
            q = query.search.lower()
            items = [o for o in items if q in o.name.lower() or q in o.description.lower()]

        sort_map = {
            "value": lambda o: o.value,
            "probability": lambda o: o.probability,
            "stage": lambda o: o.stage,
            "created_at": lambda o: o.created_at,
            "updated_at": lambda o: o.updated_at,
            "expected_close_date": lambda o: o.expected_close_date or date.min,
        }
        key_fn = sort_map.get(query.sort_by, lambda o: o.updated_at)
        items.sort(key=key_fn, reverse=(query.sort_order == "desc"))

        total = len(items)
        start = (query.page - 1) * query.page_size
        end = start + query.page_size
        return OpportunityResult(items=items[start:end], total=total, page=query.page, page_size=query.page_size)

    async def delete(self, opportunity_id: str) -> None:
        self._opportunities.pop(opportunity_id, None)

    async def count_by_stage(self, tenant_id: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for o in self._opportunities.values():
            if o.tenant_id == tenant_id:
                counts[o.stage] = counts.get(o.stage, 0) + 1
        return counts

    async def total_value_by_stage(self, tenant_id: str) -> dict[str, float]:
        totals: dict[str, float] = {}
        for o in self._opportunities.values():
            if o.tenant_id == tenant_id:
                totals[o.stage] = totals.get(o.stage, 0.0) + o.value
        return totals

    async def win_rate(self, tenant_id: str) -> float:
        total = 0
        won = 0
        for o in self._opportunities.values():
            if o.tenant_id == tenant_id and o.is_terminal:
                total += 1
                if o.status == OpportunityStatus.WON:
                    won += 1
        return won / total if total > 0 else 0.0
