"""Taqeem Scraper — fetches credit/evaluation data from تقييم API."""

from __future__ import annotations

from typing import Any

from runtime.data_fabric_runtime.scrapers import BaseScraper, ScrapeResult


class TaqeemScraper(BaseScraper):
    """Scraper for Taqeem (تقييم) credit bureau data.

    In production, set TAQEEM_API_KEY and TAQEEM_BASE_URL env vars.
    For development, use_mock=True fetches sample data.
    """

    BASE_URL = "https://api.taqeem.gov.sa/v1"
    RATE_LIMIT_RPS = 2.0
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
        return "taqeem"

    async def fetch_page(self, page: int) -> list[dict]:
        if self._use_mock:
            return self._mock_page(page)

        response = await self._client.get(
            f"{self.BASE_URL}/evaluations",
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
            f"{self.BASE_URL}/evaluations/{cr_number}",
            headers={"Authorization": f"Bearer {self._api_key}"},
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    async def health_check(self) -> dict:
        return {
            "source": "taqeem",
            "reachable": not self._use_mock,
            "mode": "mock" if self._use_mock else "live",
        }

    async def close(self) -> None:
        await self._client.aclose()

    RATINGS = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC", "D"]
    REVENUE_RANGES = ["<10M", "10M-50M", "50M-100M", ">100M"]

    def _mock_page(self, page: int) -> list[dict]:
        if page > 3:
            return []
        return [
            {
                "cr_number": f"{1000000000 + (page - 1) * self.PAGE_SIZE + i:010d}",
                "company_name_ar": f"مؤسسة تقييم {(page - 1) * self.PAGE_SIZE + i + 1}",
                "company_name_en": f"Taqeem Entity {(page - 1) * self.PAGE_SIZE + i + 1}",
                "city_ar": "جدة" if i % 2 == 0 else "الرياض",
                "city_en": "Jeddah" if i % 2 == 0 else "Riyadh",
                "employees_count": 10 + i * 5,
                "capital": 500000 + i * 100000,
                "incorporation_date": "2019-03-01",
                "credit_rating": self.RATINGS[i % len(self.RATINGS)],
                "revenue_range": self.REVENUE_RANGES[i % len(self.REVENUE_RANGES)],
            }
            for i in range(3)
        ]

    def _mock_by_cr(self, cr_number: str) -> dict | None:
        return {
            "cr_number": cr_number,
            "company_name_ar": "مؤسسة تقييم",
            "company_name_en": "Taqeem Entity",
            "city_ar": "الرياض",
            "city_en": "Riyadh",
            "employees_count": 25,
            "capital": 1000000,
            "incorporation_date": "2019-03-01",
            "credit_rating": "A",
            "revenue_range": "50M-100M",
        }
