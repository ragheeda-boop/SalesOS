"""Feature Store REST endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.dependencies import get_current_tenant_id, verify_token

router = APIRouter(dependencies=[Depends(verify_token)])


# ── Request / Response schemas ───────────────────────────────────


class RegisterFeatureRequest(BaseModel):
    key: str = Field(..., max_length=255)
    name: str = Field(..., max_length=255)
    description: str = ""
    feature_type: str = "numeric"
    domain: str = "general"


class SetFeatureRequest(BaseModel):
    feature_key: str = Field(..., max_length=255)
    entity_id: str = Field(..., max_length=255)
    entity_type: str = Field(..., max_length=50)
    value: Any = None
    ttl_seconds: int = 3600


class BatchSetFeatureRequest(BaseModel):
    entity_id: str = Field(..., max_length=255)
    entity_type: str = Field(..., max_length=50)
    features: dict[str, Any] = Field(default_factory=dict)
    ttl_seconds: int = 3600


def _get_service(request: Request):
    svc = getattr(request.app.state, "feature_store_domain_service", None)
    if not svc:
        raise HTTPException(status_code=503, detail="Feature Store domain service not initialized")
    return svc


# ── Endpoints ────────────────────────────────────────────────────


@router.post("/feature-store/register")
async def register_feature(
    req: RegisterFeatureRequest,
    request: Request,
    _tenant: str = Depends(get_current_tenant_id),
):
    svc = _get_service(request)
    from domains.feature_store.models import FeatureDefinition, FeatureType
    definition = FeatureDefinition(
        key=req.key,
        name=req.name,
        description=req.description,
        feature_type=FeatureType(req.feature_type),
        domain=req.domain,
    )
    result = await svc.register_feature(definition)
    return {"definition": result.to_dict()}


@router.post("/feature-store/set")
async def set_feature(
    req: SetFeatureRequest,
    request: Request,
    _tenant: str = Depends(get_current_tenant_id),
):
    svc = _get_service(request)
    val = await svc.set_feature(
        feature_key=req.feature_key,
        entity_id=req.entity_id,
        entity_type=req.entity_type,
        value=req.value,
        ttl_seconds=req.ttl_seconds,
    )
    return {"feature": val.to_dict()}


@router.post("/feature-store/batch-set")
async def batch_set_features(
    req: BatchSetFeatureRequest,
    request: Request,
    _tenant: str = Depends(get_current_tenant_id),
):
    svc = _get_service(request)
    vals = await svc.batch_set_features(
        entity_id=req.entity_id,
        entity_type=req.entity_type,
        features=req.features,
        ttl_seconds=req.ttl_seconds,
    )
    return {"features": [v.to_dict() for v in vals]}


@router.get("/feature-store/{entity_type}/{entity_id}")
async def get_entity_snapshot(
    entity_type: str,
    entity_id: str,
    request: Request,
    _tenant: str = Depends(get_current_tenant_id),
):
    svc = _get_service(request)
    snapshot = await svc.get_feature_snapshot(entity_id, entity_type)
    return {
        "entity_id": entity_id,
        "entity_type": entity_type,
        "features": snapshot,
    }


@router.get("/feature-store/{entity_type}/{entity_id}/{feature_key}")
async def get_single_feature(
    entity_type: str,
    entity_id: str,
    feature_key: str,
    request: Request,
    _tenant: str = Depends(get_current_tenant_id),
):
    svc = _get_service(request)
    val = await svc.get_feature(feature_key, entity_id, entity_type)
    if val is None:
        raise HTTPException(status_code=404, detail=f"Feature '{feature_key}' not found or expired")
    return {"feature": val.to_dict()}
