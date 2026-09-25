"""Commercial Relationship Model — REST router.

Tenant-scoped typed relationship edges (reports_to, influences, champion_for,
blocks, introduced_by) for person<->person and person<->company influence and
lifecycle evidence.

- Every read/write is tenant-scoped via ``get_current_tenant_id`` AND the
  store pins ``app.tenant_id`` (defence in depth, DEC-085).
- The store applies DB RLS + FORCE RLS; handlers re-check tenant equality so
  cross-tenant ids surface as 404, not leakage.
- RBAC: reads require ``contact.read``, writes require ``contact.write`` —
  the model is a contact/person-layer graph; managers/users hold both.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.dependencies import (
    get_current_tenant_id,
    get_current_user_id,
    require_permission_dep,
)
from app.modules.relationships.models import (
    RELATIONSHIP_EDGE_TYPES,
    RelationshipEdge,
    RelationshipError,
)
from app.modules.relationships.store import RelationshipStore
from sdk.permissions import PermissionAction

router = APIRouter()
logger = logging.getLogger(__name__)


def _store() -> RelationshipStore:
    return RelationshipStore()


class RelationshipEdgeCreateBody(BaseModel):
    edge_type: str = Field(..., min_length=1, max_length=32)
    source_type: str = Field(..., min_length=1, max_length=16)
    source_id: str = Field(..., min_length=1, max_length=36)
    target_type: str = Field(..., min_length=1, max_length=16)
    target_id: str = Field(..., min_length=1, max_length=36)
    basis: str = Field(default="unknown", max_length=64)
    evidence: list[dict[str, Any]] | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    observed_at: str | None = None
    edge_id: str | None = Field(default=None, max_length=36)


class RelationshipEdgeResponse(BaseModel):
    id: str
    tenant_id: str
    edge_type: str
    source_type: str
    source_id: str
    target_type: str
    target_id: str
    basis: str
    evidence: list[dict[str, Any]]
    confidence: float | None
    observed_at: str | None
    superseded_at: str | None
    created_by: str
    created_at: str


class RelationshipEdgeListResponse(BaseModel):
    items: list[RelationshipEdgeResponse]
    total: int


def _to_response(edge: RelationshipEdge) -> RelationshipEdgeResponse:
    return RelationshipEdgeResponse(**edge.as_dict())


@router.post("/relationships/edges", response_model=RelationshipEdgeResponse, status_code=201)
async def create_relationship_edge(
    body: RelationshipEdgeCreateBody,
    tenant_id: str = Depends(get_current_tenant_id),
    user_id: str = Depends(get_current_user_id),
    _rbac: None = Depends(require_permission_dep("contact", PermissionAction.UPDATE)),
):
    store = _store()
    try:
        edge = await store.create(
            tenant_id=tenant_id,
            edge_type=body.edge_type,
            source_type=body.source_type,
            source_id=body.source_id,
            target_type=body.target_type,
            target_id=body.target_id,
            basis=body.basis,
            evidence=body.evidence,
            confidence=body.confidence,
            observed_at=body.observed_at,
            created_by=user_id,
            edge_id=body.edge_id,
        )
    except RelationshipError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return _to_response(edge)


@router.get("/relationships/edges/{edge_id}", response_model=RelationshipEdgeResponse)
async def get_relationship_edge(
    edge_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("contact", PermissionAction.READ)),
):
    edge = await _store().get(edge_id, tenant_id=tenant_id)
    if edge is None:
        raise HTTPException(status_code=404, detail="Relationship edge not found")
    if edge.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Not found")
    return _to_response(edge)


@router.get("/relationships/edges", response_model=RelationshipEdgeListResponse)
async def list_relationship_edges(
    edge_type: str | None = Query(None),
    source_type: str | None = Query(None),
    source_id: str | None = Query(None),
    target_type: str | None = Query(None),
    target_id: str | None = Query(None),
    include_superseded: bool = Query(False),
    limit: int = Query(100, ge=1, le=500),
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("contact", PermissionAction.READ)),
):
    store = _store()
    try:
        edges = await store.list(
            tenant_id=tenant_id,
            edge_type=edge_type,
            source_type=source_type,
            source_id=source_id,
            target_type=target_type,
            target_id=target_id,
            include_superseded=include_superseded,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RelationshipEdgeListResponse(items=[_to_response(e) for e in edges], total=len(edges))


@router.post("/relationships/edges/{edge_id}/supersede", response_model=RelationshipEdgeResponse)
async def supersede_relationship_edge(
    edge_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("contact", PermissionAction.UPDATE)),
):
    edge = await _store().supersede(edge_id, tenant_id=tenant_id)
    if edge is None:
        raise HTTPException(status_code=404, detail="Relationship edge not found or already superseded")
    if edge.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Not found")
    return _to_response(edge)


def _edge_type_choices() -> list[str]:
    return list(RELATIONSHIP_EDGE_TYPES)