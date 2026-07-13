"""Enrichment REST API — async enrichment via Celery with Redis caching.

Endpoints:
  POST /api/v1/enrich              — Start async enrichment (returns 202)
  GET  /api/v1/enrich/{task_id}    — Poll task status
  GET  /api/v1/enrich/{task_id}/result — Get cached result
"""

from __future__ import annotations

import json as _json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.dependencies import get_current_tenant_id, verify_token

router = APIRouter(dependencies=[Depends(verify_token)])


class EnrichRequest(BaseModel):
    company_id: str
    source: str = "enrichment_api"


class EnrichStatusResponse(BaseModel):
    task_id: str
    status: str
    company_id: str
    result: dict[str, Any] | None = None


@router.post("/enrich", status_code=202)
async def start_enrichment(
    body: EnrichRequest,
    tenant_id: str = Depends(get_current_tenant_id),
):
    """Start async company enrichment. Returns 202 Accepted with task ID."""
    from app.tasks import enrich_company_task
    from app.common.redis_client import AsyncRedisClient

    client = AsyncRedisClient()
    cache_key = f"enrich:company:{body.company_id}"

    cached = await client.get(cache_key)
    if cached:
        try:
            cached_data = _json.loads(cached)
            return {
                "task_id": "cached",
                "status": "completed",
                "company_id": body.company_id,
                "result": cached_data,
                "source": "cache",
            }
        except Exception:
            pass

    task = enrich_company_task.delay(body.company_id, tenant_id)

    await client.set(
        f"enrich:task:{task.id}",
        _json.dumps({"task_id": task.id, "status": "pending", "company_id": body.company_id}),
        ttl=86400,
    )

    return {
        "task_id": task.id,
        "status": "pending",
        "company_id": body.company_id,
        "message": "Enrichment task queued. Poll GET /enrich/{task_id} for status.",
    }


@router.get("/enrich/{task_id}")
async def get_enrichment_status(
    task_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
):
    """Poll enrichment task status."""
    from celery.result import AsyncResult
    from app.tasks import enrich_company_task

    result = AsyncResult(task_id, app=enrich_company_task.app)

    if result.state == "PENDING":
        return {"task_id": task_id, "status": "pending", "result": None}
    elif result.state == "SUCCESS":
        return {"task_id": task_id, "status": "completed", "result": result.result}
    elif result.state == "FAILURE":
        return {"task_id": task_id, "status": "failed", "error": str(result.info)}
    elif result.state in ("RETRY", "STARTED"):
        return {"task_id": task_id, "status": "processing", "result": None}
    else:
        return {"task_id": task_id, "status": result.state, "result": None}


@router.get("/enrich/{task_id}/result")
async def get_enrichment_result(
    task_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
):
    """Get the final result of a completed enrichment task."""
    from celery.result import AsyncResult
    from app.tasks import enrich_company_task

    result = AsyncResult(task_id, app=enrich_company_task.app)

    if result.state != "SUCCESS":
        raise HTTPException(
            status_code=202 if result.state in ("PENDING", "STARTED") else 500,
            detail=f"Task {task_id} is {result.state}",
        )

    return {"task_id": task_id, "status": "completed", "result": result.result}
