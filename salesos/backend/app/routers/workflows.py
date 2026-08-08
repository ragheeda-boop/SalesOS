"""Workflow Engine REST API — full CRUD, execution, webhooks, jobs, templates."""

from __future__ import annotations

import logging
from datetime import UTC
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_tenant_id, get_db_session, require_permission_dep
from app.modules.webhooks.url_safety import UnsafeWebhookURLError
from domains.workflow.engine import WorkflowEngine
from domains.workflow.models import (
    JobExecution,
    ScheduledJob,
    WebhookEndpoint,
    WorkflowExecution,
    WorkflowTemplate,
)
from domains.workflow.postgres_repo import PostgresWorkflowRepository
from domains.workflow.schemas import (
    ScheduledJobCreate,
    ScheduledJobUpdate,
    WebhookEndpointCreate,
    WorkflowCreate,
    WorkflowExecuteRequest,
    WorkflowUpdate,
)
from domains.workflow.service import WorkflowService, WorkflowValidationError
from sdk.permissions import PermissionAction

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Dependencies ──


async def _get_repo(db: AsyncSession = Depends(get_db_session)) -> PostgresWorkflowRepository:
    return PostgresWorkflowRepository(session=db)


async def _get_engine(db: AsyncSession = Depends(get_db_session)) -> WorkflowEngine:
    return WorkflowEngine(repository=PostgresWorkflowRepository(session=db))


async def _get_service(
    repo: PostgresWorkflowRepository = Depends(_get_repo),
    engine: WorkflowEngine = Depends(_get_engine),
) -> WorkflowService:
    return WorkflowService(repository=repo, engine=engine)


# ── Workflow CRUD ──


def _iso(dt) -> str | None:
    if dt is None:
        return None
    return dt.isoformat() if hasattr(dt, "isoformat") else str(dt)


def _is_missing_relation(exc: Exception) -> bool:
    msg = str(exc).lower()
    return "does not exist" in msg or "undefinedtable" in msg or "undefined column" in msg


@router.get("/workflows")
async def list_workflows(
    tenant_id: str = Depends(get_current_tenant_id),
    limit: int = Query(50, ge=1, le=200),
    cursor: str | None = Query(None),
    svc: WorkflowService = Depends(_get_service),
    _rbac: None = Depends(require_permission_dep("workflow", PermissionAction.READ)),
):
    try:
        workflows = await svc.list(tenant_id)
        offset = 0
        if cursor:
            try:
                offset = int(cursor)
            except (ValueError, TypeError):
                offset = 0
        sliced = workflows[offset : offset + limit]
        next_cursor = str(offset + limit) if offset + limit < len(workflows) else None
        return {
            "items": [
                {
                    "id": w.id,
                    "name": w.name,
                    "description": w.description,
                    "trigger_type": w.trigger_type,
                    "status": w.status,
                    "steps_count": len(w.steps or []),
                    "created_at": _iso(w.created_at),
                    "updated_at": _iso(w.updated_at),
                }
                for w in sliced
            ],
            "next_cursor": next_cursor,
            "total": len(workflows),
        }
    except Exception as exc:
        if _is_missing_relation(exc):
            logger.warning("list_workflows: workflow tables missing — returning empty (%s)", exc)
            return {"items": [], "next_cursor": None, "total": 0}
        logger.error("list_workflows failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/workflows/analytics")
