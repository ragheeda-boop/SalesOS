"""Opportunity domain models — deal tracking with pipeline stages."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any


class OpportunityStatus(Enum):
    OPEN = "open"
    WON = "won"
    LOST = "lost"
    ABANDONED = "abandoned"


@dataclass
class OpportunityStage:
    """A named stage in the sales pipeline."""

    name: str
    name_ar: str
    order: int
    default_probability: float = 0.0  # 0.0 - 1.0
    is_terminal: bool = False

    @staticmethod
    def default_pipeline() -> list[OpportunityStage]:
        return [
            OpportunityStage(name="prospecting", name_ar="استكشاف", order=1, default_probability=0.10),
            OpportunityStage(name="qualification", name_ar="تأهيل", order=2, default_probability=0.25),
            OpportunityStage(name="proposal", name_ar="عرض", order=3, default_probability=0.50),
            OpportunityStage(name="negotiation", name_ar="تفاوض", order=4, default_probability=0.75),
            OpportunityStage(name="closed_won", name_ar="صفقة مغلقة", order=5, default_probability=1.0, is_terminal=True),
            OpportunityStage(name="closed_lost", name_ar="خسارة", order=6, default_probability=0.0, is_terminal=True),
        ]


@dataclass
class PipelineDefinition:
    """Defines the sales pipeline structure for a tenant."""

    tenant_id: str
    stages: list[OpportunityStage] = field(default_factory=OpportunityStage.default_pipeline)

    def stage_names(self) -> list[str]:
        return [s.name for s in self.stages]

    def stage_by_name(self, name: str) -> OpportunityStage | None:
        for s in self.stages:
            if s.name == name:
                return s
        return None

    def is_valid_transition(self, from_stage: str, to_stage: str) -> bool:
        """Stage progression: forward only (except recycling permitted)."""
        from_idx = next((i for i, s in enumerate(self.stages) if s.name == from_stage), -1)
        to_idx = next((i for i, s in enumerate(self.stages) if s.name == to_stage), -1)
        if from_idx == -1 or to_idx == -1:
            return False
        # Terminal stages cannot transition
        if self.stages[from_idx].is_terminal:
            return False
        # Forward progression or recycling to first stage
        return to_idx >= from_idx or to_idx == 0


@dataclass
class Opportunity:
    """A sales opportunity — a potential deal in the pipeline."""

    id: str
    tenant_id: str
    company_id: str
    name: str
    value: float = 0.0
    currency: str = "SAR"
    stage: str = "prospecting"
    probability: float = 0.10
    expected_close_date: date | None = None
    owner_id: str = ""
    status: OpportunityStatus = OpportunityStatus.OPEN
    won_amount: float | None = None
    loss_reason: str = ""
    description: str = ""
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def weighted_value(self) -> float:
        return self.value * self.probability

    @property
    def is_terminal(self) -> bool:
        return self.status in (OpportunityStatus.WON, OpportunityStatus.LOST, OpportunityStatus.ABANDONED)
