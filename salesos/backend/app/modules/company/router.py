import csv
import hashlib
import io
import logging
import time
import uuid
from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import safe_error_detail
from app.common.schemas import CursorResponse
from app.dependencies import get_current_tenant_id, get_db_session, require_permission_dep
from domains.search.contracts.models import SearchQuery, SearchSort
from domains.search.engine.planner import SearchPlanner
from domains.search.ranking.pipeline import RankingPipeline
from sdk.permissions import PermissionAction
from sdk.telemetry import record_metric, trace_span

from .schemas import (
    BranchCreate,
    BranchResponse,
    BulkDeleteRequest,
    BulkDeleteResponse,
    BulkEditRequest,
    BulkEditResponse,
    Company360Response,
    CompanyCreate,
    CompanyIngestRequest,
    CompanyListResponse,
    CompanyResponse,
    CompanyUpdate,
    ContactCreate,
    ContactResponse,
    LicenseCreate,
    LicenseResponse,
)
from .search_repository import CompanySearchRepository
from .service import CompanyService

router = APIRouter()
logger = logging.getLogger(__name__)


def get_service(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> CompanyService:
    return CompanyService(
        db=db,
        event_bus=getattr(request.app.state, "event_bus", None),
        logger=getattr(request.app.state, "logger", None),
    )


def get_search_planner(
    db: AsyncSession = Depends(get_db_session),
) -> SearchPlanner:
    repository = CompanySearchRepository(db)
    ranking = RankingPipeline.default(
        exact_fields=["name_ar", "name_en", "cr_number"],
        partial_fields=["name_ar", "name_en", "cr_number", "city", "activity_description"],
    )
    return SearchPlanner(repository=repository, ranking_pipeline=ranking)


@router.post(
    "",
    response_model=CompanyResponse,
    status_code=201,
    dependencies=[Depends(require_permission_dep("company", PermissionAction.CREATE))],
)
async def create_company(
    body: CompanyCreate,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    service: CompanyService = Depends(get_service),
):
    company = await service.create_company(
        tenant_id=tenant_id,
        name_ar=body.name_ar,
        name_en=body.name_en,
        cr_number=body.cr_number,
        status=body.status,
        city=body.city,
        region=body.region,
        phone=body.phone,
        email=body.email,
        website=body.website,
        address=body.address,
        activity_description=body.activity_description,
        activity_code=body.activity_code,
        legal_form=body.legal_form,
    )
    record_metric("company_created_total", 1, {"tenant_id": tenant_id})
    # Invalidate search caches so new company is findable immediately.
    sr = getattr(request.app.state, "search_runtime", None)
    if sr is not None and hasattr(sr, "clear_cache"):
        await sr.clear_cache()
    cache = getattr(request.app.state, "cache", None)
    if cache is not None and hasattr(cache, "delete_pattern"):
        try:
            await cache.delete_pattern("search:*")
        except Exception:
            pass
    return company


@router.get(
    "",
    response_model=CursorResponse,
    dependencies=[Depends(require_permission_dep("company", PermissionAction.READ))],
)
async def search_companies(
    q: str | None = Query(None),
    cr_number: str | None = Query(None),
    status: str | None = Query(None),
    city: str | None = Query(None),
    region: str | None = Query(None),
    activity_code: str | None = Query(None),
    # B-2: Advanced filtering
    industry: str | None = Query(None, description="Comma-separated list (OR)"),
    size_min: int | None = Query(None, ge=0),
    size_max: int | None = Query(None, ge=0),
    created_from: date | None = Query(None),
    created_to: date | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    cursor: str | None = Query(None),
    tenant_id: str = Depends(get_current_tenant_id),
    planner: SearchPlanner = Depends(get_search_planner),
    service: CompanyService = Depends(get_service),
):
    filters: dict[str, Any] = {}
    if cr_number:
        filters["cr_number"] = {"contains": cr_number}
    if status:
        filters["status"] = {"in": status.split(",")} if "," in status else status
    if city:
        filters["city"] = {"contains": city}
    if region:
        filters["region"] = region
    if activity_code:
        filters["activity_code"] = activity_code
    if industry:
        industries = [i.strip() for i in industry.split(",") if i.strip()]
        filters["industry"] = {"in": industries}
    if size_min is not None:
        filters["employees_count"] = {**filters.get("employees_count", {}), "gte": size_min}
    if size_max is not None:
        filters["employees_count"] = {**filters.get("employees_count", {}), "lte": size_max}
    if created_from:
        filters["created_at"] = {**filters.get("created_at", {}), "gte": created_from}
    if created_to:
        filters["created_at"] = {**filters.get("created_at", {}), "lte": created_to}

    query = SearchQuery(
        query=q or "",
        filters=filters,
        sort=SearchSort(field=sort_by, direction=sort_order),
        page=page,
        page_size=page_size,
        tenant_id=tenant_id,
        context={"cursor": cursor} if cursor else {},
    )

    result = await planner.search(query)

    record_metric("company_search_total", 1, {"tenant_id": tenant_id, "strategy": result.strategy})
    if result.total == 0:
        record_metric("search_zero_results_total", 1, {"tenant_id": tenant_id, "query": q or ""})

    items = [
        CompanyListResponse(
            id=c.id,
            name_ar=c.name_ar,
            name_en=c.name_en,
            cr_number=c.cr_number,
            status=c.status,
            city=c.city,
            region=c.region,
            confidence_score=c.confidence_score,
            created_at=c.created_at,
        )
        for c in result.items
    ]
    return CursorResponse(
        data=items,
        next_cursor=result.next_cursor,
        total=result.total,
        has_next=result.next_cursor is not None,
    )


# ── B-1: Bulk Operations (must be before /{company_id} routes) ─────────────


@router.patch(
    "/bulk",
    response_model=BulkEditResponse,
    dependencies=[Depends(require_permission_dep("company", PermissionAction.UPDATE))],
)
async def bulk_update_companies(
    body: BulkEditRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    service: CompanyService = Depends(get_service),
):
    result = await service.bulk_update_companies(
        body.company_ids, body.updates, tenant_id=tenant_id
    )
    record_metric("company_bulk_updated_total", result["updated"])
    return BulkEditResponse(**result)


@router.delete(
    "/bulk",
    response_model=BulkDeleteResponse,
    dependencies=[Depends(require_permission_dep("company", PermissionAction.DELETE))],
)
async def bulk_delete_companies(
    body: BulkDeleteRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    service: CompanyService = Depends(get_service),
):
    result = await service.bulk_delete_companies(body.company_ids, tenant_id=tenant_id)
    record_metric("company_bulk_deleted_total", result["deleted"])
    return BulkDeleteResponse(**result)


@router.get(
    "/export", dependencies=[Depends(require_permission_dep("company", PermissionAction.EXPORT))]
)
async def export_companies(
    format: str = Query("csv", pattern="^(csv)$"),
    fields: str = Query("name,industry,size,region,status"),
    company_ids: str | None = Query(None, description="Comma-separated UUIDs"),
    tenant_id: str = Depends(get_current_tenant_id),
    service: CompanyService = Depends(get_service),
):
    from sqlalchemy import select

    from .models import Company

    field_list = [f.strip() for f in fields.split(",") if f.strip()]
    allowed = {
        "name",
        "name_ar",
        "name_en",
        "industry",
        "size",
        "employees_count",
        "region",
        "status",
        "city",
        "cr_number",
        "email",
        "phone",
        "website",
        "legal_form",
        "activity_description",
        "confidence_score",
        "created_at",
    }

    field_map = {
        "name": "name_ar",
        "size": "employees_count",
    }
    model_fields = [
        field_map.get(f, f) for f in field_list if f in allowed or field_map.get(f) in allowed
    ]
    cols = [getattr(Company, mf) for mf in model_fields]

    stmt = select(*cols).where(Company.tenant_id == uuid.UUID(tenant_id))
    if company_ids:
        ids = [uuid.UUID(cid.strip()) for cid in company_ids.split(",") if cid.strip()]
        stmt = stmt.where(Company.id.in_(ids))
    result = await service.db.execute(stmt)
    rows = result.fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(field_list)
    for row_data in rows:
        writer.writerow(
            str(v.isoformat() if isinstance(v, datetime) else v) if v is not None else ""
            for v in row_data
        )

    content = output.getvalue()
    return Response(
        content=content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=companies_export_{datetime.now().strftime('%Y%m%d')}.csv"  # noqa: E501
        },
    )


