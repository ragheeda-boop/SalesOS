"""Najiz (ناجز) Data Contract — Saudi Ministry of Justice litigation portal.

Source: Ministry of Justice
Data: Court cases, case types, rulings involving commercial entities
URL: https://najiz.sa
"""

from __future__ import annotations

from datetime import date
from typing import Any



from runtime.data_fabric_runtime.contracts.base import BaseSourceContract


class NajizContract(BaseSourceContract):
    """Record from Najiz (ناجز) — court cases & litigation data."""

    source_slug = "najiz"
    priority = 60

    name_ar: str | None = None
    case_number: str | None = None
    case_type: str | None = None
    court: str | None = None
    case_status: str | None = None
    filing_date: date | None = None
    ruling_date: date | None = None
    amount_in_dispute: float | None = None
    counterparty_name: str | None = None

    def to_canonical(self) -> dict[str, Any]:
        return {
            "cr_number": self.cr_number,
            "name_ar": self.name_ar,
            "_case_number": self.case_number,
            "_case_type": self.case_type,
            "_court": self.court,
            "_case_status": self.case_status,
            "filing_date": self.filing_date.isoformat() if self.filing_date else None,
            "ruling_date": self.ruling_date.isoformat() if self.ruling_date else None,
            "amount_in_dispute": self.amount_in_dispute,
            "counterparty_name": self.counterparty_name,
        }
