"""Workflow domain models."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class WorkflowStep:
    id: str
    workflow_id: str
    step_type: str  # send_email | update_crm | create_task | webhook | nba_recommend | if_else | for_each | parallel
    config: dict[str, Any] = field(default_factory=dict)
    order: int = 0
    condition: str | None = None  # optional expression like "context.amount > 10000"
    timeout_seconds: float | None = None  # step-level timeout
    on_failure: str = "fail_workflow"  # fail_workflow | skip | retry


@dataclass
class Workflow:
    id: str
    tenant_id: str
    name: str
    description: str = ""
    trigger_type: str = "manual"  # event | scheduled | manual
    status: str = "draft"  # active | inactive | draft
    steps: list[WorkflowStep] = field(default_factory=list)
    timeout_seconds: float | None = None  # workflow-level timeout
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class WorkflowExecutionStep:
    id: str
    execution_id: str
    step_id: str
    step_type: str
    status: str = "pending"  # pending | running | completed | failed | skipped | timed_out
    result: dict[str, Any] | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None


@dataclass
class WorkflowExecution:
    id: str
    workflow_id: str
    tenant_id: str
    trigger_event: str = "manual"
    status: str = "running"  # running | completed | failed | timed_out
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    error: str | None = None
    step_results: list[WorkflowExecutionStep] = field(default_factory=list)


@dataclass
class ScheduledJob:
    id: str
    tenant_id: str
    job_type: str  # cron | one_time | interval
    name: str
    config: dict[str, Any] = field(default_factory=dict)
    schedule: str = ""  # cron expression or interval like "30m" / "2h" / "1d" or ISO timestamp for one_time
    status: str = "active"  # active | paused | completed | failed
    last_run_at: datetime | None = None
    next_run_at: datetime | None = None
    run_count: int = 0
    max_retries: int = 3
    retry_count: int = 0
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class JobExecution:
    id: str
    job_id: str
    tenant_id: str
    status: str = "pending"  # pending | running | completed | failed
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: dict[str, Any] | None = None
    error: str | None = None


@dataclass
class WebhookEndpoint:
    id: str
    tenant_id: str
    url: str
    name: str = ""
    auth_type: str = "none"  # none | hmac | jwt
    auth_config: dict[str, Any] = field(default_factory=dict)
    secret: str = ""
    status: str = "active"  # active | inactive
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class WorkflowTemplate:
    id: str
    name: str
    description: str
    category: str  # lead | deal | renewal | onboarding | follow_up
    steps: list[dict[str, Any]] = field(default_factory=list)
    variables: list[dict[str, Any]] = field(default_factory=list)
    trigger_type: str = "manual"
    tags: list[str] = field(default_factory=list)
