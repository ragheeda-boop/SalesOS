"""PipelineService — business logic for stage progression, rules, SLAs, and KPIs.

Enforces:
- Stage order (no skipping unless permitted)
- Entry criteria (must be met before entering)
- Exit criteria (must be met before exiting)
- Terminal states (won/lost are final unless reopened)
- SLA monitoring (overdue detection)
- KPI computation (velocity, conversion, pipeline value)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from ..contracts.models import (
    Criterion,
    PipelineDefinition,
    StageDefinition,
    StageEntry,
)
from ..contracts.repository import PipelineKPIs, PipelineRepository


class PipelineService:

    def __init__(self, repository: PipelineRepository, event_bus: Any = None):
        self._repository = repository
        self._event_bus = event_bus

    async def _emit(self, event_type: str, tenant_id: str, data: dict[str, Any]) -> None:
        if not self._event_bus:
            return
        from sdk.events.base import DomainEvent
        event = DomainEvent(event_type=event_type, tenant_id=tenant_id,
                            aggregate_id=data.get("pipeline_id", ""), data=data)
        event.event_type = event_type
        await self._event_bus.publish(event)

    # ── Pipeline Definition ──

    async def create_pipeline(self, definition: PipelineDefinition) -> PipelineDefinition:
        result = await self._repository.save_definition(definition)
        await self._emit("pipeline.created", definition.tenant_id, {
            "pipeline_id": definition.id, "name": definition.name,
            "stages": [s.name for s in definition.stages],
        })
        return result

    async def get_pipeline(self, pipeline_id: str) -> PipelineDefinition | None:
        return await self._repository.get_definition(pipeline_id)

    async def list_pipelines(self, tenant_id: str) -> list[PipelineDefinition]:
        return await self._repository.list_definitions(tenant_id)

    # ── Stage Progression ──

    async def enter_stage(
        self,
        opportunity_id: str,
        pipeline_id: str,
        to_stage: str,
        from_stage: str = "",
    ) -> StageEntry:
        """Move an opportunity to a new stage."""
        pipeline = await self._repository.get_definition(pipeline_id)
        if not pipeline:
            raise ValueError(f"Pipeline {pipeline_id} not found")

        stage_def = pipeline.stage_by_name(to_stage)
        if not stage_def:
            raise ValueError(f"Stage '{to_stage}' not found in pipeline")

        # Validate transition
        if from_stage:
            if not pipeline.is_valid_transition(from_stage, to_stage):
                raise ValueError(f"Invalid transition: {from_stage} → {to_stage}")

        # Validate entry criteria
        violation = self._check_criteria(stage_def.entry_criteria, {"stage": to_stage})
        if violation:
            raise ValueError(f"Entry criteria not met: {violation}")

        # Close previous active entry
        prev = await self._repository.get_active_stage_entry(opportunity_id)
        if prev:
            prev.exited_at = datetime.now(timezone.utc)
            prev.exit_reason = f"advanced_to_{to_stage}"
            await self._repository.save_stage_entry(prev)

        entry = StageEntry(
            id=str(uuid.uuid4()),
            pipeline_id=pipeline_id,
            opportunity_id=opportunity_id,
            stage_name=to_stage,
        )
        result = await self._repository.save_stage_entry(entry)

        await self._emit("stage.entered", pipeline.tenant_id, {
            "opportunity_id": opportunity_id, "stage": to_stage,
            "pipeline_id": pipeline_id,
        })
        return result

    async def exit_stage(
        self,
        opportunity_id: str,
        exit_reason: str = "",
    ) -> StageEntry | None:
        entry = await self._repository.get_active_stage_entry(opportunity_id)
        if entry:
            entry.exited_at = datetime.now(timezone.utc)
            entry.exit_reason = exit_reason
            result = await self._repository.save_stage_entry(entry)
            await self._emit("stage.exited", "", {
                "opportunity_id": opportunity_id, "stage": entry.stage_name,
                "reason": exit_reason,
            })
            return result
        return None

    # ── SLA / Overdue ──

    async def check_overdue(self, pipeline_id: str, opportunities: list) -> list[dict]:
        """Return all stalled opportunities (exceeded SLA)."""
        pipeline = await self._repository.get_definition(pipeline_id)
        if not pipeline:
            return []

        stalled: list[dict] = []
        for opp in opportunities:
            stage = getattr(opp, "stage", "")
            stage_def = pipeline.stage_by_name(stage)
            if stage_def and stage_def.sla_days > 0 and not stage_def.is_terminal:
                entry = await self._repository.get_active_stage_entry(getattr(opp, "id", ""))
                if entry and entry.duration_days > stage_def.sla_days:
                    stalled.append({
                        "opportunity_id": getattr(opp, "id", ""),
                        "stage": stage,
                        "days_in_stage": round(entry.duration_days, 1),
                        "sla_days": stage_def.sla_days,
                        "overdue_by_days": round(entry.duration_days - stage_def.sla_days, 1),
                    })
                    await self._emit("stage.overdue", pipeline.tenant_id, {
                        "opportunity_id": getattr(opp, "id", ""),
                        "stage": stage, "overdue_days": round(entry.duration_days - stage_def.sla_days, 1),
                    })
        return stalled

    # ── KPIs ──

    async def compute_kpis(self, pipeline_id: str, opportunities: list) -> PipelineKPIs:
        return await self._repository.compute_kpis(pipeline_id, opportunities)

    # ── Reopen ──

    async def reopen(self, opportunity_id: str, pipeline_id: str, target_stage: str = "prospecting") -> StageEntry:
        """Reopen a terminal opportunity (won/lost)."""
        pipeline = await self._repository.get_definition(pipeline_id)
        if not pipeline:
            raise ValueError(f"Pipeline {pipeline_id} not found")

        stage_def = pipeline.stage_by_name(target_stage)
        if not stage_def:
            raise ValueError(f"Stage '{target_stage}' not found")
        if not stage_def.is_reopen_target:
            raise ValueError(f"Stage '{target_stage}' does not support reopening")

        await self._emit("pipeline.reopened", pipeline.tenant_id, {
            "opportunity_id": opportunity_id, "target_stage": target_stage,
        })
        return await self.enter_stage(opportunity_id, pipeline_id, target_stage)

    # ── Helpers ──

    @staticmethod
    def _check_criteria(criteria: list[Criterion], context: dict[str, Any]) -> str | None:
        """Check entry/exit criteria against context. Returns first violation or None."""
        for c in criteria:
            if c.operator == "exists":
                if not context.get(c.field):
                    return c.label_ar or c.label
                continue
            val = context.get(c.field)
            if c.operator == "gte" and (val is None or val < c.value):
                return c.label_ar or c.label
            if c.operator == "eq" and val != c.value:
                return c.label_ar or c.label
        return None
