"""Balady (بلدى) Data Contract — Saudi municipality licensing data.

Source: Ministry of Municipal & Rural Affairs
Data: Commercial licenses issued by municipalities
URL: https://www.balady.gov.sa
"""

from __future__ import annotations

from datetime import date
from typing import Any

from runtime.data_fabric_runtime.contracts.base import BaseSourceContract


class BaladyContract(BaseSourceContract):
    """Record from Balady (بلدى) — municipal commercial licenses."""

    source_slug = "balady"
    priority = 100

    name_ar: str
    name_en: str | None = None
    city: str
    postal_code: str | None = None
    activity_description: str | None = None
    incorporation_date: date | None = None
    expiry_date: date | None = None
    owner_name: str | None = None
    owner_nationality: str | None = None
    license_number: str | None = None

    def to_canonical(self) -> dict[str, Any]:
        return {
            "cr_number": self.cr_number,
            "name_ar": self.name_ar,
            "name_en": self.name_en,
            "city": self.city,
            "status": self.status,
            "postal_code": self.postal_code,
            "activity_description": self.activity_description,
            "incorporation_date": (
                self.incorporation_date.isoformat() if self.incorporation_date else None
            ),
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "_owner_name": self.owner_name if self.owner_name else None,
            "_owner_nationality": self.owner_nationality if self.owner_nationality else None,
            "license_number": self.license_number,
        }
