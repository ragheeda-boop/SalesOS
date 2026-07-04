"""Tests for all government data source scrapers (mock mode)."""

from __future__ import annotations

import pytest

from runtime.data_fabric_runtime.scrapers.balady import BaladyScraper
from runtime.data_fabric_runtime.scrapers.taqeem import TaqeemScraper
from runtime.data_fabric_runtime.scrapers.ncnp import NcnpScraper
from runtime.data_fabric_runtime.scrapers.najiz import NajizScraper
from runtime.data_fabric_runtime.scrapers.rega import RegaScraper


class TestBaladyScraper:
    @pytest.fixture
    def scraper(self):
        return BaladyScraper(use_mock=True)

    @pytest.mark.asyncio
    async def test_fetch_all_returns_records(self, scraper):
        result = await scraper.fetch_all()
        assert result.total_fetched > 0
        assert result.source_slug == "balady"

    @pytest.mark.asyncio
    async def test_fetch_page_returns_three_records(self, scraper):
        records = await scraper.fetch_page(1)
        assert len(records) == 3
        assert records[0]["cr_number"] == "1000000000"
        assert "company_name_ar" in records[0]

    @pytest.mark.asyncio
    async def test_fetch_page_beyond_limit_returns_empty(self, scraper):
        records = await scraper.fetch_page(99)
        assert records == []

    @pytest.mark.asyncio
    async def test_fetch_by_cr_returns_record(self, scraper):
        record = await scraper.fetch_by_cr("1234567890")
        assert record is not None
        assert record["cr_number"] == "1234567890"

    @pytest.mark.asyncio
    async def test_health_check_returns_mock_mode(self, scraper):
        health = await scraper.health_check()
        assert health["source"] == "balady"
        assert health["mode"] == "mock"

    @pytest.mark.asyncio
    async def test_scrape_result_structure(self, scraper):
        result = await scraper.fetch_all()
        assert result.total_pages == 3
        assert result.total_fetched == 9
        assert result.duration_ms > 0
        assert len(result.errors) == 0


class TestTaqeemScraper:
    @pytest.fixture
    def scraper(self):
        return TaqeemScraper(use_mock=True)

    @pytest.mark.asyncio
    async def test_fetch_all_returns_records(self, scraper):
        result = await scraper.fetch_all()
        assert result.total_fetched > 0
        assert result.source_slug == "taqeem"

    @pytest.mark.asyncio
    async def test_fetch_page_has_credit_rating(self, scraper):
        records = await scraper.fetch_page(1)
        assert len(records) == 3
        assert records[0]["credit_rating"] in scraper.RATINGS
        assert records[0]["revenue_range"] in scraper.REVENUE_RANGES

    @pytest.mark.asyncio
    async def test_fetch_by_cr_returns_record(self, scraper):
        record = await scraper.fetch_by_cr("1234567890")
        assert record is not None
        assert record["employees_count"] == 25

    @pytest.mark.asyncio
    async def test_health_check(self, scraper):
        health = await scraper.health_check()
        assert health["source"] == "taqeem"
        assert health["mode"] == "mock"

    @pytest.mark.asyncio
    async def test_fetch_all_count(self, scraper):
        result = await scraper.fetch_all()
        assert result.total_fetched == 9
        assert result.total_pages == 3


class TestNcnpScraper:
    @pytest.fixture
    def scraper(self):
        return NcnpScraper(use_mock=True)

    @pytest.mark.asyncio
    async def test_fetch_all_returns_records(self, scraper):
        result = await scraper.fetch_all()
        assert result.total_fetched > 0
        assert result.source_slug == "ncnp"

    @pytest.mark.asyncio
    async def test_fetch_page_has_notification_type(self, scraper):
        records = await scraper.fetch_page(1)
        assert len(records) == 3
        assert records[0]["notification_type"] in scraper.NOTIFICATION_TYPES
        assert records[0]["activity"] in scraper.ACTIVITIES

    @pytest.mark.asyncio
    async def test_fetch_by_cr_returns_record(self, scraper):
        record = await scraper.fetch_by_cr("1234567890")
        assert record is not None
        assert record["notification_type"] == "تأسيس"

    @pytest.mark.asyncio
    async def test_health_check(self, scraper):
        health = await scraper.health_check()
        assert health["source"] == "ncnp"
        assert health["mode"] == "mock"

    @pytest.mark.asyncio
    async def test_fetch_all_count(self, scraper):
        result = await scraper.fetch_all()
        assert result.total_fetched == 9
        assert result.total_pages == 3


class TestNajizScraper:
    @pytest.fixture
    def scraper(self):
        return NajizScraper(use_mock=True)

    @pytest.mark.asyncio
    async def test_fetch_all_returns_records(self, scraper):
        result = await scraper.fetch_all()
        assert result.total_fetched > 0
        assert result.source_slug == "najiz"

    @pytest.mark.asyncio
    async def test_fetch_page_has_case_data(self, scraper):
        records = await scraper.fetch_page(1)
        assert len(records) == 3
        assert records[0]["case_number"] == "1445/1/1"
        assert records[0]["case_type"] in scraper.CASE_TYPES
        assert records[0]["court"] in scraper.COURTS
        assert records[0]["case_status"] in scraper.CASE_STATUSES

    @pytest.mark.asyncio
    async def test_fetch_by_cr_returns_record(self, scraper):
        record = await scraper.fetch_by_cr("1234567890")
        assert record is not None
        assert record["case_number"] == "1445/1/1"
        assert record["amount_in_dispute"] == 500000

    @pytest.mark.asyncio
    async def test_health_check(self, scraper):
        health = await scraper.health_check()
        assert health["source"] == "najiz"
        assert health["mode"] == "mock"

    @pytest.mark.asyncio
    async def test_fetch_all_count(self, scraper):
        result = await scraper.fetch_all()
        assert result.total_fetched == 9
        assert result.total_pages == 3


class TestRegaScraper:
    @pytest.fixture
    def scraper(self):
        return RegaScraper(use_mock=True)

    @pytest.mark.asyncio
    async def test_fetch_all_returns_records(self, scraper):
        result = await scraper.fetch_all()
        assert result.total_fetched > 0
        assert result.source_slug == "rega"

    @pytest.mark.asyncio
    async def test_fetch_page_has_license_data(self, scraper):
        records = await scraper.fetch_page(1)
        assert len(records) == 3
        assert records[0]["license_number"] == "LIC-100000"
        assert records[0]["cr_type"] in scraper.CR_TYPES
        assert records[0]["real_estate_type"] in scraper.REAL_ESTATE_TYPES

    @pytest.mark.asyncio
    async def test_fetch_by_cr_returns_record(self, scraper):
        record = await scraper.fetch_by_cr("1234567890")
        assert record is not None
        assert record["license_number"] == "LIC-100001"
        assert record["broker_name"] == "وسيط رئيسي"

    @pytest.mark.asyncio
    async def test_health_check(self, scraper):
        health = await scraper.health_check()
        assert health["source"] == "rega"
        assert health["mode"] == "mock"

    @pytest.mark.asyncio
    async def test_fetch_all_count(self, scraper):
        result = await scraper.fetch_all()
        assert result.total_fetched == 9
        assert result.total_pages == 3
