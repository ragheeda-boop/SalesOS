"""End-to-end tests for the Data Fabric pipeline."""
from __future__ import annotations

import pytest

from runtime.data_fabric_runtime import DataFabricPipeline, PipelineRecord, Validator


@pytest.mark.asyncio
class TestPipelineStages:
    """Tests the pipeline normalizer + validator stages in isolation."""

    async def test_normalizer_remaps_balady_fields(self):
        pipeline = DataFabricPipeline(session_factory=None)
        record = {"company_name_ar": "شركة", "cr_number": "1234567890", "city_ar": "الرياض", "license_status": "active"}
        normalized = pipeline.normalizer.normalize("balady", record)
        assert normalized["name_ar"] == "شركة"
        assert normalized["cr_number"] == "1234567890"
        assert normalized["city"] == "الرياض"
        assert normalized["status"] == "active"

    async def test_normalizer_passes_unknown_fields(self):
        pipeline = DataFabricPipeline(session_factory=None)
        record = {"cr_number": "1234567890", "unknown_field": "hello"}
        normalized = pipeline.normalizer.normalize("balady", record)
        assert normalized["unknown_field"] == "hello"

    async def test_normalizer_taqeem_mapping(self):
        pipeline = DataFabricPipeline(session_factory=None)
        record = {"company_name": "تقييم", "cr_number": "1234567890", "employee_count": 50, "capital": 1000000}
        normalized = pipeline.normalizer.normalize("taqeem", record)
        assert normalized["name_ar"] == "تقييم"
        assert normalized["employees_count"] == 50
        assert normalized["capital"] == 1000000

    async def test_normalizer_najiz_mapping_prefixes_private(self):
        pipeline = DataFabricPipeline(session_factory=None)
        record = {"case_number": "1445/1", "case_type": "تجاري", "court": "المحكمة التجارية"}
        normalized = pipeline.normalizer.normalize("najiz", record)
        assert normalized["__case_number"] == "1445/1"
        assert normalized["__case_type"] == "تجاري"
        assert normalized["__court"] == "المحكمة التجارية"

    async def test_validator_rejects_missing_cr(self):
        pipeline = DataFabricPipeline(session_factory=None)
        errors = pipeline.validator.validate("balady", {"name_ar": "شركة"})
        assert "Missing cr_number" in errors

    async def test_validator_rejects_missing_name(self):
        pipeline = DataFabricPipeline(session_factory=None)
        errors = pipeline.validator.validate("balady", {"cr_number": "1234567890"})
        assert any("name" in e.lower() for e in errors)

    async def test_validator_passes_valid_record(self):
        pipeline = DataFabricPipeline(session_factory=None)
        errors = pipeline.validator.validate("balady", {"cr_number": "1234567890", "name_ar": "شركة"})
        assert errors == []

    async def test_validator_cr_format_rule(self):
        pipeline = DataFabricPipeline(session_factory=None)
        errors = pipeline.validator.validate("balady", {"cr_number": "12", "name_ar": "شركة"})
        assert any("format" in e.lower() for e in errors)

    async def test_run_batch_returns_summary(self):
        pipeline = DataFabricPipeline(session_factory=None)
        records = [
            {"cr_number": "1234567890", "company_name_ar": "شركة الأمل", "city_ar": "الرياض"},
            {"cr_number": "2234567890", "company_name_ar": "شركة النور", "city_ar": "جدة"},
        ]
        result = await pipeline.run_batch("balady", records, tenant_id="test-tenant")
        assert result["source"] == "balady"
        assert result["records_processed"] == 2
        assert result["records_invalid"] == 0

    async def test_run_batch_tracks_invalid_records(self):
        pipeline = DataFabricPipeline(session_factory=None)
        records = [
            {"cr_number": "1234567890", "name_ar": "شركة الأمل"},
            {"name_ar": "شركة بدون سجل"},  # missing cr
        ]
        result = await pipeline.run_batch("balady", records, tenant_id="test-tenant")
        assert result["records_invalid"] == 1
        # The second error is entity resolution failure (no DB session)
        validator_errors = [e for e in result["errors"] if e.get("stage") == "validator"]
        assert len(validator_errors) == 1

    async def test_pipeline_metrics_snapshot(self):
        pipeline = DataFabricPipeline(session_factory=None)
        pipeline.metrics.record_ingested()
        pipeline.metadata = None
        snapshot = pipeline.metrics.snapshot()
        assert snapshot["records_ingested"] == 1


@pytest.mark.asyncio
class TestScrapeAndIngestFlow:
    """Tests the scrape → pipeline integration flow with mock scrapers."""

    async def test_scraper_pipeline_integration(self):
        from runtime.data_fabric_runtime.scrapers.balady import BaladyScraper

        scraper = BaladyScraper(use_mock=True)
        scrape_result = await scraper.fetch_all()
        await scraper.close()

        assert scrape_result.total_fetched == 9
        assert scrape_result.source_slug == "balady"

        pipeline = DataFabricPipeline(session_factory=None)
        pipeline_result = await pipeline.run_batch(
            source_slug=scrape_result.source_slug,
            records=scrape_result.records,
            tenant_id="test-tenant",
        )

        assert pipeline_result["records_processed"] == 9
        assert pipeline_result["source"] == "balady"
        assert pipeline_result["records_invalid"] == 0

    async def test_multiple_sources_scrape_and_normalize(self):
        from runtime.data_fabric_runtime.scrapers.balady import BaladyScraper
        from runtime.data_fabric_runtime.scrapers.taqeem import TaqeemScraper
        from runtime.data_fabric_runtime.scrapers.ncnp import NcnpScraper

        pipeline = DataFabricPipeline(session_factory=None)
        sources = [
            ("balady", BaladyScraper(use_mock=True)),
            ("taqeem", TaqeemScraper(use_mock=True)),
            ("ncnp", NcnpScraper(use_mock=True)),
        ]

        for slug, scraper in sources:
            scrape_result = await scraper.fetch_all()
            await scraper.close()
            normalized = pipeline.normalizer.normalize(slug, scrape_result.records[0])
            assert normalized.get("name_ar") or normalized.get("__case_number"), f"{slug} should have name_ar or __case_number after normalization"
            assert normalized.get("cr_number"), f"{slug} should have cr_number after normalization"

    async def test_ingest_all_5_sources_through_scrape_and_ingest_endpoint(self):
        from runtime.data_fabric_runtime.router import SCRAPER_REGISTRY, _import_scrapers

        _import_scrapers()
        assert "balady" in SCRAPER_REGISTRY
        assert "taqeem" in SCRAPER_REGISTRY
        assert "ncnp" in SCRAPER_REGISTRY
        assert "najiz" in SCRAPER_REGISTRY
        assert "rega" in SCRAPER_REGISTRY

        pipeline = DataFabricPipeline(session_factory=None)

        for slug, cls in SCRAPER_REGISTRY.items():
            scraper = cls(use_mock=True)
            scrape_result = await scraper.fetch_all()
            await scraper.close()
            assert scrape_result.total_fetched == 9, f"{slug} should fetch 9 records"

            pipeline_result = await pipeline.run_batch(
                source_slug=slug,
                records=scrape_result.records,
                tenant_id="test-tenant",
            )
            assert pipeline_result["records_processed"] == 9
