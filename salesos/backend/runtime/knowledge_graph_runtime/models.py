"""Knowledge Graph data models — node labels, edge types, graph structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class NodeLabel(str, Enum):
    COMPANY = "Company"
    PERSON = "Person"
    SOURCE = "Source"
    LICENSE = "License"
    BRANCH = "Branch"
    PRODUCT = "Product"
    FUNDING_EVENT = "FundingEvent"
    JOB_POSTING = "JobPosting"
    INTENT_SIGNAL = "IntentSignal"


class EdgeType(str, Enum):
    HAS_LICENSE = "HAS_LICENSE"
    HAS_BRANCH = "HAS_BRANCH"
    HAS_PRODUCT = "HAS_PRODUCT"
    EMPLOYS = "EMPLOYS"
    RECEIVED_FUNDING = "RECEIVED_FUNDING"
    POSTED_JOB = "POSTED_JOB"
    HAS_INTENT = "HAS_INTENT"
    SUBSIDIARY_OF = "SUBSIDIARY_OF"
    COMPETITOR_OF = "COMPETITOR_OF"
    PARTNER_WITH = "PARTNER_WITH"
    INGESTED_FROM = "INGESTED_FROM"
    CONTACT_OF = "CONTACT_OF"


@dataclass
class GraphNode:
    id: str
    labels: list[NodeLabel]
    properties: dict[str, Any]

    def to_dict(self) -> dict:
        return {"id": self.id, "labels": [l.value for l in self.labels], "properties": self.properties}


@dataclass
class GraphEdge:
    source_id: str
    target_id: str
    type: EdgeType
    properties: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"source": self.source_id, "target": self.target_id, "type": self.type.value, "properties": self.properties}


@dataclass
class GraphPath:
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    length: int = 0

    def to_dict(self) -> dict:
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "length": self.length,
        }


@dataclass
class GraphMetrics:
    nodes_created: int = 0
    edges_created: int = 0
    queries_executed: int = 0
    total_query_ms: float = 0.0
    errors: int = 0
    neo4j_available: bool = True
    sync_count: int = 0

    def snapshot(self) -> dict:
        return {
            "nodes_created": self.nodes_created,
            "edges_created": self.edges_created,
            "queries_executed": self.queries_executed,
            "total_query_ms": round(self.total_query_ms, 2),
            "avg_query_ms": round(self.total_query_ms / max(self.queries_executed, 1), 2),
            "errors": self.errors,
            "neo4j_available": self.neo4j_available,
            "sync_count": self.sync_count,
        }