@router.get(
    "/{company_id}",
    response_model=CompanyResponse,
    dependencies=[Depends(require_permission_dep("company", PermissionAction.READ))],
)
async def get_company(
    company_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    service: CompanyService = Depends(get_service),
):
    cache = getattr(request.app.state, "cache", None)
    ck = f"company:{tenant_id}:{company_id}"
    if cache:
        cached = await cache.get(ck)
        if cached:
            return CompanyResponse(**cached)
    # service returns SQLAlchemy Company — convert before cache/response
    result = CompanyResponse.model_validate(await service.get_company(company_id, tenant_id))
    if cache:
        await cache.set(ck, result.model_dump(mode="json"), ttl_seconds=300)
    return result


@router.patch(
    "/{company_id}",
    response_model=CompanyResponse,
    dependencies=[Depends(require_permission_dep("company", PermissionAction.UPDATE))],
)
async def update_company(
    company_id: str,
    body: CompanyUpdate,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    service: CompanyService = Depends(get_service),
):
    updates = body.model_dump(exclude_unset=True)
    result = await service.update_company(company_id, updates, tenant_id=tenant_id)
    cache = getattr(request.app.state, "cache", None)
    if cache:
        await cache.delete(f"company:{tenant_id}:{company_id}")
        await cache.delete_pattern("company_list:*")
    return result


