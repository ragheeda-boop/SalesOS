"""NCNP Scraper — fetches commercial notification data from إعلانات API."""

from __future__ import annotations

from typing import Any

from runtime.data_fabric_runtime.scrapers import BaseScraper, ScrapeResult


class NcnpScraper(BaseScraper):
    """Scraper for NCNP (إعلانات) commercial notification platform.

    In production, set NCNP_API_KEY and NCNP_BASE_URL env vars.
    For development, use_mock=True fetches sample data.
    """

    BASE_URL = "https://api.ncnp.gov.sa/v1"
    RATE_LIMIT_RPS = 2.5
    PAGE_SIZE = 50

    NOTIFICATION_TYPES = ["تأسيس", "تعديل", "تجديد", "إلغاء"]
    ACTIVITIES = ["تجارة عامة", "مقاولات", "نقل", "صناعة", "خدمات"]

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
        return "ncnp"

    async def fetch_page(self, page: int) -> list[dict]:
        if self._use_mock:
            return self._mock_page(page)

        response = await self._client.get(
            f"{self.BASE_URL}/notifications",
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
            f"{self.BASE_URL}/notifications/{cr_number}",
            headers={"Authorization": f"Bearer {self._api_key}"},
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    async def health_check(self) -> dict:
        return {
            "source": "ncnp",
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
                "establishment_name": f"منشأة إعلان {(page - 1) * self.PAGE_SIZE + i + 1}",
                "city_ar": "الدمام" if i == 2 else "الرياض",
                "city_en": "Dammam" if i == 2 else "Riyadh",
                "employees_total": 5 + i * 10,
                "establishment_date": "2021-06-15",
                "notification_type": self.NOTIFICATION_TYPES[i % len(self.NOTIFICATION_TYPES)],
                "capital": 300000 + i * 50000,
                "activity": self.ACTIVITIES[i % len(self.ACTIVITIES)],
            }
            for i in range(3)
        ]

    def _mock_by_cr(self, cr_number: str) -> dict | None:
        return {
            "cr_number": cr_number,
            "establishment_name": "منشأة إعلان",
            "city_ar": "الرياض",
            "city_en": "Riyadh",
            "employees_total": 15,
            "establishment_date": "2021-06-15",
            "notification_type": "تأسيس",
            "capital": 500000,
            "activity": "تجارة عامة",
        }
