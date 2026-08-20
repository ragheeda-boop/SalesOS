"""Copilot domain models — feedback, telemetry, conversations, mode system."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class CopilotMode(StrEnum):
    """P3-1: Copilot interaction modes — defines what the copilot can do."""
    ASK = "ask"              # Free-form question → answer from knowledge
    EXPLAIN = "explain"      # Explain entity/topic with evidence chain
    SUMMARIZE = "summarize"  # Summarize deal, meeting, or activity
    INVESTIGATE = "investigate"  # Deep-dive analysis, multi-source
    RECOMMEND = "recommend"  # Generate recommendations → HITL approval gate


class FeedbackRating(StrEnum):
    UP = "up"
    DOWN = "down"


@dataclass
class CopilotFeedback:
    """A single feedback record for a copilot message."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str = ""
    message_id: str = ""
    user_id: str = ""
    tenant_id: str = ""
    rating: FeedbackRating = FeedbackRating.UP
    comment: str = ""
    tool_name: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class CopilotFeedbackStats:
    """Aggregated feedback statistics."""

    total_feedback: int = 0
    positive_count: int = 0
    negative_count: int = 0
    satisfaction_rate: float = 0.0
    by_tool: dict[str, dict[str, int]] = field(default_factory=dict)


@dataclass
class ToolCallRecord:
    """A single tool execution log entry."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tool_name: str = ""
    conversation_id: str = ""
    user_id: str = ""
    tenant_id: str = ""
    success: bool = True
    latency_ms: float = 0.0
    result_count: int = 0
    error_message: str | None = None
    input_params: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ToolTelemetryStats:
    """Aggregated telemetry statistics per tool or overall."""

    tool_name: str = "overall"
    total_calls: int = 0
    success_count: int = 0
    failure_count: int = 0
    success_rate: float = 0.0
    latency_p50_ms: float = 0.0
    latency_p95_ms: float = 0.0
    latency_p99_ms: float = 0.0
    latency_avg_ms: float = 0.0
    result_count_avg: float = 0.0
    result_count_p50: float = 0.0
    calls_per_hour: float = 0.0
    period_hours: float = 24.0


@dataclass
class CopilotConversationMessage:
    """A message within a copilot conversation."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str = ""
    role: str = "user"  # user | assistant | tool
    content: str = ""
    tool_name: str | None = None
    tool_result: dict | None = None
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