@router.post(
    "/{company_id}/branches",
    response_model=BranchResponse,
    status_code=201,
    dependencies=[Depends(require_permission_dep("company", PermissionAction.UPDATE))],
)
async def add_branch(
    company_id: str,
    body: BranchCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    service: CompanyService = Depends(get_service),
):
    branch = await service.add_branch(company_id, body.model_dump(), tenant_id=tenant_id)
    return branch


@router.post(
    "/{company_id}/licenses",
    response_model=LicenseResponse,
    status_code=201,
    dependencies=[Depends(require_permission_dep("company", PermissionAction.UPDATE))],
)
async def add_license(
    company_id: str,
    body: LicenseCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    service: CompanyService = Depends(get_service),
):
    license = await service.add_license(company_id, body.model_dump(), tenant_id=tenant_id)
    return license


@router.post(
    "/{company_id}/contacts",
    response_model=ContactResponse,
    status_code=201,
    dependencies=[Depends(require_permission_dep("company", PermissionAction.UPDATE))],
)
async def add_contact(
    company_id: str,
    body: ContactCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    service: CompanyService = Depends(get_service),
):
    contact = await service.add_contact(company_id, body.model_dump(), tenant_id=tenant_id)
    return contact


@router.delete(
    "/{company_id}",
    status_code=204,
    dependencies=[Depends(require_permission_dep("company", PermissionAction.DELETE))],
)
async def delete_company(
    company_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    service: CompanyService = Depends(get_service),
):
    await service.delete_company(company_id, tenant_id=tenant_id)


