"""Evidence chain models — unified evidence linking Insight → Evidence → Source → Timestamp → Confidence."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class EvidenceType(str, Enum):
    BUSINESS_RULE = "business_rule"
    DATA_AGGREGATE = "data_aggregate"
    ACTIVITY_SIGNAL = "activity_signal"
    PIPELINE_SIGNAL = "pipeline_signal"
    FINANCIAL_SIGNAL = "financial_signal"
    RELATIONSHIP_SIGNAL = "relationship_signal"
    MARKET_SIGNAL = "market_signal"
    MANUAL_OBSERVATION = "manual_observation"


class EvidenceKind(str, Enum):
    """Auditable evidence classes used by ADR-0113 deterministic scoring."""

    OFFICIAL_REGISTRY = "source.official_registry"
    CR_NUMBER_EXACT_MATCH = "source.cr_number_exact_match"
    LICENSE_VERIFIED = "source.license_verified"
    ENTITY_RESOLUTION_MERGE = "source.entity_resolution_merge"
    CRM_EMAIL_SIGNATURE = "crm.email_signature"
    CRM_MEETING_ATTENDANCE = "crm.meeting_attendance"
    CRM_SYSTEM_RECORD = "crm.system_of_record"
    GOVERNMENT_SOURCE = "web.government_source"
    CITED_CLAIM = "web.cited_claim"
    NAME_MATCH_ONLY = "source.name_match_only"
    EMPLOYER_MATCH_ONLY = "source.employer_match_only"
    CONTRADICTION = "contradiction"


class EvidenceBand(str, Enum):
    VERIFIED = "verified"
    PROBABLE = "probable"
    POSSIBLE = "possible"
    DISCARD = "discard"


class InsightCategory(str, Enum):
    ACCOUNT_HEALTH = "account_health"
    DEAL_RISK = "deal_risk"
    DEAL_OPPORTUNITY = "deal_opportunity"
    PIPELINE_VELOCITY = "pipeline_velocity"
    REVENUE_FORECAST = "revenue_forecast"
    ENGAGEMENT_TREND = "engagement_trend"
    CHURN_RISK = "churn_risk"
    EXPANSION_POTENTIAL = "expansion_potential"
    ACTIVITY_ANOMALY = "activity_anomaly"
    CROSS_SELL = "cross_sell"


class ConfidenceLevel(str, Enum):
    HIGH = "high"        # 0.8 - 1.0
    MEDIUM = "medium"    # 0.5 - 0.79
    LOW = "low"          # 0.2 - 0.49
    UNKNOWN = "unknown"  # < 0.2


@dataclass
class EvidenceSource:
    """Where this evidence came from."""
    source_domain: str      # "company", "opportunity", "activity", "proposal", "review", "revenue"
    source_type: str        # "table_aggregate", "event", "score", "rule", "observation"
    source_id: str = ""     # specific record ID if applicable
    source_name: str = ""   # human-readable source name


@dataclass
class EvidenceItem:
    """A single piece of evidence supporting an insight."""
    id: str
    evidence_type: EvidenceType
    source: EvidenceSource
    description: str
    confidence: float               # 0.0 - 1.0
    confidence_level: ConfidenceLevel
    evidence_kind: EvidenceKind | None = None
    data: dict[str, Any] = field(default_factory=dict)
    recorded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_high_confidence(self) -> bool:
        if self.evidence_kind is not None:
            from ..engine.scoring import score_evidence

            return score_evidence([self]).score >= 0.8
        return self.confidence >= 0.8


@dataclass
class Insight:
    """A commercial insight backed by evidence chain."""
    id: str
    tenant_id: str
    category: InsightCategory
    title: str
    description: str
    target_id: str              # company_id, opportunity_id, etc.
    target_type: str            # "company", "opportunity", "contact", "proposal", "review"
    overall_confidence: float   # 0.0 - 1.0 (derived from evidence)
    confidence_level: ConfidenceLevel
    evidence_items: list[EvidenceItem] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def evidence_count(self) -> int:
        return len(self.evidence_items)

    @property
    def high_confidence_evidence(self) -> list[EvidenceItem]:
        return [e for e in self.evidence_items if e.is_high_confidence]

    @property
    def evidence_summary(self) -> list[str]:
        return [e.description for e in self.evidence_items if e.description]

    def recompute_confidence(self) -> None:
        """Recompute confidence, using ADR-0113 strength for classified evidence.

        Legacy items without an explicit evidence kind retain the historical
        average for read compatibility. New factual decisions must classify the
        kind; the `confidence` value is not an evidence weight.
        """
        if not self.evidence_items:
            self.overall_confidence = 0.0
            self.confidence_level = ConfidenceLevel.UNKNOWN
            self.metadata.pop("evidence_score_method", None)
            self.metadata.pop("evidence_contradiction_present", None)
            return

        # Apply ADR-0113 only when every item has an explicit evidence kind.
        # Scoring only the classified subset silently discarded legacy items
        # whenever an insight contained a mixture of old and new evidence.
        fully_classified = all(
            item.evidence_kind is not None for item in self.evidence_items
        )
        if fully_classified:
            from ..engine.scoring import score_evidence

            result = score_evidence(self.evidence_items)
            value = result.score
            self.metadata["evidence_score_method"] = "adr_0113_bayesian_v1"
            self.metadata["evidence_contradiction_present"] = result.contradiction_present
        else:
            # Preserve the historical behavior for unclassified or mixed
            # evidence until all producers have an approved evidence kind.
            value = sum(e.confidence for e in self.evidence_items) / len(self.evidence_items)
            self.metadata["evidence_score_method"] = "legacy_average_compatibility"
            self.metadata.pop("evidence_contradiction_present", None)

        self.overall_confidence = round(value, 3)
        if value >= 0.8:
            self.confidence_level = ConfidenceLevel.HIGH
        elif value >= 0.5:
            self.confidence_level = ConfidenceLevel.MEDIUM
        elif value >= 0.2:
            self.confidence_level = ConfidenceLevel.LOW
        else:
            self.confidence_level = ConfidenceLevel.UNKNOWN
