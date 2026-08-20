"""Approval in-memory repository — testing and fallback persistence."""

from __future__ import annotations

from .contracts.models import ApprovalRequest, ApprovalStatus
from .contracts.repository import ApprovalRepository


class InMemoryApprovalRepository(ApprovalRepository):
    """In-memory store for approval requests (testing / lightweight fallback)."""

    def __init__(self) -> None:
        self._store: dict[str, ApprovalRequest] = {}

    async def save(self, request: ApprovalRequest) -> ApprovalRequest:
        self._store[request.id] = request
        return request

    async def get(self, request_id: str) -> ApprovalRequest | None:
        return self._store.get(request_id)

    async def list_by_tenant(
        self, tenant_id: str, status: str | None = None, target_type: str | None = None
    ) -> list[ApprovalRequest]:
        results = []
        for r in self._store.values():
            if r.tenant_id != tenant_id:
                continue
            if status and r.status.value != status:
                continue
            if target_type and r.target_type.value != target_type:
                continue
            results.append(r)
        return sorted(results, key=lambda x: (x.priority, x.created_at))

    async def list_pending(
        self, tenant_id: str, assigned_to: str | None = None
    ) -> list[ApprovalRequest]:
        results = []
        for r in self._store.values():
            if r.tenant_id != tenant_id:
                continue
            if r.status != ApprovalStatus.PENDING:
                continue
            if assigned_to and r.assigned_to != assigned_to:
                continue
            results.append(r)
        return sorted(results, key=lambda x: (x.priority, x.created_at))

    async def count_by_status(self, tenant_id: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for r in self._store.values():
            if r.tenant_id != tenant_id:
                continue
            key = r.status.value
            counts[key] = counts.get(key, 0) + 1
        return counts
