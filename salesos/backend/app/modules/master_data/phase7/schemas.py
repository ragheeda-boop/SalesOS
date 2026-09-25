"""Phase 7-A — Review Queue API schemas (Pydantic request/response)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════════════════
# Disposition enums (capture-only: record intent; never trigger a side effect)
# ═══════════════════════════════════════════════════════════════════════════════


class P3PairDisposition(str, Enum):
    MATCH = "MATCH"
    SEPARATE = "SEPARATE"
    UNSURE = "UNSURE"
    ESCALATE = "ESCALATE"


class ShortCRDisposition(str, Enum):
    CONFIRMED_VALID_SHORT_CR = "CONFIRMED_VALID_SHORT_CR"
    CONFIRMED_ARTIFACT = "CONFIRMED_ARTIFACT"
    UNRESOLVED_ESCALATE = "UNRESOLVED_ESCALATE"


class TriageDisposition(str, Enum):
    CONFIRM = "CONFIRM"
    REVIEW = "REVIEW"
    ESCALATE = "ESCALATE"


class P1CandidateDisposition(str, Enum):
    """Record-only outcomes for an individually reviewed P1 candidate."""

    CONFIRM = "CONFIRM"
    REVIEW = "REVIEW"
    ESCALATE = "ESCALATE"


class P2SampleDisposition(str, Enum):
    """Record-only acceptance outcomes for a reviewed P2 sample stratum."""

    ACCEPT_SAMPLE = "ACCEPT_SAMPLE"
    REJECT_SAMPLE = "REJECT_SAMPLE"
    EXPAND_SAMPLE = "EXPAND_SAMPLE"


class MAUnresolvedDisposition(str, Enum):
    """Record-only outcomes for v0.7 MA-to-current-Master proposals."""

    CONFIRM_EXACT = "CONFIRM_EXACT"
    REVIEW = "REVIEW"
    ESCALATE = "ESCALATE"


# ═══════════════════════════════════════════════════════════════════════════════
# Review Queue State rows
# ═══════════════════════════════════════════════════════════════════════════════


class ReviewQueueRow(BaseModel):
    id: str
    queue_type: str
    subject_key: str
    global_company_id: str | None = None
    global_company_id_b: str | None = None
    status: str
    disposition: str | None = None
    notes: str | None = None


class ReviewQueueDisposition(BaseModel):
    """A record-only disposition capture into md_review_queue_state.

    This model intentionally carries NO field for any classification change,
    CR promotion, or merge action — the only permitted write is the review
    state itself.
    """

    disposition: str = Field(..., description="One of the queue-type dispositions")
    reviewer: str = Field(..., min_length=1, max_length=255)
    notes: str | None = Field(None, max_length=2000)


class ReviewQueueDispositionResponse(BaseModel):
    id: str
    queue_type: str
    subject_key: str
    status: str
    disposition: str | None
    reviewer: str | None
    reviewed_at: datetime | None
    notes: str | None


# ═══════════════════════════════════════════════════════════════════════════════
# Read-only export payloads
# ═══════════════════════════════════════════════════════════════════════════════


class P3PairRow(BaseModel):
    pair_id: str
    row_a: str
    row_b: str
    company_a_global_id: str
    company_b_global_id: str
    source_id: str
    current_identity_state_a: str | None = None
    current_identity_state_b: str | None = None
    final_review_required: str
    disposition: str | None = None
    status: str | None = None


class ShortCRRow(BaseModel):
    master_account_id: str
    global_company_id: str | None
    cr_number_raw: str
    valid_cr_count: int
    rejected_tokens: list[str] = Field(default_factory=list)


class TriageRow(BaseModel):
    global_company_id: str
    candidate_type: str
    reason: str
    identity_state: str | None = None
    status: str | None = None
    disposition: str | None = None


class ReviewQueueExport(BaseModel):
    total: int
    items: list[Any]
