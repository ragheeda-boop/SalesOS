"""PostgreSQL repository for Workflow domain."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .db_models import (
    JobExecutionModel,
    ScheduledJobModel,
    WebhookEndpointModel,
    WorkflowExecutionModel,
    WorkflowModel,
)
from .models import (
    JobExecution,
    ScheduledJob,
    WebhookEndpoint,
    Workflow,
    WorkflowExecution,
    WorkflowExecutionStep,
    WorkflowStep,
    WorkflowTemplate,
)
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
            steps=self._serialize_steps(workflow.steps),
            timeout_seconds=workflow.timeout_seconds,
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
        model.steps = self._serialize_steps(workflow.steps)
        model.timeout_seconds = workflow.timeout_seconds
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
            step_results=[self._serialize_exec_step(sr) for sr in execution.step_results],
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
        model.step_results = [self._serialize_exec_step(sr) for sr in execution.step_results]
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

    async def cancel_execution(self, execution_id: str, tenant_id: str) -> Optional[WorkflowExecution]:
        stmt = select(WorkflowExecutionModel).where(
            WorkflowExecutionModel.id == execution_id,
            WorkflowExecutionModel.tenant_id == tenant_id,
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model or model.status != "running":
            return None
        model.status = "cancelled"
        model.completed_at = datetime.now(timezone.utc)
        model.error = "Cancelled by user"
        await self.session.flush()
        return self._exec_to_domain(model)

    async def get_workflow_stats(self, tenant_id: str) -> dict:
        from sqlalchemy import case
        wf_count = await self.session.scalar(
            select(func.count()).select_from(WorkflowModel).where(WorkflowModel.tenant_id == tenant_id)
        ) or 0
        status_rows = await self.session.execute(
            select(WorkflowModel.status, func.count(WorkflowModel.id))
            .where(WorkflowModel.tenant_id == tenant_id)
            .group_by(WorkflowModel.status)
        )
        by_status = {row[0]: row[1] for row in status_rows.fetchall()}
        trigger_rows = await self.session.execute(
            select(WorkflowModel.trigger_type, func.count(WorkflowModel.id))
            .where(WorkflowModel.tenant_id == tenant_id)
            .group_by(WorkflowModel.trigger_type)
        )
        by_trigger = {row[0]: row[1] for row in trigger_rows.fetchall()}
        total_execs = await self.session.scalar(
            select(func.count()).select_from(WorkflowExecutionModel).where(WorkflowExecutionModel.tenant_id == tenant_id)
        ) or 0
        completed_execs = await self.session.scalar(
            select(func.count()).select_from(WorkflowExecutionModel).where(
                WorkflowExecutionModel.tenant_id == tenant_id,
                WorkflowExecutionModel.status == "completed",
            )
        ) or 0
        failed_execs = await self.session.scalar(
            select(func.count()).select_from(WorkflowExecutionModel).where(
                WorkflowExecutionModel.tenant_id == tenant_id,
                WorkflowExecutionModel.status == "failed",
            )
        ) or 0
        return {
            "total_workflows": wf_count,
            "by_status": by_status,
            "by_trigger": by_trigger,
            "total_executions": total_execs,
            "completed_executions": completed_execs,
            "failed_executions": failed_execs,
        }

    async def get_execution_stats(self, tenant_id: str) -> dict:
        total = await self.session.scalar(
            select(func.count()).select_from(WorkflowExecutionModel).where(WorkflowExecutionModel.tenant_id == tenant_id)
        ) or 0
        status_rows = await self.session.execute(
            select(WorkflowExecutionModel.status, func.count(WorkflowExecutionModel.id))
            .where(WorkflowExecutionModel.tenant_id == tenant_id)
            .group_by(WorkflowExecutionModel.status)
        )
        by_status = {row[0]: row[1] for row in status_rows.fetchall()}
        recent_stmt = (
            select(WorkflowExecutionModel)
            .where(WorkflowExecutionModel.tenant_id == tenant_id)
            .order_by(WorkflowExecutionModel.started_at.desc())
            .limit(20)
        )
        recent_result = await self.session.execute(recent_stmt)
        recent = [
            {
                "id": r.id,
                "workflow_id": r.workflow_id,
                "status": r.status,
                "started_at": r.started_at.isoformat(),
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                "error": r.error,
            }
            for r in recent_result.scalars().all()
        ]
        return {"total_executions": total, "by_status": by_status, "recent": recent}

    # ── Webhook endpoints ──────────────────────────────────────────────────

    async def create_webhook(self, endpoint: WebhookEndpoint) -> WebhookEndpoint:
        model = WebhookEndpointModel(
            id=endpoint.id,
            tenant_id=endpoint.tenant_id,
            url=endpoint.url,
            name=endpoint.name,
            auth_type=endpoint.auth_type,
            auth_config=endpoint.auth_config,
            secret=endpoint.secret,
            status=endpoint.status,
        )
        self.session.add(model)
        await self.session.flush()
        return endpoint

    async def get_webhook(self, endpoint_id: str, tenant_id: str) -> Optional[WebhookEndpoint]:
        stmt = select(WebhookEndpointModel).where(
            WebhookEndpointModel.id == endpoint_id,
            WebhookEndpointModel.tenant_id == tenant_id,
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._webhook_to_domain(model) if model else None

    async def list_webhooks(self, tenant_id: str) -> list[WebhookEndpoint]:
        stmt = select(WebhookEndpointModel).where(WebhookEndpointModel.tenant_id == tenant_id)
        result = await self.session.execute(stmt)
        return [self._webhook_to_domain(r) for r in result.scalars().all()]

    async def update_webhook(self, endpoint: WebhookEndpoint) -> WebhookEndpoint:
        stmt = select(WebhookEndpointModel).where(WebhookEndpointModel.id == endpoint.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            raise ValueError(f"Webhook {endpoint.id} not found")
        model.url = endpoint.url
        model.name = endpoint.name
        model.auth_type = endpoint.auth_type
        model.auth_config = endpoint.auth_config
        model.secret = endpoint.secret
        model.status = endpoint.status
        model.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        return endpoint

    async def delete_webhook(self, endpoint_id: str, tenant_id: str) -> None:
        from sqlalchemy import delete as sa_delete
        stmt = sa_delete(WebhookEndpointModel).where(
            WebhookEndpointModel.id == endpoint_id,
            WebhookEndpointModel.tenant_id == tenant_id,
        )
        await self.session.execute(stmt)
        await self.session.flush()

    # ── Scheduled jobs ─────────────────────────────────────────────────────

    async def create_job(self, job: ScheduledJob) -> ScheduledJob:
        model = ScheduledJobModel(
            id=job.id,
            tenant_id=job.tenant_id,
            job_type=job.job_type,
            name=job.name,
            config=job.config,
            schedule=job.schedule,
            status=job.status,
            last_run_at=job.last_run_at,
            next_run_at=job.next_run_at,
            run_count=job.run_count,
            max_retries=job.max_retries,
            retry_count=job.retry_count,
            payload=job.payload,
        )
        self.session.add(model)
        await self.session.flush()
        return job

    async def get_job(self, job_id: str, tenant_id: str) -> Optional[ScheduledJob]:
        stmt = select(ScheduledJobModel).where(
            ScheduledJobModel.id == job_id,
            ScheduledJobModel.tenant_id == tenant_id,
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._job_to_domain(model) if model else None

    async def list_jobs(self, tenant_id: str) -> list[ScheduledJob]:
        stmt = select(ScheduledJobModel).where(ScheduledJobModel.tenant_id == tenant_id)
        result = await self.session.execute(stmt)
        return [self._job_to_domain(r) for r in result.scalars().all()]

    async def update_job(self, job: ScheduledJob) -> ScheduledJob:
        stmt = select(ScheduledJobModel).where(ScheduledJobModel.id == job.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            raise ValueError(f"Job {job.id} not found")
        model.job_type = job.job_type
        model.name = job.name
        model.config = job.config
        model.schedule = job.schedule
        model.status = job.status
        model.last_run_at = job.last_run_at
        model.next_run_at = job.next_run_at
        model.run_count = job.run_count
        model.max_retries = job.max_retries
        model.retry_count = job.retry_count
        model.payload = job.payload
        model.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        return job

    async def delete_job(self, job_id: str, tenant_id: str) -> None:
        from sqlalchemy import delete as sa_delete
        stmt = sa_delete(ScheduledJobModel).where(
            ScheduledJobModel.id == job_id,
            ScheduledJobModel.tenant_id == tenant_id,
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def list_due_jobs(self, now: datetime | None = None) -> list[ScheduledJob]:
        now = now or datetime.now(timezone.utc)
        stmt = select(ScheduledJobModel).where(
            ScheduledJobModel.status == "active",
            ScheduledJobModel.next_run_at <= now,
        )
        result = await self.session.execute(stmt)
        return [self._job_to_domain(r) for r in result.scalars().all()]

    async def create_job_execution(self, execution: JobExecution) -> JobExecution:
        model = JobExecutionModel(
            id=execution.id,
            job_id=execution.job_id,
            tenant_id=execution.tenant_id,
            status=execution.status,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            result=execution.result,
            error=execution.error,
        )
        self.session.add(model)
        await self.session.flush()
        return execution

    async def update_job_execution(self, execution: JobExecution) -> JobExecution:
        stmt = select(JobExecutionModel).where(JobExecutionModel.id == execution.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            raise ValueError(f"JobExecution {execution.id} not found")
        model.status = execution.status
        model.started_at = execution.started_at
        model.completed_at = execution.completed_at
        model.result = execution.result
        model.error = execution.error
        await self.session.flush()
        return execution

    async def get_job_execution(self, execution_id: str) -> Optional[JobExecution]:
        stmt = select(JobExecutionModel).where(JobExecutionModel.id == execution_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._job_exec_to_domain(model) if model else None

    async def list_job_executions(self, job_id: str) -> list[JobExecution]:
        stmt = select(JobExecutionModel).where(JobExecutionModel.job_id == job_id)
        result = await self.session.execute(stmt)
        return [self._job_exec_to_domain(r) for r in result.scalars().all()]

    # ── Workflow templates ─────────────────────────────────────────────────

    async def list_templates(self) -> list[WorkflowTemplate]:
        from .templates import WORKFLOW_TEMPLATE_REGISTRY
        return list(WORKFLOW_TEMPLATE_REGISTRY.values())

    async def get_template(self, template_id: str) -> Optional[WorkflowTemplate]:
        from .templates import WORKFLOW_TEMPLATE_REGISTRY
        return WORKFLOW_TEMPLATE_REGISTRY.get(template_id)

    # ── Helpers ────────────────────────────────────────────────────────────

    @staticmethod
    def _serialize_steps(steps: list[WorkflowStep]) -> list[dict]:
        return [
            {
                "id": s.id,
                "workflow_id": s.workflow_id,
                "step_type": s.step_type,
                "config": s.config,
                "order": s.order,
                "condition": s.condition,
                "timeout_seconds": s.timeout_seconds,
                "on_failure": s.on_failure,
            }
            for s in steps
        ]

    @staticmethod
    def _serialize_exec_step(sr: WorkflowExecutionStep) -> dict:
        return {
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

    def _wf_to_domain(self, model: WorkflowModel) -> Workflow:
        steps = [
            WorkflowStep(
                id=s.get("id", ""),
                workflow_id=s.get("workflow_id", model.id),
                step_type=s.get("step_type", ""),
                config=s.get("config", {}),
                order=s.get("order", 0),
                condition=s.get("condition"),
                timeout_seconds=s.get("timeout_seconds"),
                on_failure=s.get("on_failure", "fail_workflow"),
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
            timeout_seconds=model.timeout_seconds,
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

    def _webhook_to_domain(self, model: WebhookEndpointModel) -> WebhookEndpoint:
        return WebhookEndpoint(
            id=model.id,
            tenant_id=model.tenant_id,
            url=model.url,
            name=model.name,
            auth_type=model.auth_type,
            auth_config=model.auth_config or {},
            secret=model.secret,
            status=model.status,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _job_to_domain(self, model: ScheduledJobModel) -> ScheduledJob:
        return ScheduledJob(
            id=model.id,
            tenant_id=model.tenant_id,
            job_type=model.job_type,
            name=model.name,
            config=model.config or {},
            schedule=model.schedule,
            status=model.status,
            last_run_at=model.last_run_at,
            next_run_at=model.next_run_at,
            run_count=model.run_count,
            max_retries=model.max_retries,
            retry_count=model.retry_count,
            payload=model.payload or {},
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _job_exec_to_domain(self, model: JobExecutionModel) -> JobExecution:
        return JobExecution(
            id=model.id,
            job_id=model.job_id,
            tenant_id=model.tenant_id,
            status=model.status,
            started_at=model.started_at,
            completed_at=model.completed_at,
            result=model.result,
            error=model.error,
        )
