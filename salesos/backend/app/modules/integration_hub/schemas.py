"""STORY-08-06 — Integration Hub HTTP schemas (DOM-021)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ConnectionCreate(BaseModel):
    connector_key: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=128)
    credential_ref: str = Field(..., min_length=1, max_length=512)
    connection_config: dict[str, Any] = Field(default_factory=dict)


class ConnectionResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    connector_key: str
    name: str
    credential_ref: str
    connection_config: dict[str, Any]
    cursor_state: dict[str, Any]
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class ConnectionTestResponse(BaseModel):
    ok: bool
    message: str
    latency_ms: float


class MappingCreate(BaseModel):
    model: str = Field(..., min_length=1, max_length=128)
    mappings: list[dict[str, Any]]
    baseline_fields: list[str] | None = None
    version: int = 1


class MappingResponse(BaseModel):
    id: UUID
    connection_id: UUID
    model: str
    version: int
    mappings: list[dict[str, Any]]
    baseline_fields: list[str]
    is_active: bool

    model_config = {"from_attributes": True}


class ConflictRuleIn(BaseModel):
    internal: str
    winner: Literal["source", "salesos"]
    exclude_from_pull: bool = False


class ConflictPolicyUpsert(BaseModel):
    rules: list[ConflictRuleIn] = Field(default_factory=list)
    salesos_authored_fields: list[str] | None = None
    operational_fields: list[str] | None = None


class ConflictPolicyResponse(BaseModel):
    id: UUID
    connection_id: UUID
    rules: list[dict[str, Any]]
    salesos_authored_fields: list[str]
    operational_fields: list[str]

    model_config = {"from_attributes": True}


class ScheduleCreate(BaseModel):
    model: str = Field(..., min_length=1, max_length=128)
    schedule: str = Field(default="15m", min_length=1, max_length=64)
    job_type: Literal["cron", "interval", "one_time"] = "interval"
    name: str | None = None


class ScheduleResponse(BaseModel):
    job_id: str
    connection_id: UUID
    model: str
    schedule: str
    job_type: str
    next_run_at: datetime | None = None


class SyncRunResponse(BaseModel):
    """STORY-08-05 SyncRun + STORY-09-09 cursor HTTP (write_date watermarks)."""

    id: UUID
    connection_id: UUID
    model: str
    status: str
    failure_class: str | None = None
    records_pulled: int
    records_written: int
    records_failed: int
    scheduled_job_id: str | None = None
    # STORY-09-09 — expose ORM cursor JSON for Studio Monitor (was honesty-blocked).
    cursor_before: dict[str, Any] = Field(default_factory=dict)
    cursor_after: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime
    finished_at: datetime | None = None

    model_config = {"from_attributes": True}


class DisconnectResponse(BaseModel):
    id: UUID
    is_active: bool
    message: str


class UnlinkedBadgeItemResponse(BaseModel):
    """STORY-09-01 residual — visible unlinked cr_number badge for Studio Monitor."""

    kind: Literal["unlinked_badge"] = "unlinked_badge"
    external_id: str
    status: Literal["unlinked", "invalid_cr"]
    cr_number: str | None = None
    message: str = ""
    model: str = "res.partner"
    sync_run_id: str | None = None
    recorded_at: str | None = None


class UnlinkedBadgeListResponse(BaseModel):
    connection_id: UUID
    count: int
    items: list[UnlinkedBadgeItemResponse]
