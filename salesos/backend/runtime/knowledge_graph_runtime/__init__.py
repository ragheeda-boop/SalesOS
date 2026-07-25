"""Knowledge Graph Runtime — graph engine for entity relationships and traversal.

Uses Neo4j as primary graph store with automatic pgvector fallback for
similarity queries. Integrated with the Data Fabric pipeline to
automatically populate the graph when golden records are created/updated.

Modules:
  models.py       — NodeLabel, EdgeType, GraphNode, GraphEdge, GraphPath, GraphMetrics
  repository.py   — backward-compatible shim over repository/ package
  repository/     — abstract base, Neo4j, SQL, router, query builders
  service.py      — KnowledgeGraphEngine (business logic, retry, routing)
  router.py       — FastAPI REST endpoints
"""

from .models import EdgeType, GraphEdge, GraphMetrics, GraphNode, GraphPath, NodeLabel
from .repository import (
    GraphRepository,
    KnowledgeGraphRepository,
    Neo4jGraphRepository,
    RouterGraphRepository,
    SqlGraphRepository,
    _validate_cypher_identifier,
    create_knowledge_graph_repository,
)
from .service import KnowledgeGraphEngine

__all__ = [
    "KnowledgeGraphEngine",
    "GraphNode",
    "GraphEdge",
    "GraphPath",
    "GraphMetrics",
    "NodeLabel",
    "EdgeType",
    "GraphRepository",
    "KnowledgeGraphRepository",
    "Neo4jGraphRepository",
    "SqlGraphRepository",
    "RouterGraphRepository",
    "create_knowledge_graph_repository",
    "_validate_cypher_identifier",
]
