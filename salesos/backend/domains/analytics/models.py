"""Core domain models for Analytics & Reporting."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ReportStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class OutputFormat(str, Enum):
    PDF = "pdf"
    CSV = "csv"
    JSON = "json"


class Granularity(str, Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"


class CubeType(str, Enum):
    PIPELINE = "pipeline"
    FORECAST = "forecast"
    TEAM = "team"
    ACTIVITY = "activity"
    CUSTOM = "custom"


class VisualizationType(str, Enum):
    TABLE = "table"
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    AREA = "area"
    FUNNEL = "funnel"
    HEATMAP = "heatmap"
    KPI = "kpi"


class PermissionLevel(str, Enum):
    VIEW = "view"
    EDIT = "edit"
    ADMIN = "admin"


class ScheduleCadence(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


@dataclass
class ReportDefinition:
    id: str
    tenant_id: str
    name: str
    type: CubeType = CubeType.CUSTOM
    config: dict[str, Any] = field(default_factory=dict)
    metrics: list[str] = field(default_factory=list)
    dimensions: list[str] = field(default_factory=list)
    filters: dict[str, Any] = field(default_factory=dict)
    visualization_type: VisualizationType = VisualizationType.TABLE
    created_by: str = ""
    schedule: str = "one-time"
    recipients: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ReportExecution:
    id: str
    report_id: str
    status: ReportStatus = ReportStatus.PENDING
    output_format: OutputFormat = OutputFormat.JSON
    output_path: str | None = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass
class ReportShare:
    id: str
    report_id: str
    user_id: str
    permission: PermissionLevel = PermissionLevel.VIEW
    shared_by: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ScheduledReport:
    id: str
    tenant_id: str
    report_id: str
    cadence: ScheduleCadence = ScheduleCadence.WEEKLY
    recipients: list[str] = field(default_factory=list)
    next_run: datetime | None = None
    last_run: datetime | None = None
    enabled: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class AnalyticsCube:
    id: str
    name: str
    dimensions: list[str] = field(default_factory=list)
    measures: list[str] = field(default_factory=list)
    granularity: Granularity = Granularity.DAY
    source_query: str = ""


@dataclass
class DomainMetrics:
    """Aggregated metrics across all domains for unified analytics."""
    total_deals: int = 0
    total_revenue: float = 0.0
    total_employees: int = 0
    total_workflows: int = 0
    conversion_rate: float = 0.0
    pipeline_value: float = 0.0
    avg_deal_size: float = 0.0
    win_rate: float = 0.0
    active_automations: int = 0
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
