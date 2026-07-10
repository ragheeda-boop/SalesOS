"""Data Fabric Runtime REST endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.dependencies import get_current_tenant_id

router = APIRouter()


class IngestRequest(BaseModel):
    records: list[dict] = Field(..., description="Array of records to ingest")
    source_slug: str = Field(..., description="Source identifier (balady, taqeem, ncnp, etc.)")


class ScrapeAndIngestRequest(BaseModel):
    source_slug: str = Field(..., description="Source identifier")
    use_mock: bool = Field(False, description="Use mock data instead of live API")
    api_key: str | None = Field(None, description="API key for live access")


SCRAPER_REGISTRY: dict[str, type] = {}


def register_scraper(slug: str, cls: type) -> None:
    SCRAPER_REGISTRY[slug] = cls


def _import_scrapers() -> None:
    """Lazy-import and register all scrapers."""
    if SCRAPER_REGISTRY:
        return
    from runtime.data_fabric_runtime.scrapers.balady import BaladyScraper
    from runtime.data_fabric_runtime.scrapers.taqeem import TaqeemScraper
    from runtime.data_fabric_runtime.scrapers.ncnp import NcnpScraper
    from runtime.data_fabric_runtime.scrapers.najiz import NajizScraper
    from runtime.data_fabric_runtime.scrapers.rega import RegaScraper
    register_scraper("balady", BaladyScraper)
    register_scraper("taqeem", TaqeemScraper)
    register_scraper("ncnp", NcnpScraper)
    register_scraper("najiz", NajizScraper)
    register_scraper("rega", RegaScraper)


@router.post("/data-fabric/ingest", status_code=201)
async def ingest_batch(
    body: IngestRequest,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
):
    pipeline = getattr(request.app.state, "data_fabric", None)
    if not pipeline:
        raise HTTPException(status_code=503, detail="Data Fabric Runtime not initialized")

    result = await pipeline.run_batch(
        source_slug=body.source_slug,
        records=body.records,
        tenant_id=tenant_id,
    )
    return result


@router.post("/data-fabric/ingest/{source_slug}", status_code=201)
async def ingest_from_source(
    source_slug: str,
    body: IngestRequest,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
):
    pipeline = getattr(request.app.state, "data_fabric", None)
    if not pipeline:
        raise HTTPException(status_code=503, detail="Data Fabric Runtime not initialized")

    result = await pipeline.run_batch(
        source_slug=source_slug,
        records=body.records,
        tenant_id=tenant_id,
    )
    return result


@router.post("/data-fabric/scrape-and-ingest", status_code=201)
async def scrape_and_ingest(
    body: ScrapeAndIngestRequest,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
):
    """Run a scraper end-to-end: fetch records, validate via contract, and ingest through pipeline."""
    pipeline = getattr(request.app.state, "data_fabric", None)
    if not pipeline:
        raise HTTPException(status_code=503, detail="Data Fabric Runtime not initialized")

    _import_scrapers()
    scraper_cls = SCRAPER_REGISTRY.get(body.source_slug)
    if not scraper_cls:
        raise HTTPException(status_code=400, detail=f"Unknown source slug: {body.source_slug}. Available: {list(SCRAPER_REGISTRY)}")

    scraper = scraper_cls(api_key=body.api_key, use_mock=body.use_mock)

    try:
        scrape_result = await scraper.fetch_all()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Scraper failed: {e}")
    finally:
        await scraper.close()

    if not scrape_result.records:
        return {
            "source_slug": body.source_slug,
            "scrape_result": {"total_fetched": 0, "errors": scrape_result.errors},
            "pipeline_result": None,
            "message": "No records fetched",
        }

    pipeline_result = await pipeline.run_batch(
        source_slug=body.source_slug,
        records=scrape_result.records,
        tenant_id=tenant_id,
    )

    return {
        "source_slug": body.source_slug,
        "scrape_result": {
            "total_fetched": scrape_result.total_fetched,
            "total_pages": scrape_result.total_pages,
            "duration_ms": scrape_result.duration_ms,
            "errors": scrape_result.errors,
        },
        "pipeline_result": pipeline_result,
    }


@router.get("/data-fabric/metrics")
async def data_fabric_metrics(request: Request, tenant_id: str = Depends(get_current_tenant_id)):
    pipeline = getattr(request.app.state, "data_fabric", None)
    if not pipeline:
        return {"status": "not_initialized"}
    return pipeline.metrics.snapshot()
