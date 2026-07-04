"""Pipeline domain models — aggregate defining stages, rules, SLAs."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any


@dataclass
class Criterion:
    """A condition that must be met for stage entry or exit."""

    field: str  # e.g. "value", "contact_id", "proposal_sent"
    operator: str  # e.g. "gte", "eq", "exists"
    value: Any = None
    label: str = ""
    label_ar: str = ""


@dataclass
class StageDefinition:
    """A single stage in a pipeline."""

    name: str
    name_ar: str
    order: int
    default_probability: float = 0.0
    is_terminal: bool = False
    is_reopen_target: bool = False  # if True, can be targeted by reopen
    sla_days: int = 0  # 0 = no SLA
    entry_criteria: list[Criterion] = field(default_factory=list)
    exit_criteria: list[Criterion] = field(default_factory=list)
    description: str = ""


@dataclass
class PipelineDefinition:
    """A pipeline template — defines the rules and stages for a sales process."""

    id: str
    tenant_id: str
    name: str
    name_ar: str
    stages: list[StageDefinition] = field(default_factory=list)
    description: str = ""
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def stage_by_name(self, name: str) -> StageDefinition | None:
        for s in self.stages:
            if s.name == name:
                return s
        return None

    def is_valid_transition(self, from_stage: str, to_stage: str) -> bool:
        from_idx = next((i for i, s in enumerate(self.stages) if s.name == from_stage), -1)
        to_idx = next((i for i, s in enumerate(self.stages) if s.name == to_stage), -1)
        if from_idx == -1 or to_idx == -1:
            return False
        from_stage_def = self.stages[from_idx]
        to_stage_def = self.stages[to_idx]
        if from_stage_def.is_terminal:
            return to_stage_def.is_reopen_target
        return to_idx >= from_idx or to_idx == 0

    @staticmethod
    def default_sales_pipeline(tenant_id: str, pipeline_id: str) -> PipelineDefinition:
        return PipelineDefinition(
            id=pipeline_id,
            tenant_id=tenant_id,
            name="Sales Pipeline",
            name_ar="خط المبيعات",
            stages=[
                StageDefinition(name="prospecting", name_ar="استكشاف", order=1,
                                default_probability=0.10, sla_days=30, is_reopen_target=True,
                                exit_criteria=[Criterion(field="contact_id", operator="exists",
                                                         label="Contact identified", label_ar="تم تحديد جهة الاتصال")]),
                StageDefinition(name="qualification", name_ar="تأهيل", order=2,
                                default_probability=0.25, sla_days=14,
                                entry_criteria=[Criterion(field="contact_id", operator="exists")],
                                exit_criteria=[Criterion(field="value", operator="gte", value=1000,
                                                         label="Value >= 1000 SAR", label_ar="القيمة >= ١٠٠٠ ريال")]),
                StageDefinition(name="proposal", name_ar="عرض", order=3,
                                default_probability=0.50, sla_days=21,
                                entry_criteria=[Criterion(field="value", operator="gte", value=1000)]),
                StageDefinition(name="negotiation", name_ar="تفاوض", order=4,
                                default_probability=0.75, sla_days=14),
                StageDefinition(name="closed_won", name_ar="صفقة مغلقة", order=5,
                                default_probability=1.0, is_terminal=True,
                                entry_criteria=[Criterion(field="won_amount", operator="gte", value=0)]),
                StageDefinition(name="closed_lost", name_ar="خسارة", order=6,
                                default_probability=0.0, is_terminal=True, is_reopen_target=True),
            ],
        )


@dataclass
class StageEntry:
    """Tracks an opportunity entering and exiting a stage."""

    id: str
    pipeline_id: str
    opportunity_id: str
    stage_name: str
    entered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    exited_at: datetime | None = None
    exit_reason: str = ""

    @property
    def duration_days(self) -> float:
        end = self.exited_at or datetime.now(timezone.utc)
        return (end - self.entered_at).total_seconds() / 86400

    def is_overdue(self, sla_days: int = 0) -> bool:
        if sla_days <= 0:
            return False
        return self.duration_days > sla_days


@dataclass
class PipelineKPI:
    """Computed KPIs for a pipeline."""

    pipeline_value: float = 0.0
    weighted_pipeline: float = 0.0
    stage_velocity: dict[str, float] = field(default_factory=dict)
    stage_conversion: dict[str, float] = field(default_factory=dict)
    stalled_count: int = 0
    average_deal_cycle_days: float = 0.0
    win_rate: float = 0.0
