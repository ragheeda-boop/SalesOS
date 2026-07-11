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


@dataclass
class ReportDefinition:
    id: str
    tenant_id: str
    name: str
    type: CubeType = CubeType.CUSTOM
    config: dict[str, Any] = field(default_factory=dict)
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
class AnalyticsCube:
    id: str
    name: str
    dimensions: list[str] = field(default_factory=list)
    measures: list[str] = field(default_factory=list)
    granularity: Granularity = Granularity.DAY
    source_query: str = ""
