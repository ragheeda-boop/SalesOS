"""Background task definitions for SalesOS workers."""

import asyncio
import logging
from typing import Any

from app.celery_app import celery_app
from app.config import settings

logger = logging.getLogger("salesos.tasks")


def _run_async(coro):
    """Bridge sync Celery tasks to async services via a fresh event loop."""
    return asyncio.run(coro)


# ── Helpers ─────────────────────────────────────────────────────


async def _get_entity_tenant(entity_id: str, entity_type: str) -> str | None:
    """Look up the tenant_id for an entity from PostgreSQL."""
    from sqlalchemy import text
    from app.database import async_session

    table_map = {
        "company": "companies",
        "person": "contacts",
        "contact": "contacts",
    }
    table = table_map.get(entity_type.lower(), "companies")
    async with async_session() as session:
        result = await session.execute(
            text(f"SELECT tenant_id FROM {table} WHERE id = :id LIMIT 1"),
            {"id": entity_id},
        )
        row = result.mappings().one_or_none()
        return row["tenant_id"] if row else None


async def _load_company_record(company_id: str) -> dict[str, Any] | None:
    """Load a company row as a plain dict."""
    from sqlalchemy import text
    from app.database import async_session

    async with async_session() as session:
        result = await session.execute(
            text("SELECT * FROM companies WHERE id = :id LIMIT 1"),
            {"id": company_id},
        )
        row = result.mappings().one_or_none()
        return dict(row) if row else None


# ── Placeholder implementations ─────────────────────────────────


def _sync_to_graph(entity_id: str, entity_type: str):
    """Sync entity to Neo4j knowledge graph (falls back to SQL if Neo4j unavailable)."""
    from app.config import settings
    from app.database import async_session
    from runtime.knowledge_graph_runtime import KnowledgeGraphEngine

    async def _do_sync():
        tenant_id = await _get_entity_tenant(entity_id, entity_type)
        if not tenant_id:
            logger.warning("Graph sync skipped: no tenant found for %s %s", entity_type, entity_id)
            return

        engine = KnowledgeGraphEngine(
            session_factory=async_session,
            neo4j_uri=settings.neo4j_uri,
            neo4j_user=settings.neo4j_user,
            neo4j_password=settings.neo4j_password,
            logger=logger,
        )
        try:
            if entity_type.lower() == "company":
                record = await _load_company_record(entity_id)
                if record:
                    await engine.populate_from_golden_record(record, tenant_id)
                    logger.info("Graph sync complete for company %s", entity_id)
                else:
                    logger.warning("Graph sync skipped: company %s not found", entity_id)
            else:
                logger.debug("Graph sync: entity type %s not yet supported for single-entity sync", entity_type)
        finally:
            await engine.close()

    _run_async(_do_sync())


def _generate_embedding(entity_id: str, entity_type: str):
    """Generate vector embedding for entity and store in companies.embedding + vector store."""
    from sqlalchemy import text
    from app.config import settings
    from app.database import async_session
    from sdk.vector import OpenAIEmbeddingService

    async def _do_embed():
        if not settings.openai_api_key:
            logger.debug("Embedding skipped: OPENAI_API_KEY not set")
            return

        tenant_id = await _get_entity_tenant(entity_id, entity_type)
        if not tenant_id:
            logger.warning("Embedding skipped: no tenant found for %s %s", entity_type, entity_id)
            return

        async with async_session() as session:
            # Load entity text fields for embedding
            table = "companies" if entity_type.lower() == "company" else "contacts"
            result = await session.execute(
                text(f"SELECT * FROM {table} WHERE id = :id LIMIT 1"),
                {"id": entity_id},
            )
            row = result.mappings().one_or_none()
            if not row:
                logger.warning("Embedding skipped: %s %s not found", entity_type, entity_id)
                return

            row_dict = dict(row)
            # Build embedding text from available fields
            text_parts = [
                row_dict.get("name_ar", ""),
                row_dict.get("name_en", ""),
                row_dict.get("activity_description", ""),
                row_dict.get("city", ""),
                row_dict.get("industry", ""),
                row_dict.get("position", ""),
                row_dict.get("department", ""),
            ]
            text_to_embed = " ".join(p for p in text_parts if p)
            if not text_to_embed.strip():
                logger.debug("Embedding skipped: no text content for %s %s", entity_type, entity_id)
                return

            svc = OpenAIEmbeddingService(api_key=settings.openai_api_key)
            embedding = await svc.embed(text_to_embed)

            # Store in entity table
            await session.execute(
                text(f"UPDATE {table} SET embedding = :emb WHERE id = :id"),
                {"emb": embedding, "id": entity_id},
            )
            await session.commit()
            logger.info("Embedding generated and stored for %s %s", entity_type, entity_id)

    _run_async(_do_embed())


async def _parallel_enrich(company_id: str, cr_number: str):
    """Run scraping and feature recomputation in parallel."""
    await asyncio.gather(
        _do_scrape(company_id, cr_number),
        _do_recompute(company_id),
        return_exceptions=True,
    )


