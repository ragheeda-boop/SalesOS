"""Analytics & Reporting API — cube queries, report CRUD, execution, and download."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import get_current_tenant_id, verify_token
from domains.analytics.cubes import ActivityCube, ForecastCube, PipelineCube, TeamCube
from domains.analytics.engine import CUBE_REGISTRY, ReportEngine
from domains.analytics.models import (
    CubeType,
    Granularity,
    OutputFormat,
    ReportDefinition,
    ReportExecution,
    ReportStatus,
    AnalyticsCube,
)
from domains.analytics.repository import InMemoryReportRepository
from domains.analytics.templates import STANDARD_TEMPLATES

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_engine() -> ReportEngine:
    repo = InMemoryReportRepository()
    return ReportEngine(repository=repo)


# ── Available Cubes ──────────────────────────────────────────────────────────


@router.get("/analytics/cubes")
async def list_cubes(
    tenant_id: str = Depends(get_current_tenant_id),
    _auth=Depends(verify_token),
):
    cubes = []
    for cube_type, cube in CUBE_REGISTRY.items():
        cubes.append({
            "name": cube.name,
            "type": cube_type.value,
            "dimensions": cube.dimensions,
            "measures": cube.measures,
            "granularity": cube.granularity.value,
        })
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
        raise HTTPException(status_code=404, detail=f"Unknown cube: {cube_name}")

    cube = CUBE_REGISTRY.get(cube_type)
    if cube is None:
        raise HTTPException(status_code=404, detail=f"Unknown cube: {cube_name}")

    filters = body.get("filters", {})
    granularity_str = body.get("granularity", cube.granularity.value)
    try:
        granularity = Granularity(granularity_str)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid granularity: {granularity_str}")

    try:
        rows = await cube.query(
            db=None, tenant_id=tenant_id, filters=filters, granularity=granularity
        )
    except Exception as exc:
        logger.exception("Cube query failed: %s", cube_name)
        raise HTTPException(status_code=500, detail=str(exc))

    return {"cube": cube_name, "rows": rows, "total": len(rows)}


# ── Reports CRUD ─────────────────────────────────────────────────────────────


@router.get("/analytics/reports")
async def list_reports(
    tenant_id: str = Depends(get_current_tenant_id),
    _auth=Depends(verify_token),
):
    engine = _get_engine()
    reports = await engine.repository.list_reports(tenant_id=tenant_id)
    return {
        "reports": [
            {
                "id": r.id,
                "tenant_id": r.tenant_id,
                "name": r.name,
                "type": r.type.value,
                "schedule": r.schedule,
                "recipients": r.recipients,
                "created_at": r.created_at.isoformat(),
                "updated_at": r.updated_at.isoformat(),
            }
            for r in reports
        ],
        "total": len(reports),
    }


@router.post("/analytics/reports")
async def create_report(
    body: dict[str, Any],
    tenant_id: str = Depends(get_current_tenant_id),
    _auth=Depends(verify_token),
):
    try:
        cube_type = CubeType(body.get("type", "custom"))
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid type: {body.get('type')}")

    report = ReportDefinition(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        name=body.get("name", "Untitled Report"),
        type=cube_type,
        config=body.get("config", {}),
        schedule=body.get("schedule", "one-time"),
        recipients=body.get("recipients", []),
    )
    engine = _get_engine()
    created = await engine.repository.create_report(report)
    return {
        "id": created.id,
        "name": created.name,
        "type": created.type.value,
        "schedule": created.schedule,
        "message": "Report created",
    }


@router.get("/analytics/reports/{report_id}")
async def get_report(
    report_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    _auth=Depends(verify_token),
):
    engine = _get_engine()
    report = await engine.repository.get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return {
        "id": report.id,
        "tenant_id": report.tenant_id,
        "name": report.name,
        "type": report.type.value,
        "config": report.config,
        "schedule": report.schedule,
        "recipients": report.recipients,
        "created_at": report.created_at.isoformat(),
        "updated_at": report.updated_at.isoformat(),
    }


@router.delete("/analytics/reports/{report_id}")
async def delete_report(
    report_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    _auth=Depends(verify_token),
):
    engine = _get_engine()
    deleted = await engine.repository.delete_report(report_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"message": "Report deleted", "id": report_id}


# ── Execution ────────────────────────────────────────────────────────────────


@router.post("/analytics/reports/{report_id}/execute")
async def execute_report(
    report_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    _auth=Depends(verify_token),
):
    engine = _get_engine()
    report = await engine.repository.get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    try:
        execution = await engine.generate(report_id, tenant_id)
    except Exception as exc:
        logger.exception("Report execution failed: %s", report_id)
        raise HTTPException(status_code=500, detail=str(exc))
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
    _auth=Depends(verify_token),
):
    engine = _get_engine()
    executions = await engine.repository.list_executions(report_id=report_id)
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
    }


@router.get("/analytics/executions/{execution_id}/download")
async def download_execution(
    execution_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    _auth=Depends(verify_token),
):
    engine = _get_engine()
    try:
        result = await engine.export(execution_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return result
