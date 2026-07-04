from typing import Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from ..business_objects import BusinessObject, EntityType
from ..signals import BuyingSignal, Recommendation
from ..company import CompanyIntelligenceEngine


class TwinState(str, Enum):
    INITIALIZING = "initializing"
    ACTIVE = "active"
    STALE = "stale"
    SLEEPING = "sleeping"
    ERROR = "error"


@dataclass
class TwinMetrics:
    last_sync: Optional[datetime] = None
    update_count: int = 0
    signal_count: int = 0
    recommendation_count: int = 0
    insights_count: int = 0
    errors_count: int = 0


class DigitalTwin:
    """
    A living digital twin of a business entity.
    Not a record - a continuously updating model that
    ingests data, detects signals, generates insights, and predicts behavior.
    """

    def __init__(self, business_object: BusinessObject):
        self.business_object = business_object
        self.state = TwinState.INITIALIZING
        self.metrics = TwinMetrics()
        self._insights: list[dict[str, Any]] = []
        self._state_history: list[dict[str, Any]] = []
        self.created_at = datetime.utcnow()
        self.last_updated = datetime.utcnow()

    @property
    def id(self) -> str:
        return self.business_object.id

    @property
    def name(self) -> str:
        return self.business_object.display_name

    def update(self, data: dict[str, Any], source: str = "internal") -> None:
        """Update the twin with new data."""
        for key, value in data.items():
            if key in ["name_ar", "name_en", "description", "website", "status"]:
                setattr(self.business_object.profile, key, value)
            else:
                self.business_object.profile.data[key] = value

        self.metrics.update_count += 1
        self.last_updated = datetime.utcnow()
        self.state = TwinState.ACTIVE

        self._state_history.append({
            "timestamp": self.last_updated,
            "source": source,
            "fields": list(data.keys()),
        })

    def add_signal(self, signal: BuyingSignal) -> None:
        self.business_object.signals.append(signal)
        self.metrics.signal_count += 1

    def add_recommendation(self, rec: Recommendation) -> None:
        if rec not in self.business_object.recommendations.next_best_actions:
            self.business_object.recommendations.next_best_actions.append(
                {"id": rec.id, "title": rec.title, "priority": rec.priority.value}
            )
        self.metrics.recommendation_count += 1

    def add_insight(self, insight: dict[str, Any]) -> None:
        self._insights.append(insight)
        self.metrics.insights_count += 1

    def get_insights(self, limit: int = 10) -> list[dict[str, Any]]:
        return sorted(self._insights, key=lambda x: x.get("timestamp", 0), reverse=True)[:limit]

    def get_snapshot(self) -> dict[str, Any]:
        """Get a complete snapshot of the twin's current state."""
        bo = self.business_object
        return {
            "id": bo.id,
            "entity_type": bo.entity_type.value,
            "name": bo.display_name,
            "state": self.state.value,
            "profile": {
                "name_ar": bo.profile.name_ar,
                "name_en": bo.profile.name_en,
                "description": bo.profile.description,
                "website": bo.profile.website,
                "status": bo.profile.status,
                "data_fields": len(bo.profile.data),
            },
            "intelligence": {
                "signals": self.metrics.signal_count,
                "recommendations": self.metrics.recommendation_count,
                "insights": self.metrics.insights_count,
                "data_completeness": bo.knowledge.data_quality_score,
                "ai_confidence": bo.ai.ai_confidence,
            },
            "relationships": {
                "count": bo.graph.relationship_count,
                "depth": bo.graph.depth,
            },
            "knowledge": {
                "key_facts": len(bo.knowledge.key_facts),
                "recent_events": len(bo.knowledge.recent_events),
                "sources": bo.knowledge.source_count,
            },
            "twin_metrics": {
                "age_hours": round((datetime.utcnow() - self.created_at).total_seconds() / 3600, 1),
                "updates": self.metrics.update_count,
                "last_updated": self.last_updated,
                "state": self.state.value,
            },
        }

    def health_check(self) -> dict[str, Any]:
        """Check twin health."""
        bo = self.business_object
        completeness = bo.knowledge.data_quality_score
        signal_health = min(self.metrics.signal_count * 10, 100)
        update_health = min(self.metrics.update_count * 5, 100)

        overall = round((completeness * 0.4 + signal_health * 0.3 + update_health * 0.3), 1)

        return {
            "twin_id": bo.id,
            "overall_health": overall,
            "data_health": completeness,
            "signal_health": signal_health,
            "update_health": update_health,
            "state": self.state.value,
            "issues": [] if overall > 50 else ["بيانات غير كافية", "إشارات محدودة"],
        }


class TwinEngine:
    """
    Manages all digital twins.
    Each business object gets a twin that lives and evolves.
    """

    def __init__(self, company_engine: Optional[CompanyIntelligenceEngine] = None):
        self.company_engine = company_engine
        self._twins: dict[str, DigitalTwin] = {}

    def create_twin(self, business_object: BusinessObject) -> DigitalTwin:
        twin = DigitalTwin(business_object)
        self._twins[business_object.id] = twin
        return twin

    def get_twin(self, entity_id: str) -> Optional[DigitalTwin]:
        return self._twins.get(entity_id)

    def get_or_create(self, business_object: BusinessObject) -> DigitalTwin:
        existing = self.get_twin(business_object.id)
        if existing:
            return existing
        return self.create_twin(business_object)

    def get_all_twins(self, entity_type: Optional[EntityType] = None) -> list[DigitalTwin]:
        if entity_type:
            return [t for t in self._twins.values() if t.business_object.entity_type == entity_type]
        return list(self._twins.values())

    def health_summary(self) -> dict[str, Any]:
        twins = self.get_all_twins()
        if not twins:
            return {"total": 0, "avg_health": 0, "active": 0}
        healths = [t.health_check() for t in twins]
        return {
            "total": len(twins),
            "avg_health": round(sum(h["overall_health"] for h in healths) / len(healths), 1),
            "active": sum(1 for t in twins if t.state == TwinState.ACTIVE),
            "stale": sum(1 for t in twins if t.state == TwinState.STALE),
            "error": sum(1 for t in twins if t.state == TwinState.ERROR),
        }

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "total_twins": len(self._twins),
            **self.health_summary(),
        }
