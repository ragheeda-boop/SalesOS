from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ScoringDimension(str, Enum):
    BUYING_INTENT = "buying_intent"
    ENGAGEMENT = "engagement"
    FIT = "fit"
    URGENCY = "urgency"
    RELATIONSHIP = "relationship"
    MARKET_SIGNAL = "market_signal"


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class SignalEvidence:
    source_layer: str
    source_domain: str
    signal_id: str
    signal_type: str
    intensity: float
    narrative: str
    detected_at: datetime


@dataclass
class ScoringFactor:
    dimension: ScoringDimension
    key: str
    value: float
    weight: float = 1.0
    label: str = ""
    evidence: list[SignalEvidence] = field(default_factory=list)


@dataclass
class Score:
    dimension: ScoringDimension
    raw_score: float
    normalized_score: float
    confidence: ConfidenceLevel
    factors: list[ScoringFactor] = field(default_factory=list)
    narrative: str = ""


@dataclass
class ScoreCard:
    id: str
    tenant_id: str
    target_id: str
    target_type: str
    scores: list[Score] = field(default_factory=list)
    overall_score: float = 0.0
    overall_confidence: ConfidenceLevel = ConfidenceLevel.LOW
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def top_opportunity_score(self) -> Score | None:
        if not self.scores:
            return None
        return max(self.scores, key=lambda s: s.normalized_score)

    @property
    def risk_factors(self) -> list[ScoringFactor]:
        return [
            f for s in self.scores
            for f in s.factors
            if f.value < 0.3
        ]
