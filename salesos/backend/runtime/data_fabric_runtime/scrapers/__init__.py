"""Base Scraper — abstract foundation for all government data source scrapers."""

from __future__ import annotations

import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from httpx import AsyncClient, HTTPError, Limits, Timeout

from sdk.telemetry import StructuredLogger, get_tracer


@dataclass
class ScrapeResult:
    source_slug: str
    records: list[dict] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)
    duration_ms: float = 0.0
    total_pages: int = 0
    total_fetched: int = 0


class BaseScraper(ABC):
    """Abstract base scraper with HTTP client, retries, and rate limiting.

    Usage:
        class BaladyScraper(BaseScraper):
            @property
            def source_slug(self) -> str: return "balady"
            async def fetch_page(self, page: int) -> list[dict]: ...
    """

    BASE_URL: str = ""
    RATE_LIMIT_RPS: float = 2.0
    MAX_RETRIES: int = 3
    RETRY_DELAY_MS: int = 1000
    PAGE_SIZE: int = 100

    def __init__(self, logger: StructuredLogger | None = None):
        self._logger = logger or StructuredLogger(__name__)
        self._tracer = get_tracer(f"scraper.{self.source_slug}")
        self._last_request_time: float = 0.0
        self._client = AsyncClient(
            timeout=Timeout(15.0),
            limits=Limits(max_keepalive_connections=5, max_connections=10),
        )

    @property
    @abstractmethod
    def source_slug(self) -> str:
        ...

    async def fetch_all(self) -> ScrapeResult:
        """Fetch all available records from this source."""
        start = time.monotonic()
        all_records: list[dict] = []
        errors: list[dict] = []
        page = 1

        while True:
            try:
                records = await self._rate_limited_fetch(page)
                if not records:
                    break
                all_records.extend(records)
                page += 1
            except Exception as e:
                errors.append({"page": page, "error": str(e)})
                if self._logger:
                    self._logger.error(
                        "scraper.page_error",
                        source=self.source_slug,
                        page=page,
                        error=str(e),
                    )
                break

        duration = (time.monotonic() - start) * 1000
        return ScrapeResult(
            source_slug=self.source_slug,
            records=all_records,
            errors=errors,
            duration_ms=duration,
            total_pages=page - 1,
            total_fetched=len(all_records),
        )

    async def _rate_limited_fetch(self, page: int) -> list[dict]:
        """Fetch a page with rate limiting."""
        elapsed = time.monotonic() - self._last_request_time
        min_interval = 1.0 / self.RATE_LIMIT_RPS
        if elapsed < min_interval:
            await self._sleep(min_interval - elapsed)

        for attempt in range(self.MAX_RETRIES):
            try:
                data = await self.fetch_page(page)
                self._last_request_time = time.monotonic()
                return data
            except HTTPError as e:
                if attempt == self.MAX_RETRIES - 1:
                    raise
                delay = self.RETRY_DELAY_MS * (2**attempt) / 1000
                if self._logger:
                    self._logger.warning(
                        "scraper.retry",
                        source=self.source_slug,
                        page=page,
                        attempt=attempt + 1,
                        delay=delay,
                    )
                await self._sleep(delay)
        return []

    @abstractmethod
    async def fetch_page(self, page: int) -> list[dict]:
        """Fetch a single page of records from the source API."""

    @abstractmethod
    async def health_check(self) -> dict:
        """Check if the source API is reachable."""

    async def close(self) -> None:
        await self._client.aclose()

    @staticmethod
    async def _sleep(seconds: float) -> None:
        import asyncio
        await asyncio.sleep(seconds)
