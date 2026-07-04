"""In-memory Pipeline repository for testing and development."""

from __future__ import annotations

from datetime import datetime, timezone

from ..contracts.models import PipelineDefinition, StageEntry
from ..contracts.repository import PipelineKPIs, PipelineRepository


class InMemoryPipelineRepository(PipelineRepository):

    def __init__(self):
        self._definitions: dict[str, PipelineDefinition] = {}
        self._stage_entries: dict[str, list[StageEntry]] = {}  # opportunity_id → entries

    async def save_definition(self, pipeline: PipelineDefinition) -> PipelineDefinition:
        self._definitions[pipeline.id] = pipeline
        return pipeline

    async def get_definition(self, pipeline_id: str) -> PipelineDefinition | None:
        return self._definitions.get(pipeline_id)

    async def list_definitions(self, tenant_id: str) -> list[PipelineDefinition]:
        return [p for p in self._definitions.values() if p.tenant_id == tenant_id]

    async def save_stage_entry(self, entry: StageEntry) -> StageEntry:
        if entry.opportunity_id not in self._stage_entries:
            self._stage_entries[entry.opportunity_id] = []
        existing = self._stage_entries[entry.opportunity_id]
        # Update existing entry if ID matches, otherwise append
        for i, e in enumerate(existing):
            if e.id == entry.id:
                existing[i] = entry
                return entry
        existing.append(entry)
        return entry

    async def get_active_stage_entry(self, opportunity_id: str) -> StageEntry | None:
        entries = self._stage_entries.get(opportunity_id, [])
        for e in reversed(entries):
            if e.exited_at is None:
                return e
        return None

    async def get_stage_history(self, opportunity_id: str) -> list[StageEntry]:
        return self._stage_entries.get(opportunity_id, [])

    async def compute_kpis(self, pipeline_id: str, opportunities: list) -> PipelineKPIs:
        pipeline = self._definitions.get(pipeline_id)
        if not pipeline:
            return PipelineKPIs(pipeline_id=pipeline_id)

        total = len(opportunities)
        pipeline_value = sum(getattr(o, "value", 0) for o in opportunities)
        weighted = sum(getattr(o, "value", 0) * getattr(o, "probability", 0) for o in opportunities)
        won = sum(1 for o in opportunities if getattr(o, "status", None) and getattr(o, "status").value == "won")
        lost = sum(1 for o in opportunities if getattr(o, "status", None) and getattr(o, "status").value == "lost")
        closed = won + lost

        stage_counts: dict[str, int] = {}
        stage_values: dict[str, float] = {}
        for o in opportunities:
            stage = getattr(o, "stage", "unknown")
            stage_counts[stage] = stage_counts.get(stage, 0) + 1
            stage_values[stage] = stage_values.get(stage, 0.0) + getattr(o, "value", 0)

        # Velocity: avg days per stage from entries
        stage_velocity: dict[str, float] = {}
        stage_conversion: dict[str, float] = {}
        for stage in pipeline.stages:
            entries_for_stage = []
            for opp_entries in self._stage_entries.values():
                for e in opp_entries:
                    if e.stage_name == stage.name:
                        entries_for_stage.append(e)
            if entries_for_stage:
                avg_days = sum(e.duration_days for e in entries_for_stage) / len(entries_for_stage)
                stage_velocity[stage.name] = round(avg_days, 1)
                # Conversion to next stage
                exited = [e for e in entries_for_stage if e.exited_at is not None]
                stage_conversion[stage.name] = round(len(exited) / len(entries_for_stage), 2) if entries_for_stage else 0.0

        # Stalled: opportunities in non-terminal stages exceeding SLA
        stalled = 0
        for o in opportunities:
            stage = getattr(o, "stage", "")
            stage_def = pipeline.stage_by_name(stage)
            if stage_def and not stage_def.is_terminal and stage_def.sla_days > 0:
                entry = await self.get_active_stage_entry(getattr(o, "id", ""))
                if entry and entry.duration_days > stage_def.sla_days:
                    stalled += 1

        cycle_days = 0.0
        if closed > 0:
            total_days = 0.0
            for o in opportunities:
                status = getattr(o, "status", None)
                if status and status.value in ("won", "lost"):
                    created = getattr(o, "created_at", None)
                    updated = getattr(o, "updated_at", None)
                    if created and updated:
                        total_days += (updated - created).total_seconds() / 86400
            cycle_days = round(total_days / closed, 1)

        return PipelineKPIs(
            pipeline_id=pipeline_id,
            total_opportunities=total,
            pipeline_value=pipeline_value,
            weighted_pipeline=weighted,
            stage_counts=stage_counts,
            stage_values=stage_values,
            stage_velocity_days=stage_velocity,
            stage_conversion_rate=stage_conversion,
            stalled_count=stalled,
            average_deal_cycle_days=cycle_days,
            win_rate=round(won / closed, 2) if closed > 0 else 0.0,
        )
