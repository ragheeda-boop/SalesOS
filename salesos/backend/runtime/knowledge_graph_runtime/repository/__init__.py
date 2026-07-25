"""Repository factory and re-exports for the knowledge graph runtime."""

from __future__ import annotations

from typing import Any, Callable, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

from .base import GraphRepository
from .neo4j_repository import Neo4jGraphRepository
from .query_builders import _validate_cypher_identifier, build_tenant_filter, build_tenant_params
from .router_repository import RouterGraphRepository
from .sql_repository import SqlGraphRepository


KnowledgeGraphRepository = RouterGraphRepository  # backward-compat alias


def create_knowledge_graph_repository(
    session_factory: Callable[[], AsyncSession],
    neo4j_driver: Any = None,
    metrics: Any = None,
    logger: Any = None,
    allow_fallback: bool = True,
) -> RouterGraphRepository:
    """Build a RouterGraphRepository with Neo4j primary and SQL fallback.

    Returns a RouterGraphRepository that routes all graph operations
    through the primary (Neo4j) backend, falling back to SQL when
    Neo4j is unavailable or all retries are exhausted.
    """
    sql_repo = SqlGraphRepository(session_factory=session_factory, logger=logger)
    neo4j_repo = Neo4jGraphRepository(driver=neo4j_driver, logger=logger) if neo4j_driver else None
    router = RouterGraphRepository(
        primary=neo4j_repo,
        fallback=sql_repo,
        metrics=metrics,
        logger=logger,
        allow_fallback=allow_fallback,
    )
    return router


__all__ = [
    "GraphRepository",
    "Neo4jGraphRepository",
    "SqlGraphRepository",
    "RouterGraphRepository",
    "KnowledgeGraphRepository",
    "create_knowledge_graph_repository",
    "build_tenant_filter",
    "build_tenant_params",
    "_validate_cypher_identifier",
]
