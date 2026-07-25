from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas import PaginatedResponse
from app.dependencies import get_current_tenant_id, get_db_session, require_permission_dep
from sdk.permissions import PermissionAction

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


@router.post("", response_model=ContactResponse, status_code=201, dependencies=[Depends(require_permission_dep("contact", PermissionAction.CREATE))])
async def create_contact(
    body: ContactCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    service: ContactService = Depends(get_service),
):
    return await service.create(tenant_id, body.model_dump())


@router.get("/{contact_id}", response_model=ContactResponse, dependencies=[Depends(require_permission_dep("contact", PermissionAction.READ))])
async def get_contact(
    contact_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    service: ContactService = Depends(get_service),
):
    return await service.get(contact_id)


@router.patch("/{contact_id}", response_model=ContactResponse, dependencies=[Depends(require_permission_dep("contact", PermissionAction.UPDATE))])
async def update_contact(
    contact_id: str,
    body: ContactUpdate,
    tenant_id: str = Depends(get_current_tenant_id),
    service: ContactService = Depends(get_service),
):
    return await service.update(contact_id, body.model_dump(exclude_unset=True))


@router.delete("/{contact_id}", status_code=204, dependencies=[Depends(require_permission_dep("contact", PermissionAction.DELETE))])
async def delete_contact(
    contact_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    service: ContactService = Depends(get_service),
):
    await service.delete(contact_id)


@router.get("", response_model=PaginatedResponse, dependencies=[Depends(require_permission_dep("contact", PermissionAction.READ))])
async def list_contacts(
    tenant_id: str = Depends(get_current_tenant_id),
    q: str = Query(None),
    company_id: str = Query(None),
    email: str = Query(None),
    source: str = Query(None),
    page_size: int = Query(20, ge=1, le=100),
    cursor: str | None = Query(None, description="Keyset cursor for pagination"),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    service: ContactService = Depends(get_service),
):
    from sdk.pagination import decode_cursor, encode_cursor

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
        page=1,
        page_size=page_size + 1,
        sort_by=sort_by,
        sort_desc=sort_order == "desc",
    )

    has_next = len(items) > page_size
    if has_next:
        items = items[:page_size]

    next_cursor = None
    if has_next and items:
        last = items[-1]
        next_cursor = encode_cursor(str(last.id), last.created_at)

    return PaginatedResponse(
        items=[ContactResponse.model_validate(c) for c in items],
        total=total,
        page=1,
        page_size=page_size,
        next_cursor=next_cursor,
        has_next=has_next,
    )


@router.get("/by-company/{company_id}", response_model=list[ContactResponse], dependencies=[Depends(require_permission_dep("contact", PermissionAction.READ))])
async def get_contacts_by_company(
    company_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    service: ContactService = Depends(get_service),
):
    return await service.find_by_company(tenant_id, company_id)


@router.post("/bulk-upsert", status_code=200, dependencies=[Depends(require_permission_dep("contact", PermissionAction.CREATE))])
async def bulk_upsert_contacts(
    records: list[dict],
    tenant_id: str = Depends(get_current_tenant_id),
    service: ContactService = Depends(get_service),
):
    created, updated = await service.bulk_upsert(tenant_id, records)
    return {"created": len(created), "updated": len(updated), "total": len(records)}
