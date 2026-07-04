"""Data Fabric Runtime REST endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.dependencies import get_current_tenant_id

router = APIRouter()


class IngestRequest(BaseModel):
    records: list[dict] = Field(..., description="Array of records to ingest")
    source_slug: str = Field(..., description="Source identifier (balady, taqeem, ncnp, etc.)")


@router.post("/data-fabric/ingest", status_code=201)
async def ingest_batch(
    body: IngestRequest,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
):
    pipeline = getattr(request.app.state, "data_fabric", None)
    if not pipeline:
        raise HTTPException(status_code=503, detail="Data Fabric Runtime not initialized")

    result = await pipeline.run_batch(
        source_slug=body.source_slug,
        records=body.records,
        tenant_id=tenant_id,
    )
    return result


@router.post("/data-fabric/ingest/{source_slug}", status_code=201)
async def ingest_from_source(
    source_slug: str,
    body: IngestRequest,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
):
    pipeline = getattr(request.app.state, "data_fabric", None)
    if not pipeline:
        raise HTTPException(status_code=503, detail="Data Fabric Runtime not initialized")

    result = await pipeline.run_batch(
        source_slug=source_slug,
        records=body.records,
        tenant_id=tenant_id,
    )
    return result


@router.get("/data-fabric/metrics")
async def data_fabric_metrics(request: Request):
    pipeline = getattr(request.app.state, "data_fabric", None)
    if not pipeline:
        return {"status": "not_initialized"}
    return pipeline.metrics.snapshot()
