"""Taqeem (تقييم) Data Contract — Saudi credit rating & company evaluation data.

Source: Saudi Credit Bureau (SIMAH) / Taqeem
Data: Credit ratings, employee counts, capital info
"""

from __future__ import annotations

from datetime import date
from typing import Any



from runtime.data_fabric_runtime.contracts.base import BaseSourceContract


class TaqeemContract(BaseSourceContract):
    """Record from Taqeem (تقييم) — credit rating & evaluation."""

    source_slug = "taqeem"
    priority = 80

    name_ar: str | None = None
    city: str | None = None
    employees_count: int | None = None
    capital: float | None = None
    incorporation_date: date | None = None
    credit_rating: str | None = None
    revenue_range: str | None = None

    def to_canonical(self) -> dict[str, Any]:
        return {
            "cr_number": self.cr_number,
            "name_ar": self.name_ar,
            "city": self.city,
            "status": self.status,
            "employees_count": self.employees_count,
            "capital": self.capital,
            "incorporation_date": (
                self.incorporation_date.isoformat() if self.incorporation_date else None
            ),
            "credit_rating": self.credit_rating,
            "revenue_range": self.revenue_range,
        }
