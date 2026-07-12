"""SDK interfaces for scoring cross-domain boundary.

Scoring domain depends on these interfaces instead of importing
directly from the Decision domain (Interface Segregation Principle).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


# ── Shared data types (cross-boundary contracts) ──


@dataclass
class DecisionFactor:
    """A single factor contributing to a decision context."""

    source_layer: str
    source_domain: str
    key: str
    value: Any = None
    label: str = ""
    severity: str = "info"


@dataclass
class DecisionContext:
    """Snapshot of relevant factors for decision evaluation."""

    id: str
    tenant_id: str
    target_id: str
    target_type: str
    factors: list[DecisionFactor] = field(default_factory=list)
    confidence: float = 0.0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class RecommendationEvidence:
    """Evidence item included in a recommendation."""

    source_layer: str = ""
    source_domain: str = ""
    key: str = ""
    value: Any = None
    narrative: str = ""
    source_id: str = ""
    source_type: str = ""


@dataclass
class Recommendation:
    """Minimal recommendation returned by the decision platform."""

    evidence: list[RecommendationEvidence] = field(default_factory=list)
    title: str = ""
    description: str = ""
    confidence: float = 0.0


# ── Service/Engine protocols ──


class DecisionServiceProtocol(ABC):
    """Interface for building decision contexts — consumed by ScoringEngine."""

    @abstractmethod
    async def build_context(
        self,
        tenant_id: str,
        target_id: str,
        target_type: str,
        factors: list[DecisionFactor],
    ) -> DecisionContext:
        ...

    @abstractmethod
    async def get_latest_context(
        self, target_id: str, target_type: str
    ) -> Optional[DecisionContext]:
        ...


class RecommendationEngineProtocol(ABC):
    """Interface for evaluating contexts — consumed by ScoringEngine."""

    @abstractmethod
    async def evaluate(
        self, context: DecisionContext
    ) -> Optional[Recommendation]:
        ...


class ScoreCardRepository(ABC):
    """Interface for persisting and loading ScoreCards — consumed by ScoringEngine."""

    @abstractmethod
    async def save(self, scorecard: Any) -> Any:
        ...

    @abstractmethod
    async def get(self, card_id: str) -> Optional[Any]:
        ...

    @abstractmethod
    async def get_for_target(
        self, tenant_id: str, target_id: str, target_type: str = "company"
    ) -> Optional[Any]:
        ...

    @abstractmethod
    async def list_by_tenant(
        self, tenant_id: str, limit: int = 20
    ) -> list[Any]:
        ...
