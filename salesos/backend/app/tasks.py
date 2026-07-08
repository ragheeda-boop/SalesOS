"""Background task definitions for SalesOS workers."""

import logging

from app.celery_app import celery_app

logger = logging.getLogger("salesos.tasks")


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def ping(self):
    """Simple heartbeat task to verify worker health."""
    logger.info("Worker ping OK")
    return "pong"


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def process_entity(self, entity_id: str, entity_type: str):
    """Background entity processing (vector embedding, graph sync, enrichment)."""
    from app.config import settings

    logger.info("Processing entity %s (type=%s)", entity_id, entity_type)

    try:
        _sync_to_graph(entity_id, entity_type)
        _generate_embedding(entity_id, entity_type)
    except Exception as exc:
        logger.error("Failed to process entity %s: %s", entity_id, exc)
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def index_for_search(self, entity_id: str, entity_type: str, payload: dict):
    """Index an entity in Meilisearch."""
    import httpx

    meili_url = "http://meilisearch:7700"
    api_key = "salesos_meili_master_key_dev"

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


@celery_app.task(bind=True, max_retries=3, default_retry_delay=120)
def enrich_company(self, company_id: str, cr_number: str):
    """Background company enrichment pipeline."""
    logger.info("Enriching company %s (CR: %s)", company_id, cr_number)
    try:
        _scrape_external_sources(company_id, cr_number)
        _recompute_features(company_id)
    except Exception as exc:
        logger.error("Failed to enrich company %s: %s", company_id, exc)
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=300)
def sync_notion_database(self, database_id: str, tenant_id: str):
    """Sync a Notion database into the pipeline."""
    logger.info("Syncing Notion database %s for tenant %s", database_id, tenant_id)
    from app.modules.notion_sync.service import NotionSyncService
    import asyncio

    try:
        asyncio.run(NotionSyncService().sync_database(database_id, tenant_id))
        logger.info("Notion sync complete for %s", database_id)
    except Exception as exc:
        logger.error("Notion sync failed for %s: %s", database_id, exc)
        raise self.retry(exc=exc)


def _sync_to_graph(entity_id: str, entity_type: str):
    """Placeholder — sync entity to Neo4j knowledge graph."""
    logger.debug("Graph sync placeholder: %s %s", entity_type, entity_id)


def _generate_embedding(entity_id: str, entity_type: str):
    """Placeholder — generate vector embedding for entity."""
    logger.debug("Embedding placeholder: %s %s", entity_type, entity_id)


def _scrape_external_sources(company_id: str, cr_number: str):
    """Placeholder — enrich company from external data sources."""
    logger.debug("Enrichment placeholder: %s (CR: %s)", company_id, cr_number)


def _recompute_features(company_id: str):
    """Placeholder — recompute company feature scores."""
    logger.debug("Feature recompute placeholder: %s", company_id)
