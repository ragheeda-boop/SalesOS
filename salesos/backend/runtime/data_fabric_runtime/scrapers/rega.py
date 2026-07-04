"""REGA Scraper — fetches real estate license data from الهيئة العامة للعقار API."""

from __future__ import annotations

from typing import Any

from runtime.data_fabric_runtime.scrapers import BaseScraper, ScrapeResult


class RegaScraper(BaseScraper):
    """Scraper for REGA — Real Estate General Authority (الهيئة العامة للعقار).

    In production, set REGA_API_KEY and REGA_BASE_URL env vars.
    For development, use_mock=True fetches sample data.
    """

    BASE_URL = "https://api.rega.gov.sa/v1"
    RATE_LIMIT_RPS = 2.5
    PAGE_SIZE = 50

    CR_TYPES = ["وسيط عقاري", "مطور عقاري", "مثمن عقاري", "مؤجر"]
    REAL_ESTATE_TYPES = ["سكني", "تجاري", "صناعي", "زراعي"]

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
        return "rega"

    async def fetch_page(self, page: int) -> list[dict]:
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
            "source": "rega",
            "reachable": not self._use_mock,
            "mode": "mock" if self._use_mock else "live",
        }

    async def close(self) -> None:
        await self._client.aclose()

    def _mock_page(self, page: int) -> list[dict]:
        if page > 3:
            return []
        return [
            {
                "cr_number": f"{1000000000 + (page - 1) * self.PAGE_SIZE + i:010d}",
                "company_name_ar": f"مؤسسة عقارية {(page - 1) * self.PAGE_SIZE + i + 1}",
                "cr_type": self.CR_TYPES[i % len(self.CR_TYPES)],
                "license_number": f"LIC-{100000 + (page - 1) * self.PAGE_SIZE + i}",
                "license_issue_date": "2022-01-01",
                "license_expiry_date": "2025-01-01",
                "city_ar": "الرياض" if i % 2 == 0 else "جدة",
                "city_en": "Riyadh" if i % 2 == 0 else "Jeddah",
                "real_estate_type": self.REAL_ESTATE_TYPES[i % len(self.REAL_ESTATE_TYPES)],
                "broker_name": f"وسيط {i + 1}",
            }
            for i in range(3)
        ]

    def _mock_by_cr(self, cr_number: str) -> dict | None:
        return {
            "cr_number": cr_number,
            "company_name_ar": "مؤسسة عقارية",
            "cr_type": "وسيط عقاري",
            "license_number": "LIC-100001",
            "license_issue_date": "2022-01-01",
            "license_expiry_date": "2025-01-01",
            "city_ar": "الرياض",
            "city_en": "Riyadh",
            "real_estate_type": "سكني",
            "broker_name": "وسيط رئيسي",
        }
