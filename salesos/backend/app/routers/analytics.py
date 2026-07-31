"""Analytics & Reporting API — cubes, reports, execution, sharing, export, and scheduling."""

from __future__ import annotations

import io
import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.common.exceptions import safe_error_detail
from app.dependencies import (
    get_current_tenant_id,
    get_current_user_id,
    get_db_session,
    verify_token,
)
from domains.analytics.engine import CUBE_REGISTRY, ReportEngine
from domains.analytics.infrastructure.postgres_repository import PostgresReportRepository
from domains.analytics.models import (
    CubeType,
    Granularity,
    OutputFormat,
    PermissionLevel,
    ReportDefinition,
    ScheduleCadence,
    VisualizationType,
)
from domains.analytics.schemas import (
    ReportCreate,
    ReportShareCreate,
    ReportUpdate,
    ScheduledReportCreate,
    ScheduledReportUpdate,
)
from domains.analytics.templates import STANDARD_TEMPLATES

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_engine(db) -> ReportEngine:
    repo = PostgresReportRepository(session=db)
    return ReportEngine(repository=repo)


# ── B-1: Unified Analytics ──────────────────────────────────────────────────


@router.get("/analytics")
async def get_unified_analytics(
    domain: str | None = Query(
        None, description="Filter by domain: pipeline, forecast, team, activity"
    ),
    tenant_id: str = Depends(get_current_tenant_id),
    db=Depends(get_db_session),
    _auth=Depends(verify_token),
):
    """Unified analytics endpoint — aggregates data from all domain cubes."""
    engine = _get_engine(db)
    try:
        metrics = await engine.get_unified_analytics(tenant_id, domain)
    except Exception as exc:
        logger.exception("Unified analytics failed")
        raise HTTPException(status_code=500, detail=safe_error_detail(exc)) from exc
    return {
        "total_deals": metrics.total_deals,
        "total_revenue": metrics.total_revenue,
        "total_employees": metrics.total_employees,
        "total_workflows": metrics.total_workflows,
        "conversion_rate": metrics.conversion_rate,
        "pipeline_value": metrics.pipeline_value,
        "avg_deal_size": metrics.avg_deal_size,
        "win_rate": metrics.win_rate,
        "active_automations": metrics.active_automations,
        "generated_at": metrics.generated_at.isoformat(),
    }


# ── Cubes ───────────────────────────────────────────────────────────────────


@router.get("/analytics/cubes")
async def list_cubes(
    tenant_id: str = Depends(get_current_tenant_id),
    _auth=Depends(verify_token),
):
    cubes = []
    for cube_type, cube in CUBE_REGISTRY.items():
        cubes.append(
            {
                "name": cube.name,
                "type": cube_type.value,
                "dimensions": cube.dimensions,
                "measures": cube.measures,
                "granularity": cube.granularity.value,
            }
        )
    return {"cubes": cubes}


@router.post("/analytics/cubes/{cube_name}/query")
async def query_cube(
    cube_name: str,
    body: dict[str, Any],
    tenant_id: str = Depends(get_current_tenant_id),
    _auth=Depends(verify_token),
):
    try:
        cube_type = CubeType(cube_name)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Unknown cube: {cube_name}") from None

    cube = CUBE_REGISTRY.get(cube_type)
    if cube is None:
        raise HTTPException(status_code=404, detail=f"Unknown cube: {cube_name}")

    filters = body.get("filters", {})
    granularity_str = body.get("granularity", cube.granularity.value)
    try:
        granularity = Granularity(granularity_str)
    except ValueError:
        raise HTTPException(
            status_code=422, detail=f"Invalid granularity: {granularity_str}"
        ) from None  # noqa: E501

    try:
        rows = await cube.query(
            db=None, tenant_id=tenant_id, filters=filters, granularity=granularity
        )
    except Exception as exc:
        logger.exception("Cube query failed: %s", cube_name)
        raise HTTPException(status_code=500, detail=safe_error_detail(exc)) from exc

    return {"cube": cube_name, "rows": rows, "total": len(rows)}


# ── B-2: Reports CRUD ──────────────────────────────────────────────────────


