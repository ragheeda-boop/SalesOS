"""Abstract base interface for knowledge graph repository implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from ..models import EdgeType, GraphEdge, GraphNode, GraphPath, NodeLabel


class GraphRepository(ABC):
    """Abstract repository defining graph operations.

    Implementations: Neo4jGraphRepository (primary), SqlGraphRepository (fallback).
    """

    async def ensure_indexes(self) -> None:
        """Create or verify database indexes. Override in implementations that support it."""
        pass

    @abstractmethod
    async def upsert_company(self, company: dict, tenant_id: str = "") -> GraphNode:
        """Create or update a company node."""

    @abstractmethod
    async def upsert_person(self, person: dict, tenant_id: str = "") -> GraphNode:
        """Create or update a person node."""

    @abstractmethod
    async def create_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: EdgeType,
        properties: dict,
        tenant_id: str = "",
    ) -> GraphEdge:
        """Create a directed edge between two nodes."""

    @abstractmethod
    async def get_node(
        self,
        node_id: str,
        labels: Optional[list[NodeLabel]] = None,
        tenant_id: str = "",
    ) -> Optional[GraphNode]:
        """Retrieve a node by ID, optionally filtered by labels and tenant."""

    @abstractmethod
    async def find_competitors(
        self, company_id: str, tenant_id: str = "", limit: int = 10
    ) -> list[GraphNode]:
        """Find competing companies in the same industry or city."""

    @abstractmethod
    async def find_path(
        self, source_id: str, target_id: str, max_depth: int = 6, tenant_id: str = ""
    ) -> Optional[GraphPath]:
        """Find the shortest path between two nodes."""

    @abstractmethod
    async def get_ego_network(
        self, company_id: str, depth: int = 2, tenant_id: str = ""
    ) -> list[dict]:
        """Retrieve the neighborhood around a company."""

    @abstractmethod
    async def get_decision_makers(
        self, company_id: str, tenant_id: str = ""
    ) -> list[GraphNode]:
        """Retrieve senior persons (CEO, CTO, VP, etc.) at a company."""

    @abstractmethod
    async def search(
        self,
        query: str,
        labels: Optional[list[NodeLabel]] = None,
        limit: int = 20,
        tenant_id: str = "",
    ) -> list[GraphNode]:
        """Full-text search across node properties."""

    @abstractmethod
    async def upsert_license(self, lic: dict, tenant_id: str = "") -> GraphNode:
        """Create or update a license node."""

    @abstractmethod
    async def upsert_branch(self, branch: dict, tenant_id: str = "") -> GraphNode:
        """Create or update a branch node."""

    @abstractmethod
    async def get_entity_subgraph(
        self, entity_id: str, depth: int = 2, tenant_id: str = ""
    ) -> dict:
        """Retrieve the subgraph centered on an entity."""

    @abstractmethod
    async def merge_graph_nodes(
        self, surviving_id: str, absorbed_id: str, tenant_id: str = ""
    ) -> dict:
        """Merge an absorbed node into a surviving node, rewiring edges."""
