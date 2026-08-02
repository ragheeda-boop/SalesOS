"""STORY-10-03 — Canvas → Workflow Engine compiler (CAP-083).

Compiles a no-code canvas into ``Workflow`` / ``WorkflowStep`` for the
existing ``WorkflowEngine``. No second interpreter. Sprint-13 scope:
linear + branching; ``for_each`` rejected (loops deferred).
Not Production GO. DEC-085 untouched.
"""

from __future__ import annotations

import uuid
from typing import Any

from app.modules.tenant_studio.workflow_canvas import CanvasNode, WorkflowCanvas
from domains.workflow.models import Workflow, WorkflowStep
from domains.workflow.service import VALID_STEP_TYPES

# Sprint-13 debt: loops/iterators deferred.
_DEFERRED_STEP_TYPES = frozenset({"for_each"})

_ACTION_STEP_TYPES = frozenset(VALID_STEP_TYPES) - frozenset({"if_else", "for_each", "parallel"})


class WorkflowCanvasCompileError(ValueError):
    """Raised when canvas cannot compile to a valid Workflow."""


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


def _nested_action_def(node: CanvasNode) -> dict[str, Any]:
    """Nested step dict shape expected by WorkflowEngine if_else branches."""
    if node.kind != "action":
        raise WorkflowCanvasCompileError(
            "branch then/else children must be action nodes (nested branches deferred)"
        )
    st = (node.step_type or "").strip()
    if st in _DEFERRED_STEP_TYPES:
        raise WorkflowCanvasCompileError(
            f"step_type {st!r} deferred (Sprint-13: loops not in v1 canvas)"
        )
    if st not in _ACTION_STEP_TYPES:
        raise WorkflowCanvasCompileError(
            f"invalid nested action step_type {st!r}; "
            f"expected one of {sorted(_ACTION_STEP_TYPES)}"
        )
    return {"step_type": st, "config": dict(node.config or {})}


def _compile_node(node: CanvasNode, *, workflow_id: str, order: int) -> WorkflowStep:
    kind = (node.kind or "").strip()
    if kind == "action":
        st = (node.step_type or "").strip()
        if st in _DEFERRED_STEP_TYPES:
            raise WorkflowCanvasCompileError(
                f"step_type {st!r} deferred (Sprint-13: loops not in v1 canvas)"
            )
        if st == "if_else" or st == "parallel":
            raise WorkflowCanvasCompileError(
                f"use kind=branch for branching; step_type {st!r} not valid as action"
            )
        if st not in _ACTION_STEP_TYPES:
            raise WorkflowCanvasCompileError(
                f"invalid action step_type {st!r}; expected one of {sorted(_ACTION_STEP_TYPES)}"
            )
        return WorkflowStep(
            id=node.id or _new_id(),
            workflow_id=workflow_id,
            step_type=st,
            config=dict(node.config or {}),
            order=order,
            condition=node.condition,
        )

    if kind == "branch":
        condition = (node.condition or node.config.get("condition") or "").strip()
        if not condition:
            raise WorkflowCanvasCompileError("branch node requires condition")
        then_defs = [_nested_action_def(n) for n in node.then_nodes]
        else_defs = [_nested_action_def(n) for n in node.else_nodes]
        return WorkflowStep(
            id=node.id or _new_id(),
            workflow_id=workflow_id,
            step_type="if_else",
            config={
                "condition": condition,
                "then_steps": then_defs,
                "else_steps": else_defs,
            },
            order=order,
        )

    raise WorkflowCanvasCompileError(
        f"unsupported canvas node kind {kind!r}; expected action|branch"
    )


def compile_canvas(
    canvas: WorkflowCanvas,
    *,
    workflow_id: str | None = None,
    status: str = "draft",
) -> Workflow:
    """Compile canvas → Workflow Engine model (no second interpreter)."""
    if not (canvas.name or "").strip():
        raise WorkflowCanvasCompileError("canvas name is required")
    tid = (canvas.tenant_id or "").strip()
    if not tid:
        raise WorkflowCanvasCompileError("tenant_id is required")
    trigger = (canvas.trigger_type or "manual").strip()
    if trigger not in ("event", "scheduled", "manual"):
        raise WorkflowCanvasCompileError(f"invalid trigger_type: {trigger}")

    wf_id = workflow_id or canvas.id or _new_id()
    steps: list[WorkflowStep] = []
    for i, node in enumerate(canvas.nodes):
        if not (node.id or "").strip():
            node.id = _new_id()
        steps.append(_compile_node(node, workflow_id=wf_id, order=i))

    return Workflow(
        id=wf_id,
        tenant_id=tid,
        name=canvas.name.strip(),
        description=canvas.description or "",
        trigger_type=trigger,
        status=status if status in ("active", "inactive", "draft") else "draft",
        steps=steps,
    )


def workflow_to_public_dict(workflow: Workflow) -> dict[str, Any]:
    """JSON-serializable compile result for Studio HTTP."""
    return {
        "id": workflow.id,
        "tenant_id": workflow.tenant_id,
        "name": workflow.name,
        "description": workflow.description,
        "trigger_type": workflow.trigger_type,
        "status": workflow.status,
        "steps": [
            {
                "id": s.id,
                "workflow_id": s.workflow_id,
                "step_type": s.step_type,
                "config": dict(s.config),
                "order": s.order,
                "condition": s.condition,
                "on_failure": s.on_failure,
            }
            for s in workflow.steps
        ],
    }
