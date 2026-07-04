from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class RecommendationStatus(Enum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    OVERRIDDEN = "overridden"


@dataclass
class RecommendationEvidence:
    """A single piece of evidence supporting a recommendation."""

    source_layer: str  # "fact", "knowledge", "measurement", "policy"
    source_domain: str
    key: str
    value: Any = None
    narrative: str = ""


@dataclass
class Alternative:
    """An alternative course of action."""

    title: str
    description: str = ""
    expected_outcome: str = ""
    risk: str = ""
    confidence: float = 0.0


@dataclass
class Recommendation:
    """An explainable, contextual, optional recommendation."""

    id: str
    tenant_id: str
    context_id: str
    title: str
    description: str = ""
    reasoning: str = ""
    confidence: float = 0.0
    risk: str = ""
    expected_impact: str = ""
    status: RecommendationStatus = RecommendationStatus.PROPOSED
    evidence: list[RecommendationEvidence] = field(default_factory=list)
    alternatives: list[Alternative] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    target_id: str = ""
    target_type: str = "opportunity"

    @property
    def is_accepted(self) -> bool:
        return self.status == RecommendationStatus.ACCEPTED

    @property
    def evidence_summary(self) -> list[str]:
        return [e.narrative for e in self.evidence if e.narrative]
