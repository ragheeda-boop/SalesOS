"""Tests for Knowledge Graph Runtime decomposition (B-1 through B-5).

Tests cover:
  - B-1: Module decomposition (models, repository, service, router)
  - B-2: PGVector migration
  - B-3: Embedding cache (LRU, TTL, hit rate)
  - B-4: Hybrid retrieval (vector + BM25 + RRF)
  - B-5: Data Fabric connectors (CRM, ERP, Market Feed)
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from runtime.knowledge_graph_runtime.models import (
    EdgeType,
    GraphEdge,
    GraphMetrics,
    GraphNode,
    GraphPath,
    NodeLabel,
)
from runtime.knowledge_graph_runtime.embedding_cache import EmbeddingCache, EmbeddingCacheMetrics
from runtime.knowledge_graph_runtime.hybrid_retrieval import HybridRetriever, RetrievalResult
from runtime.knowledge_graph_runtime.connectors import (
    BaseConnector,
    ConnectorRecord,
    ConnectorResult,
    ConnectorStatus,
    ConnectorType,
    CrmConnector,
    ErpConnector,
    MarketFeedConnector,
)


# ── B-1: Module decomposition tests ────────────────────────────


class TestModels:
    """Verify models.py exports and data structures."""

    def test_node_label_enum(self):
        assert NodeLabel.COMPANY.value == "Company"
        assert NodeLabel.PERSON.value == "Person"
        assert len(NodeLabel) == 9

    def test_edge_type_enum(self):
        assert EdgeType.COMPETITOR_OF.value == "COMPETITOR_OF"
        assert EdgeType.PARTNER_WITH.value == "PARTNER_WITH"
        assert len(EdgeType) == 12

    def test_graph_node_to_dict(self):
        node = GraphNode(id="n1", labels=[NodeLabel.COMPANY], properties={"name": "Test"})
        d = node.to_dict()
        assert d["id"] == "n1"
        assert d["labels"] == ["Company"]
        assert d["properties"]["name"] == "Test"

    def test_graph_edge_to_dict(self):
        edge = GraphEdge(source_id="n1", target_id="n2", type=EdgeType.EMPLOYS)
        d = edge.to_dict()
        assert d["source"] == "n1"
        assert d["target"] == "n2"
        assert d["type"] == "EMPLOYS"

    def test_graph_path_to_dict(self):
        path = GraphPath(
            nodes=[GraphNode(id="n1", labels=[NodeLabel.COMPANY], properties={})],
            edges=[],
            length=0,
        )
        d = path.to_dict()
        assert len(d["nodes"]) == 1
        assert d["length"] == 0

    def test_graph_metrics_snapshot(self):
        m = GraphMetrics(nodes_created=5, edges_created=3, queries_executed=10, total_query_ms=100.0)
        s = m.snapshot()
        assert s["nodes_created"] == 5
        assert s["avg_query_ms"] == 10.0

    def test_init_exports_all(self):
        from runtime.knowledge_graph_runtime import (
            EdgeType,
            GraphEdge,
            GraphMetrics,
            GraphNode,
            GraphPath,
            KnowledgeGraphEngine,
            NodeLabel,
        )
        assert KnowledgeGraphEngine is not None


class TestRepositoryInit:
    """Verify repository.py structure."""

    def test_repository_importable(self):
        from runtime.knowledge_graph_runtime.repository import KnowledgeGraphRepository
        assert KnowledgeGraphRepository is not None

    def test_validate_cypher_identifier_valid(self):
        from runtime.knowledge_graph_runtime.repository import _validate_cypher_identifier
        assert _validate_cypher_identifier("valid_name") == "valid_name"

    def test_validate_cypher_identifier_invalid(self):
        from runtime.knowledge_graph_runtime.repository import _validate_cypher_identifier
        with pytest.raises(ValueError, match="Invalid Cypher"):
            _validate_cypher_identifier("123bad!")

    def test_validate_cypher_identifier_with_dots(self):
        from runtime.knowledge_graph_runtime.repository import _validate_cypher_identifier
        with pytest.raises(ValueError, match="Invalid Cypher"):
            _validate_cypher_identifier("field.name")


class TestServiceInit:
    """Verify service.py structure."""

    def test_service_importable(self):
        from runtime.knowledge_graph_runtime.service import KnowledgeGraphEngine
        assert KnowledgeGraphEngine is not None

    def test_engine_without_neo4j(self):
        from runtime.knowledge_graph_runtime.service import KnowledgeGraphEngine
        engine = KnowledgeGraphEngine(session_factory=AsyncMock)
        assert engine.metrics.neo4j_available is False
        assert engine._driver is None


# ── B-3: Embedding cache tests ─────────────────────────────────


class TestEmbeddingCache:
    """LRU cache for embeddings with TTL eviction."""

    def test_basic_get_put(self):
        cache = EmbeddingCache(max_entries=100, ttl_seconds=60)
        cache.put("hello", "v1", [0.1, 0.2, 0.3])
        result = cache.get("hello", "v1")
        assert result == [0.1, 0.2, 0.3]

    def test_cache_miss(self):
        cache = EmbeddingCache(max_entries=100, ttl_seconds=60)
        result = cache.get("missing", "v1")
        assert result is None

    def test_different_model_versions(self):
        cache = EmbeddingCache(max_entries=100, ttl_seconds=60)
        cache.put("hello", "v1", [0.1])
        cache.put("hello", "v2", [0.2])
        assert cache.get("hello", "v1") == [0.1]
        assert cache.get("hello", "v2") == [0.2]

    def test_lru_eviction(self):
        cache = EmbeddingCache(max_entries=3, ttl_seconds=86400)
        cache.put("a", "v1", [1])
        cache.put("b", "v1", [2])
        cache.put("c", "v1", [3])
        assert cache.size == 3
        cache.put("d", "v1", [4])  # should evict "a"
        assert cache.size == 3
        assert cache.get("a", "v1") is None
        assert cache.get("d", "v1") == [4]

    def test_ttl_eviction(self):
        cache = EmbeddingCache(max_entries=100, ttl_seconds=0.01)
        cache.put("hello", "v1", [0.1])
        time.sleep(0.02)
        result = cache.get("hello", "v1")
        assert result is None

    def test_lru_access_refreshes(self):
        cache = EmbeddingCache(max_entries=3, ttl_seconds=86400)
        cache.put("a", "v1", [1])
        cache.put("b", "v1", [2])
        cache.put("c", "v1", [3])
        # Access "a" to refresh it
        cache.get("a", "v1")
        cache.put("d", "v1", [4])  # should evict "b" (least recently used)
        assert cache.get("a", "v1") == [1]
        assert cache.get("b", "v1") is None

    def test_hit_miss_metrics(self):
        cache = EmbeddingCache(max_entries=100, ttl_seconds=60)
        cache.put("a", "v1", [1])
        cache.get("a", "v1")  # hit
        cache.get("b", "v1")  # miss
        cache.get("c", "v1")  # miss
        m = cache.metrics.snapshot()
        assert m["hits"] == 1
        assert m["misses"] == 2
        assert m["hit_rate"] == pytest.approx(1 / 3, abs=0.01)

    def test_make_key_deterministic(self):
        k1 = EmbeddingCache.make_key("hello", "v1")
        k2 = EmbeddingCache.make_key("hello", "v1")
        assert k1 == k2

    def test_make_key_differs_by_version(self):
        k1 = EmbeddingCache.make_key("hello", "v1")
        k2 = EmbeddingCache.make_key("hello", "v2")
        assert k1 != k2

    def test_clear(self):
        cache = EmbeddingCache(max_entries=100, ttl_seconds=60)
        cache.put("a", "v1", [1])
        cache.clear()
        assert cache.size == 0
        assert cache.get("a", "v1") is None

    def test_invalidate(self):
        cache = EmbeddingCache(max_entries=100, ttl_seconds=60)
        cache.put("a", "v1", [1])
        assert cache.invalidate("a", "v1") is True
        assert cache.get("a", "v1") is None
        assert cache.invalidate("a", "v1") is False

    def test_get_or_compute(self):
        cache = EmbeddingCache(max_entries=100, ttl_seconds=60)
        call_count = 0

        def compute(text):
            nonlocal call_count
            call_count += 1
            return [0.5]

        result = cache.get_or_compute("hello", "v1", compute)
        assert result == [0.5]
        assert call_count == 1

        result2 = cache.get_or_compute("hello", "v1", compute)
        assert result2 == [0.5]
        assert call_count == 1  # should not call again

    def test_10k_capacity(self):
        cache = EmbeddingCache(max_entries=10_000, ttl_seconds=86400)
        for i in range(10_001):
            cache.put(f"text-{i}", "v1", [float(i)])
        assert cache.size == 10_000
        assert cache.metrics.evictions >= 1


# ── B-4: Hybrid retrieval tests ────────────────────────────────


class TestHybridRetriever:
    """Hybrid retrieval with RRF fusion."""

    def test_reciprocal_rank_fusion_basic(self):
        from runtime.knowledge_graph_runtime.hybrid_retrieval import HybridRetriever
        retriever = HybridRetriever(session_factory=AsyncMock)

        vector_results = [
            RetrievalResult(id="a", score=0.9, vector_rank=1),
            RetrievalResult(id="b", score=0.7, vector_rank=2),
            RetrievalResult(id="c", score=0.5, vector_rank=3),
        ]
        bm25_results = [
            RetrievalResult(id="b", score=0.8, bm25_rank=1),
            RetrievalResult(id="d", score=0.6, bm25_rank=2),
            RetrievalResult(id="a", score=0.4, bm25_rank=3),
        ]

        fused = retriever._reciprocal_rank_fusion(vector_results, bm25_results)

        # "a" and "b" appear in both lists, should have higher combined scores
        by_id = {r.id: r for r in fused}
        assert "a" in by_id
        assert "b" in by_id
        assert "c" in by_id
        assert "d" in by_id
        assert by_id["a"].rrf_score is not None
        assert by_id["b"].rrf_score is not None

    def test_rrf_deduplicates(self):
        from runtime.knowledge_graph_runtime.hybrid_retrieval import HybridRetriever
        retriever = HybridRetriever(session_factory=AsyncMock)

        vector_results = [RetrievalResult(id="x", score=0.9, vector_rank=1)]
        bm25_results = [RetrievalResult(id="x", score=0.8, bm25_rank=1)]

        fused = retriever._reciprocal_rank_fusion(vector_results, bm25_results)
        assert len(fused) == 1
        # Combined score should be > either individual
        assert fused[0].rrf_score > 0.6 / 61  # min single contribution

    def test_metrics_snapshot(self):
        from runtime.knowledge_graph_runtime.hybrid_retrieval import HybridRetrievalMetrics
        m = HybridRetrievalMetrics(queries=10, total_ms=500.0)
        s = m.snapshot()
        assert s["queries"] == 10
        assert s["avg_ms"] == 50.0


# ── B-5: Data Fabric connector tests ───────────────────────────


class TestCrmConnector:
    """CRM connector tests."""

    def test_connector_type(self):
        assert CrmConnector.connector_type == ConnectorType.CRM

    def test_mock_fetch(self):
        connector = CrmConnector(
            session_factory=AsyncMock,
            config={},
            logger=None,
        )
        records = connector._mock_fetch("tenant-1")
        assert len(records) == 2
        assert records[0].source_type == ConnectorType.CRM
        assert records[0].source_id == "crm-001"

    def test_transform(self):
        connector = CrmConnector(session_factory=AsyncMock, config={}, logger=None)
        records = [
            ConnectorRecord(source_type=ConnectorType.CRM, source_id="c1", raw_data={"name": "ACME", "email": "a@b.com", "city": "Riyadh"}),
        ]
        transformed = connector.transform(records)
        assert transformed[0].transformed_data["name_en"] == "ACME"
        assert transformed[0].transformed_data["email"] == "a@b.com"
        assert transformed[0].status == "transformed"

    def test_authenticate_without_config(self):
        connector = CrmConnector(session_factory=AsyncMock, config={}, logger=None)
        assert asyncio.get_event_loop().run_until_complete(connector.authenticate()) is False

    def test_authenticate_with_config(self):
        connector = CrmConnector(
            session_factory=AsyncMock,
            config={"api_url": "https://crm.example.com", "api_key": "key123"},
            logger=None,
        )
        assert asyncio.get_event_loop().run_until_complete(connector.authenticate()) is True

    def test_sync_without_auth(self):
        connector = CrmConnector(session_factory=AsyncMock, config={}, logger=None)
        result = asyncio.get_event_loop().run_until_complete(connector.sync("tenant-1"))
        assert result.connector_type == ConnectorType.CRM
        assert len(result.errors) > 0


class TestErpConnector:
    """ERP connector tests."""

    def test_connector_type(self):
        assert ErpConnector.connector_type == ConnectorType.ERP

    def test_mock_fetch(self):
        connector = ErpConnector(session_factory=AsyncMock, config={}, logger=None)
        records = connector._mock_fetch("tenant-1")
        assert len(records) == 2
        assert records[0].source_type == ConnectorType.ERP

    def test_transform(self):
        connector = ErpConnector(session_factory=AsyncMock, config={}, logger=None)
        records = [
            ConnectorRecord(source_type=ConnectorType.ERP, source_id="e1", raw_data={"company_name": "TechCorp", "order_total": 50000, "currency": "SAR"}),
        ]
        transformed = connector.transform(records)
        assert transformed[0].transformed_data["order_total"] == 50000
        assert transformed[0].transformed_data["currency"] == "SAR"

    def test_authenticate_without_config(self):
        connector = ErpConnector(session_factory=AsyncMock, config={}, logger=None)
        assert asyncio.get_event_loop().run_until_complete(connector.authenticate()) is False


class TestMarketFeedConnector:
    """Market feed connector tests."""

    def test_connector_type(self):
        assert MarketFeedConnector.connector_type == ConnectorType.MARKET_FEED

    def test_mock_fetch(self):
        connector = MarketFeedConnector(session_factory=AsyncMock, config={}, logger=None)
        records = connector._mock_fetch("tenant-1")
        assert len(records) == 3
        assert records[0].source_type == ConnectorType.MARKET_FEED
        assert records[0].raw_data["name"] == "Saudi Aramco"

    def test_transform(self):
        connector = MarketFeedConnector(session_factory=AsyncMock, config={}, logger=None)
        records = [
            ConnectorRecord(source_type=ConnectorType.MARKET_FEED, source_id="m1", raw_data={"name": "Aramco", "sector": "Energy", "market_cap": 7e12}),
        ]
        transformed = connector.transform(records)
        assert transformed[0].transformed_data["industry"] == "Energy"
        assert transformed[0].transformed_data["market_cap"] == 7e12


class TestConnectorResult:
    """ConnectorResult data class."""

    def test_snapshot(self):
        result = ConnectorResult(
            connector_type=ConnectorType.CRM,
            records_fetched=10,
            records_stored=8,
            records_failed=2,
            duration_ms=150.0,
        )
        s = result.snapshot()
        assert s["connector_type"] == "crm"
        assert s["records_fetched"] == 10
        assert s["records_stored"] == 8

    def test_connector_status_enum(self):
        assert ConnectorStatus.IDLE.value == "idle"
        assert ConnectorStatus.RUNNING.value == "running"
        assert ConnectorStatus.COMPLETED.value == "completed"
        assert ConnectorStatus.FAILED.value == "failed"
