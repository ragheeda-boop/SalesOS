"""HybridSearchEngine — blends full-text and semantic search using RRF.

Reciprocal Rank Fusion (RRF) combines result lists from different search
backends into a single ranked list. Each result gets a score based on its
rank in each list:

    score = sum(1 / (k + rank_i)) for each list i

where k is a constant (default 60) that controls how much lower-ranked
results are penalized. RRF is preferred over weighted score averaging
because it is rank-based and doesn't require score normalization across
heterogeneous backends.

Architecture:
    ┌───────────┐     ┌──────────────┐
    │ Full-Text  │     │   Semantic   │
    │ (tsvector) │     │ (pgvector)   │
    └─────┬─────┘     └──────┬───────┘
          │                   │
          └────────┬──────────┘
                   │
            ┌──────▼──────┐
            │ RRF Fusion  │
            │ (k=60)      │
            └──────┬──────┘
                   │
            ┌──────▼──────┐
            │ Ranked List │
            └─────────────┘
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# RRF constant — controls rank decay. Higher k = less penalty for lower ranks.
RRF_K = 60


@dataclass
class HybridSearchResult:
    """A single result from hybrid search, carrying metadata about the match."""

    id: str
    name_ar: str = ""
    name_en: str = ""
    cr_number: str = ""
    city: str = ""
    region: str = ""
    industry: str = ""
    status: str = ""
    activity_description: str = ""
    score: float = 0.0
    fulltext_score: float = 0.0
    semantic_score: float = 0.0
    match_type: str = "fulltext"  # "fulltext", "semantic", "hybrid"
    explanation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name_ar": self.name_ar,
            "name_en": self.name_en,
            "cr_number": self.cr_number,
            "city": self.city,
            "region": self.region,
            "industry": self.industry,
            "status": self.status,
            "activity_description": self.activity_description,
            "score": round(self.score, 6),
            "fulltext_score": round(self.fulltext_score, 6),
            "semantic_score": round(self.semantic_score, 6),
            "match_type": self.match_type,
            "explanation": self.explanation,
        }


@dataclass
class HybridSearchResponse:
    """Response from hybrid search with metadata."""

    items: list[HybridSearchResult]
    total: int
    query: str
    strategy: str = "hybrid"
    took_ms: float = 0.0
    fulltext_count: int = 0
    semantic_count: int = 0
    fused_count: int = 0


class HybridSearchEngine:
    """Blends full-text and semantic search using Reciprocal Rank Fusion.

    Usage:
        engine = HybridSearchEngine(session_factory, embedding_service)
        result = await engine.search("شركات مقاولات", tenant_id="...", limit=20)
    """

    def __init__(
        self,
        session_factory: Callable[[], AsyncSession],
        embedding_service: Any = None,
        alpha: float = 0.5,
        rrf_k: int = RRF_K,
        timeout_seconds: float = 10.0,
        fts_language: str = "simple",
    ):
        self._session_factory = session_factory
        self._embedding_service = embedding_service
        self._alpha = alpha  # 0.5 = equal weight, >0.5 = favor fulltext
        self._rrf_k = rrf_k
        self._timeout = timeout_seconds
        self._fts_language = fts_language

    async def search(
        self,
        query: str,
        tenant_id: str,
        limit: int = 20,
        offset: int = 0,
        filters: dict[str, str] | None = None,
    ) -> HybridSearchResponse:
        """Execute hybrid search combining full-text and semantic signals.

        Args:
            query: Raw search text (Arabic or English)
            tenant_id: Tenant UUID for multi-tenant isolation
            limit: Max results to return
            offset: Pagination offset
            filters: Optional field filters (city, region, industry, status)

        Returns:
            HybridSearchResponse with fused results
        """
        t0 = time.monotonic()

        if not query or not query.strip():
            return HybridSearchResponse(
                items=[], total=0, query=query, took_ms=0
            )

        query = query.strip()

        # Run full-text and semantic search in parallel
        tasks = [
            self._fulltext_search(query, tenant_id, limit * 2, offset, filters),
        ]

        # Only add semantic search if embedding service is available
        if self._embedding_service:
            tasks.append(self._semantic_search(query, tenant_id, limit * 2))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        ft_results: list[HybridSearchResult] = []
        sem_results: list[HybridSearchResult] = []

        if isinstance(results[0], list):
            ft_results = results[0]
        elif isinstance(results[0], Exception):
            logger.warning("Full-text search failed: %s", results[0])

        if len(results) > 1:
            if isinstance(results[1], list):
                sem_results = results[1]
            elif isinstance(results[1], Exception):
                logger.warning("Semantic search failed: %s", results[1])

        # Apply filters to full-text results (already filtered in SQL)
        # Semantic results don't support structured filters, so filter here
        if filters and sem_results:
            sem_results = self._apply_filters(sem_results, filters)

        # Fuse using RRF
        fused = self._rrf_fusion(ft_results, sem_results)

        total = len(fused)
        paginated = fused[offset : offset + limit]

        took_ms = (time.monotonic() - t0) * 1000

        return HybridSearchResponse(
            items=paginated,
            total=total,
            query=query,
            strategy="hybrid",
            took_ms=took_ms,
            fulltext_count=len(ft_results),
            semantic_count=len(sem_results),
            fused_count=total,
        )

    async def _fulltext_search(
        self,
        query: str,
        tenant_id: str,
        limit: int,
        offset: int,
        filters: dict[str, str] | None = None,
    ) -> list[HybridSearchResult]:
        """Full-text search using PostgreSQL tsvector/tsquery with GIN index."""
        async with self._session_factory() as session:
            await session.execute(
                sa_text("SET LOCAL statement_timeout = '5s'")
            )

            conditions = [
                "c.tenant_id = :tid",
                f"c.search_vector @@ plainto_tsquery('{self._fts_language}', :q)",
            ]
            params: dict[str, Any] = {
                "tid": tenant_id,
                "q": query,
                "lim": limit,
                "off": offset,
            }

            if filters:
                for field_name, value in filters.items():
                    allowed = ("city", "region", "industry", "status",
                               "legal_form", "activity")
                    if field_name in allowed:
                        conditions.append(f"c.{field_name} = :fltr_{field_name}")
                        params[f"fltr_{field_name}"] = value

            where_clause = " AND ".join(conditions)

            rows = await session.execute(
                sa_text(f"""
                    SELECT c.id::text, c.name_ar, c.name_en, c.cr_number,
                           c.city, c.region, c.industry, c.status,
                           c.activity_description,
                           ts_rank(c.search_vector,
                                   plainto_tsquery('{self._fts_language}', :q)) AS rank
                    FROM companies c
                    WHERE {where_clause}
                    ORDER BY rank DESC, c.updated_at DESC
                    LIMIT :lim OFFSET :off
                """),
                params,
            )

            return [
                HybridSearchResult(
                    id=str(r["id"]),
                    name_ar=r["name_ar"] or "",
                    name_en=r["name_en"] or "",
                    cr_number=r["cr_number"] or "",
                    city=r["city"] or "",
                    region=r["region"] or "",
                    industry=r["industry"] or "",
                    status=r["status"] or "",
                    activity_description=r["activity_description"] or "",
                    score=float(r["rank"]) if r["rank"] else 0.0,
                    fulltext_score=float(r["rank"]) if r["rank"] else 0.0,
                    match_type="fulltext",
                )
                for r in rows.mappings().all()
            ]

    async def _semantic_search(
        self,
        query: str,
        tenant_id: str,
        limit: int,
    ) -> list[HybridSearchResult]:
        """Semantic search using pgvector cosine similarity."""
        embedding = await self._embedding_service.get_embedding(query)
        if not embedding:
            return []

        async with self._session_factory() as session:
            await session.execute(
                sa_text("SET LOCAL statement_timeout = '5s'")
            )

            rows = await session.execute(
                sa_text("""
                    SELECT c.id::text, c.name_ar, c.name_en, c.cr_number,
                           c.city, c.region, c.industry, c.status,
                           c.activity_description,
                           1 - (c.embedding_vector <=> :emb::vector) AS similarity
                    FROM companies c
                    WHERE c.tenant_id = :tid
                      AND c.embedding_vector IS NOT NULL
                    ORDER BY c.embedding_vector <=> :emb::vector
                    LIMIT :lim
                """),
                {"emb": str(embedding), "tid": tenant_id, "lim": limit},
            )

            return [
                HybridSearchResult(
                    id=str(r["id"]),
                    name_ar=r["name_ar"] or "",
                    name_en=r["name_en"] or "",
                    cr_number=r["cr_number"] or "",
                    city=r["city"] or "",
                    region=r["region"] or "",
                    industry=r["industry"] or "",
                    status=r["status"] or "",
                    activity_description=r["activity_description"] or "",
                    score=float(r["similarity"]) if r["similarity"] else 0.0,
                    semantic_score=float(r["similarity"]) if r["similarity"] else 0.0,
                    match_type="semantic",
                )
                for r in rows.mappings().all()
            ]

    def _rrf_fusion(
        self,
        ft_results: list[HybridSearchResult],
        sem_results: list[HybridSearchResult],
    ) -> list[HybridSearchResult]:
        """Reciprocal Rank Fusion of full-text and semantic result lists.

        RRF score for document d:
            score(d) = sum_i( 1 / (k + rank_i(d)) )

        where rank_i(d) is the 0-based position of d in list i.

        RRF is preferred over weighted averaging because:
        1. It normalizes across different scoring scales (ts_rank vs cosine sim)
        2. It's robust to outliers (one very high score in one list doesn't dominate)
        3. It naturally handles documents appearing in only one list
        """
        scores: dict[str, float] = {}
        ft_ranks: dict[str, int] = {}
        sem_ranks: dict[str, int] = {}

        # Score full-text results
        for rank, result in enumerate(ft_results):
            scores[result.id] = scores.get(result.id, 0.0) + 1.0 / (self._rrf_k + rank)
            ft_ranks[result.id] = rank

        # Score semantic results
        for rank, result in enumerate(sem_results):
            scores[result.id] = scores.get(result.id, 0.0) + 1.0 / (self._rrf_k + rank)
            sem_ranks[result.id] = rank

        # Merge all results by ID
        all_results: dict[str, HybridSearchResult] = {}
        for r in ft_results:
            all_results[r.id] = r
        for r in sem_results:
            if r.id not in all_results:
                all_results[r.id] = r

        # Determine match_type and build explanation
        for rid, result in all_results.items():
            in_ft = rid in ft_ranks
            in_sem = rid in sem_ranks

            if in_ft and in_sem:
                result.match_type = "hybrid"
                result.explanation = (
                    f"fulltext_rank={ft_ranks[rid]}, semantic_rank={sem_ranks[rid]}, "
                    f"rrf_score={scores[rid]:.6f}"
                )
            elif in_ft:
                result.match_type = "fulltext"
                result.explanation = f"fulltext_only, rank={ft_ranks[rid]}"
            else:
                result.match_type = "semantic"
                result.explanation = f"semantic_only, rank={sem_ranks[rid]}"

            result.score = scores.get(rid, 0.0)

        # Sort by RRF score descending
        ranked = sorted(all_results.values(), key=lambda r: -r.score)
        return ranked

    def _apply_filters(
        self,
        results: list[HybridSearchResult],
        filters: dict[str, str],
    ) -> list[HybridSearchResult]:
        """Apply structured field filters to semantic results."""
        filtered = []
        for r in results:
            match = True
            for field_name, value in filters.items():
                actual = getattr(r, field_name, None)
                if actual and value.lower() not in actual.lower():
                    match = False
                    break
            if match:
                filtered.append(r)
        return filtered
