"""PostgreSQL repository for Workflow domain."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .db_models import WorkflowExecutionModel, WorkflowModel
from .models import Workflow, WorkflowExecution, WorkflowExecutionStep, WorkflowStep
from .repository import WorkflowRepository


class PostgresWorkflowRepository(WorkflowRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, workflow: Workflow) -> Workflow:
        model = WorkflowModel(
            id=workflow.id,
            tenant_id=workflow.tenant_id,
            name=workflow.name,
            description=workflow.description,
            trigger_type=workflow.trigger_type,
            status=workflow.status,
            steps=[
                {
                    "id": s.id,
                    "workflow_id": s.workflow_id,
                    "step_type": s.step_type,
                    "config": s.config,
                    "order": s.order,
                    "condition": s.condition,
                }
                for s in workflow.steps
            ],
        )
        self.session.add(model)
        await self.session.flush()
        return workflow

    async def get(self, workflow_id: str, tenant_id: str) -> Optional[Workflow]:
        stmt = select(WorkflowModel).where(
            WorkflowModel.id == workflow_id,
            WorkflowModel.tenant_id == tenant_id,
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._wf_to_domain(model) if model else None

    async def list(self, tenant_id: str) -> list[Workflow]:
        stmt = (
            select(WorkflowModel)
            .where(WorkflowModel.tenant_id == tenant_id)
            .order_by(WorkflowModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return [self._wf_to_domain(r) for r in result.scalars().all()]

    async def update(self, workflow: Workflow) -> Workflow:
        stmt = select(WorkflowModel).where(WorkflowModel.id == workflow.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            raise ValueError(f"Workflow {workflow.id} not found")
        model.name = workflow.name
        model.description = workflow.description
        model.trigger_type = workflow.trigger_type
        model.status = workflow.status
        model.steps = [
            {
                "id": s.id,
                "workflow_id": s.workflow_id,
                "step_type": s.step_type,
                "config": s.config,
                "order": s.order,
                "condition": s.condition,
            }
            for s in workflow.steps
        ]
        model.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        return workflow

    async def delete(self, workflow_id: str, tenant_id: str) -> None:
        from sqlalchemy import delete as sa_delete
        stmt = sa_delete(WorkflowModel).where(
            WorkflowModel.id == workflow_id,
            WorkflowModel.tenant_id == tenant_id,
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def create_execution(self, execution: WorkflowExecution) -> WorkflowExecution:
        model = WorkflowExecutionModel(
            id=execution.id,
            workflow_id=execution.workflow_id,
            tenant_id=execution.tenant_id,
            trigger_event=execution.trigger_event,
            status=execution.status,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            error=execution.error,
            step_results=[
                {
                    "id": sr.id,
                    "execution_id": sr.execution_id,
                    "step_id": sr.step_id,
                    "step_type": sr.step_type,
                    "status": sr.status,
                    "result": sr.result,
                    "started_at": sr.started_at.isoformat() if sr.started_at else None,
                    "completed_at": sr.completed_at.isoformat() if sr.completed_at else None,
                    "error": sr.error,
                }
                for sr in execution.step_results
            ],
        )
        self.session.add(model)
        await self.session.flush()
        return execution

    async def update_execution(self, execution: WorkflowExecution) -> WorkflowExecution:
        stmt = select(WorkflowExecutionModel).where(WorkflowExecutionModel.id == execution.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            raise ValueError(f"Execution {execution.id} not found")
        model.status = execution.status
        model.completed_at = execution.completed_at
        model.error = execution.error
        model.step_results = [
            {
                "id": sr.id,
                "execution_id": sr.execution_id,
                "step_id": sr.step_id,
                "step_type": sr.step_type,
                "status": sr.status,
                "result": sr.result,
                "started_at": sr.started_at.isoformat() if sr.started_at else None,
                "completed_at": sr.completed_at.isoformat() if sr.completed_at else None,
                "error": sr.error,
            }
            for sr in execution.step_results
        ]
        await self.session.flush()
        return execution

    async def get_execution(self, execution_id: str, tenant_id: str) -> Optional[WorkflowExecution]:
        stmt = select(WorkflowExecutionModel).where(
            WorkflowExecutionModel.id == execution_id,
            WorkflowExecutionModel.tenant_id == tenant_id,
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._exec_to_domain(model) if model else None

    async def list_executions(self, tenant_id: str, workflow_id: str | None = None) -> list[WorkflowExecution]:
        stmt = select(WorkflowExecutionModel).where(WorkflowExecutionModel.tenant_id == tenant_id)
        if workflow_id:
            stmt = stmt.where(WorkflowExecutionModel.workflow_id == workflow_id)
        stmt = stmt.order_by(WorkflowExecutionModel.started_at.desc())
        result = await self.session.execute(stmt)
        return [self._exec_to_domain(r) for r in result.scalars().all()]

    def _wf_to_domain(self, model: WorkflowModel) -> Workflow:
        steps = [
            WorkflowStep(
                id=s.get("id", ""),
                workflow_id=s.get("workflow_id", model.id),
                step_type=s.get("step_type", ""),
                config=s.get("config", {}),
                order=s.get("order", 0),
                condition=s.get("condition"),
            )
            for s in (model.steps or [])
        ]
        return Workflow(
            id=model.id,
            tenant_id=model.tenant_id,
            name=model.name,
            description=model.description,
            trigger_type=model.trigger_type,
            status=model.status,
            steps=steps,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _exec_to_domain(self, model: WorkflowExecutionModel) -> WorkflowExecution:
        step_results = [
            WorkflowExecutionStep(
                id=sr.get("id", ""),
                execution_id=sr.get("execution_id", model.id),
                step_id=sr.get("step_id", ""),
                step_type=sr.get("step_type", ""),
                status=sr.get("status", "pending"),
                result=sr.get("result"),
                started_at=datetime.fromisoformat(sr["started_at"]) if sr.get("started_at") else None,
                completed_at=datetime.fromisoformat(sr["completed_at"]) if sr.get("completed_at") else None,
                error=sr.get("error"),
            )
            for sr in (model.step_results or [])
        ]
        return WorkflowExecution(
            id=model.id,
            workflow_id=model.workflow_id,
            tenant_id=model.tenant_id,
            trigger_event=model.trigger_event,
            status=model.status,
            started_at=model.started_at,
            completed_at=model.completed_at,
            error=model.error,
            step_results=step_results,
        )
