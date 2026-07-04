"""OpportunityService — business logic for opportunity lifecycle.

Handles:
- Stage progression with validation
- Probability calculation
- Won/Lost transition
- Value changes
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from typing import Any

from ..contracts.models import (
    Opportunity,
    OpportunityStage,
    OpportunityStatus,
    PipelineDefinition,
)
from ..contracts.repository import OpportunityQuery, OpportunityRepository, OpportunityResult


class OpportunityService:

    def __init__(
        self,
        repository: OpportunityRepository,
        pipeline: PipelineDefinition | None = None,
        event_bus: Any = None,
    ):
        self._repository = repository
        self._event_bus = event_bus
        self._pipeline = pipeline or PipelineDefinition(
            tenant_id="default",
            stages=OpportunityStage.default_pipeline(),
        )

    async def _emit(self, event_type: str, tenant_id: str, data: dict[str, Any]) -> None:
        if not self._event_bus:
            return
        from sdk.events.base import DomainEvent
        event = DomainEvent(event_type=event_type, tenant_id=tenant_id, aggregate_id=data.get("id", ""), data=data)
        event.event_type = event_type
        await self._event_bus.publish(event)

    async def create_opportunity(
        self,
        tenant_id: str,
        company_id: str,
        name: str,
        value: float = 0.0,
        owner_id: str = "",
        expected_close_date: date | None = None,
        description: str = "",
    ) -> Opportunity:
        from datetime import date

        first_stage = self._pipeline.stages[0]
        opportunity = Opportunity(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            company_id=company_id,
            name=name,
            value=value,
            stage=first_stage.name,
            probability=first_stage.default_probability,
            owner_id=owner_id,
            expected_close_date=expected_close_date or date.today(),
            description=description,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        result = await self._repository.save(opportunity)
        await self._emit("opportunity.created", tenant_id, {
            "id": opportunity.id, "company_id": company_id,
            "name": name, "value": value, "stage": first_stage.name,
        })
        return result

    async def advance_stage(self, opportunity_id: str, to_stage: str) -> Opportunity:
        opportunity = await self._repository.get(opportunity_id)
        if not opportunity:
            raise ValueError(f"Opportunity {opportunity_id} not found")

        if not self._pipeline.is_valid_transition(opportunity.stage, to_stage):
            raise ValueError(f"Invalid stage transition: {opportunity.stage} → {to_stage}")

        old_stage = opportunity.stage
        opportunity.stage = to_stage
        stage_def = self._pipeline.stage_by_name(to_stage)
        if stage_def:
            opportunity.probability = stage_def.default_probability

        # Handle terminal stages
        if stage_def and stage_def.is_terminal:
            if "won" in to_stage:
                opportunity.status = OpportunityStatus.WON
                opportunity.won_amount = opportunity.value
            elif "lost" in to_stage:
                opportunity.status = OpportunityStatus.LOST

        opportunity.updated_at = datetime.now(timezone.utc)
        result = await self._repository.save(opportunity)

        event_type = "opportunity.stage_changed"
        if opportunity.status == OpportunityStatus.WON:
            event_type = "opportunity.won"
        elif opportunity.status == OpportunityStatus.LOST:
            event_type = "opportunity.lost"
        await self._emit(event_type, opportunity.tenant_id, {
            "id": opportunity.id, "old_stage": old_stage, "new_stage": to_stage,
            "value": opportunity.value, "status": opportunity.status.value,
        })
        return result

    async def update_value(self, opportunity_id: str, new_value: float) -> Opportunity:
        opportunity = await self._repository.get(opportunity_id)
        if not opportunity:
            raise ValueError(f"Opportunity {opportunity_id} not found")
        if opportunity.is_terminal:
            raise ValueError("Cannot change value of a closed opportunity")

        opportunity.value = new_value
        opportunity.updated_at = datetime.now(timezone.utc)
        return await self._repository.save(opportunity)

    async def close_won(self, opportunity_id: str, won_amount: float | None = None) -> Opportunity:
        opportunity = await self.advance_stage(opportunity_id, "closed_won")
        if won_amount is not None:
            opportunity.won_amount = won_amount
            opportunity.updated_at = datetime.now(timezone.utc)
            opportunity = await self._repository.save(opportunity)
        return opportunity

    async def close_lost(self, opportunity_id: str, loss_reason: str = "") -> Opportunity:
        opportunity = await self._repository.get(opportunity_id)
        if not opportunity:
            raise ValueError(f"Opportunity {opportunity_id} not found")

        opportunity.stage = "closed_lost"
        opportunity.status = OpportunityStatus.LOST
        opportunity.loss_reason = loss_reason
        opportunity.probability = 0.0
        opportunity.updated_at = datetime.now(timezone.utc)
        return await self._repository.save(opportunity)

    async def get(self, opportunity_id: str) -> Opportunity | None:
        return await self._repository.get(opportunity_id)

    async def query(self, query: OpportunityQuery) -> OpportunityResult:
        return await self._repository.query(query)

    async def count_by_stage(self, tenant_id: str) -> dict[str, int]:
        return await self._repository.count_by_stage(tenant_id)

    async def pipeline_summary(self, tenant_id: str) -> dict:
        """Summary of the pipeline for dashboard display."""
        counts = await self._repository.count_by_stage(tenant_id)
        values = await self._repository.total_value_by_stage(tenant_id)
        win_rate = await self._repository.win_rate(tenant_id)

        summary = {}
        for stage in self._pipeline.stages:
            summary[stage.name] = {
                "label": stage.name_ar,
                "count": counts.get(stage.name, 0),
                "total_value": values.get(stage.name, 0.0),
                "probability": stage.default_probability,
            }

        return {
            "stages": summary,
            "win_rate": win_rate,
            "total_pipeline_value": sum(values.values()),
        }

    async def win_rate(self, tenant_id: str) -> float:
        return await self._repository.win_rate(tenant_id)

    def set_pipeline(self, pipeline: PipelineDefinition) -> None:
        self._pipeline = pipeline


# Needed for type hints in service
from datetime import date
