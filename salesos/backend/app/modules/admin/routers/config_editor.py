from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session, require_role_dep

from ..schemas import (
    TenantConfigCreate,
    TenantConfigResponse,
    TenantConfigValidationResponse,
    TenantConfigVersionResponse,
)
from ..services import ConfigEditorService

router = APIRouter(
    tags=["Admin - Config Editor"],
    dependencies=[Depends(require_role_dep("admin"))],
)


@router.get("/config/{tenant_id}")
async def list_config_keys(tenant_id: str, db: AsyncSession = Depends(get_db_session)):
    svc = ConfigEditorService(db)
    keys = await svc.list_keys(tenant_id)
    return {"tenant_id": tenant_id, "keys": keys}


@router.get("/config/{tenant_id}/{key}", response_model=TenantConfigResponse)
async def get_config(tenant_id: str, key: str, db: AsyncSession = Depends(get_db_session)):
    svc = ConfigEditorService(db)
    config = await svc.get_latest(tenant_id, key)
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    return TenantConfigResponse(
        id=config.id,
        tenant_id=config.tenant_id,
        key=config.key,
        yaml_content=config.yaml_content,
        version=config.version,
        created_by=config.created_by,
        created_at=config.created_at,
    )


@router.post("/config/{tenant_id}", response_model=TenantConfigResponse, status_code=201)
async def save_config(
    tenant_id: str, body: TenantConfigCreate, db: AsyncSession = Depends(get_db_session)
):
    svc = ConfigEditorService(db)
    result = await svc.save(tenant_id, body.key, body.yaml_content)
    if not result["saved"]:
        raise HTTPException(status_code=422, detail=result["validation"])
    config = await svc.get_latest(tenant_id, body.key)
    return TenantConfigResponse(
        id=config.id,
        tenant_id=config.tenant_id,
        key=config.key,
        yaml_content=config.yaml_content,
        version=config.version,
        created_by=config.created_by,
        created_at=config.created_at,
    )


@router.get("/config/{tenant_id}/{key}/versions", response_model=list[TenantConfigVersionResponse])
async def list_config_versions(
    tenant_id: str, key: str, db: AsyncSession = Depends(get_db_session)
):
    svc = ConfigEditorService(db)
    versions = await svc.list_versions(tenant_id, key)
    return versions


@router.post("/config/validate", response_model=TenantConfigValidationResponse)
async def validate_config(body: TenantConfigCreate):
    from ..services import ConfigEditorService

    validation = ConfigEditorService.validate_yaml(body.yaml_content)
    return TenantConfigValidationResponse(valid=validation["valid"], errors=validation["errors"])
