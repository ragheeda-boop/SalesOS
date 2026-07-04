"""Quote domain models — commercial agreement draft with revision control."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any


class QuoteStatus(Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"
    REVISED = "revised"


class ApprovalLevel(Enum):
    NONE = "none"
    MANAGER = "manager"
    DIRECTOR = "director"
    EXECUTIVE = "executive"


@dataclass
class QuoteLine:
    """A single line item in a quote."""

    id: str
    description: str
    description_ar: str = ""
    quantity: int = 1
    unit_price: float = 0.0
    discount_percent: float = 0.0
    tax_percent: float = 0.0
    product_code: str = ""
    notes: str = ""

    @property
    def line_total(self) -> float:
        return self.unit_price * self.quantity

    @property
    def discount_amount(self) -> float:
        return self.line_total * self.discount_percent / 100.0

    @property
    def net_total(self) -> float:
        return self.line_total - self.discount_amount

    @property
    def tax_amount(self) -> float:
        return self.net_total * self.tax_percent / 100.0

    @property
    def grand_total(self) -> float:
        return self.net_total + self.tax_amount


@dataclass
class ApprovalState:
    """Tracks the approval workflow for a quote."""

    level: ApprovalLevel = ApprovalLevel.NONE
    approved_by: str = ""
    approved_at: datetime | None = None
    comments: str = ""

    @property
    def is_approved(self) -> bool:
        return self.level != ApprovalLevel.NONE and self.approved_at is not None


@dataclass
class QuoteRevision:
    """A revision of a quote. Immutable once created."""

    version: int
    quote_id: str
    status: QuoteStatus
    lines: list[QuoteLine] = field(default_factory=list)
    subtotal: float = 0.0
    total_discount: float = 0.0
    total_tax: float = 0.0
    grand_total: float = 0.0
    notes: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Quote:
    """A commercial agreement draft — the Aggregate Root.

    Represents the seller's commercial commitment.
    Immutable after approval. Changes create revisions.
    """

    id: str
    tenant_id: str
    opportunity_id: str = ""
    company_id: str = ""
    title: str = ""
    status: QuoteStatus = QuoteStatus.DRAFT
    version: int = 1
    lines: list[QuoteLine] = field(default_factory=list)
    revisions: list[QuoteRevision] = field(default_factory=list)
    approval: ApprovalState = field(default_factory=ApprovalState)
    currency: str = "SAR"
    payment_terms: str = ""
    delivery_terms: str = ""
    valid_until: date | None = None
    notes: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = ""

    # ── Computed totals ──

    @property
    def subtotal(self) -> float:
        return sum(li.line_total for li in self.lines)

    @property
    def total_discount(self) -> float:
        return sum(li.discount_amount for li in self.lines)

    @property
    def total_tax(self) -> float:
        return sum(li.tax_amount for li in self.lines)

    @property
    def grand_total(self) -> float:
        return sum(li.grand_total for li in self.lines)

    @property
    def discount_percent(self) -> float:
        if self.subtotal == 0:
            return 0.0
        return round(self.total_discount / self.subtotal * 100, 2)

    @property
    def is_editable(self) -> bool:
        return self.status in (QuoteStatus.DRAFT,)

    @property
    def is_terminal(self) -> bool:
        return self.status in (QuoteStatus.ACCEPTED, QuoteStatus.REJECTED, QuoteStatus.EXPIRED)

    @property
    def has_expired(self) -> bool:
        if not self.valid_until:
            return False
        return date.today() > self.valid_until
