from __future__ import annotations
import uuid
from typing import Any

from .models import DecisionContext, DecisionFactor, Policy
from .repo import DecisionRepository


class DecisionService:
    """Builds decision contexts from facts, knowledge, measurements, and policies."""

    def __init__(self, repository: DecisionRepository, event_bus: Any = None):
        self._repository = repository
        self._event_bus = event_bus

    async def build_context(
        self,
        tenant_id: str,
        target_id: str,
        target_type: str = "opportunity",
        factors: list[DecisionFactor] | None = None,
        policies: list[Policy] | None = None,
    ) -> DecisionContext:
        context = DecisionContext(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            target_id=target_id,
            target_type=target_type,
            factors=factors or [],
            policies=policies or [],
        )
        result = await self._repository.save_context(context)
        if self._event_bus:
            from sdk.events.base import DomainEvent
            event = DomainEvent(event_type="decision.context_built", tenant_id=tenant_id,
                                aggregate_id=context.id,
                                data={"target_id": target_id, "target_type": target_type,
                                      "factor_count": len(context.factors)})
            event.event_type = "decision.context_built"
            await self._event_bus.publish(event)
        return result

    async def add_factor(self, context_id: str, factor: DecisionFactor) -> DecisionContext:
        ctx = await self._repository.get_context(context_id)
        if not ctx:
            raise ValueError(f"Context {context_id} not found")
        ctx.factors.append(factor)
        return await self._repository.save_context(ctx)

    async def add_policy(self, tenant_id: str, policy: Policy) -> Policy:
        return await self._repository.save_policy(policy)

    async def get_context(self, context_id: str) -> DecisionContext | None:
        return await self._repository.get_context(context_id)

    async def get_latest_context(self, target_id: str, target_type: str) -> DecisionContext | None:
        return await self._repository.get_latest_for_target(target_id, target_type)

    async def list_policies(self, tenant_id: str) -> list[Policy]:
        return await self._repository.list_policies(tenant_id)

    @staticmethod
    def create_factor(source_layer: str, source_domain: str, key: str, value: Any,
                      label: str = "", severity: str = "info") -> DecisionFactor:
        return DecisionFactor(
            source_layer=source_layer, source_domain=source_domain,
            key=key, value=value, label=label, severity=severity,
        )
