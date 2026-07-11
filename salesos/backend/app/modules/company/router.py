from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas import PaginatedResponse
from app.dependencies import get_current_tenant_id, get_db_session, require_permission_dep
from sdk.permissions import PermissionAction
from domains.search.contracts.models import SearchQuery, SearchSort
from domains.search.engine.planner import SearchPlanner
from domains.search.ranking.pipeline import RankingPipeline
from sdk.telemetry import record_metric

from .schemas import (
    BranchCreate,
    BranchResponse,
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


@router.post("", response_model=CompanyResponse, status_code=201,
             dependencies=[Depends(require_permission_dep("company", PermissionAction.CREATE))])
async def create_company(
    body: CompanyCreate,
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
    return company


@router.get("", response_model=PaginatedResponse)
async def search_companies(
    q: str | None = Query(None),
    cr_number: str | None = Query(None),
    status: str | None = Query(None),
    city: str | None = Query(None),
    region: str | None = Query(None),
    activity_code: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    tenant_id: str = Depends(get_current_tenant_id),
    planner: SearchPlanner = Depends(get_search_planner),
    service: CompanyService = Depends(get_service),
):
    filters = {}
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

    query = SearchQuery(
        query=q or "",
        filters=filters,
        sort=SearchSort(field=sort_by, direction=sort_order),
        page=page,
        page_size=page_size,
        tenant_id=tenant_id,
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
    return PaginatedResponse(total=result.total, page=result.page, page_size=result.page_size, items=items)


@router.get("/{company_id}", response_model=CompanyResponse,
            dependencies=[Depends(require_permission_dep("company", PermissionAction.READ))])
async def get_company(
    company_id: str,
    service: CompanyService = Depends(get_service),
):
    return await service.get_company(company_id)


@router.patch("/{company_id}", response_model=CompanyResponse,
              dependencies=[Depends(require_permission_dep("company", PermissionAction.UPDATE))])
async def update_company(
    company_id: str,
    body: CompanyUpdate,
    service: CompanyService = Depends(get_service),
):
    updates = body.model_dump(exclude_unset=True)
    return await service.update_company(company_id, updates)


@router.post("/{company_id}/branches", response_model=BranchResponse, status_code=201,
             dependencies=[Depends(require_permission_dep("company", PermissionAction.UPDATE))])
async def add_branch(
    company_id: str,
    body: BranchCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    service: CompanyService = Depends(get_service),
):
    branch = await service.add_branch(company_id, body.model_dump())
    return branch


@router.post("/{company_id}/licenses", response_model=LicenseResponse, status_code=201,
             dependencies=[Depends(require_permission_dep("company", PermissionAction.UPDATE))])
async def add_license(
    company_id: str,
    body: LicenseCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    service: CompanyService = Depends(get_service),
):
    license = await service.add_license(company_id, body.model_dump())
    return license


@router.post("/{company_id}/contacts", response_model=ContactResponse, status_code=201,
             dependencies=[Depends(require_permission_dep("company", PermissionAction.UPDATE))])
async def add_contact(
    company_id: str,
    body: ContactCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    service: CompanyService = Depends(get_service),
):
    contact = await service.add_contact(company_id, body.model_dump())
    return contact


@router.delete("/{company_id}", status_code=204,
               dependencies=[Depends(require_permission_dep("company", PermissionAction.DELETE))])
async def delete_company(
    company_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    service: CompanyService = Depends(get_service),
):
    await service.delete_company(company_id)


@router.get("/{company_id}/360", response_model=Company360Response,
            dependencies=[Depends(require_permission_dep("company", PermissionAction.READ))])
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
    result = await service.get_company_360(
        company_id=company_id, tenant_id=tenant_id,
        activity_runtime=activity_runtime, db=db,
        kg_engine=kg_engine,
        page=page, page_size=page_size,
    )
    return Company360Response(**result)

# Alias: /intelligence → /360 (للتطابق مع frontend)
@router.get("/{company_id}/intelligence", response_model=Company360Response,
            dependencies=[Depends(require_permission_dep("company", PermissionAction.READ))])
async def company_intelligence(
    company_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    service: CompanyService = Depends(get_service),
    db: AsyncSession = Depends(get_db_session),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    return await company_360(company_id, request, tenant_id, service, db, page, page_size)


@router.post("/ingest", status_code=201,
             dependencies=[Depends(require_permission_dep("company", PermissionAction.CREATE))])
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
