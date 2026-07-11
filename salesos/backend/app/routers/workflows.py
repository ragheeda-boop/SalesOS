"""Workflow Engine REST API."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.dependencies import get_current_tenant_id
from sdk.permissions import PermissionAction
from app.dependencies import require_permission_dep
from domains.workflow import InMemoryWorkflowRepository, WorkflowEngine, Workflow, WorkflowStep, WORKFLOW_TEMPLATES

logger = logging.getLogger(__name__)

router = APIRouter()

# Shared in-memory store (replaced by Postgres in production)
_repo = InMemoryWorkflowRepository()
_engine = WorkflowEngine(_repo)


# ── Schemas ──

class WorkflowStepSchema(BaseModel):
    step_type: str = Field(..., pattern=r"^(send_email|update_crm|create_task|webhook|nba_recommend)$")
    config: dict = Field(default_factory=dict)
    order: int = 0
    condition: str | None = None


class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    trigger_type: str = Field(default="manual", pattern=r"^(event|scheduled|manual)$")
    status: str = Field(default="draft", pattern=r"^(active|inactive|draft)$")
    steps: list[WorkflowStepSchema] = Field(default_factory=list)
    template: str | None = Field(None, description="Template key to base the workflow on")


class WorkflowUpdate(BaseModel):
    name: str | None = Field(None, max_length=200)
    description: str | None = None
    trigger_type: str | None = Field(None, pattern=r"^(event|scheduled|manual)$")
    status: str | None = Field(None, pattern=r"^(active|inactive|draft)$")
    steps: list[WorkflowStepSchema] | None = None


class WorkflowExecuteRequest(BaseModel):
    context: dict = Field(default_factory=dict)


# ── Dependencies ──

async def _get_repo() -> InMemoryWorkflowRepository:
    return _repo


async def _get_engine() -> WorkflowEngine:
    return _engine


# ── Endpoints ──

@router.get("/workflows")
async def list_workflows(
    tenant_id: str = Depends(get_current_tenant_id),
    repo: InMemoryWorkflowRepository = Depends(_get_repo),
    _rbac: None = Depends(require_permission_dep("workflow", PermissionAction.READ)),
):
    try:
        workflows = await repo.list(tenant_id)
        return [
            {
                "id": w.id,
                "name": w.name,
                "description": w.description,
                "trigger_type": w.trigger_type,
                "status": w.status,
                "steps_count": len(w.steps),
                "created_at": w.created_at.isoformat(),
                "updated_at": w.updated_at.isoformat(),
            }
            for w in workflows
        ]
    except Exception as exc:
        logger.error("list_workflows failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/workflows", status_code=201)
async def create_workflow(
    body: WorkflowCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    repo: InMemoryWorkflowRepository = Depends(_get_repo),
    _rbac: None = Depends(require_permission_dep("workflow", PermissionAction.CREATE)),
):
    try:
        steps: list[WorkflowStep] = []
        if body.template:
            template = WORKFLOW_TEMPLATES.get(body.template)
            if not template:
                raise HTTPException(status_code=404, detail=f"Template '{body.template}' not found")
            for s in template.steps:
                steps.append(WorkflowStep(
                    id=uuid.uuid4().hex[:12],
                    workflow_id="",
                    step_type=s.step_type,
                    config=s.config,
                    order=s.order,
                    condition=s.condition,
                ))
        else:
            for i, s in enumerate(body.steps):
                steps.append(WorkflowStep(
                    id=uuid.uuid4().hex[:12],
                    workflow_id="",
                    step_type=s.step_type,
                    config=s.config,
                    order=s.order or i,
                    condition=s.condition,
                ))

        wf = Workflow(
            id=uuid.uuid4().hex[:12],
            tenant_id=tenant_id,
            name=body.name,
            description=body.description,
            trigger_type=body.trigger_type,
            status=body.status if not body.template else "draft",
        )
        wf.steps = steps
        for s in wf.steps:
            s.workflow_id = wf.id

        await repo.create(wf)
        return {"id": wf.id, "name": wf.name, "steps_count": len(wf.steps), "status": wf.status}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("create_workflow failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/workflows/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    repo: InMemoryWorkflowRepository = Depends(_get_repo),
    _rbac: None = Depends(require_permission_dep("workflow", PermissionAction.READ)),
):
    try:
        wf = await repo.get(workflow_id, tenant_id)
        if not wf:
            raise HTTPException(status_code=404, detail="Workflow not found")
        return {
            "id": wf.id,
            "name": wf.name,
            "description": wf.description,
            "trigger_type": wf.trigger_type,
            "status": wf.status,
            "steps": [
                {
                    "id": s.id,
                    "step_type": s.step_type,
                    "config": s.config,
                    "order": s.order,
                    "condition": s.condition,
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
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/workflows/{workflow_id}")
async def update_workflow(
    workflow_id: str,
    body: WorkflowUpdate,
    tenant_id: str = Depends(get_current_tenant_id),
    repo: InMemoryWorkflowRepository = Depends(_get_repo),
    _rbac: None = Depends(require_permission_dep("workflow", PermissionAction.UPDATE)),
):
    try:
        wf = await repo.get(workflow_id, tenant_id)
        if not wf:
            raise HTTPException(status_code=404, detail="Workflow not found")

        if body.name is not None:
            wf.name = body.name
        if body.description is not None:
            wf.description = body.description
        if body.trigger_type is not None:
            wf.trigger_type = body.trigger_type
        if body.status is not None:
            wf.status = body.status
        if body.steps is not None:
            wf.steps = [
                WorkflowStep(
                    id=uuid.uuid4().hex[:12],
                    workflow_id=wf.id,
                    step_type=s.step_type,
                    config=s.config,
                    order=s.order or i,
                    condition=s.condition,
                )
                for i, s in enumerate(body.steps)
            ]
        wf.updated_at = datetime.now(timezone.utc)
        await repo.update(wf)
        return {"id": wf.id, "name": wf.name, "status": wf.status}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("update_workflow failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/workflows/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    repo: InMemoryWorkflowRepository = Depends(_get_repo),
    _rbac: None = Depends(require_permission_dep("workflow", PermissionAction.DELETE)),
):
    try:
        wf = await repo.get(workflow_id, tenant_id)
        if not wf:
            raise HTTPException(status_code=404, detail="Workflow not found")
        await repo.delete(workflow_id, tenant_id)
        return {"deleted": True, "id": workflow_id}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("delete_workflow failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/workflows/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    body: WorkflowExecuteRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    repo: InMemoryWorkflowRepository = Depends(_get_repo),
    engine: WorkflowEngine = Depends(_get_engine),
    _rbac: None = Depends(require_permission_dep("workflow", PermissionAction.UPDATE)),
):
    try:
        wf = await repo.get(workflow_id, tenant_id)
        if not wf:
            raise HTTPException(status_code=404, detail="Workflow not found")
        if wf.status != "active":
            raise HTTPException(status_code=400, detail=f"Workflow is '{wf.status}', must be 'active' to execute")

        execution = await engine.execute(wf, body.context)
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
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("execute_workflow failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/workflows/executions")
async def list_executions(
    workflow_id: str | None = None,
    tenant_id: str = Depends(get_current_tenant_id),
    repo: InMemoryWorkflowRepository = Depends(_get_repo),
    _rbac: None = Depends(require_permission_dep("workflow", PermissionAction.READ)),
):
    try:
        executions = await repo.list_executions(tenant_id, workflow_id)
        return [
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
            for ex in executions
        ]
    except Exception as exc:
        logger.error("list_executions failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/workflows/executions/{execution_id}")
async def get_execution(
    execution_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    repo: InMemoryWorkflowRepository = Depends(_get_repo),
    _rbac: None = Depends(require_permission_dep("workflow", PermissionAction.READ)),
):
    try:
        ex = await repo.get_execution(execution_id, tenant_id)
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
        raise HTTPException(status_code=500, detail="Internal server error")