@router.get("/analytics/reports")
async def list_reports(
    tenant_id: str = Depends(get_current_tenant_id),
    db=Depends(get_db_session),
    limit: int = Query(50, ge=1, le=200),
    cursor: str | None = Query(None),
    _auth=Depends(verify_token),
):
    engine = _get_engine(db)
    reports, next_cursor = await engine.repository.list_reports(
        tenant_id=tenant_id, limit=limit, cursor=cursor
    )
    return {
        "reports": [
            {
                "id": r.id,
                "tenant_id": r.tenant_id,
                "name": r.name,
                "type": r.type.value,
                "metrics": r.metrics,
                "dimensions": r.dimensions,
                "filters": r.filters,
                "visualization_type": r.visualization_type.value,
                "created_by": r.created_by,
                "schedule": r.schedule,
                "recipients": r.recipients,
                "created_at": r.created_at.isoformat(),
                "updated_at": r.updated_at.isoformat(),
            }
            for r in reports
        ],
        "total": len(reports),
        "next_cursor": next_cursor,
    }


@router.post("/analytics/reports")
async def create_report(
    body: ReportCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_db_session),
    _auth=Depends(verify_token),
):
    try:
        cube_type = CubeType(body.type)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid type: {body.type}") from None
    try:
        viz_type = VisualizationType(body.visualization_type)
    except ValueError:
        raise HTTPException(
            status_code=422, detail=f"Invalid visualization_type: {body.visualization_type}"
        ) from None

    report = ReportDefinition(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        name=body.name,
        type=cube_type,
        config=body.config,
        metrics=body.metrics,
        dimensions=body.dimensions,
        filters=body.filters,
        visualization_type=viz_type,
        created_by=user_id,
        schedule=body.schedule,
        recipients=body.recipients,
    )
    engine = _get_engine(db)
    created = await engine.repository.create_report(report)
    return {
        "id": created.id,
        "name": created.name,
        "type": created.type.value,
        "visualization_type": created.visualization_type.value,
        "metrics": created.metrics,
        "dimensions": created.dimensions,
        "message": "Report created",
    }


@router.get("/analytics/reports/{report_id}")
async def get_report(
    report_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db=Depends(get_db_session),
    _auth=Depends(verify_token),
):
    engine = _get_engine(db)
    report = await engine.repository.get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return {
        "id": report.id,
        "tenant_id": report.tenant_id,
        "name": report.name,
        "type": report.type.value,
        "config": report.config,
        "metrics": report.metrics,
        "dimensions": report.dimensions,
        "filters": report.filters,
        "visualization_type": report.visualization_type.value,
        "created_by": report.created_by,
        "schedule": report.schedule,
        "recipients": report.recipients,
        "created_at": report.created_at.isoformat(),
        "updated_at": report.updated_at.isoformat(),
    }


@router.put("/analytics/reports/{report_id}")
async def update_report(
    report_id: str,
    body: ReportUpdate,
    tenant_id: str = Depends(get_current_tenant_id),
    db=Depends(get_db_session),
    _auth=Depends(verify_token),
):
    engine = _get_engine(db)
    report = await engine.repository.get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    if body.name is not None:
        report.name = body.name
    if body.config is not None:
        report.config = body.config
    if body.metrics is not None:
        report.metrics = body.metrics
    if body.dimensions is not None:
        report.dimensions = body.dimensions
    if body.filters is not None:
        report.filters = body.filters
    if body.visualization_type is not None:
        report.visualization_type = VisualizationType(body.visualization_type)
    if body.schedule is not None:
        report.schedule = body.schedule
    if body.recipients is not None:
        report.recipients = body.recipients
    updated = await engine.repository.update_report(report)
    return {"id": updated.id, "message": "Report updated"}


@router.delete("/analytics/reports/{report_id}")
async def delete_report(
    report_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db=Depends(get_db_session),
    _auth=Depends(verify_token),
):
    engine = _get_engine(db)
    deleted = await engine.repository.delete_report(report_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"message": "Report deleted", "id": report_id}


# ── Report Sharing ──────────────────────────────────────────────────────────


@router.post("/analytics/reports/{report_id}/share")
async def share_report(
    report_id: str,
    body: ReportShareCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_db_session),
    _auth=Depends(verify_token),
):
    engine = _get_engine(db)
    try:
        permission = PermissionLevel(body.permission)
    except ValueError:
        raise HTTPException(
            status_code=422, detail=f"Invalid permission: {body.permission}"
        ) from None  # noqa: E501
    try:
        share = await engine.share_report(report_id, body.user_id, permission, shared_by=user_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=safe_error_detail(exc)) from exc
    return {
        "id": share.id,
        "report_id": share.report_id,
        "user_id": share.user_id,
        "permission": share.permission.value,
        "message": "Report shared",
    }


