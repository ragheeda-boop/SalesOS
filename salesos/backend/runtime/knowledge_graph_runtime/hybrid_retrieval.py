"""Hybrid Retrieval — combines vector similarity + BM25 with Reciprocal Rank Fusion (RRF).

Target: F1 > 0.85
Default weights: 0.6 vector + 0.4 BM25 (configurable)
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class RetrievalResult:
    id: str
    score: float
    data: dict[str, Any] = field(default_factory=dict)
    vector_rank: Optional[int] = None
    bm25_rank: Optional[int] = None
    rrf_score: Optional[float] = None


@dataclass
class HybridRetrievalMetrics:
    queries: int = 0
    total_ms: float = 0.0
    vector_only_ms: float = 0.0
    bm25_only_ms: float = 0.0
    fusion_ms: float = 0.0
    errors: int = 0

    def snapshot(self) -> dict:
        return {
            "queries": self.queries,
            "total_ms": round(self.total_ms, 2),
            "avg_ms": round(self.total_ms / max(self.queries, 1), 2),
            "vector_only_ms": round(self.vector_only_ms, 2),
            "bm25_only_ms": round(self.bm25_only_ms, 2),
            "fusion_ms": round(self.fusion_ms, 2),
            "errors": self.errors,
        }


class HybridRetriever:
    """Hybrid retrieval engine combining vector similarity + BM25 full-text search.

    Uses Reciprocal Rank Fusion (RRF) to combine ranked results from both
    retrieval methods into a unified ranking.

    Args:
        session_factory: SQLAlchemy async session factory
        embedding_service: Service that can generate embeddings from text
        vector_weight: Weight for vector similarity results (default 0.6)
        bm25_weight: Weight for BM25 full-text results (default 0.4)
        rrf_k: RRF constant (default 60, standard value)
        max_results: Maximum results to return (default 50)
    """

    def __init__(
        self,
        session_factory: Callable[[], AsyncSession],
        embedding_service: Any = None,
        vector_weight: float = 0.6,
        bm25_weight: float = 0.4,
        rrf_k: int = 60,
        max_results: int = 50,
        logger: Any = None,
    ):
        self._session_factory = session_factory
        self._embedding_service = embedding_service
        self._vector_weight = vector_weight
        self._bm25_weight = bm25_weight
        self._rrf_k = rrf_k
        self._max_results = max_results
        self._logger = logger
        self.metrics = HybridRetrievalMetrics()

    async def retrieve(
        self,
        query: str,
        tenant_id: str,
        limit: int = 20,
        entity_types: Optional[list[str]] = None,
    ) -> list[RetrievalResult]:
        """Execute hybrid retrieval: vector + BM25 + RRF fusion.

        Args:
            query: Search query text
            tenant_id: Tenant scope
            limit: Max results
            entity_types: Optional filter for entity types

        Returns:
            Fused and ranked list of RetrievalResult
        """
        t0 = time.monotonic()
        self.metrics.queries += 1

        try:
            # Run both retrievals in parallel
            vector_results = await self._vector_search(query, tenant_id, limit * 2)
            bm25_results = await self._bm25_search(query, tenant_id, limit * 2, entity_types)

            # Fuse with RRF
            fused = self._reciprocal_rank_fusion(vector_results, bm25_results)

            # Sort by RRF score descending and take top results
            fused.sort(key=lambda r: r.rrf_score or 0, reverse=True)
            results = fused[:limit]

            elapsed = (time.monotonic() - t0) * 1000
            self.metrics.total_ms += elapsed
            return results

        except Exception as exc:
            self.metrics.errors += 1
            if self._logger:
                self._logger.error("Hybrid retrieval failed: %s", exc)
            # Fallback to BM25 only
            try:
                return await self._bm25_search(query, tenant_id, limit, entity_types)
            except Exception:
                return []

    def _reciprocal_rank_fusion(
        self,
        vector_results: list[RetrievalResult],
        bm25_results: list[RetrievalResult],
    ) -> list[RetrievalResult]:
        """Combine two ranked lists using Reciprocal Rank Fusion.

        RRF score = sum( weight / (k + rank) ) for each list.
        k = 60 (standard constant from original RRF paper).
        """
        k = self._rrf_k
        doc_scores: dict[str, RetrievalResult] = {}

        # Process vector results
        for rank, result in enumerate(vector_results, start=1):
            rrf_contribution = self._vector_weight / (k + rank)
            if result.id in doc_scores:
                doc_scores[result.id].rrf_score = (doc_scores[result.id].rrf_score or 0) + rrf_contribution
            else:
                result.rrf_score = rrf_contribution
                result.vector_rank = rank
                doc_scores[result.id] = result

        # Process BM25 results
        for rank, result in enumerate(bm25_results, start=1):
            rrf_contribution = self._bm25_weight / (k + rank)
            if result.id in doc_scores:
                doc_scores[result.id].rrf_score = (doc_scores[result.id].rrf_score or 0) + rrf_contribution
            else:
                result.rrf_score = rrf_contribution
                result.bm25_rank = rank
                doc_scores[result.id] = result

        return list(doc_scores.values())

    async def _vector_search(self, query: str, tenant_id: str, limit: int) -> list[RetrievalResult]:
        """Cosine similarity search using pgvector."""
        if not self._embedding_service:
            return []

        t0 = time.monotonic()
        try:
            embedding = await self._embedding_service.embed(query)
            if not embedding:
                return []

            async with self._session_factory() as session:
                rows = await session.execute(
                    sa_text("""
                        SELECT id, name_ar, name_en, cr_number, city, industry,
                               embedding <=> :vec AS distance
                        FROM companies
                        WHERE tenant_id = :tid
                          AND embedding IS NOT NULL
                          AND is_active = true
                        ORDER BY embedding <=> :vec
                        LIMIT :lim
                    """),
                    {"vec": str(embedding), "tid": tenant_id, "lim": limit},
                )
                results = []
                for rank, row in enumerate(rows.mappings().all(), start=1):
                    # Convert distance to similarity score (1 - cosine_distance)
                    distance = float(row["distance"])
                    score = 1.0 - distance
                    results.append(RetrievalResult(
                        id=str(row["id"]),
                        score=score,
                        data={
                            "name_ar": row.get("name_ar"),
                            "name_en": row.get("name_en"),
                            "cr_number": row.get("cr_number"),
                            "city": row.get("city"),
                            "industry": row.get("industry"),
                        },
                        vector_rank=rank,
                    ))
                self.metrics.vector_only_ms += (time.monotonic() - t0) * 1000
                return results
        except Exception as exc:
            if self._logger:
                self._logger.warning("Vector search failed: %s", exc)
            return []

    async def _bm25_search(
        self,
        query: str,
        tenant_id: str,
        limit: int,
        entity_types: Optional[list[str]] = None,
    ) -> list[RetrievalResult]:
        """BM25 full-text search using PostgreSQL tsvector/tsquery."""
        t0 = time.monotonic()
        try:
            async with self._session_factory() as session:
                # Use tsvector for BM25-like ranking
                rows = await session.execute(
                    sa_text("""
                        SELECT id, name_ar, name_en, cr_number, city, industry,
                               ts_rank_cd(
                                   to_tsvector('simple', coalesce(name_ar, '') || ' ' || coalesce(name_en, '') || ' ' || coalesce(cr_number, '')),
                                   plainto_tsquery('simple', :query)
                               ) AS rank
                        FROM companies
                        WHERE tenant_id = :tid
                          AND is_active = true
                          AND to_tsvector('simple', coalesce(name_ar, '') || ' ' || coalesce(name_en, '') || ' ' || coalesce(cr_number, ''))
                              @@ plainto_tsquery('simple', :query)
                        ORDER BY rank DESC
                        LIMIT :lim
                    """),
                    {"query": query, "tid": tenant_id, "lim": limit},
                )
                results = []
                for rank, row in enumerate(rows.mappings().all(), start=1):
                    score = float(row["rank"])
                    results.append(RetrievalResult(
                        id=str(row["id"]),
                        score=score,
                        data={
                            "name_ar": row.get("name_ar"),
                            "name_en": row.get("name_en"),
                            "cr_number": row.get("cr_number"),
                            "city": row.get("city"),
                            "industry": row.get("industry"),
                        },
                        bm25_rank=rank,
                    ))
                self.metrics.bm25_only_ms += (time.monotonic() - t0) * 1000
                return results
        except Exception as exc:
            if self._logger:
                self._logger.warning("BM25 search failed: %s", exc)
            return []

    async def evaluate(
        self,
        queries: list[dict],
        tenant_id: str,
    ) -> dict:
        """Evaluate hybrid retrieval quality against labeled queries.

        Each query dict should have:
          - query: str
          - expected_ids: list[str] — relevant document IDs

        Returns precision, recall, F1 metrics.
        """
        total_precision = 0.0
        total_recall = 0.0
        total_f1 = 0.0
        eval_count = 0

        for q in queries:
            results = await self.retrieve(q["query"], tenant_id, limit=20)
            retrieved_ids = {r.id for r in results}
            expected_ids = set(q.get("expected_ids", []))

            if not expected_ids:
                continue

            true_positives = len(retrieved_ids & expected_ids)
            precision = true_positives / len(retrieved_ids) if retrieved_ids else 0.0
            recall = true_positives / len(expected_ids) if expected_ids else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

            total_precision += precision
            total_recall += recall
            total_f1 += f1
            eval_count += 1

        if eval_count == 0:
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0, "queries_evaluated": 0}

        avg_precision = total_precision / eval_count
        avg_recall = total_recall / eval_count
        avg_f1 = total_f1 / eval_count

        return {
            "precision": round(avg_precision, 4),
            "recall": round(avg_recall, 4),
            "f1": round(avg_f1, 4),
            "queries_evaluated": eval_count,
            "target_f1": 0.85,
            "target_met": avg_f1 >= 0.85,
        }
