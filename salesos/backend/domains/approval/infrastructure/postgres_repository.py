"""Approval Postgres repository — database-backed persistence for approval requests."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..contracts.models import (
    ApprovalDecision,
    ApprovalLevel,
    ApprovalRequest,
    ApprovalStatus,
    ApprovalTargetType,
)
from ..contracts.repository import ApprovalRepository
from .models import ApprovalRequestModel


class PostgresApprovalRepository(ApprovalRepository):
    """P3-5: Postgres-backed approval request repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_domain(self, model: ApprovalRequestModel) -> ApprovalRequest:
        decisions = []
        for d in (model.decisions or []):
            decisions.append(ApprovalDecision(
                decision=d.get("decision", ""),
                decided_by=d.get("decided_by", ""),
                decided_at=datetime.fromisoformat(d["decided_at"]) if d.get("decided_at") else datetime.now(timezone.utc),
                comments=d.get("comments", ""),
                authority_level=ApprovalLevel(d.get("authority_level", "self")),
            ))
        return ApprovalRequest(
            id=model.id,
            tenant_id=model.tenant_id,
            target_type=ApprovalTargetType(model.target_type),
            target_id=model.target_id,
            requested_by=model.requested_by,
            action_summary=model.action_summary,
            action_evidence=model.action_evidence or [],
            required_level=ApprovalLevel(model.required_level),
            status=ApprovalStatus(model.status),
            assigned_to=model.assigned_to,
            decisions=decisions,
            metadata=model.extra_metadata or {},
            priority=int(model.priority),
            expires_at=model.expires_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _from_domain(self, request: ApprovalRequest) -> ApprovalRequestModel:
        decisions_data = [
            {
                "decision": d.decision,
                "decided_by": d.decided_by,
                "decided_at": d.decided_at.isoformat(),
                "comments": d.comments,
                "authority_level": d.authority_level.value,
            }
            for d in request.decisions
        ]
        return ApprovalRequestModel(
            id=request.id,
            tenant_id=request.tenant_id,
            target_type=request.target_type.value,
            target_id=request.target_id,
            requested_by=request.requested_by,
            action_summary=request.action_summary,
            action_evidence=request.action_evidence,
            required_level=request.required_level.value,
            status=request.status.value,
            assigned_to=request.assigned_to,
            decisions=decisions_data,
            extra_metadata=request.metadata,
            priority=float(request.priority),
            expires_at=request.expires_at,
            created_at=request.created_at,
            updated_at=request.updated_at,
        )

    async def save(self, request: ApprovalRequest) -> ApprovalRequest:
        existing = await self.session.get(ApprovalRequestModel, request.id)
        if existing:
            model = self._from_domain(request)
            for col in ApprovalRequestModel.__table__.columns.keys():
                if col == "id":
                    continue
                setattr(existing, col, getattr(model, col))
        else:
            existing = self._from_domain(request)
            self.session.add(existing)
        await self.session.flush()
        return request

    async def get(self, request_id: str) -> ApprovalRequest | None:
        model = await self.session.get(ApprovalRequestModel, request_id)
        if not model:
            return None
        return self._to_domain(model)

    async def list_by_tenant(
        self, tenant_id: str, status: str | None = None, target_type: str | None = None
    ) -> list[ApprovalRequest]:
        q = select(ApprovalRequestModel).where(ApprovalRequestModel.tenant_id == tenant_id)
        if status:
            q = q.where(ApprovalRequestModel.status == status)
        if target_type:
            q = q.where(ApprovalRequestModel.target_type == target_type)
        q = q.order_by(ApprovalRequestModel.priority.asc(), ApprovalRequestModel.created_at.desc())
        result = await self.session.execute(q)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    async def list_pending(
        self, tenant_id: str, assigned_to: str | None = None
    ) -> list[ApprovalRequest]:
        q = select(ApprovalRequestModel).where(
            ApprovalRequestModel.tenant_id == tenant_id,
            ApprovalRequestModel.status == "pending",
        )
        if assigned_to:
            q = q.where(ApprovalRequestModel.assigned_to == assigned_to)
        q = q.order_by(ApprovalRequestModel.priority.asc(), ApprovalRequestModel.created_at.desc())
        result = await self.session.execute(q)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    async def count_by_status(self, tenant_id: str) -> dict[str, int]:
        q = select(
            ApprovalRequestModel.status,
            func.count(ApprovalRequestModel.id),
        ).where(ApprovalRequestModel.tenant_id == tenant_id).group_by(ApprovalRequestModel.status)
        result = await self.session.execute(q)
        return {row[0]: row[1] for row in result.all()}
