"""Pydantic schemas for the Workflow domain."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

VALID_STEP_TYPES = (
    "send_email|update_crm|create_task|webhook|nba_recommend|"
    "if_else|for_each|parallel|set_variable|log_message"
)
VALID_STEP_TYPE_PATTERN = rf"^({VALID_STEP_TYPES})$"


class WorkflowStepSchema(BaseModel):
    step_type: str = Field(..., pattern=VALID_STEP_TYPE_PATTERN)
    config: dict = Field(default_factory=dict)
    order: int = 0
    condition: str | None = None
    timeout_seconds: float | None = Field(None, ge=0)
    on_failure: str = Field(default="fail_workflow", pattern=r"^(fail_workflow|skip|retry)$")
    children: list[dict] = Field(default_factory=list, description="Sub-steps for if_else/for_each/parallel")


class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    trigger_type: str = Field(default="manual", pattern=r"^(event|scheduled|manual)$")
    status: str = Field(default="draft", pattern=r"^(active|inactive|draft)$")
    steps: list[WorkflowStepSchema] = Field(default_factory=list)
    template: str | None = Field(None, description="Template key to base the workflow on")
    timeout_seconds: float | None = Field(None, ge=0)


class WorkflowUpdate(BaseModel):
    name: str | None = Field(None, max_length=200)
    description: str | None = None
    trigger_type: str | None = Field(None, pattern=r"^(event|scheduled|manual)$")
    status: str | None = Field(None, pattern=r"^(active|inactive|draft)$")
    steps: list[WorkflowStepSchema] | None = None
    timeout_seconds: float | None = None


class WorkflowExecuteRequest(BaseModel):
    context: dict = Field(default_factory=dict)


class WorkflowResponse(BaseModel):
    id: str
    name: str
    description: str
    trigger_type: str
    status: str
    steps_count: int
    created_at: str
    updated_at: str


class WorkflowDetailResponse(BaseModel):
    id: str
    name: str
    description: str
    trigger_type: str
    status: str
    steps: list[dict]
    created_at: str
    updated_at: str


class WorkflowExecutionResponse(BaseModel):
    id: str
    workflow_id: str
    trigger_event: str
    status: str
    error: str | None
    started_at: str
    completed_at: str | None
    steps_count: int


class WorkflowExecutionDetailResponse(BaseModel):
    id: str
    workflow_id: str
    trigger_event: str
    status: str
    error: str | None
    started_at: str
    completed_at: str | None
    step_results: list[dict]


class WebhookEndpointCreate(BaseModel):
    url: str = Field(..., min_length=1)
    name: str = ""
    auth_type: str = Field(default="none", pattern=r"^(none|hmac|jwt)$")
    auth_config: dict = Field(default_factory=dict)
    secret: str = ""


class WebhookEndpointResponse(BaseModel):
    id: str
    tenant_id: str
    url: str
    name: str
    auth_type: str
    status: str
    created_at: str


class ScheduledJobCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    job_type: str = Field(..., pattern=r"^(cron|one_time|interval)$")
    schedule: str = Field(..., min_length=1, description="Cron expression, interval string (30m/2h/1d), or ISO timestamp")
    config: dict = Field(default_factory=dict)
    payload: dict = Field(default_factory=dict)
    max_retries: int = Field(default=3, ge=0, le=10)


class ScheduledJobUpdate(BaseModel):
    name: str | None = None
    status: str | None = Field(None, pattern=r"^(active|paused)$")
    schedule: str | None = None
    config: dict | None = None
    payload: dict | None = None
    max_retries: int | None = Field(None, ge=0, le=10)


class ScheduledJobResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    job_type: str
    schedule: str
    status: str
    last_run_at: str | None
    next_run_at: str | None
    run_count: int
    created_at: str


class JobExecutionResponse(BaseModel):
    id: str
    job_id: str
    status: str
    started_at: str | None
    completed_at: str | None
    result: dict | None
    error: str | None


class WorkflowTemplateResponse(BaseModel):
    id: str
    name: str
    description: str
    category: str
    variables: list[dict]
    trigger_type: str
    tags: list[str]


class WorkflowTemplateDetailResponse(BaseModel):
    id: str
    name: str
    description: str
    category: str
    steps: list[dict]
    variables: list[dict]
    trigger_type: str
    tags: list[str]


class WorkflowStatsResponse(BaseModel):
    total_workflows: int = 0
    by_status: dict[str, int] = Field(default_factory=dict)
    by_trigger: dict[str, int] = Field(default_factory=dict)
    total_executions: int = 0
    completed_executions: int = 0
    failed_executions: int = 0


class ExecutionStatsResponse(BaseModel):
    total_executions: int = 0
    by_status: dict[str, int] = Field(default_factory=dict)
    recent: list[dict] = Field(default_factory=list)


class ExecutionCancelResponse(BaseModel):
    execution_id: str
    cancelled: bool
    previous_status: str | None = None


class BulkDeleteWorkflowsRequest(BaseModel):
    workflow_ids: list[str] = Field(..., min_length=1, max_length=100)


class BulkDeleteWorkflowsResponse(BaseModel):
    deleted: int = 0
    failed: int = 0
    errors: list[dict] = Field(default_factory=list)


class JobRunResponse(BaseModel):
    execution_id: str
    job_id: str
    status: str
