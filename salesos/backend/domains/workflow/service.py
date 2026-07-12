"""WorkflowService — CRUD + execute + validation for workflows."""
from __future__ import annotations

import uuid
import logging
from datetime import datetime, timezone
from typing import Any

from domains.workflow.models import Workflow, WorkflowStep, WorkflowExecution
from domains.workflow.repository import WorkflowRepository
from domains.workflow.engine import WorkflowEngine

logger = logging.getLogger(__name__)


class WorkflowValidationError(ValueError):
    ...


class WorkflowService:
    def __init__(
        self,
        repository: WorkflowRepository,
        engine: WorkflowEngine | None = None,
        decision_platform: Any = None,
    ) -> None:
        self._repo = repository
        self._engine = engine or WorkflowEngine(repository)
        self._decision_platform = decision_platform

    def _validate_workflow(self, workflow: Workflow) -> None:
        if not workflow.name.strip():
            raise WorkflowValidationError("Workflow name is required")
        if workflow.trigger_type not in ("event", "scheduled", "manual"):
            raise WorkflowValidationError(f"Invalid trigger_type: {workflow.trigger_type}")
        if workflow.status not in ("active", "inactive", "draft"):
            raise WorkflowValidationError(f"Invalid status: {workflow.status}")
        for step in workflow.steps:
            if step.step_type not in ("send_email", "update_crm", "create_task", "webhook", "nba_recommend"):
                raise WorkflowValidationError(f"Invalid step_type: {step.step_type}")
            if step.order < 0:
                raise WorkflowValidationError(f"Step order must be >= 0, got {step.order}")

    async def create(
        self,
        tenant_id: str,
        name: str,
        description: str = "",
        trigger_type: str = "manual",
        status: str = "draft",
        steps: list[dict[str, Any]] | None = None,
        template: str | None = None,
    ) -> Workflow:
        wf = Workflow(
            id=uuid.uuid4().hex[:12],
            tenant_id=tenant_id,
            name=name,
            description=description,
            trigger_type=trigger_type,
            status=status,
        )
        if template:
            from domains.workflow.templates import WORKFLOW_TEMPLATES
            tmpl = WORKFLOW_TEMPLATES.get(template)
            if not tmpl:
                raise WorkflowValidationError(f"Template '{template}' not found")
            for s in tmpl.steps:
                wf.steps.append(WorkflowStep(
                    id=uuid.uuid4().hex[:12],
                    workflow_id=wf.id,
                    step_type=s.step_type,
                    config=s.config,
                    order=s.order,
                    condition=s.condition,
                ))
        elif steps:
            for i, s in enumerate(steps):
                wf.steps.append(WorkflowStep(
                    id=uuid.uuid4().hex[:12],
                    workflow_id=wf.id,
                    step_type=s["step_type"],
                    config=s.get("config", {}),
                    order=s.get("order", i),
                    condition=s.get("condition"),
                ))
        for s in wf.steps:
            s.workflow_id = wf.id
        self._validate_workflow(wf)
        return await self._repo.create(wf)

    async def get(self, workflow_id: str, tenant_id: str) -> Workflow | None:
        return await self._repo.get(workflow_id, tenant_id)

    async def list(self, tenant_id: str) -> list[Workflow]:
        return await self._repo.list(tenant_id)

    async def update(
        self,
        workflow_id: str,
        tenant_id: str,
        name: str | None = None,
        description: str | None = None,
        trigger_type: str | None = None,
        status: str | None = None,
        steps: list[dict[str, Any]] | None = None,
    ) -> Workflow:
        wf = await self._repo.get(workflow_id, tenant_id)
        if not wf:
            raise WorkflowValidationError(f"Workflow {workflow_id} not found")
        if name is not None:
            wf.name = name
        if description is not None:
            wf.description = description
        if trigger_type is not None:
            wf.trigger_type = trigger_type
        if status is not None:
            wf.status = status
        if steps is not None:
            wf.steps = [
                WorkflowStep(
                    id=uuid.uuid4().hex[:12],
                    workflow_id=wf.id,
                    step_type=s["step_type"],
                    config=s.get("config", {}),
                    order=s.get("order", i),
                    condition=s.get("condition"),
                )
                for i, s in enumerate(steps)
            ]
        wf.updated_at = datetime.now(timezone.utc)
        self._validate_workflow(wf)
        return await self._repo.update(wf)

    async def delete(self, workflow_id: str, tenant_id: str) -> None:
        wf = await self._repo.get(workflow_id, tenant_id)
        if not wf:
            raise WorkflowValidationError(f"Workflow {workflow_id} not found")
        await self._repo.delete(workflow_id, tenant_id)

    async def execute(self, workflow_id: str, tenant_id: str, context: dict[str, Any] | None = None) -> WorkflowExecution:
        wf = await self._repo.get(workflow_id, tenant_id)
        if not wf:
            raise WorkflowValidationError(f"Workflow {workflow_id} not found")
        if wf.status != "active":
            raise WorkflowValidationError(f"Workflow is '{wf.status}', must be 'active' to execute")
        context = context or {}

        if self._decision_platform and wf.trigger_type == "event":
            try:
                decision = await self._decision_platform.evaluate(wf.id, context)
                if decision and decision.get("block"):
                    import uuid
                    execution = WorkflowExecution(
                        id=f"exec_{wf.id}_{uuid.uuid4().hex[:8]}",
                        workflow_id=wf.id,
                        tenant_id=tenant_id,
                        trigger_event=context.get("trigger", "manual"),
                        status="skipped",
                        completed_at=datetime.now(timezone.utc),
                        error=f"Blocked by Decision Platform: {decision.get('reason', '')}",
                    )
                    await self._repo.create_execution(execution)
                    return execution
            except Exception as exc:
                logger.warning("Decision Platform evaluation failed (non-blocking): %s", exc)

        return await self._engine.execute(wf, context)

    async def list_executions(self, tenant_id: str, workflow_id: str | None = None) -> list[WorkflowExecution]:
        return await self._repo.list_executions(tenant_id, workflow_id)

    async def get_execution(self, execution_id: str, tenant_id: str) -> WorkflowExecution | None:
        return await self._repo.get_execution(execution_id, tenant_id)
