"""Admin routes for system monitoring and management."""

import time

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

from app.common.schemas import PaginatedResponse
from app.dependencies import get_current_tenant_id, get_db_session, require_role_dep

router = APIRouter(prefix="/api/v1/admin")


@router.get("/metrics")
async def system_metrics(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    _=Depends(require_role_dep("admin")),
):
    """Prometheus-style system metrics."""
    lines = [
        "# HELP salesos_info SalesOS application info",
        "# TYPE salesos_info gauge",
        f'salesos_info{{version="{settings.service_version}",env="{settings.env}"}} 1',
    ]

    try:
        row = await db.execute(text("SELECT COUNT(*) FROM companies"))
        count = row.scalar() or 0
        lines.append("# HELP salesos_companies_total Total companies in database")
        lines.append("# TYPE salesos_companies_total gauge")
        lines.append(f"salesos_companies_total {count}")

        row = await db.execute(text("SELECT COUNT(*) FROM golden_records"))
        count = row.scalar() or 0
        lines.append("# HELP salesos_golden_records_total Total golden records")
        lines.append("# TYPE salesos_golden_records_total gauge")
        lines.append(f"salesos_golden_records_total {count}")

        row = await db.execute(text("SELECT COUNT(*) FROM entity_resolution_conflicts WHERE status = 'open'"))
        count = row.scalar() or 0
        lines.append("# HELP salesos_open_conflicts_total Open entity resolution conflicts")
        lines.append("# TYPE salesos_open_conflicts_total gauge")
        lines.append(f"salesos_open_conflicts_total {count}")

        row = await db.execute(text("SELECT COUNT(*) FROM dead_letter_queue WHERE status = 'failed'"))
        count = row.scalar() or 0
        lines.append("# HELP salesos_dlq_failed_total Dead letter queue failed records")
        lines.append("# TYPE salesos_dlq_failed_total gauge")
        lines.append(f"salesos_dlq_failed_total {count}")
    except Exception:
        pass

    df = getattr(request.app.state, "data_fabric", None)
    if df:
        metrics = df.metrics.snapshot()
        lines.append("# HELP salesos_pipeline_records_ingested Pipeline records ingested")
        lines.append("# TYPE salesos_pipeline_records_ingested counter")
        lines.append(f"salesos_pipeline_records_ingested_total {metrics.get('records_ingested', 0)}")
        lines.append("# HELP salesos_pipeline_errors_total Pipeline errors by stage")
        lines.append("# TYPE salesos_pipeline_errors_total gauge")
        for stage, count in metrics.get("errors_by_stage", {}).items():
            lines.append(f'salesos_pipeline_errors_total{{stage="{stage}"}} {count}')
        lines.append("# HELP salesos_pipeline_stage_duration_ms_avg Average stage duration in ms")
        lines.append("# TYPE salesos_pipeline_stage_duration_ms_avg gauge")
        for stage, dur in metrics.get("stage_avg_durations_ms", {}).items():
            lines.append(f'salesos_pipeline_stage_duration_ms_avg{{stage="{stage}"}} {dur}')
        lines.append("# HELP salesos_pipeline_companies_synced Companies synced from golden records")
        lines.append("# TYPE salesos_pipeline_companies_synced counter")
        lines.append(f"salesos_pipeline_companies_synced_total {metrics.get('companies_synced', 0)}")
        lines.append("# HELP salesos_pipeline_embeddings_stored Embeddings stored in vector store")
        lines.append("# TYPE salesos_pipeline_embeddings_stored counter")
        lines.append(f"salesos_pipeline_embeddings_stored_total {metrics.get('embeddings_stored', 0)}")
        lines.append("# HELP salesos_pipeline_kg_triples_created Knowledge graph triples created")
        lines.append("# TYPE salesos_pipeline_kg_triples_created counter")
        lines.append(f"salesos_pipeline_kg_triples_created_total {metrics.get('kg_triples_created', 0)}")

    fs = getattr(request.app.state, "feature_store", None)
    if fs:
        fm = fs.metrics.snapshot()
        lines.append("# HELP salesos_feature_computations_total Feature store computations")
        lines.append("# TYPE salesos_feature_computations_total counter")
        lines.append(f"salesos_feature_computations_total {fm.get('computations', 0)}")
        lines.append("# HELP salesos_feature_cache_hits_total Feature store cache hits")
        lines.append("# TYPE salesos_feature_cache_hits_total counter")
        lines.append(f"salesos_feature_cache_hits_total {fm.get('cache_hits', 0)}")
        lines.append("# HELP salesos_feature_compute_ms_total Total compute ms")
        lines.append("# TYPE salesos_feature_compute_ms_total gauge")
        lines.append(f"salesos_feature_compute_ms_total {fm.get('total_compute_ms', 0)}")

    # Include system/performance metrics from in-memory tracker
    try:
        from app.common.metrics import metrics as sys_metrics
        lines.append("")
        lines.extend(sys_metrics.generate().split("\n")[1:-1])
    except Exception:
        pass

    lines.append(f"# EOF {time.time()}")
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse("\n".join(lines) + "\n")


