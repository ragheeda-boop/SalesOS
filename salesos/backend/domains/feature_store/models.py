from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class FeatureType(str, Enum):
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    TEXT = "text"
    EMBEDDING = "embedding"


class EntityType(str, Enum):
    COMPANY = "company"
    OPPORTUNITY = "opportunity"
    CONTACT = "contact"
    EMPLOYEE = "employee"


@dataclass
class FeatureDefinition:
    key: str
    name: str
    description: str = ""
    feature_type: FeatureType = FeatureType.NUMERIC
    domain: str = "general"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "name": self.name,
            "description": self.description,
            "feature_type": self.feature_type.value,
            "domain": self.domain,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class FeatureValue:
    feature_key: str
    entity_id: str
    entity_type: EntityType
    value: Any = None
    computed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ttl_seconds: int = 3600

    @property
    def is_expired(self) -> bool:
        elapsed = (datetime.now(timezone.utc) - self.computed_at).total_seconds()
        return elapsed >= self.ttl_seconds

    def to_dict(self) -> dict[str, Any]:
        return {
            "feature_key": self.feature_key,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type.value,
            "value": self.value,
            "computed_at": self.computed_at.isoformat(),
            "ttl_seconds": self.ttl_seconds,
        }


@dataclass
class FeatureSet:
    name: str
    features: list[str] = field(default_factory=list)
    description: str = ""
