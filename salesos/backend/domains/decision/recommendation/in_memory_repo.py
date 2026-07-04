from __future__ import annotations
from .models import Recommendation, RecommendationStatus
from .repo import RecommendationRepository


class InMemoryRecommendationRepository(RecommendationRepository):
    def __init__(self):
        self._items: dict[str, Recommendation] = {}

    async def save(self, recommendation: Recommendation) -> Recommendation:
        self._items[recommendation.id] = recommendation
        return recommendation

    async def get(self, recommendation_id: str) -> Recommendation | None:
        return self._items.get(recommendation_id)

    async def list_by_target(self, target_id: str, target_type: str, limit: int = 20) -> list[Recommendation]:
        items = [r for r in self._items.values() if r.target_id == target_id and r.target_type == target_type]
        items.sort(key=lambda r: r.created_at, reverse=True)
        return items[:limit]

    async def list_by_tenant(self, tenant_id: str, status: RecommendationStatus | None = None) -> list[Recommendation]:
        items = [r for r in self._items.values() if r.tenant_id == tenant_id]
        if status:
            items = [r for r in items if r.status == status]
        return items
