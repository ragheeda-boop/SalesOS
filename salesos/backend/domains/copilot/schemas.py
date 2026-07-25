"""Pydantic schemas for the Copilot domain API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SearchCompaniesRequest(BaseModel):
    """Request body for copilot search_companies tool."""

    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    city: str | None = Field(None, max_length=100)
    industry: str | None = Field(None, max_length=100)
    limit: int = Field(10, ge=1, le=20)


class CopilotFeedbackSubmit(BaseModel):
    """Request body for submitting copilot feedback."""

    conversation_id: str = Field(..., min_length=1, max_length=100)
    message_id: str = Field(..., min_length=1, max_length=100)
    rating: str = Field(..., pattern=r"^(up|down)$")
    comment: str = Field("", max_length=1000)
    tool_name: str | None = Field(None, max_length=100)


class CopilotFeedbackResponse(BaseModel):
    """Response after submitting feedback."""

    id: str
    conversation_id: str
    message_id: str
    rating: str
    comment: str
    tool_name: str | None
    created_at: str


class CopilotFeedbackStatsResponse(BaseModel):
    """Aggregated feedback statistics."""

    total_feedback: int
    positive_count: int
    negative_count: int
    satisfaction_rate: float
    by_tool: dict[str, dict[str, int]]


class ToolTelemetryStatsResponse(BaseModel):
    """Aggregated tool telemetry statistics."""

    tool_name: str
    total_calls: int
    success_count: int
    failure_count: int
    success_rate: float
    latency_p50_ms: float
    latency_p95_ms: float
    latency_p99_ms: float
    latency_avg_ms: float
    result_count_avg: float
    calls_per_hour: float
    period_hours: float


class ToolTelemetryBreakdownResponse(BaseModel):
    """Per-tool telemetry breakdown."""

    overall: ToolTelemetryStatsResponse
    by_tool: dict[str, ToolTelemetryStatsResponse]


class ToolTelemetryVolumeResponse(BaseModel):
    """Volume over time data point."""

    timestamp: str
    total: int
    success: int
    failure: int


class ToolTelemetryLogRequest(BaseModel):
    """Manual telemetry log entry (for testing)."""

    tool_name: str = Field(..., min_length=1, max_length=100)
    success: bool = True
    latency_ms: float = Field(0.0, ge=0)
    result_count: int = Field(0, ge=0)
    error_message: str | None = None


class ArabicDetectRequest(BaseModel):
    """Request for Arabic language detection."""

    text: str = Field(..., min_length=1, max_length=5000)


class ArabicDetectResponse(BaseModel):
    """Response for Arabic language detection."""

    is_arabic: bool
    arabic_ratio: float
    contains_diacritics: bool
    detected_entities: list[str]
    language: str
