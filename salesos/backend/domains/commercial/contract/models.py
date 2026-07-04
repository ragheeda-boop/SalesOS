from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum


class ContractStatus(Enum):
    DRAFT = "draft"
    SIGNED = "signed"
    ACTIVE = "active"
    COMPLETED = "completed"
    TERMINATED = "terminated"
    EXPIRED = "expired"
    RENEWED = "renewed"


@dataclass
class ContractParty:
    name: str = ""
    role: str = ""  # provider, customer
    contact_email: str = ""
    signatory_name: str = ""


@dataclass
class ContractObligation:
    description: str = ""
    owner: str = ""
    due_date: date | None = None
    status: str = "pending"  # pending, fulfilled, waived
    completed_at: datetime | None = None


@dataclass
class RenewalRule:
    auto_renew: bool = False
    notice_days: int = 30
    renewal_term_months: int = 12
    max_renewals: int = 0  # 0 = unlimited


@dataclass
class Contract:
    id: str
    tenant_id: str
    opportunity_id: str = ""
    quote_id: str = ""
    quote_revision: int = 1
    title: str = ""
    status: ContractStatus = ContractStatus.DRAFT
    parties: list[ContractParty] = field(default_factory=list)
    obligations: list[ContractObligation] = field(default_factory=list)
    effective_date: date | None = None
    expiry_date: date | None = None
    renewal: RenewalRule = field(default_factory=RenewalRule)
    legal_terms: str = ""
    governing_law: str = ""
    signed_by_provider: datetime | None = None
    signed_by_customer: datetime | None = None
    notes: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: int = 1

    @property
    def is_signed(self) -> bool:
        return self.status in (ContractStatus.SIGNED, ContractStatus.ACTIVE, ContractStatus.COMPLETED)

    @property
    def is_terminal(self) -> bool:
        return self.status in (ContractStatus.COMPLETED, ContractStatus.TERMINATED, ContractStatus.EXPIRED)

    @property
    def is_expired(self) -> bool:
        if not self.expiry_date:
            return False
        return date.today() > self.expiry_date
