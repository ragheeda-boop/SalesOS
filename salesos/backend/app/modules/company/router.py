import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas import PaginatedResponse
from app.dependencies import get_current_tenant_id, get_db_session, require_permission
from sdk.permissions import PermissionAction
from domains.search.contracts.models import SearchQuery, SearchSort
from domains.search.engine.planner import SearchPlanner
from domains.search.ranking.pipeline import RankingPipeline
from sdk.telemetry import record_metric

from .models import Branch, License
from .schemas import (
    BranchCreate,
    BranchResponse,
    Company360Response,
    CompanyCreate,
    CompanyOrganization,
    CompanyOverview,
    CompanySignals,
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


def _detect_signals(company, contacts: list, opportunities: list, contracts: list, tenant_id: str) -> dict:
    """Detect business signals for a company."""
    items = []
    now = __import__("datetime").datetime.now()

    # Expiry signals
    if hasattr(company, "expiry_date") and company.expiry_date:
        days_left = (company.expiry_date - now.date()).days if company.expiry_date else 365
        if days_left < 0:
            items.append({"type": "expired", "severity": "critical",
                          "title": "License expired", "days": abs(days_left)})
        elif days_left < 30:
            items.append({"type": "expiring_soon", "severity": "high",
                          "title": "License expiring soon", "days": days_left})
        elif days_left < 90:
            items.append({"type": "expiring", "severity": "medium",
                          "title": "License expiring", "days": days_left})

    if opportunities:
        stalled = [o for o in opportunities if o.get("stage") == "prospecting" and o.get("status") == "open"]
        if len(stalled) > 3:
            items.append({"type": "stalled_pipeline", "severity": "medium",
                          "title": f"{len(stalled)} deals stuck in prospecting"})

        won = sum(1 for o in opportunities if o.get("status") in ("won", "closed_won"))
        if won > 0:
            items.append({"type": "won_deals", "severity": "positive",
                          "title": f"{won} deals won", "value": won})

    if not contacts:
        items.append({"type": "no_contacts", "severity": "info",
                      "title": "No contacts saved yet"})

    return {"items": items, "total": len(items)}


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
             dependencies=[Depends(lambda: require_permission("company", PermissionAction.CREATE))])
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
            dependencies=[Depends(lambda: require_permission("company", PermissionAction.READ))])
async def get_company(
    company_id: str,
    service: CompanyService = Depends(get_service),
):
    return await service.get_company(company_id)


@router.patch("/{company_id}", response_model=CompanyResponse,
              dependencies=[Depends(lambda: require_permission("company", PermissionAction.UPDATE))])
async def update_company(
    company_id: str,
    body: CompanyUpdate,
    service: CompanyService = Depends(get_service),
):
    updates = body.model_dump(exclude_unset=True)
    return await service.update_company(company_id, updates)


@router.post("/{company_id}/branches", response_model=BranchResponse, status_code=201)
async def add_branch(
    company_id: str,
    body: BranchCreate,
    service: CompanyService = Depends(get_service),
):
    branch = await service.add_branch(company_id, body.model_dump())
    return branch


@router.post("/{company_id}/licenses", response_model=LicenseResponse, status_code=201)
async def add_license(
    company_id: str,
    body: LicenseCreate,
    service: CompanyService = Depends(get_service),
):
    license = await service.add_license(company_id, body.model_dump())
    return license


@router.post("/{company_id}/contacts", response_model=ContactResponse, status_code=201)
async def add_contact(
    company_id: str,
    body: ContactCreate,
    service: CompanyService = Depends(get_service),
):
    contact = await service.add_contact(company_id, body.model_dump())
    return contact


@router.delete("/{company_id}", status_code=204)
async def delete_company(
    company_id: str,
    service: CompanyService = Depends(get_service),
):
    await service.delete_company(company_id)