@router.get("/health/full")
async def full_health(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    _=Depends(require_role_dep("admin")),
):
    """Detailed health status of all system components."""
    import redis.asyncio as aioredis
    from app.config import settings

    result = {"status": "ok", "checks": {}}

    try:
        await db.execute(text("SELECT 1"))
        result["checks"]["postgres"] = "connected"
    except Exception as e:
        result["checks"]["postgres"] = f"error: {e}"
        result["status"] = "degraded"

    try:
        r = aioredis.Redis.from_url(settings.redis_url)
        await r.ping()
        await r.aclose()
        result["checks"]["redis"] = "connected"
    except Exception as e:
        result["checks"]["redis"] = f"error: {e}"
        result["status"] = "degraded"

    kg = getattr(request.app.state, "kg_engine", None)
    if kg:
        try:
            is_healthy = await kg.health_check()
            result["checks"]["neo4j"] = "connected" if is_healthy else "unhealthy"
            result["checks"]["neo4j_metrics"] = kg.metrics.snapshot()
            if not is_healthy:
                result["status"] = "degraded"
        except Exception as e:
            result["checks"]["neo4j"] = f"error: {e}"
            result["status"] = "degraded"

    # Check dead letter queue count
    try:
        row = await db.execute(text("SELECT COUNT(*) FROM dead_letter_queue WHERE status = 'failed'"))
        result["dlq_failed_count"] = row.scalar() or 0
    except Exception:
        result["dlq_failed_count"] = -1

    df = getattr(request.app.state, "data_fabric", None)
    result["pipeline"] = df.metrics.snapshot() if df else {"status": "not_initialized"}

    return result


# ─── DLQ Admin Endpoints ─────────────────────────────────────


class DlqEntryResponse(BaseModel):
    id: int
    tenant_id: str
    source_slug: str
    cr_number: str | None
    stage: str
    error_message: str
    error_type: str | None
    retry_count: int
    max_retries: int
    status: str
    created_at: str
    last_retry_at: str | None


@router.get("/dlq", response_model=PaginatedResponse)
async def list_dlq(
    status: str | None = Query(None),
    stage: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
    tenant_id: str = Depends(get_current_tenant_id),
    _=Depends(require_role_dep("admin")),
):
    """List dead letter queue entries."""
    from app.modules.entity_resolution.repositories import DeadLetterRepository
    from app.modules.entity_resolution.models import DeadLetterRecord

    repo = DeadLetterRepository(db)
    records, total = await repo.list(
        tenant_id, status=status, stage=stage, page=page, page_size=page_size,
    )
    items = [
        DlqEntryResponse(
            id=r.id,
            tenant_id=str(r.tenant_id),
            source_slug=r.source_slug,
            cr_number=r.cr_number,
            stage=r.stage,
            error_message=r.error_message[:500],
            error_type=r.error_type,
            retry_count=r.retry_count,
            max_retries=r.max_retries,
            status=r.status,
            created_at=r.created_at.isoformat() if r.created_at else "",
            last_retry_at=r.last_retry_at.isoformat() if r.last_retry_at else None,
        )
        for r in records
    ]
    return PaginatedResponse(total=total, page=page, page_size=page_size, items=items)


class DlqRetryResponse(BaseModel):
    processed: int
    retried: int
    resolved: int
    still_failed: int


@router.post("/dlq/retry")
async def retry_dlq(
    limit: int = Query(50, ge=1, le=200),
    tenant_id: str = Depends(get_current_tenant_id),
    request: Request = ...,
    _=Depends(require_role_dep("admin")),
):
    """Retry failed records from the dead letter queue."""
    df = getattr(request.app.state, "data_fabric", None)
    if not df:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Data fabric pipeline not initialized")

    result = await df.retry_dlq(tenant_id, limit=limit)
    return DlqRetryResponse(**result)


@router.delete("/dlq")
async def purge_dlq(
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db_session),
    tenant_id: str = Depends(get_current_tenant_id),
    _=Depends(require_role_dep("admin")),
):
    """Purge dead letter queue entries."""
    from app.modules.entity_resolution.repositories import DeadLetterRepository

    repo = DeadLetterRepository(db)
    count = await repo.purge(tenant_id, status=status)
    await db.commit()
    return {"purged": count}


@router.get("/dlq/stats")
async def dlq_stats(
    db: AsyncSession = Depends(get_db_session),
    tenant_id: str = Depends(get_current_tenant_id),
    _=Depends(require_role_dep("admin")),
):
    """DLQ statistics grouped by stage and status."""
    from app.modules.entity_resolution.repositories import DeadLetterRepository

    repo = DeadLetterRepository(db)
    by_stage = await repo.count_by_stage(tenant_id)
    return {"failed_by_stage": by_stage}
