"""Pipeline Analytics REST API."""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_tenant_id, get_db_session, require_permission_dep
from app.common.rate_limit import rate_limit_dep
from sdk.permissions import PermissionAction
from runtime.pipeline_analytics import PipelineAnalytics

logger = logging.getLogger(__name__)

router = APIRouter(
    dependencies=[Depends(rate_limit_dep("pipeline", 20, 60))]
)


@router.get("/pipeline/summary")
async def get_pipeline_summary(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("pipeline", PermissionAction.READ)),
):
    try:
        analytics = PipelineAnalytics(db, tenant_id)
        return await analytics.summary()
    except Exception as exc:
        logger.error("pipeline_summary failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/pipeline/velocity")
async def get_pipeline_velocity(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("pipeline", PermissionAction.READ)),
):
    try:
        analytics = PipelineAnalytics(db, tenant_id)
        return await analytics.velocity()
    except Exception as exc:
        logger.error("pipeline_velocity failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/pipeline/conversion")
async def get_pipeline_conversion(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("pipeline", PermissionAction.READ)),
):
    try:
        analytics = PipelineAnalytics(db, tenant_id)
        return await analytics.conversion_rates()
    except Exception as exc:
        logger.error("pipeline_conversion failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/pipeline/health")
async def get_pipeline_health(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("pipeline", PermissionAction.READ)),
):
    try:
        analytics = PipelineAnalytics(db, tenant_id)
        return await analytics.health_map()
    except Exception as exc:
        logger.error("pipeline_health failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/pipeline/forecast")
async def get_pipeline_forecast(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("pipeline", PermissionAction.READ)),
):
    try:
        analytics = PipelineAnalytics(db, tenant_id)
        return await analytics.forecast()
    except Exception as exc:
        logger.error("pipeline_forecast failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error")
