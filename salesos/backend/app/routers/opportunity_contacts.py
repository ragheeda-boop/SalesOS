"""ADR-030: Opportunity Contacts CRUD Router.

Provides REST endpoints for managing opportunity-to-contact associations.
Uses PostgresOpportunityContactRepository via FastAPI dependency injection.
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_tenant_id, get_db_session
from domains.commercial.infrastructure.postgres_repositories import PostgresOpportunityContactRepository
from domains.commercial.opportunity.contracts.opportunity_contact_repository import (
    OpportunityContact,
    OpportunityContactQuery,
)

router = APIRouter()
logger = logging.getLogger(__name__)


class OpportunityContactCreateBody(BaseModel):
    opportunity_id: str = Field(..., min_length=1, max_length=36)
    contact_id: UUID
    role: str | None = Field(None, max_length=50)
    is_primary: bool = False


class OpportunityContactResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    opportunity_id: str
    contact_id: UUID
    role: str | None = None
    is_primary: bool = False
    created_at: str | None = None
    updated_at: str | None = None

    model_config = {"from_attributes": True}


class OpportunityContactListResponse(BaseModel):
    items: list[OpportunityContactResponse]
    total: int
    page: int
    page_size: int


async def _get_repo(db: AsyncSession = Depends(get_db_session)) -> PostgresOpportunityContactRepository:
    return PostgresOpportunityContactRepository(session=db)


@router.post("/opportunity-contacts", response_model=OpportunityContactResponse, status_code=201)
async def create_opportunity_contact(
    body: OpportunityContactCreateBody,
    tenant_id: str = Depends(get_current_tenant_id),
    repo: PostgresOpportunityContactRepository = Depends(_get_repo),
):
    oc = OpportunityContact(
        id=UUID(int=0),  # Will be replaced by DB-generated UUID
        tenant_id=UUID(tenant_id),
        opportunity_id=body.opportunity_id,
        contact_id=body.contact_id,
        role=body.role,
        is_primary=body.is_primary,
    )
    try:
        result = await repo.create(oc)
        return _to_response(result)
    except Exception as e:
        detail = str(e).lower()
        if "unique" in detail or "duplicate" in detail:
            raise HTTPException(status_code=409, detail="This contact is already associated with this opportunity.")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/opportunity-contacts/{oc_id}", response_model=OpportunityContactResponse)
async def get_opportunity_contact(
    oc_id: UUID,
    tenant_id: str = Depends(get_current_tenant_id),
    repo: PostgresOpportunityContactRepository = Depends(_get_repo),
):
    result = await repo.get(oc_id)
    if not result:
        raise HTTPException(status_code=404, detail="Opportunity contact association not found.")
    if str(result.tenant_id) != tenant_id:
        raise HTTPException(status_code=404, detail="Not found.")
    return _to_response(result)


@router.get("/opportunity-contacts", response_model=OpportunityContactListResponse)
async def list_opportunity_contacts(
    opportunity_id: str | None = Query(None),
    contact_id: UUID | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    tenant_id: str = Depends(get_current_tenant_id),
    repo: PostgresOpportunityContactRepository = Depends(_get_repo),
):
    query = OpportunityContactQuery(
        tenant_id=tenant_id,
        opportunity_id=opportunity_id or "",
        contact_id=str(contact_id) if contact_id else "",
        page=page,
        page_size=page_size,
    )
    result = await repo.query(query)
    return OpportunityContactListResponse(
        items=[_to_response(item) for item in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@router.delete("/opportunity-contacts/{oc_id}", status_code=204)
async def delete_opportunity_contact(
    oc_id: UUID,
    tenant_id: str = Depends(get_current_tenant_id),
    repo: PostgresOpportunityContactRepository = Depends(_get_repo),
):
    existing = await repo.get(oc_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Not found.")
    if str(existing.tenant_id) != tenant_id:
        raise HTTPException(status_code=404, detail="Not found.")
    await repo.delete(oc_id)


def _to_response(oc: OpportunityContact) -> OpportunityContactResponse:
    return OpportunityContactResponse(
        id=oc.id,
        tenant_id=oc.tenant_id,
        opportunity_id=oc.opportunity_id,
        contact_id=oc.contact_id,
        role=oc.role,
        is_primary=oc.is_primary,
        created_at=oc.created_at.isoformat() if oc.created_at else None,
        updated_at=oc.updated_at.isoformat() if oc.updated_at else None,
    )
