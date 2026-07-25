from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class EmployeeSignalResponse(BaseModel):
    id: str
    employee_id: str
    tenant_id: str
    signal_type: str
    source: str
    metadata: dict[str, Any] = {}
    timestamp: datetime
    created_at: datetime


class EmployeeScoreResponse(BaseModel):
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
    generated_at: datetime


class EmployeeSignalSummaryResponse(BaseModel):
    total_signals: int = 0
    by_source: dict[str, int] = {}
    by_type: dict[str, int] = {}
    recent_signals: list[EmployeeSignalResponse] = []
    score: EmployeeScoreResponse | None = None


class BulkEditEmployeesRequest(BaseModel):
    employee_ids: list[str] = Field(..., min_length=1)
    updates: dict = Field(..., description="Fields to update: role, is_active, department")


class BulkEditEmployeesResponse(BaseModel):
    updated: int
    failed: int
    errors: list[dict]


class BulkDeleteEmployeesRequest(BaseModel):
    employee_ids: list[str] = Field(..., min_length=1)


class BulkDeleteEmployeesResponse(BaseModel):
    deleted: int


class CursorResponse(BaseModel):
    data: list
    next_cursor: str | None = None
    has_next: bool = False
    total: int | None = None


# ── Frontend-matched response schemas ──────────────────────────────


class SignalTypeBreakdown(BaseModel):
    type: str
    count: int
    label: str


class SignalSourceBreakdown(BaseModel):
    source: str
    count: int
    label: str


class SignalTrendPoint(BaseModel):
    date: str
    count: int


class EmployeeSignalsSummaryResponse(BaseModel):
    by_type: list[SignalTypeBreakdown] = []
    by_source: list[SignalSourceBreakdown] = []
    trend: list[SignalTrendPoint] = []
    total: int = 0


SOURCE_LABELS: dict[str, str] = {
    "crm": "CRM",
    "timeline": "Timeline",
    "workflow": "Workflow",
    "email": "Email",
    "calendar": "Calendar",
    "manual": "Manual",
}

SIGNAL_TYPE_LABELS: dict[str, str] = {
    "email_sent": "Email Sent",
    "email_received": "Email Received",
    "meeting_created": "Meeting Created",
    "meeting_completed": "Meeting Completed",
    "call": "Call",
    "call_completed": "Call Completed",
    "task_created": "Task Created",
    "task_completed": "Task Completed",
    "note_added": "Note Added",
    "contract_signed": "Contract Signed",
    "deal_assigned": "Deal Assigned",
    "deal_stage_changed": "Deal Stage Changed",
    "contact_modified": "Contact Modified",
    "approval_completed": "Approval Completed",
    "workflow_completed": "Workflow Completed",
}


class ScoreFactor(BaseModel):
    name: str
    contribution: float = 0.0
    signal_type: str = ""
    label: str = ""


class EmployeeScoreDetailResponse(BaseModel):
    score: float = 0.0
    trend: str = "stable"
    confidence: float = 0.0
    factors: list[ScoreFactor] = []


class EmployeeTimelineEvent(BaseModel):
    id: str
    action: str = ""
    title: str = ""
    source: str = ""
    source_label: str = ""
    timestamp: str = ""
    actor: str = ""
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    metadata: dict[str, Any] = {}


class EmployeeTimelineDataResponse(BaseModel):
    events: list[EmployeeTimelineEvent] = []
    next_cursor: str | None = None
    has_next: bool = False
    total: int = 0


class ScoreTrendPoint(BaseModel):
    date: str
    score: float = 0.0


class PeerComparisonItem(BaseModel):
    metric: str = ""
    employee_value: float = 0.0
    department_avg: float = 0.0
    label: str = ""


class RiskFlagResponse(BaseModel):
    type: str = ""
    label: str = ""
    severity: str = "low"
    description: str = ""


class EmployeePerformanceResponse(BaseModel):
    score_trend: list[ScoreTrendPoint] = []
    peer_comparison: list[PeerComparisonItem] = []
    risk_flags: list[RiskFlagResponse] = []
    factors: list[ScoreFactor] = []
    current_score: float = 0.0
    score_trend_direction: str = "stable"
    department: str | None = None
