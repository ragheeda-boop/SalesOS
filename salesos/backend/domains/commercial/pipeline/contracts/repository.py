"""PipelineRepository — persistence for pipeline definitions, entries, and KPIs."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from .models import PipelineDefinition, PipelineKPI, StageEntry


@dataclass
class PipelineKPIs:
    """Aggregated KPI snapshot for a pipeline."""

    pipeline_id: str
    total_opportunities: int = 0
    pipeline_value: float = 0.0
    weighted_pipeline: float = 0.0
    stage_counts: dict[str, int] = field(default_factory=dict)
    stage_values: dict[str, float] = field(default_factory=dict)
    stage_velocity_days: dict[str, float] = field(default_factory=dict)
    stage_conversion_rate: dict[str, float] = field(default_factory=dict)
    stalled_count: int = 0
    average_deal_cycle_days: float = 0.0
    win_rate: float = 0.0


class PipelineRepository(ABC):

    @abstractmethod
    async def save_definition(self, pipeline: PipelineDefinition) -> PipelineDefinition: ...

    @abstractmethod
    async def get_definition(self, pipeline_id: str) -> PipelineDefinition | None: ...

    @abstractmethod
    async def list_definitions(self, tenant_id: str) -> list[PipelineDefinition]: ...

    @abstractmethod
    async def save_stage_entry(self, entry: StageEntry) -> StageEntry: ...

    @abstractmethod
    async def get_active_stage_entry(self, opportunity_id: str) -> StageEntry | None: ...

    @abstractmethod
    async def get_stage_history(self, opportunity_id: str) -> list[StageEntry]: ...

    @abstractmethod
    async def compute_kpis(self, pipeline_id: str, opportunities: list) -> PipelineKPIs: ...