@router.get(
    "/{company_id}/360",
    response_model=Company360Response,
    dependencies=[Depends(require_permission_dep("company", PermissionAction.READ))],
)
async def company_360(
    company_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    service: CompanyService = Depends(get_service),
    db: AsyncSession = Depends(get_db_session),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    activity_runtime = getattr(request.app.state, "activity_runtime", None)
    kg_engine = getattr(request.app.state, "kg_engine", None)
    try:
        result = await service.get_company_360(
            company_id=company_id,
            tenant_id=tenant_id,
            activity_runtime=activity_runtime,
            db=db,
            kg_engine=kg_engine,
            page=page,
            page_size=page_size,
        )
    except HTTPException:
        # Includes NotFoundError (404) for missing / invalid company ids.
        raise
    except Exception as exc:
        # Do not invent health_score or empty 360 payloads — surface failure honestly.
        logger.exception(
            "company_360.failed", extra={"company_id": company_id, "tenant_id": tenant_id}
        )
        raise HTTPException(
            status_code=500,
            detail=safe_error_detail(exc, "Failed to load company 360"),
        ) from exc
    return Company360Response(**result)


@router.get(
    "/{company_id}/intelligence",
    dependencies=[Depends(require_permission_dep("company", PermissionAction.READ))],
)
async def company_intelligence(
    company_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    service: CompanyService = Depends(get_service),
    db: AsyncSession = Depends(get_db_session),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    from .intelligence_computer import build_intelligence_dto

    start = time.monotonic()
    tenant_hash = hashlib.sha256(tenant_id.encode()).hexdigest()[:12]
    widget_count = 0

    try:
        async with trace_span(
            "company_intelligence",
            {
                "company_id": company_id,
                "tenant_hash": tenant_hash,
            },
        ):
            resp = await company_360(company_id, request, tenant_id, service, db, page, page_size)
            dto = build_intelligence_dto(resp)
            duration_ms = (time.monotonic() - start) * 1000

            dto_dict = dto.model_dump() if hasattr(dto, "model_dump") else dto
            if isinstance(dto_dict, dict):
                widget_count = sum(
                    1
                    for k, v in dto_dict.items()
                    if k not in ("companyId", "generatedAt", "firmographic")
                    and v is not None
                    and v != []
                    and v != {}
                )
                _ = len(str(dto_dict))

            record_metric(
                "company_intelligence_request_total",
                1,
                {
                    "tenant_hash": tenant_hash,
                    "status": "success",
                },
            )
            record_metric(
                "company_intelligence_duration_ms",
                duration_ms,
                {
                    "tenant_hash": tenant_hash,
                },
            )
            record_metric(
                "company_intelligence_widget_count",
                widget_count,
                {
                    "tenant_hash": tenant_hash,
                },
            )

            return dto

    except HTTPException:
        duration_ms = (time.monotonic() - start) * 1000
        record_metric(
            "company_intelligence_request_total",
            1,
            {
                "tenant_hash": tenant_hash,
                "status": "client_error",
            },
        )
        record_metric(
            "company_intelligence_duration_ms",
            duration_ms,
            {
                "tenant_hash": tenant_hash,
            },
        )
        raise
    except Exception:
        _ = 500
        duration_ms = (time.monotonic() - start) * 1000
        record_metric(
            "company_intelligence_request_total",
            1,
            {
                "tenant_hash": tenant_hash,
                "status": "error",
            },
        )
        record_metric(
            "company_intelligence_duration_ms",
            duration_ms,
            {
                "tenant_hash": tenant_hash,
            },
        )
        raise


@router.get(
    "/cursors",
    response_model=CursorResponse,
    dependencies=[Depends(require_permission_dep("company", PermissionAction.READ))],
)
async def search_companies_cursor(
    q: str | None = Query(None),
    cr_number: str | None = Query(None),
    status: str | None = Query(None),
    city: str | None = Query(None),
    region: str | None = Query(None),
    activity_code: str | None = Query(None),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    cursor: str | None = Query(None),
    tenant_id: str = Depends(get_current_tenant_id),
    service: CompanyService = Depends(get_service),
):
    filters: dict[str, Any] = {}
    if cr_number:
        filters["cr_number"] = {"contains": cr_number}
    if status:
        filters["status"] = status
    if city:
        filters["city"] = {"contains": city}
    if region:
        filters["region"] = {"contains": region}
    if activity_code:
        filters["activity_code"] = activity_code

    result = await service.search_companies_cursored(
        tenant_id=tenant_id,
        query=q,
        filters=filters,
        page_size=page_size,
        sort_by=sort_by,
        sort_desc=sort_order == "desc",
        cursor=cursor,
    )
    return CursorResponse(
        data=[
            CompanyListResponse(
                id=c.id,
                name_ar=c.name_ar,
                name_en=c.name_en,
                cr_number=c.cr_number,
                status=c.status,
                city=c.city,
                region=c.region,
                confidence_score=c.confidence_score,
                created_at=c.created_at,
            )
            for c in result.items
        ],
        next_cursor=result.next_cursor,
        previous_cursor=result.previous_cursor,
        has_next=result.has_next,
        has_previous=result.has_previous,
    )


@router.post(
    "/ingest",
    status_code=201,
    dependencies=[Depends(require_permission_dep("company", PermissionAction.CREATE))],
)
async def ingest_companies(
    body: CompanyIngestRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    service: CompanyService = Depends(get_service),
):
    result = await service.ingest_from_source(
        tenant_id=tenant_id,
        source_slug=body.source,
        records=body.data,
    )
    return result


# ── P1-1: Account Ownership Assignment ──


class AssignOwnerBody:
    owner_id: str | None = None
    segment: str | None = None


@router.patch(
    "/{company_id}/assign",
    tags=["Companies"],
    dependencies=[Depends(require_permission_dep("company", PermissionAction.UPDATE))],
)
async def assign_company_owner(
    company_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    service: CompanyService = Depends(get_service),
):
    """P1-1: Assign owner and/or segment to a company account."""
    body = await request.json()
    owner_id = body.get("owner_id")
    segment = body.get("segment")

    from sqlalchemy import update as sql_update
    from app.modules.company.models import Company

    stmt = sql_update(Company).where(
        Company.id == company_id,
        Company.tenant_id == uuid.UUID(tenant_id),
    )
    updates = {}
    if owner_id is not None:
        updates[Company.owner_id] = uuid.UUID(owner_id) if owner_id else None
    if segment is not None:
        updates[Company.segment] = segment
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    stmt = stmt.values(**updates)
    await service.db.execute(stmt)
    await service.db.commit()
    return {"ok": True, "company_id": company_id, "updates": {k: str(v) for k, v in updates.items()}}