@router.get("/analytics/reports/{report_id}/shares")
async def list_shares(
    report_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db=Depends(get_db_session),
    limit: int = Query(50, ge=1, le=200),
    cursor: str | None = Query(None),
    _auth=Depends(verify_token),
):
    engine = _get_engine(db)
    all_shares = await engine.list_shares(report_id)
    offset = 0
    if cursor:
        try:
            offset = int(cursor)
        except (ValueError, TypeError):
            offset = 0
    sliced = all_shares[offset : offset + limit]
    next_cursor = str(offset + limit) if offset + limit < len(all_shares) else None
    return {
        "shares": [
            {
                "id": s.id,
                "report_id": s.report_id,
                "user_id": s.user_id,
                "permission": s.permission.value,
                "shared_by": s.shared_by,
                "created_at": s.created_at.isoformat(),
            }
            for s in sliced
        ],
        "next_cursor": next_cursor,
        "total": len(all_shares),
    }


@router.delete("/analytics/shares/{share_id}")
async def remove_share(
    share_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db=Depends(get_db_session),
    _auth=Depends(verify_token),
):
    engine = _get_engine(db)
    removed = await engine.remove_share(share_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Share not found")
    return {"message": "Share removed", "id": share_id}


# ── Execution ───────────────────────────────────────────────────────────────


@router.post("/analytics/reports/{report_id}/execute")
async def execute_report(
    report_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db=Depends(get_db_session),
    _auth=Depends(verify_token),
):
    engine = _get_engine(db)
    report = await engine.repository.get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    try:
        execution = await engine.generate(report_id, tenant_id)
    except Exception as exc:
        logger.exception("Report execution failed: %s", report_id)
        raise HTTPException(status_code=500, detail=safe_error_detail(exc)) from exc
    return {
        "execution_id": execution.id,
        "status": execution.status.value,
        "output_format": execution.output_format.value,
        "output_path": execution.output_path,
    }


@router.get("/analytics/executions")
async def list_executions(
    report_id: str | None = Query(None),
    tenant_id: str = Depends(get_current_tenant_id),
    db=Depends(get_db_session),
    limit: int = Query(50, ge=1, le=200),
    cursor: str | None = Query(None),
    _auth=Depends(verify_token),
):
    engine = _get_engine(db)
    offset = 0
    if cursor:
        try:
            offset = int(cursor)
        except (ValueError, TypeError):
            offset = 0
    executions, next_cursor = await engine.repository.list_executions(
        report_id=report_id, limit=limit, offset=offset
    )
    return {
        "executions": [
            {
                "id": e.id,
                "report_id": e.report_id,
                "status": e.status.value,
                "output_format": e.output_format.value,
                "error": e.error,
                "started_at": e.started_at.isoformat() if e.started_at else None,
                "completed_at": e.completed_at.isoformat() if e.completed_at else None,
            }
            for e in executions
        ],
        "total": len(executions),
        "next_cursor": next_cursor,
    }


@router.get("/analytics/executions/{execution_id}/download")
async def download_execution(
    execution_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db=Depends(get_db_session),
    _auth=Depends(verify_token),
):
    engine = _get_engine(db)
    try:
        result = await engine.export(execution_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=404, detail=safe_error_detail(exc, "Export not found")
        ) from exc  # noqa: E501
    return result


# ── B-3: Export Engine ──────────────────────────────────────────────────────


@router.get("/analytics/export")
async def export_report(
    report_id: str = Query(..., description="Report ID to export"),
    format: str = Query("csv", description="Export format: csv, pdf, json"),
    tenant_id: str = Depends(get_current_tenant_id),
    db=Depends(get_db_session),
    _auth=Depends(verify_token),
):
    """Export report data in CSV (streaming), PDF, or JSON format."""
    engine = _get_engine(db)
    try:
        output_format = OutputFormat(format)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid format: {format}") from None
    try:
        result = await engine.export_report(report_id, tenant_id, output_format)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=safe_error_detail(exc)) from exc

    if output_format == OutputFormat.CSV:
        csv_bytes = result["content"].encode("utf-8")
        return StreamingResponse(
            io.BytesIO(csv_bytes),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="report_{report_id}.csv"'},
        )
    return {
        "content": result["content"],
        "format": result["format"],
        "path": result.get("path"),
    }


# ── B-4: Scheduled Reports ─────────────────────────────────────────────────


@router.post("/analytics/schedules")
async def create_schedule(
    body: ScheduledReportCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    db=Depends(get_db_session),
    _auth=Depends(verify_token),
):
    engine = _get_engine(db)
    try:
        cadence = ScheduleCadence(body.cadence)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid cadence: {body.cadence}") from None
    try:
        schedule = await engine.create_schedule(tenant_id, body.report_id, cadence, body.recipients)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=safe_error_detail(exc)) from exc
    return {
        "id": schedule.id,
        "report_id": schedule.report_id,
        "cadence": schedule.cadence.value,
        "recipients": schedule.recipients,
        "next_run": schedule.next_run.isoformat() if schedule.next_run else None,
        "message": "Schedule created",
    }


