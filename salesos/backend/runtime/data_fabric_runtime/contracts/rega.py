"""REGA Data Contract — Real Estate General Authority (الهيئة العامة للعقار).

Source: Real Estate General Authority (REGA)
Data: Real estate licenses, property records, broker info
URL: https://rega.gov.sa
"""

from __future__ import annotations

from datetime import date
from typing import Any



from runtime.data_fabric_runtime.contracts.base import BaseSourceContract


class RegaContract(BaseSourceContract):
    """Record from REGA — Real Estate General Authority data."""

    source_slug = "rega"
    priority = 70

    name_ar: str | None = None
    cr_type: str | None = None
    license_number: str | None = None
    license_issue_date: date | None = None
    license_expiry_date: date | None = None
    city: str | None = None
    real_estate_type: str | None = None
    broker_name: str | None = None

    def to_canonical(self) -> dict[str, Any]:
        return {
            "cr_number": self.cr_number,
            "name_ar": self.name_ar,
            "cr_type": self.cr_type,
            "status": self.status,
            "license_number": self.license_number,
            "license_issue_date": (
                self.license_issue_date.isoformat() if self.license_issue_date else None
            ),
            "license_expiry_date": (
                self.license_expiry_date.isoformat() if self.license_expiry_date else None
            ),
            "city": self.city,
            "real_estate_type": self.real_estate_type,
            "broker_name": self.broker_name,
        }
