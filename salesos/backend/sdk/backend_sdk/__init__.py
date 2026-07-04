"""Backend SDK — typed runtime client for backend services.

Provides: Runtime client, Entity client, Query builder, Event publisher, Feature access.
Every backend service uses this SDK instead of accessing runtimes directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class EntityQuery:
    entity_type: str
    filters: dict = field(default_factory=dict)
    fields: Optional[list[str]] = None
    order_by: Optional[str] = None
    limit: int = 20
    offset: int = 0

    def to_dict(self) -> dict:
        return {
            "entity_type": self.entity_type,
            "filters": self.filters,
            "fields": self.fields,
            "order_by": self.order_by,
            "limit": self.limit,
            "offset": self.offset,
        }


@dataclass
class EntityResult:
    entity_type: str
    entity_id: str
    data: dict
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "data": self.data,
            "errors": self.errors,
        }


class BackendClient:
    """Abstract interface for backend SDK consumers."""

    def __init__(self, runtime_registry: dict[str, Any]):
        self._runtimes = runtime_registry

    def get_runtime(self, name: str) -> Any:
        return self._runtimes.get(name)

    def event_runtime(self):
        return self._runtimes.get("event_runtime")

    def search_runtime(self):
        return self._runtimes.get("search_runtime")

    def feature_store(self):
        return self._runtimes.get("feature_store")

    def decision_engine(self):
        return self._runtimes.get("decision_engine")

    def kg_engine(self):
        return self._runtimes.get("kg_engine")

    def timeline_runtime(self):
        return self._runtimes.get("timeline_runtime")

    def data_fabric(self):
        return self._runtimes.get("data_fabric")

    def __repr__(self) -> str:
        return f"BackendClient(runtimes={len(self._runtimes)})"