async def workflow_analytics(
    tenant_id: str = Depends(get_current_tenant_id),
    days: int = Query(30, ge=1, le=365),
    svc: WorkflowService = Depends(_get_service),
    _rbac: None = Depends(require_permission_dep("workflow", PermissionAction.READ)),
):
    """Aggregate workflow + execution stats for automation analytics UI."""
    from collections import defaultdict
    from datetime import datetime, timedelta

    try:
        # Service method named `list` shadows builtin `list` in annotations → mypy list?
        workflows = cast(list[Any], await svc.list(tenant_id) or [])
        executions = cast(list[WorkflowExecution], await svc.list_executions(tenant_id) or [])
    except Exception as exc:
        if _is_missing_relation(exc):
            logger.warning("workflow_analytics: tables missing — empty payload (%s)", exc)
            workflows, executions = [], []
        else:
            logger.error("workflow_analytics failed: %s", exc)
            raise HTTPException(status_code=500, detail="Internal server error") from exc

    cutoff = datetime.now(UTC) - timedelta(days=days)
    recent = [
        e
        for e in executions
        if e.started_at
        and (e.started_at if e.started_at.tzinfo else e.started_at.replace(tzinfo=UTC)) >= cutoff
    ]

    successful = [e for e in recent if e.status in ("completed", "success")]
    failed = [e for e in recent if e.status in ("failed", "error", "cancelled")]
    total_exec = len(recent)
    success_n = len(successful)
    failed_n = len(failed)

    durations = []
    for e in successful:
        if e.started_at and e.completed_at:
            durations.append((e.completed_at - e.started_at).total_seconds())

    by_day: dict[str, dict[str, int]] = defaultdict(lambda: {"count": 0, "success": 0, "failed": 0})
    for e in recent:
        day = e.started_at.date().isoformat() if e.started_at else "unknown"
        by_day[day]["count"] += 1
        if e.status in ("completed", "success"):
            by_day[day]["success"] += 1
        elif e.status in ("failed", "error", "cancelled"):
            by_day[day]["failed"] += 1

    wf_name = {w.id: w.name for w in workflows}
    runs_by_wf: dict[str, list] = defaultdict(list)
    for e in recent:
        runs_by_wf[e.workflow_id].append(e)

    top_workflows = []
    for wf_id, runs in runs_by_wf.items():
        ok = sum(1 for r in runs if r.status in ("completed", "success"))
        top_workflows.append(
            {
                "id": wf_id,
                "name": wf_name.get(wf_id, wf_id),
                "runs": len(runs),
                "success_rate": round(ok / len(runs), 4) if runs else 0.0,
            }
        )
    top_workflows.sort(key=lambda x: int(x["runs"]), reverse=True)

    active = sum(1 for w in workflows if w.status == "active")
    draft = sum(1 for w in workflows if w.status == "draft")

    return {
        "total_workflows": len(workflows),
        "active_workflows": active,
        "draft_workflows": draft,
        "total_executions": total_exec,
        "successful_executions": success_n,
        "failed_executions": failed_n,
        "completion_rate": round((success_n / total_exec) * 100, 2) if total_exec else 0.0,
        "avg_duration_seconds": round(sum(durations) / len(durations), 2) if durations else 0.0,
        "failure_rate": round((failed_n / total_exec) * 100, 2) if total_exec else 0.0,
        "executions_over_time": [{"date": day, **vals} for day, vals in sorted(by_day.items())],
        "top_workflows": top_workflows[:10],
        "recent_executions": [
            {
                "id": e.id,
                "workflow_id": e.workflow_id,
                "status": e.status,
                "started_at": _iso(e.started_at),
                "completed_at": _iso(e.completed_at),
                "error": e.error,
            }
            for e in sorted(
                recent, key=lambda x: x.started_at or datetime.min.replace(tzinfo=UTC), reverse=True
            )[:20]
        ],
        "period_days": days,
    }


