"""Authenticated API for reading and reviewing canonical fact proposals."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.rate_limit import rate_limit_dep
from app.dependencies import (
    get_current_tenant_id,
    get_current_user_id,
    get_current_user_role,
    get_db_session,
    require_permission_dep,
    verify_token,
)
from app.modules.agent_reach.fact_proposals import AgentReachFactProposalBridge
from app.modules.facts.apply_service import (
    FactApplyNotFound,
    FactApplyRejected,
    FactApplyService,
)
from app.modules.facts.review_service import (
    FactReviewNotFound,
    FactReviewService,
    FactTransitionRejected,
)
from app.modules.facts.service import (
    DismissedValueBlocked,
    DuplicateOpenProposal,
    FactPolicyRejected,
    FactProposalService,
    IdempotencyConflict,
)
from app.modules.identity.models import User
from domains.commercial.evidence.contracts.models import ConfidenceLevel, EvidenceItem, EvidenceKind
from sdk.exceptions import PermissionDeniedError
from sdk.permissions import PermissionAction, PermissionEnforcer

router = APIRouter(dependencies=[Depends(rate_limit_dep("fact-review", 30, 60))])

_AGENT_REACH_SERVICE_SCOPES = frozenset(
    {"agent_reach:read", "master-data-review:create"}
)


@dataclass(frozen=True)
class AgentReachProposalActor:
    tenant_id: str
    actor_id: str
    actor_type: Literal["human", "agent"]


async def get_agent_reach_proposal_actor(
    request: Request,
    authorization: str | None = Header(None, description="Bearer token for human callers"),
    x_api_key: str | None = Header(None, alias="X-API-Key", description="Scoped Minder API key"),
    x_tenant_id: str | None = Header(None, alias="X-Tenant-Id"),
    db: AsyncSession = Depends(get_db_session),
) -> AgentReachProposalActor:
    """Authorize a human JWT or the least-privilege Minder producer API key."""
    if authorization:
        token = await verify_token(authorization=authorization)
        user_id = str(token.get("sub", "") or "")
        token_tenant = str(token.get("tenant_id", "") or "")
        tenant_id = x_tenant_id or token_tenant
        if not user_id or not tenant_id or (x_tenant_id and token_tenant != x_tenant_id):
            raise HTTPException(status_code=403, detail="Authenticated tenant context is invalid")

        try:
            user_uuid = UUID(user_id)
            tenant_uuid = UUID(tenant_id)
        except ValueError as exc:
            raise HTTPException(status_code=401, detail="Authenticated identity is invalid") from exc
        user = await db.scalar(
            select(User).where(
                User.id == user_uuid,
                User.tenant_id == tenant_uuid,
                User.is_active.is_(True),
                User.deleted_at.is_(None),
            )
        )
        if user is None:
            raise HTTPException(status_code=401, detail="Authenticated user is unavailable")
        if user.role == "agent_reach_service":
            raise HTTPException(
                status_code=403,
                detail="Agent Reach service principals must use a scoped API key",
            )
        try:
            PermissionEnforcer.check(user.role, "agent_reach", PermissionAction.READ)
            PermissionEnforcer.check(
                user.role, "master-data-review", PermissionAction.CREATE
            )
        except PermissionDeniedError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        return AgentReachProposalActor(tenant_id, user_id, "human")

    state = request.state
    if not x_api_key or not getattr(state, "api_key_authenticated", False):
        raise HTTPException(status_code=401, detail="Not authenticated")

    api_key_id = str(getattr(state, "api_key_id", "") or "")
    user_id = str(getattr(state, "api_key_user_id", "") or "")
    tenant_id = str(getattr(state, "api_key_tenant_id", "") or "")
    scopes = frozenset(getattr(state, "api_key_scopes", []) or [])
    if not api_key_id or not user_id or not tenant_id:
        raise HTTPException(status_code=401, detail="API key identity is incomplete")
    if scopes != _AGENT_REACH_SERVICE_SCOPES:
        raise HTTPException(status_code=403, detail="API key scopes are not permitted")
    if not x_tenant_id or x_tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="API key tenant mismatch")

    try:
        user_uuid = UUID(user_id)
        tenant_uuid = UUID(tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="API key identity is invalid") from exc

    user = await db.scalar(
        select(User).where(
            User.id == user_uuid,
            User.tenant_id == tenant_uuid,
            User.role == "agent_reach_service",
            User.is_active.is_(True),
            User.deleted_at.is_(None),
        )
    )
    if user is None:
        raise HTTPException(status_code=403, detail="API key is not bound to an active service user")
    try:
        PermissionEnforcer.check(user.role, "agent_reach", PermissionAction.READ)
        PermissionEnforcer.check(user.role, "master-data-review", PermissionAction.CREATE)
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    return AgentReachProposalActor(
        tenant_id,
        f"agent_reach_service:{user_id}:api_key:{api_key_id}",
        "agent",
    )


class FactDecisionRequest(BaseModel):
    decision: str = Field(pattern="^(approve|reject|dismiss)$")
    reason: str = Field(min_length=1, max_length=2000)


class FactApplyRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=2000)


class FactProposalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subject_type: Literal["company", "contact"]
    subject_id: UUID
    field_name: str = Field(min_length=1, max_length=100)
    proposed_value: Any
    evidence: list[EvidenceItem] = Field(min_length=1, max_length=20)
    idempotency_token: str = Field(min_length=1, max_length=255)


class AgentReachFactProposalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_id: UUID
    evidence_id: UUID
    field_name: str = Field(min_length=1, max_length=100)
    proposed_value: Any


def _fact_response(fact: Any) -> dict[str, Any]:
    return {
        "id": str(fact.id),
        "subject_type": fact.subject_type,
        "subject_id": str(fact.subject_id),
        "field_name": fact.field_name,
        "proposed_value": fact.proposed_value,
        "value_hash": fact.value_hash,
        "status": fact.status,
        "evidence_band": fact.evidence_band,
        "score": fact.score,
        "decision_reason": fact.decision_reason,
        "actor_type": fact.actor_type,
        "actor_id": fact.actor_id,
        "evidence_snapshot": fact.evidence_snapshot,
        "created_at": (
            fact.created_at.isoformat() if isinstance(fact.created_at, datetime) else None
        ),
        "reviewer_id": fact.reviewer_id,
        "reviewed_at": fact.reviewed_at.isoformat() if fact.reviewed_at else None,
    }


@router.post(
    "/facts/proposals",
    dependencies=[Depends(require_permission_dep("master-data-review", PermissionAction.CREATE))],
)
async def create_fact_proposal(
    body: FactProposalRequest,
    user_id: str = Depends(get_current_user_id),
    user_role: str = Depends(get_current_user_role),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    if user_role == "agent_reach_service":
        raise HTTPException(
            status_code=403,
            detail="Agent Reach service principals must use the scoped evidence proposal route",
        )
    try:
        # The human-facing API cannot verify a client's claimed evidence class.
        # Treat every submitted item as a cited claim until a trusted producer
        # independently classifies its source; confidence input is not proof.
        submitted_evidence = [
            replace(
                item,
                evidence_kind=EvidenceKind.CITED_CLAIM,
                confidence_level=ConfidenceLevel.UNKNOWN,
            )
            for item in body.evidence
        ]
        result = await FactProposalService(db).propose(
            tenant_id=tenant_id,
            subject_type=body.subject_type,
            subject_id=body.subject_id,
            field_name=body.field_name,
            proposed_value=body.proposed_value,
            evidence=submitted_evidence,
            idempotency_token=body.idempotency_token,
            actor_type="human",
            actor_id=user_id,
        )
    except (DuplicateOpenProposal, DismissedValueBlocked, IdempotencyConflict) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except FactPolicyRejected as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "id": str(result.fact_id),
        "status": result.status,
        "created": result.created,
        "crm_applied": False,
    }


@router.post(
    "/facts/proposals/from-agent-reach",
    summary="Propose a fact from persisted Agent Reach evidence",
    description=(
        "Creates a review-only proposal. Supports an authorized human JWT or a scoped "
        "Minder API key bound to an active agent_reach_service user. API-key callers "
        "must also send X-Tenant-Id and satisfy the standard CSRF cookie/header check. "
        "This endpoint never applies values to CRM."
    ),
)
async def create_agent_reach_fact_proposal(
    body: AgentReachFactProposalRequest,
    actor: AgentReachProposalActor = Depends(get_agent_reach_proposal_actor),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """Create a review-only proposal from persisted Agent Reach evidence.

    Human JWT callers and the dedicated, narrowly-scoped Minder API principal
    are supported. This endpoint never applies the proposed value to CRM.
    """
    try:
        actor_fields = (
            {"requested_by": actor.actor_id}
            if actor.actor_type == "human"
            else {"service_actor_id": actor.actor_id}
        )
        result = await AgentReachFactProposalBridge(db).propose_from_evidence(
            tenant_id=actor.tenant_id,
            company_id=body.company_id,
            evidence_id=body.evidence_id,
            field_name=body.field_name,
            proposed_value=body.proposed_value,
            **actor_fields,
        )
    except (DuplicateOpenProposal, DismissedValueBlocked, IdempotencyConflict) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except FactPolicyRejected as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "id": str(result.fact_id),
        "status": result.status,
        "created": result.created,
        "crm_applied": False,
    }


@router.get(
    "/facts/proposals",
    dependencies=[Depends(require_permission_dep("master-data-review", PermissionAction.READ))],
)
async def list_fact_proposals(
    status: str = Query(
        default="PROPOSED",
        pattern="^(PROPOSED|APPROVED|REJECTED|DISMISSED|APPLIED|SUPERSEDED|STALE)$",
    ),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=100_000),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    try:
        facts = await FactReviewService(db).list_proposals(
            tenant_id=tenant_id,
            status=status,
            limit=limit,
            offset=offset,
        )
    except FactTransitionRejected as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"items": [_fact_response(fact) for fact in facts], "limit": limit, "offset": offset}


@router.post(
    "/facts/{fact_id}/decision",
    dependencies=[Depends(require_permission_dep("master-data-review", PermissionAction.UPDATE))],
)
async def decide_fact_proposal(
    fact_id: str,
    body: FactDecisionRequest,
    user_id: str = Depends(get_current_user_id),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    try:
        result = await FactReviewService(db).decide(
            tenant_id=tenant_id,
            fact_id=fact_id,
            decision=body.decision,
            reviewer_id=user_id,
            reason=body.reason,
        )
    except FactReviewNotFound as exc:
        raise HTTPException(status_code=404, detail="Fact proposal not found") from exc
    except FactTransitionRejected as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {
        "id": str(result.fact_id),
        "status": result.status,
        "reviewed_at": result.reviewed_at.isoformat(),
        "changed": result.changed,
        "crm_applied": False,
    }


@router.post(
    "/facts/{fact_id}/apply",
    dependencies=[Depends(require_permission_dep("master-data-review", PermissionAction.UPDATE))],
    summary="Apply an approved canonical fact to CRM",
)
async def apply_fact_proposal(
    fact_id: str,
    body: FactApplyRequest,
    user_id: str = Depends(get_current_user_id),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """Cross the explicit human-approved, tenant-scoped CRM write boundary."""
    try:
        result = await FactApplyService(db).apply(
            tenant_id=tenant_id,
            fact_id=fact_id,
            actor_id=user_id,
            reason=body.reason,
        )
    except FactApplyNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FactApplyRejected as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {
        "id": str(result.fact_id),
        "status": result.status,
        "changed": result.changed,
        "subject_type": result.subject_type,
        "subject_id": str(result.subject_id),
        "field_name": result.field_name,
        "previous_value": result.previous_value,
        "applied_value": result.applied_value,
        "applied_at": result.applied_at.isoformat(),
        "crm_applied": True,
    }
