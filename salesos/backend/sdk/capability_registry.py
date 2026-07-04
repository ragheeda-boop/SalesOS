"""Capability Registry — كل Capability تعلن عن نفسها مرة واحدة.

Each module declares its capabilities here. The rest of the platform
reads this registry dynamically — no hardcoded if/else chains.

Consumed by:
  - SearchPlanner (select executor by capability)
  - Permission system (generate default roles)
  - Event system (route events)
  - AI Agents (discover tools)
  - Documentation generator
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CapabilityType(Enum):
    DOMAIN = "domain"
    SEARCH = "search"
    TIMELINE = "timeline"
    GRAPH = "graph"
    WORKFLOW = "workflow"
    AI = "ai"
    INTEGRATION = "integration"


class ExecutionStrategy(Enum):
    POSTGRES_BTREE = "postgres_btree"
    POSTGRES_TRIGRAM = "postgres_trigram"
    POSTGRES_TSVECTOR = "postgres_tsvector"
    PGVECTOR_HNSW = "pgvector_hnsw"
    NEO4J = "neo4j"
    HYBRID = "hybrid"
    IN_MEMORY = "in_memory"


@dataclass
class ExecutorDeclaration:
    """Declares an executor implementation."""

    name: str
    strategy: ExecutionStrategy
    supports: list[str]  # e.g. ["exact", "partial", "semantic"]
    frozen: bool = False
    verified_p95: str = ""


@dataclass
class EventDeclaration:
    """Declares events a module produces or consumes."""

    produces: list[str] = field(default_factory=list)
    consumes: list[str] = field(default_factory=list)


@dataclass
class MetricDeclaration:
    """Declares OpenTelemetry metrics."""

    counters: list[str] = field(default_factory=list)
    histograms: list[str] = field(default_factory=list)


@dataclass
class AIDeclaration:
    """Declares AI capabilities."""

    semantic_search: bool = False
    similar_companies: bool = False
    copilot: bool = False
    rag: bool = False
    classification: bool = False


@dataclass
class Capability:
    """A capability is a bounded concern with executors, events, and metadata."""

    name: str
    label: str
    label_ar: str
    description: str
    type: CapabilityType
    version: str = "1.0.0"
    executors: list[ExecutorDeclaration] = field(default_factory=list)
    events: EventDeclaration = field(default_factory=EventDeclaration)
    metrics: MetricDeclaration = field(default_factory=MetricDeclaration)
    ai: AIDeclaration = field(default_factory=AIDeclaration)
    permissions: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    frozen_interfaces: list[str] = field(default_factory=list)


class CapabilityRegistry:
    """Global registry — modules declare themselves once, platform consumes dynamically."""

    _capabilities: dict[str, Capability] = {}

    @classmethod
    def register(cls, cap: Capability) -> None:
        cls._capabilities[cap.name] = cap

    @classmethod
    def get(cls, name: str) -> Capability | None:
        return cls._capabilities.get(name)

    @classmethod
    def all(cls) -> dict[str, Capability]:
        return dict(cls._capabilities)

    @classmethod
    def find_by_type(cls, cap_type: CapabilityType) -> list[Capability]:
        return [c for c in cls._capabilities.values() if c.type == cap_type]

    @classmethod
    def find_executor(cls, strategy: ExecutionStrategy) -> ExecutorDeclaration | None:
        for cap in cls._capabilities.values():
            for ex in cap.executors:
                if ex.strategy == strategy:
                    return ex
        return None

    @classmethod
    def supports_intent(cls, intent: str) -> list[ExecutorDeclaration]:
        """Find all executors that support a given search intent."""
        result: list[ExecutorDeclaration] = []
        for cap in cls._capabilities.values():
            for ex in cap.executors:
                if intent in ex.supports:
                    result.append(ex)
        return result

    @classmethod
    def to_dict(cls) -> dict[str, Any]:
        return {
            name: {
                "label": cap.label,
                "type": cap.type.value,
                "version": cap.version,
                "executors": [
                    {"name": e.name, "strategy": e.strategy.value, "supports": e.supports}
                    for e in cap.executors
                ],
                "events": {
                    "produces": cap.events.produces,
                    "consumes": cap.events.consumes,
                },
                "ai": {
                    "semantic_search": cap.ai.semantic_search,
                    "similar_companies": cap.ai.similar_companies,
                    "copilot": cap.ai.copilot,
                },
                "frozen_interfaces": cap.frozen_interfaces,
            }
            for name, cap in cls._capabilities.items()
        }