@router.get("/analytics/schedules")
async def list_schedules(
    tenant_id: str = Depends(get_current_tenant_id),
    db=Depends(get_db_session),
    limit: int = Query(50, ge=1, le=200),
    cursor: str | None = Query(None),
    _auth=Depends(verify_token),
):
    engine = _get_engine(db)
    all_schedules = await engine.list_schedules(tenant_id)
    offset = 0
    if cursor:
        try:
            offset = int(cursor)
        except (ValueError, TypeError):
            offset = 0
    sliced = all_schedules[offset : offset + limit]
    next_cursor = str(offset + limit) if offset + limit < len(all_schedules) else None
    return {
        "schedules": [
            {
                "id": s.id,
                "tenant_id": s.tenant_id,
                "report_id": s.report_id,
                "cadence": s.cadence.value,
                "recipients": s.recipients,
                "next_run": s.next_run.isoformat() if s.next_run else None,
                "last_run": s.last_run.isoformat() if s.last_run else None,
                "enabled": s.enabled,
                "created_at": s.created_at.isoformat(),
                "updated_at": s.updated_at.isoformat(),
            }
            for s in sliced
        ],
        "next_cursor": next_cursor,
        "total": len(all_schedules),
    }


@router.get("/analytics/schedules/{schedule_id}")
async def get_schedule(
    schedule_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db=Depends(get_db_session),
    _auth=Depends(verify_token),
):
    engine = _get_engine(db)
    schedule = await engine.get_schedule(schedule_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return {
        "id": schedule.id,
        "tenant_id": schedule.tenant_id,
        "report_id": schedule.report_id,
        "cadence": schedule.cadence.value,
        "recipients": schedule.recipients,
        "next_run": schedule.next_run.isoformat() if schedule.next_run else None,
        "last_run": schedule.last_run.isoformat() if schedule.last_run else None,
        "enabled": schedule.enabled,
        "created_at": schedule.created_at.isoformat(),
        "updated_at": schedule.updated_at.isoformat(),
    }


@router.put("/analytics/schedules/{schedule_id}")
async def update_schedule(
    schedule_id: str,
    body: ScheduledReportUpdate,
    tenant_id: str = Depends(get_current_tenant_id),
    db=Depends(get_db_session),
    _auth=Depends(verify_token),
):
    engine = _get_engine(db)
    cadence = ScheduleCadence(body.cadence) if body.cadence else None
    try:
        updated = await engine.update_schedule(
            schedule_id, cadence=cadence, recipients=body.recipients, enabled=body.enabled
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=safe_error_detail(exc)) from exc
    return {
        "id": updated.id,
        "cadence": updated.cadence.value,
        "enabled": updated.enabled,
        "next_run": updated.next_run.isoformat() if updated.next_run else None,
        "message": "Schedule updated",
    }


@router.delete("/analytics/schedules/{schedule_id}")
async def delete_schedule(
    schedule_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db=Depends(get_db_session),
    _auth=Depends(verify_token),
):
    engine = _get_engine(db)
    deleted = await engine.delete_schedule(schedule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return {"message": "Schedule deleted", "id": schedule_id}


@router.post("/analytics/schedules/execute-due")
async def execute_due_schedules(
    tenant_id: str = Depends(get_current_tenant_id),
    db=Depends(get_db_session),
    _auth=Depends(verify_token),
):
    """Pick up and execute all due scheduled reports."""
    engine = _get_engine(db)
    results = await engine.execute_due_schedules()
    return {"executed": len(results), "results": results}


# ── Templates ───────────────────────────────────────────────────────────────


@router.get("/analytics/templates")
async def list_templates(
    _auth=Depends(verify_token),
):
    templates = []
    for key, factory in STANDARD_TEMPLATES.items():
        sample = factory("template-preview")
        templates.append(
            {
                "key": key,
                "name": sample.name,
                "type": sample.type.value,
                "schedule": sample.schedule,
            }
        )
    return {"templates": templates}


# ── Client Analytics Events ─────────────────────────────────────────────────


@router.post("/analytics/events")
async def ingest_analytics_events(
    body: dict,
    tenant_id: str = Depends(get_current_tenant_id),
    _auth=Depends(verify_token),
):
    """Accept batched analytics events from the frontend (fire-and-forget)."""
    events = body.get("events", [])
    logger.debug("Received %d analytics events for tenant %s", len(events), tenant_id)
    return {"status": "ok", "received": len(events)}
