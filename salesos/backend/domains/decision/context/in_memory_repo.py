from __future__ import annotations
from .models import DecisionContext, Policy
from .repo import DecisionRepository


class InMemoryDecisionRepository(DecisionRepository):
    def __init__(self):
        self._contexts: list[DecisionContext] = []
        self._policies: dict[str, Policy] = {}

    async def save_context(self, context: DecisionContext) -> DecisionContext:
        for i, c in enumerate(self._contexts):
            if c.id == context.id:
                self._contexts[i] = context
                return context
        self._contexts.append(context)
        return context

    async def get_context(self, context_id: str) -> DecisionContext | None:
        for c in self._contexts:
            if c.id == context_id:
                return c
        return None

    async def get_latest_for_target(self, target_id: str, target_type: str) -> DecisionContext | None:
        for c in reversed(self._contexts):
            if c.target_id == target_id and c.target_type == target_type:
                return c
        return None

    async def save_policy(self, policy: Policy) -> Policy:
        self._policies[policy.id] = policy
        return policy

    async def list_policies(self, tenant_id: str) -> list[Policy]:
        return list(self._policies.values())
