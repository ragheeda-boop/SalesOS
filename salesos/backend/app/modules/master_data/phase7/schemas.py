"""Phase 7-A — Review Queue API schemas (Pydantic request/response)."""

from __future__ import annotations

import re
from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

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


# Evidence bags are persisted to a shared review table, so they must stay
# PII-free: company-level facts only, never natural-person contact data.
# Retained for the legacy free-form `notes` channel (see ReviewEvidence's
# docstring for why the typed model below no longer needs a key blocklist).
EVIDENCE_PII_FORBIDDEN_KEYS = frozenset({
    "name", "full_name", "first_name", "last_name", "contact_name",
    "email", "email_address", "mail", "phone", "phone_number", "mobile",
    "fax", "address", "street", "contact_id", "person_name",
})

# Value-level PII patterns (report 116 W1 gap #1: a key-only blocklist misses
# PII carried as a *value*, e.g. evidence["detail"] = "contact ali@x.com").
# Checked against every string value in evidence and against `notes` itself —
# both channels persist to the same shared review table.
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# A run of >=7 digits (with optional separators) is treated as a phone number.
# Saudi CR numbers are handled by dedicated typed fields (cr_class etc.), not
# by free text, so this bound does not need a CR-number carve-out.
_PHONE_RE = re.compile(r"(?:\+?\d[\s.-]?){7,}\d")


def _assert_text_pii_free(text: str | None, *, field: str) -> None:
    """Reject free text carrying an email address or a phone-number-shaped run.

    This is the value-level complement to the old key-only blocklist: it
    catches PII regardless of which field or key it was typed into.
    """
    if not text:
        return
    if _EMAIL_RE.search(text):
        raise ValueError(f"{field} contains what looks like an email address; PII is not permitted")
    if _PHONE_RE.search(text):
        raise ValueError(f"{field} contains what looks like a phone number; PII is not permitted")


def _assert_evidence_pii_free(evidence: dict[str, Any] | None) -> None:
    """Reject any evidence bag carrying natural-person contact PII.

    Company-level keys (domain, cr_number, reason, ...) are allowed; anything
    that would identify a natural person is refused at the API boundary so a
    PII payload can never reach `md_review_queue_state`. Retained for the
    legacy free-form dict path (`ReviewQueueService.record_disposition`
    accepting a raw dict); `ReviewEvidence` below makes this unnecessary for
    new callers because its fields are typed and cannot hold contact PII by
    construction, and its string fields are value-scanned individually.
    """
    if not evidence:
        return

    def _walk(node: Any, path: str) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if str(key).strip().lower() in EVIDENCE_PII_FORBIDDEN_KEYS:
                    raise ValueError(
                        f"evidence.{path}{key} is PII and must not be stored in "
                        "md_review_queue_state"
                    )
                _walk(value, f"{path}{key}.")
        elif isinstance(node, list | tuple):
            for index, value in enumerate(node):
                _walk(value, f"{path}[{index}].")
        elif isinstance(node, str):
            _assert_text_pii_free(node, field=f"evidence.{path.rstrip('.')}")

    _walk(evidence, "")


# Established vocabulary from the G4 review workbooks (report 113):
# "error_type (NOT_EXIST / WRONG_IDENTITY / WRONG_DOMAIN / WRONG_CR / OTHER)".
ReviewErrorType = Literal["NOT_EXIST", "WRONG_IDENTITY", "WRONG_DOMAIN", "WRONG_CR", "OTHER"]


class ReviewEvidence(BaseModel):
    """Typed, whitelisted review evidence (report 116 W1).

    Replaces the free-form `evidence: dict[str, Any]` bag. Every field is a
    fixed, strictly-typed, company-level fact; none can hold a natural
    person's name, email, phone, or address, so PII is impossible **by
    construction** here — not merely filtered by key name (the old
    `EVIDENCE_PII_FORBIDDEN_KEYS` gap: a value could still carry PII under an
    innocuous key, or inside free text). `extra="forbid"` means an unlisted
    key is rejected outright rather than silently dropped or silently stored.

    `reason` is REQUIRED: report 116 SS6.2 found 591 of 643 reviewed G4 rows
    carry no `error_type` at all, which is why a later attempt to bulk-certify
    similar-looking rows failed (identical evidence signatures produced mixed
    human verdicts) — the reviewer's reasoning was never captured in the first
    place. Requiring `reason` going forward closes that gap for new captures;
    it does not retroactively fix the 591 historical rows.

    `detail` is the one remaining free-text field (bounded, PII-scanned) for
    narrative context that does not fit a typed field below.
    """

    model_config = ConfigDict(extra="forbid")

    reason: str = Field(..., min_length=1, max_length=300,
                        description="Required: why this disposition was reached")
    error_type: ReviewErrorType | None = None
    domain_relation: str | None = Field(None, max_length=32)
    cr_class: str | None = Field(None, max_length=32)
    candidate_domain: str | None = Field(None, max_length=253)
    similarity_score: float | None = Field(None, ge=0.0, le=1.0)
    source_count: int | None = Field(None, ge=0, le=1000)
    valid_cr_count: int | None = Field(None, ge=0, le=100)
    pair_id: str | None = Field(None, max_length=64)
    evidence_type: str | None = Field(None, max_length=32)
    sample_n: int | None = Field(None, ge=0, le=1_000_000)
    stratum: str | None = Field(None, max_length=64)
    linkage_status: str | None = Field(None, max_length=64)
    detail: str | None = Field(None, max_length=2000)

    # Only the two genuinely free-text narrative fields are value-scanned for
    # PII patterns. The other fields are typed, constrained identifiers
    # (pair_id, cr_class, candidate_domain, ...) that legitimately contain
    # long digit runs (e.g. "FZ-00001-315216-318033") which a phone-number
    # heuristic would otherwise false-positive on; their PII-safety instead
    # comes from being a fixed, narrow-purpose field in the first place (no
    # field here can hold a person's name, email, or phone number at all).
    @field_validator("reason", "detail")
    @classmethod
    def _scan_strings_for_pii(cls, v: str | None, info: Any) -> str | None:
        if v is not None:
            _assert_text_pii_free(v, field=f"evidence.{info.field_name}")
        return v


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

    `evidence` is REQUIRED and typed (`ReviewEvidence`, report 116 W1) — this
    is an intentional API-breaking change from the prior optional free-form
    dict. It records what the reviewer relied on and, via `reason`, why; it
    asserts no new identity. PII is impossible by construction (fixed,
    strictly-typed fields) rather than merely filtered by key name.

    `notes` remains for legacy free-text narrative; it is scanned the same
    way (value-level, not key-based) since it persists to the same shared
    review table.
    """

    disposition: str = Field(..., description="One of the queue-type dispositions")
    reviewer: str = Field(..., min_length=1, max_length=255)
    notes: str | None = Field(None, max_length=2000)
    evidence: ReviewEvidence = Field(
        ...,
        description="Required, typed review evidence — see ReviewEvidence.",
    )

    @field_validator("notes")
    @classmethod
    def _scan_notes_for_pii(cls, v: str | None) -> str | None:
        if v is not None:
            _assert_text_pii_free(v, field="notes")
        return v


class ReviewQueueDispositionResponse(BaseModel):
    id: str
    queue_type: str
    subject_key: str
    global_company_id: str | None = None
    evidence_ref: dict[str, Any] = Field(default_factory=dict)
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
