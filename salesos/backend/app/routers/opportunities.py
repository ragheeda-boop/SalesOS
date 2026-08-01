"""Opportunity REST API — CRUD, stage management, pipeline analytics."""

import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from app.common.rate_limit import rate_limit_dep
from app.dependencies import get_current_tenant_id, require_permission_dep
from sdk.permissions import PermissionAction

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(rate_limit_dep("opportunity", 60, 60))])


class OpportunityCreateRequest(BaseModel):
    company_id: str
    name: str
    value: float = 0.0
    currency: str = "SAR"
    expected_close_date: date | None = None
    owner_id: str = ""
    description: str = ""


class OpportunityUpdateRequest(BaseModel):
    name: str | None = None
    value: float | None = None
    expected_close_date: date | None = None
    description: str | None = None


class OpportunityStageChangeRequest(BaseModel):
    stage: str
    reason: str | None = None


class OpportunityResponse(BaseModel):
    id: str
    company_id: str
    name: str
    stage: str
    value: float
    currency: str
    probability: float
    health: str = "healthy"
    expected_close_date: date | None = None
    owner_id: str
    status: str
    description: str = ""
    created_at: str
    updated_at: str


def _to_response(opp) -> OpportunityResponse:
    return OpportunityResponse(
        id=opp.id,
        company_id=opp.company_id,
        name=opp.name,
        stage=opp.stage,
        value=opp.value,
        currency=opp.currency,
        probability=opp.probability,
        health=getattr(opp, "health", "healthy"),
        expected_close_date=opp.expected_close_date,
        owner_id=opp.owner_id,
        status=opp.status.value if hasattr(opp.status, "value") else opp.status,
        description=opp.description,
        created_at=opp.created_at.isoformat()
        if hasattr(opp.created_at, "isoformat")
        else str(opp.created_at),
        updated_at=opp.updated_at.isoformat()
        if hasattr(opp.updated_at, "isoformat")
        else str(opp.updated_at),
    )


@router.get("/opportunities", response_model=list[OpportunityResponse])
async def list_opportunities(
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    stage: str | None = Query(None),
    status: str | None = Query(None),
    company_id: str | None = Query(None),
    owner_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    cursor: str | None = Query(None),
    _rbac: None = Depends(require_permission_dep("opportunity", PermissionAction.READ)),
):
    """List opportunities with cursor-based pagination."""
    try:
        svc = getattr(request.app.state, "opportunity_service", None)
        if not svc:
            raise HTTPException(status_code=503, detail="Opportunity service not initialized")
        from domains.commercial.opportunity.contracts.models import OpportunityStatus
        from domains.commercial.opportunity.contracts.repository import OpportunityQuery

        offset = 0
        if cursor:
            try:
                offset = int(cursor)
            except (ValueError, TypeError):
                offset = 0
        page = (offset // limit) + 1 if limit else 1
        status_enum: OpportunityStatus | None = None
        if status:
            try:
                status_enum = OpportunityStatus(status)
            except ValueError:
                status_enum = None
        query = OpportunityQuery(
            tenant_id=tenant_id,
            stage=stage or "",
            status=status_enum,
            company_id=company_id or "",
            owner_id=owner_id or "",
            page=page,
            page_size=limit,
        )
        result = await svc.query(query)
        next_cursor = str(offset + limit) if offset + limit < result.total else None
        return {
            "items": [_to_response(o) for o in result.items],
            "next_cursor": next_cursor,
            "total": result.total,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("list_opportunities failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/opportunities/{opportunity_id}", response_model=OpportunityResponse)
async def get_opportunity(
    opportunity_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("opportunity", PermissionAction.READ)),
):
    try:
        svc = getattr(request.app.state, "opportunity_service", None)
        if not svc:
            raise HTTPException(status_code=503, detail="Opportunity service not initialized")
        opp = await svc.get(opportunity_id)
        if not opp:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        if getattr(opp, "tenant_id", None) != tenant_id:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        return _to_response(opp)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("get_opportunity failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post("/opportunities", response_model=OpportunityResponse, status_code=201)
async def create_opportunity(
    body: OpportunityCreateRequest,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("opportunity", PermissionAction.CREATE)),
):
    svc = getattr(request.app.state, "opportunity_service", None)
    if not svc:
        raise HTTPException(status_code=503, detail="Opportunity service not initialized")
    opp = await svc.create_opportunity(
        tenant_id=tenant_id,
        company_id=body.company_id,
        name=body.name,
        value=body.value,
        owner_id=body.owner_id,
        expected_close_date=body.expected_close_date,
        description=body.description,
    )
    return _to_response(opp)


@router.put("/opportunities/{opportunity_id}", response_model=OpportunityResponse)
async def update_opportunity(
    opportunity_id: str,
    body: OpportunityUpdateRequest,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("opportunity", PermissionAction.UPDATE)),
):
    try:
        svc = getattr(request.app.state, "opportunity_service", None)
        if not svc:
            raise HTTPException(status_code=503, detail="Opportunity service not initialized")
        opp = await svc.get(opportunity_id)
        if not opp:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        if getattr(opp, "tenant_id", None) != tenant_id:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        if body.name is not None:
            opp.name = body.name
        if body.value is not None:
            opp = await svc.update_value(opportunity_id, body.value)
        if body.expected_close_date is not None:
            opp.expected_close_date = body.expected_close_date
        if body.description is not None:
            opp.description = body.description
        return _to_response(opp)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("update_opportunity failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.patch("/opportunities/{opportunity_id}/stage", response_model=OpportunityResponse)
async def advance_stage(
    opportunity_id: str,
    body: OpportunityStageChangeRequest,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("opportunity", PermissionAction.UPDATE)),
):
    try:
        svc = getattr(request.app.state, "opportunity_service", None)
        if not svc:
            raise HTTPException(status_code=503, detail="Opportunity service not initialized")
        opp = await svc.get(opportunity_id)
        if not opp or getattr(opp, "tenant_id", None) != tenant_id:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        opp = await svc.advance_stage(opportunity_id, body.stage)
        return _to_response(opp)
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid stage transition") from None
    except Exception as exc:
        logger.error("advance_stage failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post("/opportunities/{opportunity_id}/close-won", response_model=OpportunityResponse)
async def close_won(
    opportunity_id: str,
    request: Request,
    won_amount: float | None = None,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("opportunity", PermissionAction.UPDATE)),
):
    try:
        svc = getattr(request.app.state, "opportunity_service", None)
        if not svc:
            raise HTTPException(status_code=503, detail="Opportunity service not initialized")
        opp = await svc.get(opportunity_id)
        if not opp or getattr(opp, "tenant_id", None) != tenant_id:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        opp = await svc.close_won(opportunity_id, won_amount)
        return _to_response(opp)
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid close operation") from None
    except Exception as exc:
        logger.error("close_won failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post("/opportunities/{opportunity_id}/close-lost", response_model=OpportunityResponse)
async def close_lost(
    opportunity_id: str,
    request: Request,
    loss_reason: str = "",
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("opportunity", PermissionAction.UPDATE)),
):
    try:
        svc = getattr(request.app.state, "opportunity_service", None)
        if not svc:
            raise HTTPException(status_code=503, detail="Opportunity service not initialized")
        opp = await svc.get(opportunity_id)
        if not opp or getattr(opp, "tenant_id", None) != tenant_id:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        opp = await svc.close_lost(opportunity_id, loss_reason)
        return _to_response(opp)
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid close operation") from None
    except Exception as exc:
        logger.error("close_lost failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc
