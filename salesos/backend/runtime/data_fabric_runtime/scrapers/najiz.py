"""Najiz Scraper — fetches litigation/court case data from ناجز API."""

from __future__ import annotations

from typing import Any

from runtime.data_fabric_runtime.scrapers import BaseScraper, ScrapeResult


class NajizScraper(BaseScraper):
    """Scraper for Najiz (ناجز) — Saudi Ministry of Justice litigation data.

    In production, set NAJIZ_API_KEY and NAJIZ_BASE_URL env vars.
    For development, use_mock=True fetches sample data.
    """

    BASE_URL = "https://api.najiz.gov.sa/v1"
    RATE_LIMIT_RPS = 2.0
    PAGE_SIZE = 50

    CASE_TYPES = ["تجاري", "مدني", "إداري", "عمالي"]
    COURTS = ["ديوان المظالم", "المحكمة التجارية", "المحكمة العامة", "محكمة الاستئناف"]
    CASE_STATUSES = ["منظورة", "مقيدة", "محكومة", "مؤيدة"]

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
        return "najiz"

    async def fetch_page(self, page: int) -> list[dict]:
        if self._use_mock:
            return self._mock_page(page)

        response = await self._client.get(
            f"{self.BASE_URL}/cases",
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
            f"{self.BASE_URL}/cases/{cr_number}",
            headers={"Authorization": f"Bearer {self._api_key}"},
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    async def health_check(self) -> dict:
        return {
            "source": "najiz",
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
                "company_name_ar": f"شركة قانون {(page - 1) * self.PAGE_SIZE + i + 1}",
                "case_number": f"1445/{page}/{i + 1}",
                "case_type": self.CASE_TYPES[i % len(self.CASE_TYPES)],
                "court": self.COURTS[i % len(self.COURTS)],
                "case_status": self.CASE_STATUSES[i % len(self.CASE_STATUSES)],
                "filing_date": "2024-01-15",
                "ruling_date": "2024-06-30",
                "amount_in_dispute": 500000 + i * 100000,
                "counterparty_name": f"الطرف المقابل {i + 1}",
            }
            for i in range(3)
        ]

    def _mock_by_cr(self, cr_number: str) -> dict | None:
        return {
            "cr_number": cr_number,
            "company_name_ar": "شركة قانون",
            "case_number": "1445/1/1",
            "case_type": "تجاري",
            "court": "المحكمة التجارية",
            "case_status": "منظورة",
            "filing_date": "2024-01-15",
            "ruling_date": "2024-06-30",
            "amount_in_dispute": 500000,
            "counterparty_name": "الطرف المقابل",
        }
