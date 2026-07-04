"""Proposal domain models — communication layer referencing Quote revisions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ProposalStatus(Enum):
    DRAFT = "draft"
    GENERATED = "generated"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    DELIVERED = "delivered"
    VIEWED = "viewed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class ProposalSection:
    """A named section within a proposal."""

    title: str
    title_ar: str = ""
    content: str = ""
    content_ar: str = ""
    order: int = 0
    type: str = "text"  # text, scope, terms, pricing_ref


@dataclass
class ProposalTemplate:
    """A reusable template for proposal structure."""

    id: str
    name: str
    name_ar: str
    sections: list[ProposalSection] = field(default_factory=list)

    @staticmethod
    def default() -> ProposalTemplate:
        return ProposalTemplate(
            id="default",
            name="Default Proposal",
            name_ar="عرض افتراضي",
            sections=[
                ProposalSection(title="Executive Summary", title_ar="ملخص تنفيذي", order=1, type="text"),
                ProposalSection(title="Scope of Work", title_ar="نطاق العمل", order=2, type="scope"),
                ProposalSection(title="Commercial Terms", title_ar="الشروط التجارية", order=3, type="pricing_ref"),
                ProposalSection(title="Deliverables", title_ar="التسليمات", order=4, type="text"),
                ProposalSection(title="Acceptance Conditions", title_ar="شروط القبول", order=5, type="text"),
            ],
        )


@dataclass
class Proposal:
    """A business proposal — communication packaging for a Quote.

    References a QuoteRevision. Never copies commercial data.
    """

    id: str
    tenant_id: str
    opportunity_id: str = ""
    quote_id: str = ""
    quote_revision: int = 1  # Which quote revision this proposal represents
    title: str = ""
    status: ProposalStatus = ProposalStatus.DRAFT
    sections: list[ProposalSection] = field(default_factory=list)
    template_id: str = "default"
    recipient_name: str = ""
    recipient_email: str = ""
    delivery_method: str = "email"  # email, portal, link, pdf
    delivery_url: str = ""
    viewed_at: datetime | None = None
    accepted_at: datetime | None = None
    valid_until: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = ""
    version: int = 1

    @property
    def is_editable(self) -> bool:
        return self.status in (ProposalStatus.DRAFT,)

    @property
    def is_terminal(self) -> bool:
        return self.status in (ProposalStatus.ACCEPTED, ProposalStatus.REJECTED, ProposalStatus.EXPIRED)

    @property
    def is_delivered(self) -> bool:
        return self.status in (ProposalStatus.DELIVERED, ProposalStatus.VIEWED,
                               ProposalStatus.ACCEPTED, ProposalStatus.REJECTED)
