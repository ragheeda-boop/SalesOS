"""EvidenceService — business logic for evidence chain management.

Handles:
- Recording insights backed by evidence
- Adding evidence items to insights
- Querying insights by category, confidence, target
- Recomputing confidence from evidence
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from ..contracts.models import (
    Insight, InsightCategory, EvidenceItem, EvidenceType,
    EvidenceSource, ConfidenceLevel,
)
from ..contracts.repository import EvidenceRepository


class EvidenceService:

    def __init__(self, repository: EvidenceRepository, event_bus: Any = None):
        self._repository = repository
        self._event_bus = event_bus

    async def _emit(self, event_type: str, tenant_id: str, data: dict[str, Any]) -> None:
        if not self._event_bus:
            return
        from sdk.events.base import DomainEvent
        event = DomainEvent(
            event_type=event_type, tenant_id=tenant_id,
            aggregate_id=data.get("insight_id", ""), data=data,
        )
        event.event_type = event_type
        await self._event_bus.publish(event)

    async def record_insight(
        self,
        tenant_id: str,
        category: InsightCategory,
        title: str,
        description: str,
        target_id: str,
        target_type: str,
        evidence_items: list[EvidenceItem] | None = None,
        metadata: dict | None = None,
    ) -> Insight:
        """Record a new insight with optional evidence items."""
        insight = Insight(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            category=category,
            title=title,
            description=description,
            target_id=target_id,
            target_type=target_type,
            overall_confidence=0.0,
            confidence_level=ConfidenceLevel.UNKNOWN,
            evidence_items=evidence_items or [],
            metadata=metadata or {},
        )
        insight.recompute_confidence()
        result = await self._repository.save_insight(insight)
        await self._emit("insight.recorded", tenant_id, {
            "insight_id": insight.id, "category": category.value,
            "target_id": target_id, "target_type": target_type,
            "confidence": insight.overall_confidence,
        })
        return result

    async def add_evidence(
        self,
        insight_id: str,
        evidence_type: EvidenceType,
        source_domain: str,
        source_type: str,
        description: str,
        confidence: float,
        source_id: str = "",
        source_name: str = "",
        data: dict | None = None,
    ) -> EvidenceItem:
        """Add a piece of evidence to an existing insight."""
        insight = await self._repository.get_insight(insight_id)
        if not insight:
            raise ValueError(f"Insight {insight_id} not found")

        level = self._confidence_level(confidence)
        evidence = EvidenceItem(
            id=str(uuid.uuid4()),
            evidence_type=evidence_type,
            source=EvidenceSource(
                source_domain=source_domain,
                source_type=source_type,
                source_id=source_id,
                source_name=source_name,
            ),
            description=description,
            confidence=confidence,
            confidence_level=level,
            data=data or {},
        )
        await self._repository.save_evidence(insight_id, evidence)
        insight.evidence_items.append(evidence)
        insight.recompute_confidence()
        insight.updated_at = datetime.now(timezone.utc)
        await self._repository.save_insight(insight)
        return evidence

    async def get_insight(self, insight_id: str) -> Insight | None:
        return await self._repository.get_insight(insight_id)

    async def list_insights(
        self,
        tenant_id: str,
        target_id: str | None = None,
        target_type: str | None = None,
        category: InsightCategory | None = None,
        limit: int = 50,
    ) -> list[Insight]:
        return await self._repository.list_insights(
            tenant_id, target_id, target_type, category, limit,
        )

    async def list_high_confidence(
        self,
        tenant_id: str,
        category: InsightCategory | None = None,
        limit: int = 20,
    ) -> list[Insight]:
        return await self._repository.list_insights_by_confidence(
            tenant_id, min_confidence=0.8, category=category, limit=limit,
        )

    async def kpis(self, tenant_id: str) -> dict:
        category_counts = await self._repository.count_by_category(tenant_id)
        confidence_counts = await self._repository.count_by_confidence(tenant_id)
        total = sum(category_counts.values())
        return {
            "total": total,
            "by_category": category_counts,
            "by_confidence": confidence_counts,
            "high_confidence": confidence_counts.get("high", 0),
        }

    @staticmethod
    def _confidence_level(confidence: float) -> ConfidenceLevel:
        if confidence >= 0.8:
            return ConfidenceLevel.HIGH
        elif confidence >= 0.5:
            return ConfidenceLevel.MEDIUM
        elif confidence >= 0.2:
            return ConfidenceLevel.LOW
        return ConfidenceLevel.UNKNOWN
