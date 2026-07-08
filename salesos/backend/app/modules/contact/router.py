from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas import PaginatedResponse
from app.dependencies import get_current_tenant_id, get_db_session

from .schemas import (
    ContactCreate,
    ContactResponse,
    ContactSearchParams,
    ContactUpdate,
)
from .service import ContactService

router = APIRouter()


def get_service(db: AsyncSession = Depends(get_db_session)) -> ContactService:
    return ContactService(db=db)


@router.post("", response_model=ContactResponse, status_code=201)
async def create_contact(
    body: ContactCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    service: ContactService = Depends(get_service),
):
    return await service.create(tenant_id, body.model_dump())


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    service: ContactService = Depends(get_service),
):
    return await service.get(contact_id)


@router.patch("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: str,
    body: ContactUpdate,
    tenant_id: str = Depends(get_current_tenant_id),
    service: ContactService = Depends(get_service),
):
    return await service.update(contact_id, body.model_dump(exclude_unset=True))


@router.delete("/{contact_id}", status_code=204)
async def delete_contact(
    contact_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    service: ContactService = Depends(get_service),
):
    await service.delete(contact_id)


@router.get("", response_model=PaginatedResponse)
async def list_contacts(
    tenant_id: str = Depends(get_current_tenant_id),
    q: str = Query(None),
    company_id: str = Query(None),
    email: str = Query(None),
    source: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    service: ContactService = Depends(get_service),
):
    filters = {}
    if company_id:
        filters["company_id"] = company_id
    if email:
        filters["email"] = email
    if source:
        filters["source"] = source

    items, total = await service.search(
        tenant_id,
        query=q,
        filters=filters or None,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_desc=sort_order == "desc",
    )
    return PaginatedResponse(
        items=[ContactResponse.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/by-company/{company_id}", response_model=list[ContactResponse])
async def get_contacts_by_company(
    company_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    service: ContactService = Depends(get_service),
):
    return await service.find_by_company(tenant_id, company_id)


@router.post("/bulk-upsert", status_code=200)
async def bulk_upsert_contacts(
    records: list[dict],
    tenant_id: str = Depends(get_current_tenant_id),
    service: ContactService = Depends(get_service),
):
    created, updated = await service.bulk_upsert(tenant_id, records)
    return {"created": len(created), "updated": len(updated), "total": len(records)}
