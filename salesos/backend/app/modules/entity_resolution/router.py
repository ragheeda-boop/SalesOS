"""REST endpoints for Entity Resolution module."""

from fastapi import APIRouter, Depends, Path, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas import PaginatedResponse
from app.dependencies import get_current_tenant_id, get_db_session, require_permission_dep
from sdk.permissions import PermissionAction

from .schemas import (
    ConflictResolveRequest,
    GoldenRecordListResponse,
    GoldenRecordResponse,
    ResolutionRunRequest,
    ResolutionRunResponse,
)
from .service import EntityResolutionService

router = APIRouter()


def get_service(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> EntityResolutionService:
    return EntityResolutionService(
        db=db,
        event_bus=getattr(request.app.state, "event_bus", None),
        logger=getattr(request.app.state, "logger", None),
    )


@router.post("/resolve", response_model=ResolutionRunResponse, status_code=201, dependencies=[Depends(require_permission_dep(PermissionAction.ADMIN, "entity-resolution"))])
async def resolve_batch(
    body: ResolutionRunRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    service: EntityResolutionService = Depends(get_service),
):
    result = await service.resolve_records(
        tenant_id=tenant_id,
        source_slug=body.source_slug or "__manual__",
        records=body.model_dump().get("records", []),
        confidence_threshold=body.confidence_threshold,
    )
    return ResolutionRunResponse(
        operation_id=result.get("source", ""),
        source_slug=body.source_slug,
        records_processed=result["records_processed"],
        records_matched=result["records_matched"],
        records_created=result["records_created"],
        records_merged=result["records_merged"],
        conflicts_detected=result["conflicts_detected"],
        duration_seconds=result["duration_seconds"],
    )


@router.get("/golden-records", response_model=PaginatedResponse, dependencies=[Depends(require_permission_dep(PermissionAction.READ, "entity-resolution"))])
async def list_golden_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    tenant_id: str = Depends(get_current_tenant_id),
    service: EntityResolutionService = Depends(get_service),
):
    records, total = await service.list_golden_records(tenant_id, page=page, page_size=page_size)
    items = [
        GoldenRecordListResponse(
            id=r.id,
            cr_number=r.cr_number,
            company_id=r.company_id,
            confidence_score=r.confidence_score,
            source_count=len(r.source_ids) if r.source_ids else 0,
            created_at=r.created_at,
        )
        for r in records
    ]
    return PaginatedResponse(total=total, page=page, page_size=page_size, items=items)


@router.get("/golden-records/{golden_id}", response_model=GoldenRecordResponse, dependencies=[Depends(require_permission_dep(PermissionAction.READ, "entity-resolution"))])
async def get_golden_record(
    golden_id: str = Path(...),
    tenant_id: str = Depends(get_current_tenant_id),
    service: EntityResolutionService = Depends(get_service),
):
    return await service.get_golden_record(golden_id)


@router.get("/golden-records/by-cr/{cr_number}", response_model=GoldenRecordResponse | None, dependencies=[Depends(require_permission_dep(PermissionAction.READ, "entity-resolution"))])
async def get_golden_by_cr(
    cr_number: str = Path(...),
    tenant_id: str = Depends(get_current_tenant_id),
    service: EntityResolutionService = Depends(get_service),
):
    return await service.get_golden_by_cr(tenant_id, cr_number)


@router.get("/conflicts", response_model=PaginatedResponse, dependencies=[Depends(require_permission_dep(PermissionAction.READ, "entity-resolution"))])
async def list_conflicts(
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    tenant_id: str = Depends(get_current_tenant_id),
    service: EntityResolutionService = Depends(get_service),
):
    conflicts, total = await service.list_conflicts(
        tenant_id, status=status, page=page, page_size=page_size
    )
    from .schemas import ConflictResponse

    items = [
        ConflictResponse(
            id=c.id,
            golden_record_id=c.golden_record_id,
            field_name=c.field_name,
            source_a_value=c.source_a_value,
            source_a_source=c.source_a_source,
            source_b_value=c.source_b_value,
            source_b_source=c.source_b_source,
            resolution_strategy=c.resolution_strategy,
            status=c.status,
            created_at=c.created_at,
        )
        for c in conflicts
    ]
    return PaginatedResponse(total=total, page=page, page_size=page_size, items=items)


@router.post("/conflicts/{conflict_id}/resolve", dependencies=[Depends(require_permission_dep(PermissionAction.UPDATE, "entity-resolution"))])
async def resolve_conflict(
    conflict_id: str = Path(...),
    body: ConflictResolveRequest = ...,
    tenant_id: str = Depends(get_current_tenant_id),
    service: EntityResolutionService = Depends(get_service),
):
    await service.resolve_conflict(
        conflict_id=conflict_id,
        strategy=body.resolution_strategy,
        custom_value=body.custom_value,
        resolved_by=tenant_id,
    )
    return {"message": f"Conflict {conflict_id} resolved with strategy: {body.resolution_strategy}"}


@router.get("/stats", dependencies=[Depends(require_permission_dep(PermissionAction.READ, "entity-resolution"))])
async def get_resolution_stats(
    tenant_id: str = Depends(get_current_tenant_id),
    service: EntityResolutionService = Depends(get_service),
):
    return await service.get_stats(tenant_id)