async def _do_scrape(company_id: str, cr_number: str):
    """Enrich company by scraping Balady and Taqeem APIs in parallel."""
    from runtime.data_fabric_runtime.scrapers.balady import BaladyScraper
    from runtime.data_fabric_runtime.scrapers.taqeem import TaqeemScraper

    scrapers = [
        ("balady", BaladyScraper(use_mock=False)),
        ("taqeem", TaqeemScraper(use_mock=False)),
    ]

    async def _scrape_one(slug: str, scraper):
        try:
            async with asyncio.timeout(10):
                result = await scraper.fetch_all()
                if result.records:
                    logger.info("Scraped %d records from %s for company %s", len(result.records), slug, company_id)
                else:
                    logger.debug("No records from %s for company %s (errors: %s)", slug, company_id, result.errors)
        except TimeoutError:
            logger.warning("Scraper %s timed out for company %s", slug, company_id)
        except Exception as e:
            logger.warning("Scraper %s failed for company %s: %s", slug, company_id, e)
        finally:
            await scraper.close()

    await asyncio.gather(*[_scrape_one(slug, s) for slug, s in scrapers], return_exceptions=True)


async def _do_recompute(company_id: str):
    """Recompute all feature scores for a company via the Feature Store."""
    from app.database import async_session
    from runtime.event_runtime import EventRuntime
    from runtime.feature_store import FeatureStore
    from runtime.feature_store.features import (
        ExpansionScoreComputer,
        FundingScoreComputer,
        GrowthScoreComputer,
        HiringScoreComputer,
        IcpComputer,
        IntentScoreComputer,
        RevenueScoreComputer,
    )

    tenant_id = await _get_entity_tenant(company_id, "company")
    if not tenant_id:
        logger.warning("Feature recompute skipped: no tenant found for company %s", company_id)
        return

    event_runtime = EventRuntime()
    computers = [
        IcpComputer(),
        FundingScoreComputer(),
        HiringScoreComputer(),
        GrowthScoreComputer(),
        IntentScoreComputer(),
        ExpansionScoreComputer(),
        RevenueScoreComputer(),
    ]
    store = FeatureStore(
        session_factory=async_session,
        event_runtime=event_runtime,
        computers=computers,
        logger=logger,
    )
    results = await store.recompute(company_id, tenant_id)
    feature_scores = {name: r.score for name, r in results.items()}
    logger.info("Feature recompute complete for company %s: %s", company_id, feature_scores)


# ── Celery Tasks ────────────────────────────────────────────────


@celery_app.task(bind=True, max_retries=settings.celery_max_retries, default_retry_delay=settings.celery_default_retry_delay)
def ping(self):
    """Simple heartbeat task to verify worker health."""
    logger.info("Worker ping OK")
    return "pong"


@celery_app.task(bind=True, max_retries=settings.celery_max_retries, default_retry_delay=settings.celery_process_entity_delay)
def process_entity(self, entity_id: str, entity_type: str):
    """Background entity processing (vector embedding, graph sync, enrichment)."""
    logger.info("Processing entity %s (type=%s)", entity_id, entity_type)

    try:
        _sync_to_graph(entity_id, entity_type)
        _generate_embedding(entity_id, entity_type)
    except Exception as exc:
        logger.error("Failed to process entity %s: %s", entity_id, exc)
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=settings.celery_max_retries, default_retry_delay=settings.celery_index_delay)
def index_for_search(self, entity_id: str, entity_type: str, payload: dict):
    """Index an entity in Meilisearch."""
    import httpx

    meili_url = settings.meili_url
    api_key = settings.meili_master_key

    if not api_key:
        logger.warning("Meilisearch indexing skipped: MEILI_MASTER_KEY not set")
        return

    try:
        index_name = entity_type.lower()
        with httpx.Client() as client:
            resp = client.post(
                f"{meili_url}/indexes/{index_name}/documents",
                json=[{"id": entity_id, **payload}],
                headers={"Authorization": f"Bearer {api_key}"},
            )
            resp.raise_for_status()
            logger.info("Indexed %s %s in Meilisearch", entity_type, entity_id)
    except Exception as exc:
        logger.error("Failed to index %s %s: %s", entity_type, entity_id, exc)
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=settings.celery_max_retries, default_retry_delay=settings.celery_enrich_delay)
def enrich_company(self, company_id: str, cr_number: str):
    """Background company enrichment pipeline.

    Scraping and feature recomputation run in parallel since they are independent.
    """
    logger.info("Enriching company %s (CR: %s)", company_id, cr_number)
    try:
        _run_async(_parallel_enrich(company_id, cr_number))
    except Exception as exc:
        logger.error("Failed to enrich company %s: %s", company_id, exc)
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=settings.celery_max_retries - 1, default_retry_delay=settings.celery_sync_notion_delay)
def sync_notion_database(self, database_id: str, tenant_id: str):
    """Sync a Notion database into the pipeline."""
    logger.info("Syncing Notion database %s for tenant %s", database_id, tenant_id)
    from app.config import settings
    from app.modules.notion_sync.service import NotionSyncService
    from app.database import async_session

    async def _do_sync():
        async with async_session() as session:
            svc = NotionSyncService(db=session)
            await svc.import_companies(database_id, settings.notion_token, tenant_id)

    try:
        _run_async(_do_sync())
        logger.info("Notion sync complete for %s", database_id)
    except Exception as exc:
        logger.error("Notion sync failed for %s: %s", database_id, exc)
        raise self.retry(exc=exc)
