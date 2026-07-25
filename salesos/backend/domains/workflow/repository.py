"""Workflow repository — abstract and in-memory implementations."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone

from domains.workflow.models import (
    JobExecution,
    ScheduledJob,
    WebhookEndpoint,
    Workflow,
    WorkflowExecution,
    WorkflowTemplate,
)


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

    @abstractmethod
    async def cancel_execution(self, execution_id: str, tenant_id: str) -> WorkflowExecution | None:
        ...

    # ── Analytics ──────────────────────────────────────────────────────────

    @abstractmethod
    async def get_workflow_stats(self, tenant_id: str) -> dict:
        ...

    @abstractmethod
    async def get_execution_stats(self, tenant_id: str) -> dict:
        ...

    # ── Webhook endpoints ──────────────────────────────────────────────────

    @abstractmethod
    async def create_webhook(self, endpoint: WebhookEndpoint) -> WebhookEndpoint:
        ...

    @abstractmethod
    async def get_webhook(self, endpoint_id: str, tenant_id: str) -> WebhookEndpoint | None:
        ...

    @abstractmethod
    async def list_webhooks(self, tenant_id: str) -> list[WebhookEndpoint]:
        ...

    @abstractmethod
    async def update_webhook(self, endpoint: WebhookEndpoint) -> WebhookEndpoint:
        ...

    @abstractmethod
    async def delete_webhook(self, endpoint_id: str, tenant_id: str) -> None:
        ...

    # ── Scheduled jobs ─────────────────────────────────────────────────────

    @abstractmethod
    async def create_job(self, job: ScheduledJob) -> ScheduledJob:
        ...

    @abstractmethod
    async def get_job(self, job_id: str, tenant_id: str) -> ScheduledJob | None:
        ...

    @abstractmethod
    async def list_jobs(self, tenant_id: str) -> list[ScheduledJob]:
        ...

    @abstractmethod
    async def update_job(self, job: ScheduledJob) -> ScheduledJob:
        ...

    @abstractmethod
    async def delete_job(self, job_id: str, tenant_id: str) -> None:
        ...

    @abstractmethod
    async def list_due_jobs(self, now: datetime | None = None) -> list[ScheduledJob]:
        ...

    @abstractmethod
    async def create_job_execution(self, execution: JobExecution) -> JobExecution:
        ...

    @abstractmethod
    async def update_job_execution(self, execution: JobExecution) -> JobExecution:
        ...

    @abstractmethod
    async def get_job_execution(self, execution_id: str) -> JobExecution | None:
        ...

    @abstractmethod
    async def list_job_executions(self, job_id: str) -> list[JobExecution]:
        ...

    # ── Workflow templates ─────────────────────────────────────────────────

    @abstractmethod
    async def list_templates(self) -> list[WorkflowTemplate]:
        ...

    @abstractmethod
    async def get_template(self, template_id: str) -> WorkflowTemplate | None:
        ...


class InMemoryWorkflowRepository(WorkflowRepository):
    def __init__(self) -> None:
        self._workflows: dict[str, Workflow] = {}
        self._executions: dict[str, WorkflowExecution] = {}
        self._webhooks: dict[str, WebhookEndpoint] = {}
        self._jobs: dict[str, ScheduledJob] = {}
        self._job_executions: dict[str, JobExecution] = {}
        self._templates: dict[str, WorkflowTemplate] = {}

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

    async def cancel_execution(self, execution_id: str, tenant_id: str) -> WorkflowExecution | None:
        ex = self._executions.get(execution_id)
        if ex and ex.tenant_id == tenant_id and ex.status == "running":
            ex.status = "cancelled"
            ex.completed_at = datetime.now(timezone.utc)
            ex.error = "Cancelled by user"
            return ex
        return None

    async def get_workflow_stats(self, tenant_id: str) -> dict:
        wfs = [w for w in self._workflows.values() if w.tenant_id == tenant_id]
        statuses: dict[str, int] = {}
        triggers: dict[str, int] = {}
        for w in wfs:
            statuses[w.status] = statuses.get(w.status, 0) + 1
            triggers[w.trigger_type] = triggers.get(w.trigger_type, 0) + 1
        total_executions = sum(1 for e in self._executions.values() if e.tenant_id == tenant_id)
        completed_execs = sum(1 for e in self._executions.values() if e.tenant_id == tenant_id and e.status == "completed")
        failed_execs = sum(1 for e in self._executions.values() if e.tenant_id == tenant_id and e.status == "failed")
        return {
            "total_workflows": len(wfs),
            "by_status": statuses,
            "by_trigger": triggers,
            "total_executions": total_executions,
            "completed_executions": completed_execs,
            "failed_executions": failed_execs,
        }

    async def get_execution_stats(self, tenant_id: str) -> dict:
        execs = [e for e in self._executions.values() if e.tenant_id == tenant_id]
        statuses: dict[str, int] = {}
        for e in execs:
            statuses[e.status] = statuses.get(e.status, 0) + 1
        recent = sorted(execs, key=lambda x: x.started_at, reverse=True)[:20]
        return {
            "total_executions": len(execs),
            "by_status": statuses,
            "recent": [
                {
                    "id": e.id,
                    "workflow_id": e.workflow_id,
                    "status": e.status,
                    "started_at": e.started_at.isoformat(),
                    "completed_at": e.completed_at.isoformat() if e.completed_at else None,
                    "error": e.error,
                }
                for e in recent
            ],
        }

    # ── Webhook endpoints ──────────────────────────────────────────────────

    async def create_webhook(self, endpoint: WebhookEndpoint) -> WebhookEndpoint:
        self._webhooks[endpoint.id] = endpoint
        return endpoint

    async def get_webhook(self, endpoint_id: str, tenant_id: str) -> WebhookEndpoint | None:
        ep = self._webhooks.get(endpoint_id)
        if ep and ep.tenant_id == tenant_id:
            return ep
        return None

    async def list_webhooks(self, tenant_id: str) -> list[WebhookEndpoint]:
        return [w for w in self._webhooks.values() if w.tenant_id == tenant_id]

    async def update_webhook(self, endpoint: WebhookEndpoint) -> WebhookEndpoint:
        endpoint.updated_at = datetime.now(timezone.utc)
        self._webhooks[endpoint.id] = endpoint
        return endpoint

    async def delete_webhook(self, endpoint_id: str, tenant_id: str) -> None:
        ep = self._webhooks.get(endpoint_id)
        if ep and ep.tenant_id == tenant_id:
            del self._webhooks[endpoint_id]

    # ── Scheduled jobs ─────────────────────────────────────────────────────

    async def create_job(self, job: ScheduledJob) -> ScheduledJob:
        self._jobs[job.id] = job
        return job

    async def get_job(self, job_id: str, tenant_id: str) -> ScheduledJob | None:
        job = self._jobs.get(job_id)
        if job and job.tenant_id == tenant_id:
            return job
        return None

    async def list_jobs(self, tenant_id: str) -> list[ScheduledJob]:
        return [j for j in self._jobs.values() if j.tenant_id == tenant_id]

    async def update_job(self, job: ScheduledJob) -> ScheduledJob:
        job.updated_at = datetime.now(timezone.utc)
        self._jobs[job.id] = job
        return job

    async def delete_job(self, job_id: str, tenant_id: str) -> None:
        job = self._jobs.get(job_id)
        if job and job.tenant_id == tenant_id:
            del self._jobs[job_id]

    async def list_due_jobs(self, now: datetime | None = None) -> list[ScheduledJob]:
        now = now or datetime.now(timezone.utc)
        due = []
        for job in self._jobs.values():
            if job.status != "active":
                continue
            if job.next_run_at and job.next_run_at <= now:
                due.append(job)
        return due

    async def create_job_execution(self, execution: JobExecution) -> JobExecution:
        self._job_executions[execution.id] = execution
        return execution

    async def update_job_execution(self, execution: JobExecution) -> JobExecution:
        self._job_executions[execution.id] = execution
        return execution

    async def get_job_execution(self, execution_id: str) -> JobExecution | None:
        return self._job_executions.get(execution_id)

    async def list_job_executions(self, job_id: str) -> list[JobExecution]:
        results = [e for e in self._job_executions.values() if e.job_id == job_id]
        return sorted(results, key=lambda x: x.started_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)

    # ── Workflow templates ─────────────────────────────────────────────────

    async def list_templates(self) -> list[WorkflowTemplate]:
        from .templates import WORKFLOW_TEMPLATE_REGISTRY
        return list(WORKFLOW_TEMPLATE_REGISTRY.values())

    async def get_template(self, template_id: str) -> WorkflowTemplate | None:
        from .templates import WORKFLOW_TEMPLATE_REGISTRY
        # Check by template ID field first, then by dict key
        for t in WORKFLOW_TEMPLATE_REGISTRY.values():
            if t.id == template_id:
                return t
        return WORKFLOW_TEMPLATE_REGISTRY.get(template_id)
