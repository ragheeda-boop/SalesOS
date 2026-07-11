"""Pipeline Analytics REST API."""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_tenant_id, get_db_session
from runtime.pipeline_analytics import PipelineAnalytics

router = APIRouter()


@router.get("/pipeline/summary")
async def get_pipeline_summary(
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
):
    analytics = PipelineAnalytics(db, tenant_id)
    return await analytics.summary()


@router.get("/pipeline/velocity")
async def get_pipeline_velocity(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
):
    analytics = PipelineAnalytics(db, tenant_id)
    return await analytics.velocity()


@router.get("/pipeline/conversion")
async def get_pipeline_conversion(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
):
    analytics = PipelineAnalytics(db, tenant_id)
    return await analytics.conversion_rates()


@router.get("/pipeline/health")
async def get_pipeline_health(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
):
    analytics = PipelineAnalytics(db, tenant_id)
    return await analytics.health_map()


@router.get("/pipeline/forecast")
async def get_pipeline_forecast(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
):
    analytics = PipelineAnalytics(db, tenant_id)
    return await analytics.forecast()
