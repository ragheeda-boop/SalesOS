"""In-memory Evidence repository for testing."""

from __future__ import annotations

from ..contracts.models import Insight, EvidenceItem, InsightCategory, ConfidenceLevel
from ..contracts.repository import EvidenceRepository


class InMemoryEvidenceRepository(EvidenceRepository):

    def __init__(self):
        self._insights: dict[str, Insight] = {}
        self._evidence: dict[str, list[EvidenceItem]] = {}

    async def save_insight(self, insight: Insight) -> Insight:
        self._insights[insight.id] = insight
        return insight

    async def get_insight(self, insight_id: str) -> Insight | None:
        return self._insights.get(insight_id)

    async def list_insights(
        self,
        tenant_id: str,
        target_id: str | None = None,
        target_type: str | None = None,
        category: InsightCategory | None = None,
        limit: int = 50,
    ) -> list[Insight]:
        results = [i for i in self._insights.values() if i.tenant_id == tenant_id]
        if target_id:
            results = [i for i in results if i.target_id == target_id]
        if target_type:
            results = [i for i in results if i.target_type == target_type]
        if category:
            results = [i for i in results if i.category == category]
        return sorted(results, key=lambda x: x.created_at, reverse=True)[:limit]

    async def list_insights_by_confidence(
        self,
        tenant_id: str,
        min_confidence: float = 0.0,
        category: InsightCategory | None = None,
        limit: int = 50,
    ) -> list[Insight]:
        results = [i for i in self._insights.values()
                   if i.tenant_id == tenant_id and i.overall_confidence >= min_confidence]
        if category:
            results = [i for i in results if i.category == category]
        return sorted(results, key=lambda x: x.overall_confidence, reverse=True)[:limit]

    async def save_evidence(self, insight_id: str, evidence: EvidenceItem) -> EvidenceItem:
        if insight_id not in self._evidence:
            self._evidence[insight_id] = []
        self._evidence[insight_id].append(evidence)
        return evidence

    async def list_evidence(self, insight_id: str) -> list[EvidenceItem]:
        return self._evidence.get(insight_id, [])

    async def count_by_category(self, tenant_id: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for insight in self._insights.values():
            if insight.tenant_id == tenant_id:
                key = insight.category.value
                counts[key] = counts.get(key, 0) + 1
        return counts

    async def count_by_confidence(self, tenant_id: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for insight in self._insights.values():
            if insight.tenant_id == tenant_id:
                key = insight.confidence_level.value
                counts[key] = counts.get(key, 0) + 1
        return counts
