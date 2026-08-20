"""ApprovalService — human-in-the-loop approval workflow for AI recommendations.

Enforces:
- Status machine: PENDING → APPROVED/REJECTED/ESCALATED/EXPIRED/CANCELLED
- RBAC level enforcement (required_level vs authority_level)
- Expiration handling
- Audit trail (decisions logged with timestamps)
- Event emission for downstream consumers
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

from ..contracts.models import (
    ApprovalDecision,
    ApprovalLevel,
    ApprovalRequest,
    ApprovalStatus,
    ApprovalTargetType,
)
from ..contracts.repository import ApprovalRepository


_LEVEL_RANK = {
    ApprovalLevel.SELF: 0,
    ApprovalLevel.MANAGER: 1,
    ApprovalLevel.VP: 2,
    ApprovalLevel.EXECUTIVE: 3,
}


class ApprovalService:

    def __init__(self, repository: ApprovalRepository, event_bus: Any = None):
        self._repository = repository
        self._event_bus = event_bus

    async def _emit(self, event_type: str, tenant_id: str, data: dict[str, Any]) -> None:
        if not self._event_bus:
            return
        from sdk.events.base import DomainEvent
        event = DomainEvent(
            event_type=event_type,
            tenant_id=tenant_id,
            aggregate_id=data.get("approval_id", ""),
            data=data,
        )
        event.event_type = event_type
        await self._event_bus.publish(event)

    async def create_request(
        self,
        tenant_id: str,
        target_type: ApprovalTargetType,
        target_id: str,
        requested_by: str,
        action_summary: str,
        action_evidence: list[str] | None = None,
        required_level: ApprovalLevel = ApprovalLevel.MANAGER,
        assigned_to: str = "",
        priority: int = 5,
        ttl_hours: int = 48,
        metadata: dict | None = None,
    ) -> ApprovalRequest:
        request = ApprovalRequest(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            target_type=target_type,
            target_id=target_id,
            requested_by=requested_by,
            action_summary=action_summary,
            action_evidence=action_evidence or [],
            required_level=required_level,
            assigned_to=assigned_to,
            priority=priority,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=ttl_hours),
            metadata=metadata or {},
        )
        result = await self._repository.save(request)
        await self._emit("approval.requested", tenant_id, {
            "approval_id": request.id,
            "target_type": target_type.value,
            "target_id": target_id,
            "required_level": required_level.value,
            "assigned_to": assigned_to,
            "priority": priority,
        })
        return result

    async def approve(
        self,
        request_id: str,
        approved_by: str,
        authority_level: ApprovalLevel = ApprovalLevel.SELF,
        comments: str = "",
    ) -> ApprovalRequest:
        request = await self._repository.get(request_id)
        if not request:
            raise ValueError(f"Approval request {request_id} not found")
        if request.is_terminal:
            raise ValueError(f"Cannot approve request in status: {request.status.value}")

        if _LEVEL_RANK.get(authority_level, 0) < _LEVEL_RANK.get(request.required_level, 1):
            raise PermissionError(
                f"Insufficient authority: {authority_level.value} < {request.required_level.value}"
            )

        decision = ApprovalDecision(
            decision="approve",
            decided_by=approved_by,
            comments=comments,
            authority_level=authority_level,
        )
        request.decisions.append(decision)
        request.status = ApprovalStatus.APPROVED
        request.updated_at = datetime.now(timezone.utc)
        result = await self._repository.save(request)

        await self._emit("approval.approved", request.tenant_id, {
            "approval_id": request_id,
            "approved_by": approved_by,
            "authority_level": authority_level.value,
            "target_type": request.target_type.value,
            "target_id": request.target_id,
            "comments": comments,
        })
        return result

    async def reject(
        self,
        request_id: str,
        rejected_by: str,
        authority_level: ApprovalLevel = ApprovalLevel.SELF,
        comments: str = "",
    ) -> ApprovalRequest:
        request = await self._repository.get(request_id)
        if not request:
            raise ValueError(f"Approval request {request_id} not found")
        if request.is_terminal:
            raise ValueError(f"Cannot reject request in status: {request.status.value}")

        decision = ApprovalDecision(
            decision="reject",
            decided_by=rejected_by,
            comments=comments,
            authority_level=authority_level,
        )
        request.decisions.append(decision)
        request.status = ApprovalStatus.REJECTED
        request.updated_at = datetime.now(timezone.utc)
        result = await self._repository.save(request)

        await self._emit("approval.rejected", request.tenant_id, {
            "approval_id": request_id,
            "rejected_by": rejected_by,
            "authority_level": authority_level.value,
            "target_type": request.target_type.value,
            "target_id": request.target_id,
            "comments": comments,
        })
        return result

    async def escalate(
        self,
        request_id: str,
        escalated_by: str,
        comments: str = "",
    ) -> ApprovalRequest:
        request = await self._repository.get(request_id)
        if not request:
            raise ValueError(f"Approval request {request_id} not found")
        if request.is_terminal:
            raise ValueError(f"Cannot escalate request in status: {request.status.value}")

        decision = ApprovalDecision(
            decision="escalate",
            decided_by=escalated_by,
            comments=comments,
        )
        request.decisions.append(decision)
        request.status = ApprovalStatus.ESCALATED
        request.updated_at = datetime.now(timezone.utc)
        result = await self._repository.save(request)

        await self._emit("approval.escalated", request.tenant_id, {
            "approval_id": request_id,
            "escalated_by": escalated_by,
            "target_type": request.target_type.value,
            "target_id": request.target_id,
            "comments": comments,
        })
        return result

    async def cancel(self, request_id: str) -> ApprovalRequest:
        request = await self._repository.get(request_id)
        if not request:
            raise ValueError(f"Approval request {request_id} not found")
        if request.is_terminal:
            raise ValueError(f"Cannot cancel request in status: {request.status.value}")

        request.status = ApprovalStatus.CANCELLED
        request.updated_at = datetime.now(timezone.utc)
        return await self._repository.save(request)

    async def check_expiration(self, request_id: str) -> ApprovalRequest | None:
        request = await self._repository.get(request_id)
        if not request or request.is_terminal:
            return None
        if request.expires_at and datetime.now(timezone.utc) > request.expires_at:
            request.status = ApprovalStatus.EXPIRED
            request.updated_at = datetime.now(timezone.utc)
            await self._repository.save(request)
            await self._emit("approval.expired", request.tenant_id, {
                "approval_id": request_id,
                "target_type": request.target_type.value,
                "target_id": request.target_id,
            })
            return request
        return None

    async def get(self, request_id: str) -> ApprovalRequest | None:
        return await self._repository.get(request_id)

    async def list_pending(
        self, tenant_id: str, assigned_to: str | None = None
    ) -> list[ApprovalRequest]:
        return await self._repository.list_pending(tenant_id, assigned_to)

    async def list_by_tenant(
        self, tenant_id: str, status: str | None = None, target_type: str | None = None
    ) -> list[ApprovalRequest]:
        return await self._repository.list_by_tenant(tenant_id, status, target_type)

    async def kpis(self, tenant_id: str) -> dict:
        counts = await self._repository.count_by_status(tenant_id)
        total = sum(counts.values())
        return {
            "total": total,
            "pending": counts.get("pending", 0),
            "approved": counts.get("approved", 0),
            "rejected": counts.get("rejected", 0),
            "escalated": counts.get("escalated", 0),
            "expired": counts.get("expired", 0),
            "cancelled": counts.get("cancelled", 0),
        }
