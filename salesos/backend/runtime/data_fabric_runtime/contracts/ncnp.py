"""NCNP Data Contract — National Commercial Notification Platform (المنصة الوطنية للإشعارات التجارية).

Source: Ministry of Commerce (MC)
Data: Company establishment notifications, employee counts
"""

from __future__ import annotations

from datetime import date
from typing import Any



from runtime.data_fabric_runtime.contracts.base import BaseSourceContract


class NcnpContract(BaseSourceContract):
    """Record from NCNP — National Commercial Notification Platform."""

    source_slug = "ncnp"
    priority = 90

    name_ar: str | None = None
    city: str | None = None
    employees_total: int | None = None
    establishment_date: date | None = None
    notification_type: str | None = None
    capital: float | None = None
    activity: str | None = None

    def to_canonical(self) -> dict[str, Any]:
        return {
            "cr_number": self.cr_number,
            "name_ar": self.name_ar,
            "city": self.city,
            "status": self.status,
            "employees_count": self.employees_total,
            "incorporation_date": (
                self.establishment_date.isoformat() if self.establishment_date else None
            ),
            "notification_type": self.notification_type,
            "capital": self.capital,
            "activity_description": self.activity,
        }
