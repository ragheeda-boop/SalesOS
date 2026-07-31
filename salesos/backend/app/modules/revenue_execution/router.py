from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_tenant_id, get_db_session, require_permission_dep
from app.modules.revenue_execution.schemas import (
    OpportunityCreate,
    OpportunityResponse,
    OpportunityStageUpdate,
    PipelineResponse,
    TaskCreate,
    TaskResponse,
)
from app.modules.revenue_execution.service import RevenueService
from sdk.permissions import PermissionAction

router = APIRouter(prefix="/api/v1")


def get_service(db: AsyncSession = Depends(get_db_session)) -> RevenueService:
    return RevenueService(db)


@router.post(
    "/opportunities",
    response_model=OpportunityResponse,
    status_code=201,
    dependencies=[Depends(require_permission_dep("opportunity", PermissionAction.CREATE))],
)
async def create_opportunity(
    body: OpportunityCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    service: RevenueService = Depends(get_service),
):
    return await service.create_opportunity(
        tenant_id=tenant_id,
        company_id=body.company_id,
        title=body.title,
        estimated_value=float(body.estimated_value),
        confidence=float(body.confidence),
        buying_intent=float(body.buying_intent) if body.buying_intent else 0.5,
        relationship_strength=float(body.relationship_strength)
        if body.relationship_strength
        else 0.5,
        source_action_id=body.source_action_id,
    )


@router.get(
    "/opportunities",
    dependencies=[Depends(require_permission_dep("opportunity", PermissionAction.READ))],
)
async def list_opportunities(
    stage: str | None = Query(None),
    page: int = Query(1, ge=1),
    tenant_id: str = Depends(get_current_tenant_id),
    service: RevenueService = Depends(get_service),
):
    return await service.list_opportunities(tenant_id, stage, page)


@router.put(
    "/opportunities/{opportunity_id}/stage",
    dependencies=[Depends(require_permission_dep("opportunity", PermissionAction.UPDATE))],
)
async def update_opportunity_stage(
    opportunity_id: str,
    body: OpportunityStageUpdate,
    tenant_id: str = Depends(get_current_tenant_id),
    service: RevenueService = Depends(get_service),
):
    result = await service.update_stage(opportunity_id, body.stage, tenant_id)
    if not result:
        from fastapi import HTTPException

        raise HTTPException(404, "Opportunity not found")
    return result


@router.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=201,
    dependencies=[Depends(require_permission_dep("task", PermissionAction.CREATE))],
)
async def create_task(
    body: TaskCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    service: RevenueService = Depends(get_service),
):
    return await service.create_task(
        tenant_id=tenant_id,
        title=body.title,
        priority=body.priority,
        source=body.source,
        company_id=body.company_id,
        due_date=str(body.due_date) if body.due_date else None,
    )


@router.get("/tasks", dependencies=[Depends(require_permission_dep("task", PermissionAction.READ))])
async def list_tasks(
    priority: str | None = Query(None),
    tenant_id: str = Depends(get_current_tenant_id),
    service: RevenueService = Depends(get_service),
):
    return await service.list_tasks(tenant_id, priority)


@router.put(
    "/tasks/{task_id}/complete",
    dependencies=[Depends(require_permission_dep("task", PermissionAction.UPDATE))],
)
async def complete_task(
    task_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    service: RevenueService = Depends(get_service),
):
    result = await service.complete_task(task_id, tenant_id)
    if not result:
        from fastapi import HTTPException

        raise HTTPException(404, "Task not found")
    return result


@router.get(
    "/pipeline",
    response_model=PipelineResponse,
    dependencies=[Depends(require_permission_dep("pipeline", PermissionAction.READ))],
)
async def get_pipeline(
    tenant_id: str = Depends(get_current_tenant_id), service: RevenueService = Depends(get_service)
):
    return await service.get_pipeline(tenant_id)
