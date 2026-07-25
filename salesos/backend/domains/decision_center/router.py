"""Decision Center REST endpoints."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.dependencies import get_current_tenant_id, verify_token

router = APIRouter(dependencies=[Depends(verify_token)])


# ── Request / Response schemas ────────────────────────────────────────


class CreateDecisionRequest(BaseModel):
    domain: str = Field(..., description="Source domain: pipeline, employee, company, revenue")
    decision_type: str = Field(..., description="Decision type")
    entity_id: str
    entity_type: str
    decision: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    provider: str = "rule_engine"
    alternatives: Optional[list[dict[str, Any]]] = None
    metadata: Optional[dict[str, Any]] = None


class DecisionResponse(BaseModel):
    id: str
    domain: str
    type: str
    entityId: str
    entityType: str
    decision: str
    confidence: float
    reasoning: str
    provider: str
    alternatives: list[dict[str, Any]]
    timestamp: str
    status: str
    metadata: Optional[dict[str, Any]] = None
    isEnsemble: bool
    ensembleVotes: Optional[list[dict[str, Any]]] = None


class DecisionListResponse(BaseModel):
    items: list[DecisionResponse]
    total: int
    limit: int
    next_cursor: str | None = None
    has_next: bool = False


class AuditResponse(BaseModel):
    decisionId: str
    inputContext: dict[str, Any]
    reasoningSteps: list[dict[str, Any]]
    confidenceBreakdown: dict[str, Any]
    providerUsed: str
    alternativesConsidered: list[dict[str, Any]]
    timestamp: str
    ensembleMetadata: Optional[dict[str, Any]] = None


class FeedbackRequest(BaseModel):
    rating: str = Field(..., pattern="^(up|down)$")
    comment: Optional[str] = None
    actor_id: Optional[str] = None


class FeedbackResponse(BaseModel):
    id: str
    decisionId: str
    rating: str
    comment: Optional[str]
    actorId: Optional[str]
    createdAt: str


class FeedbackAggregateResponse(BaseModel):
    decisionType: str
    totalFeedback: int
    upCount: int
    downCount: int
    approvalRate: float


class TemplateRequest(BaseModel):
    name: str
    type: str
    config: dict[str, Any]


class TemplateResponse(BaseModel):
    id: str
    name: str
    type: str
    config: dict[str, Any]
    createdAt: str


class TemplateUpdateRequest(BaseModel):
    name: Optional[str] = None
    config: Optional[dict[str, Any]] = None


def _get_service(request: Request):
    svc = getattr(request.app.state, "decision_center_service", None)
    if not svc:
        raise HTTPException(status_code=503, detail="Decision Center service not initialized")
    return svc


# ── B-1: Decision Center Aggregation ──────────────────────────────────


@router.post("/decisions", response_model=DecisionResponse, status_code=201)
async def create_decision(
    body: CreateDecisionRequest,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
):
    svc = _get_service(request)
    decision = await svc.create_decision(
        domain=body.domain,
        decision_type=body.decision_type,
        entity_id=body.entity_id,
        entity_type=body.entity_type,
        decision=body.decision,
        confidence=body.confidence,
        reasoning=body.reasoning,
        provider=body.provider,
        tenant_id=tenant_id,
        alternatives=body.alternatives,
        metadata=body.metadata,
    )
    return DecisionResponse(**decision.to_dict())


@router.get("/decisions", response_model=DecisionListResponse)
async def list_decisions(
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    domain: Optional[str] = Query(None),
    type: Optional[str] = Query(None, alias="type"),
    entity_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    confidence_min: Optional[float] = Query(None, ge=0.0, le=1.0),
    confidence_max: Optional[float] = Query(None, ge=0.0, le=1.0),
    limit: int = Query(50, ge=1, le=200),
    cursor: str | None = Query(None, description="Keyset cursor for pagination"),
):
    from sdk.pagination import decode_cursor, encode_cursor

    svc = _get_service(request)
    items, total = await svc.list_decisions(
        tenant_id,
        domain=domain,
        decision_type=type,
        entity_id=entity_id,
        status=status,
        date_from=date_from,
        date_to=date_to,
        confidence_min=confidence_min,
        confidence_max=confidence_max,
        limit=limit + 1,
        offset=0,
    )

    has_next = len(items) > limit
    if has_next:
        items = items[:limit]

    next_cursor = None
    if has_next and items:
        last = items[-1]
        next_cursor = encode_cursor(str(last.id), last.created_at)

    return DecisionListResponse(
        items=[DecisionResponse(**d.to_dict()) for d in items],
        total=total,
        limit=limit,
        next_cursor=next_cursor,
        has_next=has_next,
    )


@router.get("/decisions/{decision_id}", response_model=DecisionResponse)
async def get_decision(
    decision_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
):
    svc = _get_service(request)
    decision = await svc.get_decision(decision_id, tenant_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    return DecisionResponse(**decision.to_dict())


# ── B-2: Audit Trail ──────────────────────────────────────────────────


@router.get("/decisions/{decision_id}/audit", response_model=AuditResponse)
async def get_audit_trail(
    decision_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
):
    svc = _get_service(request)
    audit = await svc.get_audit(decision_id, tenant_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit trail not found for this decision")
    return AuditResponse(**audit.to_dict())


# ── B-3: Feedback ─────────────────────────────────────────────────────


@router.post("/decisions/{decision_id}/feedback", response_model=FeedbackResponse, status_code=201)
async def submit_feedback(
    decision_id: str,
    body: FeedbackRequest,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
):
    svc = _get_service(request)
    feedback = await svc.submit_feedback(
        decision_id=decision_id,
        rating=body.rating,
        tenant_id=tenant_id,
        comment=body.comment,
        actor_id=body.actor_id,
    )
    if not feedback:
        raise HTTPException(status_code=404, detail="Decision not found")
    return FeedbackResponse(**feedback.to_dict())


@router.get(
    "/decisions/{decision_id}/feedback",
    response_model=list[FeedbackResponse],
)
async def get_decision_feedback(
    decision_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
):
    svc = _get_service(request)
    feedbacks = await svc.get_feedback_for_decision(decision_id, tenant_id)
    return [FeedbackResponse(**fb.to_dict()) for fb in feedbacks]


@router.get(
    "/decisions/feedback/aggregate",
    response_model=list[FeedbackAggregateResponse],
)
async def get_feedback_aggregates(
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
):
    svc = _get_service(request)
    aggregates = await svc.get_feedback_aggregates(tenant_id)
    return [FeedbackAggregateResponse(**a.to_dict()) for a in aggregates]


# ── B-4: Decision Templates ───────────────────────────────────────────


@router.post("/decision-templates", response_model=TemplateResponse, status_code=201)
async def create_template(
    body: TemplateRequest,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
):
    svc = _get_service(request)
    template = await svc.create_template(body.name, body.type, body.config, tenant_id)
    return TemplateResponse(**template.to_dict())


@router.get("/decision-templates", response_model=list[TemplateResponse])
async def list_templates(
    request: Request,
    type: Optional[str] = Query(None, alias="type"),
    tenant_id: str = Depends(get_current_tenant_id),
):
    svc = _get_service(request)
    templates = await svc.list_templates(type, tenant_id)
    return [TemplateResponse(**t.to_dict()) for t in templates]


@router.get("/decision-templates/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
):
    svc = _get_service(request)
    template = await svc.get_template(template_id, tenant_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return TemplateResponse(**template.to_dict())


@router.patch("/decision-templates/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: str,
    body: TemplateUpdateRequest,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
):
    svc = _get_service(request)
    template = await svc.update_template(
        template_id, name=body.name, config=body.config, tenant_id=tenant_id
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return TemplateResponse(**template.to_dict())


@router.delete("/decision-templates/{template_id}", status_code=204)
async def delete_template(
    template_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
):
    svc = _get_service(request)
    deleted = await svc.delete_template(template_id, tenant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Template not found")
    return None


@router.post("/decision-templates/seed", response_model=list[TemplateResponse])
async def seed_default_templates(
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
):
    svc = _get_service(request)
    templates = await svc.seed_default_templates(tenant_id)
    return [TemplateResponse(**t.to_dict()) for t in templates]
