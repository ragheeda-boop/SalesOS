"""Approval REST API — human-in-the-loop approval workflow for AI recommendations."""
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.dependencies import get_current_tenant_id, require_permission_dep
from app.common.rate_limit import rate_limit_dep
from sdk.permissions import PermissionAction
from domains.approval.engine.service import ApprovalService
from domains.approval.contracts.models import (
    ApprovalLevel,
    ApprovalStatus,
    ApprovalTargetType,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    dependencies=[Depends(rate_limit_dep("approval", 30, 60))]
)


class ApprovalRequestCreate(BaseModel):
    target_type: str = Field(max_length=50)
    target_id: str = Field(max_length=36)
    action_summary: str = Field(max_length=2000)
    action_evidence: list[str] = Field(default_factory=list)
    required_level: str = Field(default="manager", max_length=20)
    assigned_to: str = Field(default="", max_length=36)
    priority: int = Field(default=5, ge=1, le=10)
    ttl_hours: int = Field(default=48, ge=1, le=720)
    metadata: dict = Field(default_factory=dict)


class ApprovalDecisionRequest(BaseModel):
    decision: str = Field(pattern="^(approve|reject|escalate)$")
    comments: str = Field(default="", max_length=2000)
    authority_level: str = Field(default="self", max_length=20)


def _to_response(request) -> dict:
    return {
        "id": request.id,
        "tenant_id": request.tenant_id,
        "target_type": request.target_type.value,
        "target_id": request.target_id,
        "requested_by": request.requested_by,
        "action_summary": request.action_summary,
        "action_evidence": request.action_evidence,
        "required_level": request.required_level.value,
        "status": request.status.value,
        "assigned_to": request.assigned_to,
        "decisions": [
            {
                "decision": d.decision,
                "decided_by": d.decided_by,
                "decided_at": d.decided_at.isoformat(),
                "comments": d.comments,
                "authority_level": d.authority_level.value,
            }
            for d in request.decisions
        ],
        "metadata": request.metadata,
        "priority": request.priority,
        "expires_at": request.expires_at.isoformat() if request.expires_at else None,
        "created_at": request.created_at.isoformat(),
        "updated_at": request.updated_at.isoformat(),
    }


def _get_service(request: Request) -> ApprovalService:
    svc = getattr(request.app.state, "approval_service", None)
    if not svc:
        raise HTTPException(status_code=503, detail="Approval service not initialized")
    return svc


@router.post("/approvals")
async def create_approval(
    body: ApprovalRequestCreate,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("approval", PermissionAction.CREATE)),
):
    svc = _get_service(request)
    user_id = getattr(request.state, "user_id", "system")
    try:
        target_type = ApprovalTargetType(body.target_type)
        required_level = ApprovalLevel(body.required_level)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    req = await svc.create_request(
        tenant_id=tenant_id,
        target_type=target_type,
        target_id=body.target_id,
        requested_by=user_id,
        action_summary=body.action_summary,
        action_evidence=body.action_evidence,
        required_level=required_level,
        assigned_to=body.assigned_to,
        priority=body.priority,
        ttl_hours=body.ttl_hours,
        metadata=body.metadata,
    )
    return _to_response(req)


@router.get("/approvals")
async def list_approvals(
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    status: str | None = None,
    target_type: str | None = None,
    _rbac: None = Depends(require_permission_dep("approval", PermissionAction.READ)),
):
    svc = _get_service(request)
    items = await svc.list_by_tenant(tenant_id, status=status, target_type=target_type)
    return {"approvals": [_to_response(i) for i in items], "count": len(items)}


@router.get("/approvals/pending")
async def list_pending_approvals(
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    assigned_to: str | None = None,
    _rbac: None = Depends(require_permission_dep("approval", PermissionAction.READ)),
):
    svc = _get_service(request)
    items = await svc.list_pending(tenant_id, assigned_to=assigned_to)
    return {"approvals": [_to_response(i) for i in items], "count": len(items)}


@router.get("/approvals/{approval_id}")
async def get_approval(
    approval_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("approval", PermissionAction.READ)),
):
    svc = _get_service(request)
    req = await svc.get(approval_id)
    if not req:
        raise HTTPException(status_code=404, detail="Approval request not found")
    return _to_response(req)


@router.post("/approvals/{approval_id}/decide")
async def decide_approval(
    approval_id: str,
    body: ApprovalDecisionRequest,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("approval", PermissionAction.UPDATE)),
):
    svc = _get_service(request)
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="User identity required")
    try:
        authority_level = ApprovalLevel(body.authority_level)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    try:
        if body.decision == "approve":
            req = await svc.approve(
                approval_id, user_id, authority_level=authority_level, comments=body.comments
            )
        elif body.decision == "reject":
            req = await svc.reject(
                approval_id, user_id, authority_level=authority_level, comments=body.comments
            )
        else:
            req = await svc.escalate(approval_id, user_id, comments=body.comments)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _to_response(req)


@router.get("/approvals/kpis")
async def approval_kpis(
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("approval", PermissionAction.READ)),
):
    svc = _get_service(request)
    return await svc.kpis(tenant_id)
