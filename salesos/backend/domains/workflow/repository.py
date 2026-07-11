"""Workflow repository — abstract and in-memory implementations."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone

from domains.workflow.models import Workflow, WorkflowExecution


class WorkflowRepository(ABC):
    @abstractmethod
    async def create(self, workflow: Workflow) -> Workflow:
        ...

    @abstractmethod
    async def get(self, workflow_id: str, tenant_id: str) -> Workflow | None:
        ...

    @abstractmethod
    async def list(self, tenant_id: str) -> list[Workflow]:
        ...

    @abstractmethod
    async def update(self, workflow: Workflow) -> Workflow:
        ...

    @abstractmethod
    async def delete(self, workflow_id: str, tenant_id: str) -> None:
        ...

    @abstractmethod
    async def create_execution(self, execution: WorkflowExecution) -> WorkflowExecution:
        ...

    @abstractmethod
    async def update_execution(self, execution: WorkflowExecution) -> WorkflowExecution:
        ...

    @abstractmethod
    async def get_execution(self, execution_id: str, tenant_id: str) -> WorkflowExecution | None:
        ...

    @abstractmethod
    async def list_executions(self, tenant_id: str, workflow_id: str | None = None) -> list[WorkflowExecution]:
        ...


class InMemoryWorkflowRepository(WorkflowRepository):
    def __init__(self) -> None:
        self._workflows: dict[str, Workflow] = {}
        self._executions: dict[str, WorkflowExecution] = {}

    async def create(self, workflow: Workflow) -> Workflow:
        self._workflows[workflow.id] = workflow
        return workflow

    async def get(self, workflow_id: str, tenant_id: str) -> Workflow | None:
        wf = self._workflows.get(workflow_id)
        if wf and wf.tenant_id == tenant_id:
            return wf
        return None

    async def list(self, tenant_id: str) -> list[Workflow]:
        return [w for w in self._workflows.values() if w.tenant_id == tenant_id]

    async def update(self, workflow: Workflow) -> Workflow:
        workflow.updated_at = datetime.now(timezone.utc)
        self._workflows[workflow.id] = workflow
        return workflow

    async def delete(self, workflow_id: str, tenant_id: str) -> None:
        wf = self._workflows.get(workflow_id)
        if wf and wf.tenant_id == tenant_id:
            del self._workflows[workflow_id]

    async def create_execution(self, execution: WorkflowExecution) -> WorkflowExecution:
        self._executions[execution.id] = execution
        return execution

    async def update_execution(self, execution: WorkflowExecution) -> WorkflowExecution:
        self._executions[execution.id] = execution
        return execution

    async def get_execution(self, execution_id: str, tenant_id: str) -> WorkflowExecution | None:
        ex = self._executions.get(execution_id)
        if ex and ex.tenant_id == tenant_id:
            return ex
        return None

    async def list_executions(self, tenant_id: str, workflow_id: str | None = None) -> list[WorkflowExecution]:
        results = [ex for ex in self._executions.values() if ex.tenant_id == tenant_id]
        if workflow_id:
            results = [ex for ex in results if ex.workflow_id == workflow_id]
        return sorted(results, key=lambda x: x.started_at, reverse=True)
