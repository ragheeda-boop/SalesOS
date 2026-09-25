"""Pydantic schemas for Entity Resolution API endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ── Matching Pipeline ────────────────────────────────────────────────────────


class RunMatchingRequest(BaseModel):
    """Request to run the matching pipeline."""
    tenant_id: str | None = None
    source_file_id: str | None = None
    max_candidates: int = Field(default=10000, ge=1, le=100000)


class MatchSignal(BaseModel):
    """A signal that matched between two records."""
    name: str
    matched: bool
    weight: int = 0
    tier: str = ""


class MatchResultItem(BaseModel):
    """A single match result."""
    id: str
    source_a_id: str
    source_b_id: str
    match_score: float
    match_method: str
    match_signals: list[dict[str, Any]]
    match_status: str
    created_at: datetime


class RunMatchingResponse(BaseModel):
    """Response from the matching pipeline."""
    total_candidates: int
    matches_found: int
    auto_merge: int
    review: int
    separate: int
    vetoed: int
    errors: int
    duration_seconds: float


# ── Conflicts ────────────────────────────────────────────────────────────────


class ConflictItem(BaseModel):
    """A field-level conflict."""
    id: str
    global_entity_id: str
    field_name: str
    value_a: str | None = None
    source_a_id: str | None = None
    value_b: str | None = None
    source_b_id: str | None = None
    is_government_id: bool = False
    veto_enabled: bool = False
    resolution: str = "open"
    resolved_value: str | None = None
    resolved_by: str | None = None
    created_at: datetime


class ResolveConflictRequest(BaseModel):
    """Request to resolve a conflict."""
    resolution: str = Field(..., description="Resolution strategy: use_a, use_b, custom, dismiss")
    resolved_value: str | None = None
    resolved_by: str | None = None


# ── Field Provenance ─────────────────────────────────────────────────────────


class FieldProvenanceItem(BaseModel):
    """A field provenance record."""
    id: str
    global_entity_id: str
    field_name: str
    field_value: str
    source_row_id: str | None = None
    source_file_id: str | None = None
    evidence_tier: str
    authority_score: float
    selection_reason: str
    conflict_status: str
    is_current: bool
    created_at: datetime


# ── Quality Scores ───────────────────────────────────────────────────────────


class QualityScoreResponse(BaseModel):
    """Quality score for a global entity."""
    id: str
    global_entity_id: str
    completeness_score: float
    accuracy_score: float
    consistency_score: float
    freshness_score: float
    provenance_score: float
    overall_score: float
    scored_at: datetime
    details: dict[str, Any] | None = None


# ── Merge History ────────────────────────────────────────────────────────────


class MergeHistoryItem(BaseModel):
    """A merge/unmerge history record."""
    id: str
    operation: str
    target_entity_id: str
    source_entity_ids: list[str]
    match_score: float | None = None
    match_method: str | None = None
    performed_by: str | None = None
    performed_at: datetime
    rollback_available: bool = True


class MergeRequest(BaseModel):
    """Request to merge two entities."""
    target_entity_id: str
    source_entity_id: str
    performed_by: str | None = None


class UnmergeRequest(BaseModel):
    """Request to unmerge (rollback) a merge."""
    merge_history_id: str
    performed_by: str | None = None