@router.get("/{company_id}/360", response_model=Company360Response)
async def company_360(
    company_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    service: CompanyService = Depends(get_service),
    db: AsyncSession = Depends(get_db_session),
):
    company = await service.get_company(company_id)

    contacts = []
    assigned_employees = []
    opportunities = []
    timeline = []
    contracts = []
    invoices = []
    documents = []
    meetings = []
    tasks = []
    emails = []
    branches = []
    licenses = []

    company_uuid = uuid.UUID(company_id)

    try:
        from app.modules.contact.models import Contact
        result = await db.execute(
            select(Contact).where(
                Contact.company_id == company_id,
            ).order_by(Contact.created_at.desc()).limit(50)
        )
        contacts = [
            {"id": str(c.id), "name": c.name, "email": c.email, "phone": c.phone,
             "position": c.position, "is_primary": c.is_primary}
            for c in result.scalars().all()
        ]
    except Exception:
        pass

    try:
        from domains.commercial.opportunity.contracts.repository import OpportunityQuery
        from domains.commercial.infrastructure.postgres_repositories import PostgresOpportunityRepository
        opp_repo = PostgresOpportunityRepository(db)
        opp_result = await opp_repo.query(OpportunityQuery(tenant_id=tenant_id, page_size=50))
        opportunities = [
            {"id": o.id, "name": o.name, "value": o.value, "stage": o.stage,
             "status": o.status.value, "probability": o.probability,
             "owner_id": o.owner_id}
            for o in opp_result.items if o.company_id == company_id
        ]
        owner_ids = set(o["owner_id"] for o in opportunities if o.get("owner_id"))
        if owner_ids:
            from app.modules.identity.models import User
            user_result = await db.execute(
                select(User).where(User.id.in_(list(owner_ids)))
            )
            assigned_employees = [
                {"id": str(u.id), "full_name": u.full_name, "email": u.email, "role": u.role}
                for u in user_result.scalars().all()
            ]
    except Exception:
        pass

    try:
        activity_runtime = getattr(request.app.state, "activity_runtime", None)
        if activity_runtime:
            items, total = await activity_runtime.get_by_entity("company", company_id, tenant_id=tenant_id, limit=50)
            timeline = items
            for a in items:
                action = a.get("action", "")
                if action.startswith("meeting"):
                    meetings.append(a)
                elif action.startswith("email"):
                    emails.append(a)
                elif action.startswith("task"):
                    tasks.append(a)
                elif action.startswith("document"):
                    documents.append(a)
                elif action.startswith("invoice"):
                    invoices.append(a)
                elif action.startswith("contract"):
                    contracts.append(a)
    except Exception:
        pass

    try:
        branch_result = await db.execute(
            select(Branch).where(Branch.company_id == company_uuid)
        )
        branches = [BranchResponse.model_validate(b) for b in branch_result.scalars().all()]
        license_result = await db.execute(
            select(License).where(License.company_id == company_uuid)
        )
        licenses = [LicenseResponse.model_validate(l) for l in license_result.scalars().all()]
    except Exception:
        pass

    total_revenue = sum(o.get("value", 0) or 0 for o in opportunities)
    active_contracts = sum(1 for c in contracts if c.get("metadata", {}).get("status") in ("active", "signed"))
    pending_tasks = sum(1 for t in tasks if t.get("metadata", {}).get("status") != "completed")
    upcoming_meetings = sum(1 for m in meetings if m.get("metadata", {}).get("status") == "scheduled")
    last_activity = timeline[0].get("timestamp") if timeline else None

    signals = _detect_signals(company, contacts, opportunities, contracts, tenant_id)

    return Company360Response(
        company=company,
        overview=CompanyOverview(
            total_contacts=len(contacts),
            total_opportunities=len(opportunities),
            total_revenue=total_revenue,
            active_contracts=active_contracts,
            pending_tasks=pending_tasks,
            upcoming_meetings=upcoming_meetings,
            last_activity=last_activity,
            signal_count=signals["total"],
        ),
        organization=CompanyOrganization(
            branches=branches,
            employees_count=company.employees_count or 0,
            legal_form=company.legal_form,
            incorporation_date=str(company.incorporation_date) if company.incorporation_date else None,
        ),
        contacts=contacts,
        assigned_employees=assigned_employees,
        emails=emails,
        meetings=meetings,
        tasks=tasks,
        opportunities=opportunities,
        contracts=contracts,
        invoices=invoices,
        timeline=timeline,
        documents=documents,
        signals=CompanySignals(items=signals["items"], total=signals["total"]),
        branches=branches,
        licenses=licenses,
        contact_count=len(contacts),
        opportunity_count=len(opportunities),
        total_revenue=total_revenue,
    )


@router.post("/ingest", status_code=201)
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
