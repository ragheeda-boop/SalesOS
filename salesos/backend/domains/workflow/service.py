"""WorkflowService — CRUD + execute + validation for workflows, webhooks, jobs."""
from __future__ import annotations

import uuid
import logging
from datetime import datetime, timezone
from typing import Any

from domains.workflow.models import (
    JobExecution,
    ScheduledJob,
    WebhookEndpoint,
    Workflow,
    WorkflowExecution,
    WorkflowStep,
    WorkflowTemplate,
)
from domains.workflow.repository import WorkflowRepository
from domains.workflow.engine import WorkflowEngine

logger = logging.getLogger(__name__)

VALID_STEP_TYPES = (
    "send_email", "update_crm", "create_task", "webhook", "nba_recommend",
    "if_else", "for_each", "parallel", "set_variable", "log_message",
)


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
            if step.step_type not in VALID_STEP_TYPES:
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
        timeout_seconds: float | None = None,
    ) -> Workflow:
        wf = Workflow(
            id=uuid.uuid4().hex[:12],
            tenant_id=tenant_id,
            name=name,
            description=description,
            trigger_type=trigger_type,
            status=status,
            timeout_seconds=timeout_seconds,
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
                    timeout_seconds=getattr(s, "timeout_seconds", None),
                    on_failure=getattr(s, "on_failure", "fail_workflow"),
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
                    timeout_seconds=s.get("timeout_seconds"),
                    on_failure=s.get("on_failure", "fail_workflow"),
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
        timeout_seconds: float | None = None,
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
        if timeout_seconds is not None:
            wf.timeout_seconds = timeout_seconds
        if steps is not None:
            wf.steps = [
                WorkflowStep(
                    id=uuid.uuid4().hex[:12],
                    workflow_id=wf.id,
                    step_type=s["step_type"],
                    config=s.get("config", {}),
                    order=s.get("order", i),
                    condition=s.get("condition"),
                    timeout_seconds=s.get("timeout_seconds"),
                    on_failure=s.get("on_failure", "fail_workflow"),
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

    # ── Webhook endpoints ──────────────────────────────────────────────────

    async def create_webhook(
        self,
        tenant_id: str,
        url: str,
        name: str = "",
        auth_type: str = "none",
        auth_config: dict[str, Any] | None = None,
        secret: str = "",
    ) -> WebhookEndpoint:
        from app.modules.webhooks.url_safety import validate_webhook_url
        safe_url = validate_webhook_url(url, resolve_dns=True)
        endpoint = WebhookEndpoint(
            id=uuid.uuid4().hex[:12],
            tenant_id=tenant_id,
            url=safe_url,
            name=name,
            auth_type=auth_type,
            auth_config=auth_config or {},
            secret=secret,
        )
        return await self._repo.create_webhook(endpoint)

    async def get_webhook(self, endpoint_id: str, tenant_id: str) -> WebhookEndpoint | None:
        return await self._repo.get_webhook(endpoint_id, tenant_id)

    async def list_webhooks(self, tenant_id: str) -> list[WebhookEndpoint]:
        return await self._repo.list_webhooks(tenant_id)

    async def update_webhook(
        self,
        endpoint_id: str,
        tenant_id: str,
        url: str | None = None,
        name: str | None = None,
        auth_type: str | None = None,
        secret: str | None = None,
    ) -> WebhookEndpoint:
        ep = await self._repo.get_webhook(endpoint_id, tenant_id)
        if not ep:
            raise WorkflowValidationError(f"Webhook {endpoint_id} not found")
        if url is not None:
            from app.modules.webhooks.url_safety import validate_webhook_url
            ep.url = validate_webhook_url(url, resolve_dns=True)
        if name is not None:
            ep.name = name
        if auth_type is not None:
            ep.auth_type = auth_type
        if secret is not None:
            ep.secret = secret
        return await self._repo.update_webhook(ep)

    async def delete_webhook(self, endpoint_id: str, tenant_id: str) -> None:
        ep = await self._repo.get_webhook(endpoint_id, tenant_id)
        if not ep:
            raise WorkflowValidationError(f"Webhook {endpoint_id} not found")
        await self._repo.delete_webhook(endpoint_id, tenant_id)

    # ── Scheduled jobs ─────────────────────────────────────────────────────

    async def create_job(
        self,
        tenant_id: str,
        name: str,
        job_type: str,
        schedule: str,
        config: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
        max_retries: int = 3,
    ) -> ScheduledJob:
        from domains.workflow.scheduler import (
            parse_cron_next_run,
            parse_interval_next_run,
            parse_one_time_next_run,
        )

        if job_type == "cron":
            next_run = parse_cron_next_run(schedule)
        elif job_type == "interval":
            next_run = parse_interval_next_run(schedule)
        elif job_type == "one_time":
            next_run = parse_one_time_next_run(schedule)
        else:
            raise WorkflowValidationError(f"Invalid job_type: {job_type}")

        job = ScheduledJob(
            id=uuid.uuid4().hex[:12],
            tenant_id=tenant_id,
            job_type=job_type,
            name=name,
            schedule=schedule,
            config=config or {},
            payload=payload or {},
            max_retries=max_retries,
            next_run_at=next_run,
        )
        return await self._repo.create_job(job)

    async def get_job(self, job_id: str, tenant_id: str) -> ScheduledJob | None:
        return await self._repo.get_job(job_id, tenant_id)

    async def list_jobs(self, tenant_id: str) -> list[ScheduledJob]:
        return await self._repo.list_jobs(tenant_id)

    async def update_job(
        self,
        job_id: str,
        tenant_id: str,
        name: str | None = None,
        status: str | None = None,
        schedule: str | None = None,
    ) -> ScheduledJob:
        job = await self._repo.get_job(job_id, tenant_id)
        if not job:
            raise WorkflowValidationError(f"Job {job_id} not found")
        if name is not None:
            job.name = name
        if status is not None:
            job.status = status
        if schedule is not None:
            job.schedule = schedule
        return await self._repo.update_job(job)

    async def delete_job(self, job_id: str, tenant_id: str) -> None:
        job = await self._repo.get_job(job_id, tenant_id)
        if not job:
            raise WorkflowValidationError(f"Job {job_id} not found")
        await self._repo.delete_job(job_id, tenant_id)

    async def list_job_executions(self, job_id: str) -> list[JobExecution]:
        return await self._repo.list_job_executions(job_id)

    async def run_job_now(self, job_id: str, tenant_id: str) -> JobExecution:
        job = await self._repo.get_job(job_id, tenant_id)
        if not job:
            raise WorkflowValidationError(f"Job {job_id} not found")
        from domains.workflow.scheduler import JobScheduler
        scheduler = JobScheduler(self._repo)
        now = datetime.now(timezone.utc)
        execution = JobExecution(
            id=f"jobexec_{job.id}_{int(now.timestamp())}",
            job_id=job.id,
            tenant_id=tenant_id,
            status="running",
            started_at=now,
        )
        execution = await self._repo.create_job_execution(execution)
        try:
            from domains.workflow.templates import log_message
            execution.status = "completed"
            execution.result = {"manual_trigger": True, "timestamp": now.isoformat()}
            execution.completed_at = datetime.now(timezone.utc)
            job.last_run_at = execution.completed_at
            job.run_count += 1
            job.retry_count = 0
            await self._repo.update_job(job)
        except Exception as exc:
            execution.status = "failed"
            execution.error = str(exc)
            execution.completed_at = datetime.now(timezone.utc)
        await self._repo.update_job_execution(execution)
        return execution

    # ── Execution control ──────────────────────────────────────────────────

    async def cancel_execution(self, execution_id: str, tenant_id: str) -> WorkflowExecution | None:
        return await self._repo.cancel_execution(execution_id, tenant_id)

    # ── Analytics ──────────────────────────────────────────────────────────

    async def get_workflow_stats(self, tenant_id: str) -> dict:
        return await self._repo.get_workflow_stats(tenant_id)

    async def get_execution_stats(self, tenant_id: str) -> dict:
        return await self._repo.get_execution_stats(tenant_id)

    async def run_scheduler_tick(self) -> list[JobExecution]:
        from domains.workflow.scheduler import JobScheduler
        scheduler = JobScheduler(self._repo)
        return await scheduler.tick()

    # ── Workflow templates ─────────────────────────────────────────────────

    async def list_templates(self) -> list[WorkflowTemplate]:
        return await self._repo.list_templates()

    async def get_template(self, template_id: str) -> WorkflowTemplate | None:
        return await self._repo.get_template(template_id)
