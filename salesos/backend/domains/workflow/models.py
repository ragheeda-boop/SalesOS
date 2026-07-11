"""Workflow domain models."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class WorkflowStep:
    id: str
    workflow_id: str
    step_type: str  # send_email | update_crm | create_task | webhook | nba_recommend
    config: dict[str, Any] = field(default_factory=dict)
    order: int = 0
    condition: str | None = None  # optional expression like "context.amount > 10000"


@dataclass
class Workflow:
    id: str
    tenant_id: str
    name: str
    description: str = ""
    trigger_type: str = "manual"  # event | scheduled | manual
    status: str = "draft"  # active | inactive | draft
    steps: list[WorkflowStep] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class WorkflowExecutionStep:
    id: str
    execution_id: str
    step_id: str
    step_type: str
    status: str = "pending"  # pending | running | completed | failed | skipped
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
    status: str = "running"  # running | completed | failed
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    error: str | None = None
    step_results: list[WorkflowExecutionStep] = field(default_factory=list)
