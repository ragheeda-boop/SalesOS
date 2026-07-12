"""Pydantic schemas for the Workflow domain."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class WorkflowStepSchema(BaseModel):
    step_type: str = Field(..., pattern=r"^(send_email|update_crm|create_task|webhook|nba_recommend)$")
    config: dict = Field(default_factory=dict)
    order: int = 0
    condition: str | None = None


class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    trigger_type: str = Field(default="manual", pattern=r"^(event|scheduled|manual)$")
    status: str = Field(default="draft", pattern=r"^(active|inactive|draft)$")
    steps: list[WorkflowStepSchema] = Field(default_factory=list)
    template: str | None = Field(None, description="Template key to base the workflow on")


class WorkflowUpdate(BaseModel):
    name: str | None = Field(None, max_length=200)
    description: str | None = None
    trigger_type: str | None = Field(None, pattern=r"^(event|scheduled|manual)$")
    status: str | None = Field(None, pattern=r"^(active|inactive|draft)$")
    steps: list[WorkflowStepSchema] | None = None


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
