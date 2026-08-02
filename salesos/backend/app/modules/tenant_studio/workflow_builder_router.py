"""STORY-10-03 — Tenant Studio Workflow Builder HTTP (CAP-083).

Canvas CRUD + compile to existing Workflow Engine models.
Not Production GO. DEC-085 untouched.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.dependencies import get_current_tenant_id, verify_token
from app.modules.tenant_studio.workflow_canvas import CanvasNode, WorkflowCanvas
from app.modules.tenant_studio.workflow_canvas_store import (
    DEFAULT_CANVAS_STORE,
    MemWorkflowCanvasStore,
)
from app.modules.tenant_studio.workflow_compiler import (
    WorkflowCanvasCompileError,
    compile_canvas,
    workflow_to_public_dict,
)

router = APIRouter(prefix="/studio/workflows", tags=["Tenant Studio"])
_AUTH = [Depends(verify_token)]

_STORE = DEFAULT_CANVAS_STORE


class CanvasNodeIn(BaseModel):
    id: str = ""
    kind: str = "action"
    step_type: str = ""
    config: dict[str, Any] = Field(default_factory=dict)
    condition: str | None = None
    then_nodes: list[CanvasNodeIn] = Field(default_factory=list)
    else_nodes: list[CanvasNodeIn] = Field(default_factory=list)


class WorkflowCanvasUpsert(BaseModel):
    id: str | None = None
    name: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    trigger_type: str = "manual"
    nodes: list[CanvasNodeIn] = Field(default_factory=list)


class WorkflowCanvasResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    description: str = ""
    trigger_type: str = "manual"
    nodes: list[dict[str, Any]] = Field(default_factory=list)
    schema_version: int = 1
    created_at: str = ""
    updated_at: str = ""


def _node_from_in(n: CanvasNodeIn) -> CanvasNode:
    return CanvasNode(
        id=n.id,
        kind=n.kind,  # type: ignore[arg-type]
        step_type=n.step_type,
        config=dict(n.config),
        condition=n.condition,
        then_nodes=[_node_from_in(c) for c in n.then_nodes],
        else_nodes=[_node_from_in(c) for c in n.else_nodes],
    )


@router.post("", response_model=WorkflowCanvasResponse, dependencies=_AUTH)
async def upsert_workflow_canvas(
    body: WorkflowCanvasUpsert,
    tenant_id: str = Depends(get_current_tenant_id),
) -> WorkflowCanvasResponse:
    canvas = WorkflowCanvas(
        id=body.id or "",
        tenant_id=str(tenant_id),
        name=body.name,
        description=body.description,
        trigger_type=body.trigger_type,
        nodes=[_node_from_in(n) for n in body.nodes],
    )
    try:
        saved = _STORE.save(canvas)
    except (WorkflowCanvasCompileError, PermissionError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return WorkflowCanvasResponse.model_validate(saved.as_dict())


@router.get("", response_model=list[WorkflowCanvasResponse], dependencies=_AUTH)
async def list_workflow_canvases(
    tenant_id: str = Depends(get_current_tenant_id),
) -> list[WorkflowCanvasResponse]:
    rows = _STORE.list_for_tenant(tenant_id=str(tenant_id))
    return [WorkflowCanvasResponse.model_validate(r.as_dict()) for r in rows]


@router.get("/{canvas_id}", response_model=WorkflowCanvasResponse, dependencies=_AUTH)
async def get_workflow_canvas(
    canvas_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
) -> WorkflowCanvasResponse:
    row = _STORE.get(canvas_id, tenant_id=str(tenant_id))
    if row is None:
        raise HTTPException(status_code=404, detail="canvas not found")
    return WorkflowCanvasResponse.model_validate(row.as_dict())


@router.post("/{canvas_id}/compile", dependencies=_AUTH)
async def compile_workflow_canvas(
    canvas_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
) -> dict[str, Any]:
    """Compile saved canvas → Workflow Engine graph (no second interpreter)."""
    try:
        canvas, _wf, public = _STORE.compile(canvas_id, tenant_id=str(tenant_id))
    except KeyError:
        raise HTTPException(status_code=404, detail="canvas not found") from None
    except WorkflowCanvasCompileError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "canvas_id": canvas.id,
        "schema_version": canvas.schema_version,
        "workflow": public,
    }


@router.post("/compile", dependencies=_AUTH)
async def compile_workflow_canvas_ephemeral(
    body: WorkflowCanvasUpsert,
    tenant_id: str = Depends(get_current_tenant_id),
) -> dict[str, Any]:
    """Compile an unsaved canvas body → Workflow Engine graph."""
    canvas = WorkflowCanvas(
        id=body.id or "ephemeral",
        tenant_id=str(tenant_id),
        name=body.name,
        description=body.description,
        trigger_type=body.trigger_type,
        nodes=[_node_from_in(n) for n in body.nodes],
    )
    try:
        workflow = compile_canvas(canvas)
    except WorkflowCanvasCompileError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"workflow": workflow_to_public_dict(workflow)}


def _reset_canvas_store_for_tests() -> MemWorkflowCanvasStore:
    global _STORE
    from app.modules.tenant_studio import workflow_canvas_store as store_mod

    store_mod.DEFAULT_CANVAS_STORE = MemWorkflowCanvasStore()
    _STORE = store_mod.DEFAULT_CANVAS_STORE
    return _STORE
