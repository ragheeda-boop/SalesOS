"""Pydantic schemas for Analytics & Reporting domain."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ReportCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    type: str = Field(default="custom", description="Cube type: pipeline, forecast, team, activity, custom")
    config: dict[str, Any] = Field(default_factory=dict)
    metrics: list[str] = Field(default_factory=list)
    dimensions: list[str] = Field(default_factory=list)
    filters: dict[str, Any] = Field(default_factory=dict)
    visualization_type: str = Field(default="table", description="table, bar, line, pie, area, funnel, heatmap, kpi")
    schedule: str = "one-time"
    recipients: list[str] = Field(default_factory=list)


class ReportUpdate(BaseModel):
    name: str | None = Field(None, max_length=500)
    config: dict[str, Any] | None = None
    metrics: list[str] | None = None
    dimensions: list[str] | None = None
    filters: dict[str, Any] | None = None
    visualization_type: str | None = None
    schedule: str | None = None
    recipients: list[str] | None = None


class ReportResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    type: str
    metrics: list[str]
    dimensions: list[str]
    filters: dict[str, Any]
    visualization_type: str
    created_by: str
    schedule: str
    recipients: list[str]
    created_at: str
    updated_at: str


class ReportListResponse(BaseModel):
    reports: list[ReportResponse]
    total: int
    next_cursor: str | None = None


class ReportShareCreate(BaseModel):
    user_id: str = Field(..., min_length=1)
    permission: str = Field(default="view", description="view, edit, admin")


class ReportShareResponse(BaseModel):
    id: str
    report_id: str
    user_id: str
    permission: str
    shared_by: str
    created_at: str


class ScheduledReportCreate(BaseModel):
    report_id: str = Field(..., min_length=1)
    cadence: str = Field(default="weekly", description="daily, weekly, monthly, quarterly")
    recipients: list[str] = Field(default_factory=list)


class ScheduledReportUpdate(BaseModel):
    cadence: str | None = None
    recipients: list[str] | None = None
    enabled: bool | None = None


class ScheduledReportResponse(BaseModel):
    id: str
    tenant_id: str
    report_id: str
    cadence: str
    recipients: list[str]
    next_run: str | None
    last_run: str | None
    enabled: bool
    created_at: str
    updated_at: str


class UnifiedAnalyticsResponse(BaseModel):
    total_deals: int
    total_revenue: float
    total_employees: int
    total_workflows: int
    conversion_rate: float
    pipeline_value: float
    avg_deal_size: float
    win_rate: float
    active_automations: int
    generated_at: str


class ExportRequest(BaseModel):
    format: str = Field(default="csv", description="csv, pdf, json")
    report_id: str | None = None


class ExportResponse(BaseModel):
    content: str
    format: str
    execution_id: str | None = None
    path: str | None = None


class ExecutionResponse(BaseModel):
    execution_id: str
    status: str
    output_format: str
    output_path: str | None
    error: str | None = None
    started_at: str | None = None
    completed_at: str | None = None


class ExecutionListResponse(BaseModel):
    executions: list[ExecutionResponse]
    total: int
    next_cursor: str | None = None


class ExecuteDueSchedulesResponse(BaseModel):
    executed: int
    results: list[dict[str, Any]]
