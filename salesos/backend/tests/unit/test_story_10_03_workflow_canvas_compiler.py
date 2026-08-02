"""STORY-10-03 — Canvas → Workflow Engine compiler equivalence suite."""

from __future__ import annotations

import pytest

from app.modules.tenant_studio.workflow_canvas import CanvasNode, WorkflowCanvas
from app.modules.tenant_studio.workflow_canvas_store import MemWorkflowCanvasStore
from app.modules.tenant_studio.workflow_compiler import (
    WorkflowCanvasCompileError,
    compile_canvas,
)
from domains.workflow.engine import WorkflowEngine
from domains.workflow.models import Workflow, WorkflowStep
from domains.workflow.repository import InMemoryWorkflowRepository


def _linear_canvas(tenant_id: str = "t1") -> WorkflowCanvas:
    return WorkflowCanvas(
        id="cv-1",
        tenant_id=tenant_id,
        name="Lead follow-up",
        trigger_type="manual",
        nodes=[
            CanvasNode(
                id="n1",
                kind="action",
                step_type="set_variable",
                config={"name": "stage", "value": "contacted"},
            ),
            CanvasNode(
                id="n2",
                kind="action",
                step_type="log_message",
                config={"message": "done", "level": "info"},
            ),
        ],
    )


def test_compile_linear_canvas_to_workflow_steps() -> None:
    wf = compile_canvas(_linear_canvas())
    assert wf.name == "Lead follow-up"
    assert len(wf.steps) == 2
    assert wf.steps[0].step_type == "set_variable"
    assert wf.steps[0].order == 0
    assert wf.steps[1].step_type == "log_message"
    assert wf.steps[1].order == 1


def test_compile_rejects_for_each_deferred() -> None:
    canvas = WorkflowCanvas(
        id="cv-x",
        tenant_id="t1",
        name="Loop",
        nodes=[
            CanvasNode(
                id="n1",
                kind="action",
                step_type="for_each",
                config={"collection_key": "items", "item_var": "item", "steps": []},
            )
        ],
    )
    with pytest.raises(WorkflowCanvasCompileError, match="deferred"):
        compile_canvas(canvas)


def test_compile_branch_nests_if_else_config() -> None:
    canvas = WorkflowCanvas(
        id="cv-b",
        tenant_id="t1",
        name="Branching",
        nodes=[
            CanvasNode(
                id="br1",
                kind="branch",
                condition="amount > 100",
                then_nodes=[
                    CanvasNode(
                        id="t1",
                        kind="action",
                        step_type="log_message",
                        config={"message": "big"},
                    )
                ],
                else_nodes=[
                    CanvasNode(
                        id="e1",
                        kind="action",
                        step_type="log_message",
                        config={"message": "small"},
                    )
                ],
            )
        ],
    )
    wf = compile_canvas(canvas)
    assert len(wf.steps) == 1
    step = wf.steps[0]
    assert step.step_type == "if_else"
    assert step.config["condition"] == "amount > 100"
    assert step.config["then_steps"][0]["step_type"] == "log_message"
    assert step.config["else_steps"][0]["config"]["message"] == "small"


@pytest.mark.asyncio
async def test_compiled_canvas_equivalent_to_hand_coded_execution() -> None:
    """AC: no-code compile executes identically to hand-coded Workflow."""
    canvas = _linear_canvas()
    compiled = compile_canvas(canvas, status="active")

    hand = Workflow(
        id="hand-1",
        tenant_id="t1",
        name="Lead follow-up",
        status="active",
        trigger_type="manual",
        steps=[
            WorkflowStep(
                id="h1",
                workflow_id="hand-1",
                step_type="set_variable",
                config={"name": "stage", "value": "contacted"},
                order=0,
            ),
            WorkflowStep(
                id="h2",
                workflow_id="hand-1",
                step_type="log_message",
                config={"message": "done", "level": "info"},
                order=1,
            ),
        ],
    )

    repo = InMemoryWorkflowRepository()
    engine = WorkflowEngine(repo)
    ctx_a: dict = {}
    ctx_b: dict = {}
    ex_compiled = await engine.execute(compiled, ctx_a)
    ex_hand = await engine.execute(hand, ctx_b)

    assert ex_compiled.status == "completed"
    assert ex_hand.status == "completed"
    assert ctx_a.get("stage") == ctx_b.get("stage") == "contacted"
    assert len(ex_compiled.step_results) == len(ex_hand.step_results) == 2
    assert [s.step_type for s in ex_compiled.step_results] == [
        s.step_type for s in ex_hand.step_results
    ]
    assert [s.status for s in ex_compiled.step_results] == [s.status for s in ex_hand.step_results]


@pytest.mark.asyncio
async def test_canvas_store_tenant_isolation_and_compile() -> None:
    store = MemWorkflowCanvasStore()
    a = store.save(_linear_canvas("tenant-a"))
    b = store.save(
        WorkflowCanvas(
            id="",
            tenant_id="tenant-b",
            name="Other",
            nodes=[
                CanvasNode(
                    id="x",
                    kind="action",
                    step_type="log_message",
                    config={"message": "b"},
                )
            ],
        )
    )
    assert len(store.list_for_tenant(tenant_id="tenant-a")) == 1
    assert store.get(a.id, tenant_id="tenant-b") is None
    _canvas, wf, public = store.compile(a.id, tenant_id="tenant-a")
    assert wf.tenant_id == "tenant-a"
    assert public["steps"][0]["step_type"] == "set_variable"
    assert b.tenant_id == "tenant-b"
