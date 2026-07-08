from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.dependencies import get_current_tenant_id, require_permission_dep
from sdk.permissions import PermissionAction
from .schemas import WorkIntelligenceResponse

router = APIRouter()


def _get_engine(request: Request):
    engine = getattr(request.app.state, "work_intelligence_engine", None)
    if not engine:
        raise HTTPException(status_code=503, detail="Work Intelligence Engine not initialized")
    return engine


@router.get("/work-intelligence/{employee_id}", response_model=WorkIntelligenceResponse, dependencies=[Depends(require_permission_dep("work-intelligence", PermissionAction.READ))])
async def get_work_intelligence(
    employee_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    period_days: int = Query(30, ge=1, le=90),
):
    engine = _get_engine(request)
    return await engine.analyze(
        employee_id=employee_id,
        tenant_id=tenant_id,
        period_days=period_days,
    )


@router.get("/work-intelligence/me", response_model=WorkIntelligenceResponse, dependencies=[Depends(require_permission_dep("work-intelligence", PermissionAction.READ))])
async def get_my_work_intelligence(
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    period_days: int = Query(30, ge=1, le=90),
):
    engine = _get_engine(request)
    employee_id = getattr(request.state, "user_id", None)
    if not employee_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
    return await engine.analyze(
        employee_id=employee_id,
        tenant_id=tenant_id,
        period_days=period_days,
    )
