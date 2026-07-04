from __future__ import annotations
from abc import ABC, abstractmethod
from .models import Recommendation, RecommendationStatus


class RecommendationRepository(ABC):
    @abstractmethod
    async def save(self, recommendation: Recommendation) -> Recommendation:
        ...

    @abstractmethod
    async def get(self, recommendation_id: str) -> Recommendation | None:
        ...

    @abstractmethod
    async def list_by_target(self, target_id: str, target_type: str, limit: int = 20) -> list[Recommendation]:
        ...

    @abstractmethod
    async def list_by_tenant(self, tenant_id: str, status: RecommendationStatus | None = None) -> list[Recommendation]:
        ...
