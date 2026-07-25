from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class SignalSource(str, Enum):
    CRM = "crm"
    TIMELINE = "timeline"
    WORKFLOW = "workflow"


class SignalType(str, Enum):
    DEAL_ASSIGNED = "deal_assigned"
    DEAL_STAGE_CHANGED = "deal_stage_changed"
    CONTACT_MODIFIED = "contact_modified"
    MEETING_COMPLETED = "meeting_completed"
    CALL_COMPLETED = "call_completed"
    EMAIL_SENT = "email_sent"
    TASK_COMPLETED = "task_completed"
    APPROVAL_COMPLETED = "approval_completed"
    WORKFLOW_COMPLETED = "workflow_completed"


@dataclass
class EmployeeSignal:
    id: str
    employee_id: str
    tenant_id: str
    signal_type: str
    source: str
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class EmployeeScore:
    id: str
    employee_id: str
    tenant_id: str
    overall_score: float = 0.0
    signal_volume_score: float = 0.0
    recency_score: float = 0.0
    diversity_score: float = 0.0
    completion_rate: float = 0.0
    confidence_interval_low: float = 0.0
    confidence_interval_high: float = 0.0
    signal_count: int = 0
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class EmployeeSignalSummary:
    total_signals: int = 0
    by_source: dict[str, int] = field(default_factory=dict)
    by_type: dict[str, int] = field(default_factory=dict)
    recent_signals: list[EmployeeSignal] = field(default_factory=list)
    score: EmployeeScore | None = None
