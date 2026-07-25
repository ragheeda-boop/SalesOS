"""Router repository — delegates to primary backend with automatic fallback."""

from __future__ import annotations

import asyncio
import random
import time
from typing import Any, Callable, Optional

from app.config import settings

from ..models import EdgeType, GraphEdge, GraphNode, GraphPath, NodeLabel
from .base import GraphRepository

_NEO4J_MAX_RETRIES = 3
_NEO4J_RETRY_BASE_DELAY = 0.1


class RouterGraphRepository(GraphRepository):
    """Routes graph operations to a primary backend with automatic fallback.

    Primary attempts one or more retries on transient failures.
    When all retries are exhausted (or no primary is configured), calls
    fall to the secondary backend.

    Metrics are tracked on the ``metrics`` object passed to the constructor.
    """

    def __init__(
        self,
        primary: Optional[GraphRepository],
        fallback: GraphRepository,
        metrics: Any,
        logger: Any = None,
        allow_fallback: bool = True,
        max_retries: int = _NEO4J_MAX_RETRIES,
        base_delay: float = _NEO4J_RETRY_BASE_DELAY,
    ):
        self._primary = primary
        self._fallback = fallback
        self._metrics = metrics
        self._logger = logger
        self._allow_fallback = allow_fallback
        self._max_retries = max_retries
        self._base_delay = base_delay

    async def ensure_indexes(self) -> None:
        if self._primary:
            await self._primary.ensure_indexes()

    # ── Routing helpers ─────────────────────────────────────────

    @property
    def primary_available(self) -> bool:
        return getattr(self._metrics, "neo4j_available", False) and self._primary is not None

    def _sql_fallback_allowed(self) -> bool:
        if not self._allow_fallback:
            return False
        return settings.is_kg_sql_fallback_allowed()

    async def _route(self, op_name: str, primary_call: Callable, fallback_call: Callable) -> Any:
        self._metrics.queries_executed += 1
        t0 = time.monotonic()

        if self.primary_available:
            last_error = None
            for attempt in range(1, self._max_retries + 1):
                try:
                    result = await primary_call()
                    if not getattr(self._metrics, "neo4j_available", True):
                        self._metrics.neo4j_available = True
                    elapsed = (time.monotonic() - t0) * 1000
                    self._metrics.total_query_ms += elapsed
                    return result
                except Exception as exc:
                    last_error = exc
                    elapsed = (time.monotonic() - t0) * 1000
                    if attempt < self._max_retries:
                        delay = self._base_delay * (2 ** (attempt - 1)) * (1 + random.random() * 0.1)
                        if self._logger:
                            self._logger.warning(
                                "Graph %s primary attempt %d/%d failed (%.0fms), retrying in %.0fms: %s",
                                op_name, attempt, self._max_retries, elapsed, delay * 1000, exc,
                            )
                        await asyncio.sleep(delay)
                    else:
                        self._metrics.errors += 1
                        if self._logger:
                            self._logger.error(
                                "Graph %s primary failed after %d retries (%.0fms): %s",
                                op_name, self._max_retries, elapsed, exc,
                            )
            self._metrics.neo4j_available = False
            if not self._sql_fallback_allowed():
                self._metrics.errors += 1
                raise RuntimeError(
                    f"Graph {op_name}: primary unavailable and fallback disabled in production"
                ) from last_error
            try:
                result = await fallback_call()
                elapsed = (time.monotonic() - t0) * 1000
                self._metrics.total_query_ms += elapsed
                return result
            except Exception as sql_exc:
                self._metrics.errors += 1
                raise sql_exc from last_error

        if not self._sql_fallback_allowed():
            self._metrics.errors += 1
            raise RuntimeError(
                f"Graph {op_name}: primary unavailable and fallback disabled in production"
            )

        try:
            result = await fallback_call()
            elapsed = (time.monotonic() - t0) * 1000
            self._metrics.total_query_ms += elapsed
            return result
        except Exception as exc:
            elapsed = (time.monotonic() - t0) * 1000
            self._metrics.errors += 1
            if self._logger:
                self._logger.error("Graph %s fallback error (%.0fms): %s", op_name, elapsed, exc)
            raise

    # ── Node CRUD ───────────────────────────────────────────────

    async def upsert_company(self, company: dict, tenant_id: str = "") -> GraphNode:
        return await self._route(
            "upsert_company",
            lambda: self._primary.upsert_company(company=company, tenant_id=tenant_id),
            lambda: self._fallback.upsert_company(company=company, tenant_id=tenant_id),
        )

    async def upsert_person(self, person: dict, tenant_id: str = "") -> GraphNode:
        return await self._route(
            "upsert_person",
            lambda: self._primary.upsert_person(person=person, tenant_id=tenant_id),
            lambda: self._fallback.upsert_person(person=person, tenant_id=tenant_id),
        )

    async def get_node(
        self, node_id: str, labels: Optional[list[NodeLabel]] = None, tenant_id: str = ""
    ) -> Optional[GraphNode]:
        return await self._route(
            "get_node",
            lambda: self._primary.get_node(node_id=node_id, labels=labels, tenant_id=tenant_id),
            lambda: self._fallback.get_node(node_id=node_id, labels=labels, tenant_id=tenant_id),
        )

    # ── Edge CRUD ───────────────────────────────────────────────

    async def create_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: EdgeType,
        properties: dict,
        tenant_id: str = "",
    ) -> GraphEdge:
        return await self._route(
            "create_edge",
            lambda: self._primary.create_edge(
                source_id=source_id, target_id=target_id,
                edge_type=edge_type, properties=properties, tenant_id=tenant_id,
            ),
            lambda: self._fallback.create_edge(
                source_id=source_id, target_id=target_id,
                edge_type=edge_type, properties=properties, tenant_id=tenant_id,
            ),
        )

    # ── Graph queries ───────────────────────────────────────────

    async def find_competitors(
        self, company_id: str, tenant_id: str = "", limit: int = 10
    ) -> list[GraphNode]:
        return await self._route(
            "find_competitors",
            lambda: self._primary.find_competitors(company_id=company_id, tenant_id=tenant_id, limit=limit),
            lambda: self._fallback.find_competitors(company_id=company_id, tenant_id=tenant_id, limit=limit),
        )

    async def find_path(
        self, source_id: str, target_id: str, max_depth: int = 6, tenant_id: str = ""
    ) -> Optional[GraphPath]:
        return await self._route(
            "find_path",
            lambda: self._primary.find_path(source_id=source_id, target_id=target_id, max_depth=max_depth, tenant_id=tenant_id),
            lambda: self._fallback.find_path(source_id=source_id, target_id=target_id, max_depth=max_depth, tenant_id=tenant_id),
        )

    async def get_ego_network(
        self, company_id: str, depth: int = 2, tenant_id: str = ""
    ) -> list[dict]:
        return await self._route(
            "ego_network",
            lambda: self._primary.get_ego_network(company_id=company_id, depth=depth, tenant_id=tenant_id),
            lambda: self._fallback.get_ego_network(company_id=company_id, depth=depth, tenant_id=tenant_id),
        )

    async def get_decision_makers(self, company_id: str, tenant_id: str = "") -> list[GraphNode]:
        return await self._route(
            "get_decision_makers",
            lambda: self._primary.get_decision_makers(company_id=company_id, tenant_id=tenant_id),
            lambda: self._fallback.get_decision_makers(company_id=company_id, tenant_id=tenant_id),
        )

    async def search(
        self,
        query: str,
        labels: Optional[list[NodeLabel]] = None,
        limit: int = 20,
        tenant_id: str = "",
    ) -> list[GraphNode]:
        return await self._route(
            "search",
            lambda: self._primary.search(query=query, labels=labels, limit=limit, tenant_id=tenant_id),
            lambda: self._fallback.search(query=query, labels=labels, limit=limit, tenant_id=tenant_id),
        )

    # ── Entity operations ───────────────────────────────────────

    async def upsert_license(self, lic: dict, tenant_id: str = "") -> GraphNode:
        if self.primary_available and self._primary:
            return await self._primary.upsert_license(lic=lic, tenant_id=tenant_id)
        return await self._fallback.upsert_license(lic=lic, tenant_id=tenant_id)

    async def upsert_branch(self, branch: dict, tenant_id: str = "") -> GraphNode:
        if self.primary_available and self._primary:
            return await self._primary.upsert_branch(branch=branch, tenant_id=tenant_id)
        return await self._fallback.upsert_branch(branch=branch, tenant_id=tenant_id)

    async def get_entity_subgraph(self, entity_id: str, depth: int = 2, tenant_id: str = "") -> dict:
        return await self._route(
            "get_entity_subgraph",
            lambda: self._primary.get_entity_subgraph(entity_id=entity_id, depth=depth, tenant_id=tenant_id),
            lambda: self._fallback.get_entity_subgraph(entity_id=entity_id, depth=depth, tenant_id=tenant_id),
        )

    async def merge_graph_nodes(self, surviving_id: str, absorbed_id: str, tenant_id: str = "") -> dict:
        return await self._route(
            "merge_graph_nodes",
            lambda: self._primary.merge_graph_nodes(surviving_id=surviving_id, absorbed_id=absorbed_id, tenant_id=tenant_id),
            lambda: self._fallback.merge_graph_nodes(surviving_id=surviving_id, absorbed_id=absorbed_id, tenant_id=tenant_id),
        )
