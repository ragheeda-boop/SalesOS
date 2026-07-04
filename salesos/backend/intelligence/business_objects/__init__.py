from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Any
from datetime import datetime


class EntityType(str, Enum):
    COMPANY = "company"
    DEAL = "deal"
    CONTACT = "contact"
    MEETING = "meeting"
    SUPPLIER = "supplier"
    PROJECT = "project"
    OPPORTUNITY = "opportunity"
    CAMPAIGN = "campaign"
    DOCUMENT = "document"
    PRODUCT = "product"
    TASK = "task"


class SignalType(str, Enum):
    HIRING = "hiring"
    FUNDING = "funding"
    EXPANSION = "expansion"
    CONTRACT = "contract"
    PROJECT = "project"
    NEWS = "news"
    PARTNERSHIP = "partnership"
    MERGER = "merger"
    LEADERSHIP = "leadership"
    TENDER = "tender"
    COMPETITOR_MOVE = "competitor_move"
    REGULATORY = "regulatory"


@dataclass
class ObjectIdentity:
    """Core identity of a business object - immutable."""
    id: str
    entity_type: EntityType
    external_ids: dict[str, str] = field(default_factory=dict)     # CR number, VAT, DUNS, etc.
    source: str = "manual"
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ObjectProfile:
    """Mutable profile data enriched over time."""
    name_ar: Optional[str] = None
    name_en: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    status: Optional[str] = None
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class ObjectSignal:
    """A signal detected about this business object."""
    id: str
    type: SignalType
    title: str
    description: Optional[str] = None
    source: str = ""
    source_url: Optional[str] = None
    confidence: float = 0.5
    detected_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ObjectGraph:
    """Relationship graph centered on this object."""
    related_objects: list[dict[str, Any]] = field(default_factory=list)
    relationship_count: int = 0
    depth: int = 1
    last_built_at: Optional[datetime] = None


@dataclass
class ObjectKnowledge:
    """Aggregated knowledge from all sources."""
    summary: Optional[str] = None
    key_facts: list[str] = field(default_factory=list)
    recent_events: list[str] = field(default_factory=list)
    data_quality_score: float = 0.0
    last_updated: Optional[datetime] = None
    source_count: int = 0


@dataclass
class ObjectAI:
    """AI-generated insights."""
    summary: Optional[str] = None
    key_topics: list[str] = field(default_factory=list)
    sentiment: Optional[str] = None
    risk_level: Optional[str] = None
    ai_confidence: float = 0.0
    last_analysis: Optional[datetime] = None
    raw_analysis: Optional[dict[str, Any]] = None


@dataclass
class ObjectRecommendations:
    """Actionable recommendations."""
    next_best_actions: list[dict[str, Any]] = field(default_factory=list)
    priorities: list[dict[str, Any]] = field(default_factory=list)
    risks: list[dict[str, Any]] = field(default_factory=list)
    opportunities: list[dict[str, Any]] = field(default_factory=list)
    last_generated: Optional[datetime] = None


@dataclass
class BusinessObject:
    """The unified business object - every entity in the platform."""
    identity: ObjectIdentity
    profile: ObjectProfile = field(default_factory=ObjectProfile)
    signals: list[ObjectSignal] = field(default_factory=list)
    graph: ObjectGraph = field(default_factory=ObjectGraph)
    knowledge: ObjectKnowledge = field(default_factory=ObjectKnowledge)
    ai: ObjectAI = field(default_factory=ObjectAI)
    recommendations: ObjectRecommendations = field(default_factory=ObjectRecommendations)

    @property
    def id(self) -> str:
        return self.identity.id

    @property
    def entity_type(self) -> EntityType:
        return self.identity.entity_type

    @property
    def display_name(self) -> str:
        return self.profile.name_ar or self.profile.name_en or self.identity.id


class BusinessObjectRegistry:
    """Registry of all business objects in the platform."""

    def __init__(self):
        self._objects: dict[str, BusinessObject] = {}

    def register(self, obj: BusinessObject) -> None:
        self._objects[obj.id] = obj

    def get(self, object_id: str) -> Optional[BusinessObject]:
        return self._objects.get(object_id)

    def get_by_type(self, entity_type: EntityType) -> list[BusinessObject]:
        return [o for o in self._objects.values() if o.entity_type == entity_type]

    def get_or_create(self, object_id: str, entity_type: EntityType) -> BusinessObject:
        existing = self.get(object_id)
        if existing:
            return existing
        obj = BusinessObject(
            identity=ObjectIdentity(id=object_id, entity_type=entity_type)
        )
        self.register(obj)
        return obj

    def search(self, query: str) -> list[BusinessObject]:
        q = query.lower()
        results = []
        for obj in self._objects.values():
            name = (obj.profile.name_ar or "").lower()
            name_en = (obj.profile.name_en or "").lower()
            if q in name or q in name_en:
                results.append(obj)
        return results[:20]

    def count(self) -> int:
        return len(self._objects)

    def count_by_type(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for obj in self._objects.values():
            counts[obj.entity_type.value] = counts.get(obj.entity_type.value, 0) + 1
        return counts

    def all_ids(self) -> list[str]:
        return list(self._objects.keys())
