"""Evidence repository — abstract interface for evidence persistence."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from .models import Insight, EvidenceItem, InsightCategory, ConfidenceLevel


class EvidenceRepository(ABC):

    @abstractmethod
    async def save_insight(self, insight: Insight) -> Insight:
        ...

    @abstractmethod
    async def get_insight(self, insight_id: str) -> Insight | None:
        ...

    @abstractmethod
    async def list_insights(
        self,
        tenant_id: str,
        target_id: str | None = None,
        target_type: str | None = None,
        category: InsightCategory | None = None,
        limit: int = 50,
    ) -> list[Insight]:
        ...

    @abstractmethod
    async def list_insights_by_confidence(
        self,
        tenant_id: str,
        min_confidence: float = 0.0,
        category: InsightCategory | None = None,
        limit: int = 50,
    ) -> list[Insight]:
        ...

    @abstractmethod
    async def save_evidence(self, insight_id: str, evidence: EvidenceItem) -> EvidenceItem:
        ...

    @abstractmethod
    async def list_evidence(self, insight_id: str) -> list[EvidenceItem]:
        ...

    @abstractmethod
    async def count_by_category(self, tenant_id: str) -> dict[str, int]:
        ...

    @abstractmethod
    async def count_by_confidence(self, tenant_id: str) -> dict[str, int]:
        ...
