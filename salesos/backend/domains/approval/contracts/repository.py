"""Approval repository — abstract interface for persistence."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .models import ApprovalRequest


class ApprovalRepository(ABC):

    @abstractmethod
    async def save(self, request: ApprovalRequest) -> ApprovalRequest:
        ...

    @abstractmethod
    async def get(self, request_id: str) -> ApprovalRequest | None:
        ...

    @abstractmethod
    async def list_by_tenant(
        self, tenant_id: str, status: str | None = None, target_type: str | None = None
    ) -> list[ApprovalRequest]:
        ...

    @abstractmethod
    async def list_pending(
        self, tenant_id: str, assigned_to: str | None = None
    ) -> list[ApprovalRequest]:
        ...

    @abstractmethod
    async def count_by_status(self, tenant_id: str) -> dict[str, int]:
        ...