@router.post("/workflows", status_code=201)
async def create_workflow(
    body: WorkflowCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    svc: WorkflowService = Depends(_get_service),
    _rbac: None = Depends(require_permission_dep("workflow", PermissionAction.CREATE)),
):
    try:
        steps_dicts = [s.model_dump() for s in body.steps] if body.steps else None
        wf = await svc.create(
            tenant_id=tenant_id,
            name=body.name,
            description=body.description,
            trigger_type=body.trigger_type,
            status=body.status,
            steps=steps_dicts,
            template=body.template,
            timeout_seconds=body.timeout_seconds,
        )
        return {"id": wf.id, "name": wf.name, "steps_count": len(wf.steps), "status": wf.status}
    except WorkflowValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as exc:
        logger.error("create_workflow failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


# ── Execution & Template routes (must be before /workflows/{workflow_id}) ──


@router.get("/workflows/executions")
async def list_executions(
    workflow_id: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    cursor: str | None = Query(None),
    tenant_id: str = Depends(get_current_tenant_id),
    svc: WorkflowService = Depends(_get_service),
    _rbac: None = Depends(require_permission_dep("workflow", PermissionAction.READ)),
):
    try:
        executions = cast(
            list[WorkflowExecution], await svc.list_executions(tenant_id, workflow_id) or []
        )
        offset = 0
        if cursor:
            try:
                offset = int(cursor)
            except (ValueError, TypeError):
                offset = 0
        sliced = executions[offset : offset + limit]
        next_cursor = str(offset + limit) if offset + limit < len(executions) else None
        return {
            "items": [
                {
                    "id": ex.id,
                    "workflow_id": ex.workflow_id,
                    "trigger_event": ex.trigger_event,
                    "status": ex.status,
                    "error": ex.error,
                    "started_at": ex.started_at.isoformat(),
                    "completed_at": ex.completed_at.isoformat() if ex.completed_at else None,
                    "steps_count": len(ex.step_results),
                }
                for ex in sliced
            ],
            "next_cursor": next_cursor,
            "total": len(executions),
        }
    except Exception as exc:
        logger.error("list_executions failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/workflows/executions/{execution_id}")
async def get_execution(
    execution_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    svc: WorkflowService = Depends(_get_service),
    _rbac: None = Depends(require_permission_dep("workflow", PermissionAction.READ)),
):
    try:
        ex = await svc.get_execution(execution_id, tenant_id)
        if not ex:
            raise HTTPException(status_code=404, detail="Execution not found")
        return {
            "id": ex.id,
            "workflow_id": ex.workflow_id,
            "trigger_event": ex.trigger_event,
            "status": ex.status,
            "error": ex.error,
            "started_at": ex.started_at.isoformat(),
            "completed_at": ex.completed_at.isoformat() if ex.completed_at else None,
            "step_results": [
                {
                    "step_id": sr.step_id,
                    "step_type": sr.step_type,
                    "status": sr.status,
                    "result": sr.result,
                    "error": sr.error,
                    "started_at": sr.started_at.isoformat() if sr.started_at else None,
                    "completed_at": sr.completed_at.isoformat() if sr.completed_at else None,
                }
                for sr in ex.step_results
            ],
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("get_execution failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/workflows/templates")
async def list_templates(
    svc: WorkflowService = Depends(_get_service),
    _rbac: None = Depends(require_permission_dep("workflow", PermissionAction.READ)),
):
    try:
        templates = cast(list[WorkflowTemplate], await svc.list_templates() or [])
        return [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "category": t.category,
                "trigger_type": t.trigger_type,
                "tags": t.tags,
                "variables": t.variables,
            }
            for t in templates
        ]
    except Exception as exc:
        logger.error("list_templates failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/workflows/templates/{template_id}")
async def get_template(
    template_id: str,
    svc: WorkflowService = Depends(_get_service),
    _rbac: None = Depends(require_permission_dep("workflow", PermissionAction.READ)),
):
    try:
        tmpl = await svc.get_template(template_id)
        if not tmpl:
            raise HTTPException(status_code=404, detail="Template not found")
        return {
            "id": tmpl.id,
            "name": tmpl.name,
            "description": tmpl.description,
            "category": tmpl.category,
            "trigger_type": tmpl.trigger_type,
            "tags": tmpl.tags,
            "variables": tmpl.variables,
            "steps": tmpl.steps,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("get_template failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/workflows/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    svc: WorkflowService = Depends(_get_service),
    _rbac: None = Depends(require_permission_dep("workflow", PermissionAction.READ)),
):
    try:
        wf = await svc.get(workflow_id, tenant_id)
        if not wf:
            raise HTTPException(status_code=404, detail="Workflow not found")
        return {
            "id": wf.id,
            "name": wf.name,
            "description": wf.description,
            "trigger_type": wf.trigger_type,
            "status": wf.status,
            "timeout_seconds": wf.timeout_seconds,
            "steps": [
                {
                    "id": s.id,
                    "step_type": s.step_type,
                    "config": s.config,
                    "order": s.order,
                    "condition": s.condition,
                    "timeout_seconds": s.timeout_seconds,
                    "on_failure": s.on_failure,
                }
                for s in wf.steps
            ],
            "created_at": wf.created_at.isoformat(),
            "updated_at": wf.updated_at.isoformat(),
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("get_workflow failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.put("/workflows/{workflow_id}")
async def update_workflow(
    workflow_id: str,
    body: WorkflowUpdate,
    tenant_id: str = Depends(get_current_tenant_id),
    svc: WorkflowService = Depends(_get_service),
    _rbac: None = Depends(require_permission_dep("workflow", PermissionAction.UPDATE)),
):
    try:
        steps_dicts = [s.model_dump() for s in body.steps] if body.steps else None
        wf = await svc.update(
            workflow_id=workflow_id,
            tenant_id=tenant_id,
            name=body.name,
            description=body.description,
            trigger_type=body.trigger_type,
            status=body.status,
            steps=steps_dicts,
            timeout_seconds=body.timeout_seconds,
        )
        return {"id": wf.id, "name": wf.name, "status": wf.status}
    except WorkflowValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("update_workflow failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.delete("/workflows/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    svc: WorkflowService = Depends(_get_service),
    _rbac: None = Depends(require_permission_dep("workflow", PermissionAction.DELETE)),
):
    try:
        await svc.delete(workflow_id, tenant_id)
        return {"deleted": True, "id": workflow_id}
    except WorkflowValidationError:
        raise HTTPException(status_code=404, detail="Workflow not found") from None
    except Exception as exc:
        logger.error("delete_workflow failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


# ── Execution ──


@router.post("/workflows/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    body: WorkflowExecuteRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    svc: WorkflowService = Depends(_get_service),
    _rbac: None = Depends(require_permission_dep("workflow", PermissionAction.UPDATE)),
):
    try:
        execution = await svc.execute(workflow_id, tenant_id, body.context)
        return {
            "execution_id": execution.id,
            "workflow_id": execution.workflow_id,
            "status": execution.status,
            "error": execution.error,
            "steps": [
                {
                    "step_id": sr.step_id,
                    "step_type": sr.step_type,
                    "status": sr.status,
                    "result": sr.result,
                    "error": sr.error,
                }
                for sr in execution.step_results
            ],
        }
    except WorkflowValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("execute_workflow failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


# EAB-001-P1-DUP-02: remounted from `/webhooks` → `/workflow/webhooks` so Hub
# owns `/api/v1/webhooks/*` without prefix-family collision.
@router.post("/workflow/webhooks", status_code=201)
async def create_webhook(
    body: WebhookEndpointCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    svc: WorkflowService = Depends(_get_service),
    _rbac: None = Depends(require_permission_dep("workflow", PermissionAction.CREATE)),
):
    try:
        ep = await svc.create_webhook(
            tenant_id=tenant_id,
            url=body.url,
            name=body.name,
            auth_type=body.auth_type,
            auth_config=body.auth_config,
            secret=body.secret,
        )
        return {
            "id": ep.id,
            "url": ep.url,
            "name": ep.name,
            "auth_type": ep.auth_type,
            "status": ep.status,
        }
    except UnsafeWebhookURLError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as exc:
        logger.error("create_webhook failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/workflow/webhooks")
async def list_webhooks(
    tenant_id: str = Depends(get_current_tenant_id),
    svc: WorkflowService = Depends(_get_service),
    _rbac: None = Depends(require_permission_dep("workflow", PermissionAction.READ)),
):
    try:
        webhooks = cast(list[WebhookEndpoint], await svc.list_webhooks(tenant_id) or [])
        return [
            {
                "id": ep.id,
                "url": ep.url,
                "name": ep.name,
                "auth_type": ep.auth_type,
                "status": ep.status,
                "created_at": ep.created_at.isoformat(),
            }
            for ep in webhooks
        ]
    except Exception as exc:
        logger.error("list_webhooks failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/workflow/webhooks/{endpoint_id}")
async def get_webhook(
    endpoint_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    svc: WorkflowService = Depends(_get_service),
    _rbac: None = Depends(require_permission_dep("workflow", PermissionAction.READ)),
):
    try:
        ep = await svc.get_webhook(endpoint_id, tenant_id)
        if not ep:
            raise HTTPException(status_code=404, detail="Webhook not found")
        return {
            "id": ep.id,
            "url": ep.url,
            "name": ep.name,
            "auth_type": ep.auth_type,
            "status": ep.status,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("get_webhook failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.put("/workflow/webhooks/{endpoint_id}")
async def update_webhook(
    endpoint_id: str,
    body: WebhookEndpointCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    svc: WorkflowService = Depends(_get_service),
    _rbac: None = Depends(require_permission_dep("workflow", PermissionAction.UPDATE)),
):
    try:
        ep = await svc.update_webhook(
            endpoint_id=endpoint_id,
            tenant_id=tenant_id,
            url=body.url,
            name=body.name,
            auth_type=body.auth_type,
            secret=body.secret,
        )
        return {
            "id": ep.id,
            "url": ep.url,
            "name": ep.name,
            "auth_type": ep.auth_type,
            "status": ep.status,
        }
    except UnsafeWebhookURLError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except WorkflowValidationError:
        raise HTTPException(status_code=404, detail="Webhook not found") from None
    except Exception as exc:
        logger.error("update_webhook failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.delete("/workflow/webhooks/{endpoint_id}")
async def delete_webhook(
    endpoint_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    svc: WorkflowService = Depends(_get_service),
    _rbac: None = Depends(require_permission_dep("workflow", PermissionAction.DELETE)),
):
    try:
        await svc.delete_webhook(endpoint_id, tenant_id)
        return {"deleted": True, "id": endpoint_id}
    except WorkflowValidationError:
        raise HTTPException(status_code=404, detail="Webhook not found") from None
    except Exception as exc:
        logger.error("delete_webhook failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


# ── Scheduled Job CRUD ──


@router.post("/jobs", status_code=201)
async def create_job(
    body: ScheduledJobCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    svc: WorkflowService = Depends(_get_service),
    _rbac: None = Depends(require_permission_dep("workflow", PermissionAction.CREATE)),
):
    try:
        job = await svc.create_job(
            tenant_id=tenant_id,
            name=body.name,
            job_type=body.job_type,
            schedule=body.schedule,
            config=body.config,
            payload=body.payload,
            max_retries=body.max_retries,
        )
        return {
            "id": job.id,
            "name": job.name,
            "job_type": job.job_type,
            "schedule": job.schedule,
            "status": job.status,
            "next_run_at": job.next_run_at.isoformat() if job.next_run_at else None,
        }
    except WorkflowValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as exc:
        logger.error("create_job failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/jobs")
async def list_jobs(
    tenant_id: str = Depends(get_current_tenant_id),
    svc: WorkflowService = Depends(_get_service),
    _rbac: None = Depends(require_permission_dep("workflow", PermissionAction.READ)),
):
    try:
        jobs = cast(list[ScheduledJob], await svc.list_jobs(tenant_id) or [])
        return [
            {
                "id": j.id,
                "name": j.name,
                "job_type": j.job_type,
                "schedule": j.schedule,
                "status": j.status,
                "last_run_at": j.last_run_at.isoformat() if j.last_run_at else None,
                "next_run_at": j.next_run_at.isoformat() if j.next_run_at else None,
                "run_count": j.run_count,
            }
            for j in jobs
        ]
    except Exception as exc:
        logger.error("list_jobs failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/jobs/{job_id}")
async def get_job(
    job_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    svc: WorkflowService = Depends(_get_service),
    _rbac: None = Depends(require_permission_dep("workflow", PermissionAction.READ)),
):
    try:
        job = await svc.get_job(job_id, tenant_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return {
            "id": job.id,
            "name": job.name,
            "job_type": job.job_type,
            "schedule": job.schedule,
            "status": job.status,
            "config": job.config,
            "payload": job.payload,
            "last_run_at": job.last_run_at.isoformat() if job.last_run_at else None,
            "next_run_at": job.next_run_at.isoformat() if job.next_run_at else None,
            "run_count": job.run_count,
            "max_retries": job.max_retries,
            "retry_count": job.retry_count,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("get_job failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.put("/jobs/{job_id}")
async def update_job(
    job_id: str,
    body: ScheduledJobUpdate,
    tenant_id: str = Depends(get_current_tenant_id),
    svc: WorkflowService = Depends(_get_service),
    _rbac: None = Depends(require_permission_dep("workflow", PermissionAction.UPDATE)),
):
    try:
        job = await svc.update_job(
            job_id=job_id,
            tenant_id=tenant_id,
            name=body.name,
            status=body.status,
            schedule=body.schedule,
        )
        return {"id": job.id, "name": job.name, "status": job.status}
    except WorkflowValidationError:
        raise HTTPException(status_code=404, detail="Job not found") from None
    except Exception as exc:
        logger.error("update_job failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.delete("/jobs/{job_id}")
async def delete_job(
    job_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    svc: WorkflowService = Depends(_get_service),
    _rbac: None = Depends(require_permission_dep("workflow", PermissionAction.DELETE)),
):
    try:
        await svc.delete_job(job_id, tenant_id)
        return {"deleted": True, "id": job_id}
    except WorkflowValidationError:
        raise HTTPException(status_code=404, detail="Job not found") from None
    except Exception as exc:
        logger.error("delete_job failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/jobs/{job_id}/executions")
async def list_job_executions(
    job_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    svc: WorkflowService = Depends(_get_service),
    _rbac: None = Depends(require_permission_dep("workflow", PermissionAction.READ)),
):
    try:
        executions = cast(list[JobExecution], await svc.list_job_executions(job_id) or [])
        return [
            {
                "id": e.id,
                "job_id": e.job_id,
                "status": e.status,
                "started_at": e.started_at.isoformat() if e.started_at else None,
                "completed_at": e.completed_at.isoformat() if e.completed_at else None,
                "error": e.error,
            }
            for e in executions
        ]
    except Exception as exc:
        logger.error("list_job_executions failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc
