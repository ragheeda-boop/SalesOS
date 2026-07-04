from __future__ import annotations
from abc import ABC, abstractmethod
from .models import DecisionContext, Policy


class DecisionRepository(ABC):
    @abstractmethod
    async def save_context(self, context: DecisionContext) -> DecisionContext:
        ...

    @abstractmethod
    async def get_context(self, context_id: str) -> DecisionContext | None:
        ...

    @abstractmethod
    async def get_latest_for_target(self, target_id: str, target_type: str) -> DecisionContext | None:
        ...

    @abstractmethod
    async def save_policy(self, policy: Policy) -> Policy:
        ...

    @abstractmethod
    async def list_policies(self, tenant_id: str) -> list[Policy]:
        ...
