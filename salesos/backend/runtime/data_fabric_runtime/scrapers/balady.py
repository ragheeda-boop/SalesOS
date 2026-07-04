"""Balady Scraper — fetches municipal commercial license data from بلدى API.

This is an abstract implementation. In production, this would connect
to the actual Balady API endpoint. For development/testing, it can use
mock data.
"""

from __future__ import annotations

from typing import Any

from runtime.data_fabric_runtime.scrapers import BaseScraper, ScrapeResult


class BaladyScraper(BaseScraper):
    """Scraper for Balady (بلدى) municipal commercial license data.

    In production, set BALADY_API_KEY and BALADY_BASE_URL env vars.
    For development, use_mock=True fetches sample data.
    """

    BASE_URL = "https://api.balady.gov.sa/v1"
    RATE_LIMIT_RPS = 3.0
    PAGE_SIZE = 50

    def __init__(
        self,
        api_key: str | None = None,
        use_mock: bool = False,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self._api_key = api_key
        self._use_mock = use_mock

    @property
    def source_slug(self) -> str:
        return "balady"

    async def fetch_page(self, page: int) -> list[dict]:
        """Fetch a page of license records from Balady API."""
        if self._use_mock:
            return self._mock_page(page)

        response = await self._client.get(
            f"{self.BASE_URL}/licenses",
            params={"page": page, "page_size": self.PAGE_SIZE},
            headers={"Authorization": f"Bearer {self._api_key}"},
        )
        response.raise_for_status()
        data = response.json()
        return data.get("records", data.get("data", []))

    async def fetch_by_cr(self, cr_number: str) -> dict | None:
        """Lookup a specific company by CR number."""
        if self._use_mock:
            return self._mock_by_cr(cr_number)

        response = await self._client.get(
            f"{self.BASE_URL}/licenses/{cr_number}",
            headers={"Authorization": f"Bearer {self._api_key}"},
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    async def health_check(self) -> dict:
        return {
            "source": "balady",
            "reachable": not self._use_mock,
            "mode": "mock" if self._use_mock else "live",
        }

    async def close(self) -> None:
        await self._client.aclose()

    # ---- Mock data for development ----

    def _mock_page(self, page: int) -> list[dict]:
        if page > 3:
            return []
        return [
            {
                "cr_number": f"{1000000000 + (page - 1) * self.PAGE_SIZE + i:010d}",
                "company_name_ar": f"شركة تجربة رقم {(page - 1) * self.PAGE_SIZE + i + 1}",
                "company_name_en": f"Test Company {(page - 1) * self.PAGE_SIZE + i + 1}",
                "city_ar": "الرياض",
                "city_en": "Riyadh",
                "postal_code": f"12{i:03d}",
                "activity": "تجارة عامة",
                "license_status": "active",
                "issue_date": "2020-01-15",
                "expiry_date": "2025-01-15",
                "owner_name": f"مالك {i + 1}",
                "owner_nationality": "سعودي",
            }
            for i in range(3)
        ]

    def _mock_by_cr(self, cr_number: str) -> dict | None:
        return {
            "cr_number": cr_number,
            "company_name_ar": "شركة تجربة",
            "company_name_en": "Test Company",
            "city_ar": "الرياض",
            "city_en": "Riyadh",
            "activity": "تجارة عامة",
            "license_status": "active",
            "issue_date": "2020-01-15",
            "expiry_date": "2025-01-15",
        }
