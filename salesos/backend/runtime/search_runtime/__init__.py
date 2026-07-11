"""Search Runtime — unified search orchestrator combining full-text, semantic, and graph search.

Search strategies:
  1. Full-Text (PostgreSQL ILIKE + tsvector) — fast, exact, structured filters
  2. Semantic (pgvector + OpenAI embeddings) — meaning-based similarity
  3. Graph (Neo4j) — relationship-based discovery
  4. Hybrid — weighted combination of all three with ranking
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional, ClassVar

from sqlalchemy import func, or_, select, text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession


class SearchStrategy(str, Enum):
    FULLTEXT = "fulltext"
    SEMANTIC = "semantic"
    GRAPH = "graph"
    HYBRID = "hybrid"


@dataclass
class SearchResultItem:
    id: str
    type: str
    score: float
    data: dict[str, Any]
    matched_fields: list[str] = field(default_factory=list)
    explanation: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "score": self.score,
            "data": self.data,
            "matched_fields": self.matched_fields,
            "explanation": self.explanation,
        }


@dataclass
class SearchResult:
    items: list[SearchResultItem]
    total: int
    query: str
    strategy: SearchStrategy
    took_ms: float
    facets: dict[str, dict[str, int]] = field(default_factory=dict)
    suggestions: list[str] = field(default_factory=list)


@dataclass
class SearchMetrics:
    searches: int = 0
    total_search_ms: float = 0.0
    fulltext_searches: int = 0
    semantic_searches: int = 0
    graph_searches: int = 0
    hybrid_searches: int = 0
    errors: int = 0

    def snapshot(self) -> dict:
        return {
            "searches": self.searches,
            "total_search_ms": round(self.total_search_ms, 2),
            "avg_search_ms": round(self.total_search_ms / max(self.searches, 1), 2),
            "by_strategy": {
                "fulltext": self.fulltext_searches,
                "semantic": self.semantic_searches,
                "graph": self.graph_searches,
                "hybrid": self.hybrid_searches,
            },
            "errors": self.errors,
        }


class SearchCache:
    """In-memory search result cache with TTL eviction."""

    def __init__(self, ttl_seconds: float = 60.0, max_entries: int = 256):
        self._ttl = ttl_seconds
        self._max = max_entries
        self._data: dict[str, tuple[float, Any]] = {}

    def _key(self, **kwargs) -> str:
        raw = json.dumps(kwargs, sort_keys=True, default=str)
        return hashlib.md5(raw.encode()).hexdigest()

    def get(self, **kwargs) -> Any | None:
        k = self._key(**kwargs)
        entry = self._data.get(k)
        if entry is None:
            return None
        ts, val = entry
        if time.monotonic() - ts > self._ttl:
            del self._data[k]
            return None
        return val

    def set(self, value: Any, **kwargs) -> None:
        if len(self._data) >= self._max:
            self._evict_oldest()
        k = self._key(**kwargs)
        self._data[k] = (time.monotonic(), value)

    def _evict_oldest(self) -> None:
        oldest = min(self._data.keys(), key=lambda k: self._data[k][0])
        del self._data[oldest]

    def clear(self) -> None:
        self._data.clear()

    @property
    def size(self) -> int:
        return len(self._data)


class SearchRuntime:
    """Unified search engine — coordinates full-text, semantic, and graph search.

    Usage:
        rt = SearchRuntime(session_factory, kg_engine)
        results = await rt.search("شركة عبد اللطيف", tenant_id="...")
    """

    ALLOWED_FILTER_FIELDS: ClassVar[frozenset[str]] = frozenset({
        "city", "region", "industry", "status", "legal_form",
        "activity", "is_active", "created_at", "updated_at",
        "cr_number", "phone", "email",
    })

    ALLOWED_SUGGEST_FIELDS: ClassVar[frozenset[str]] = frozenset({
        "name_ar", "name_en", "cr_number", "city", "email", "phone",
    })

    ALLOWED_FACET_FIELDS: ClassVar[frozenset[str]] = frozenset({
        "city", "region", "industry", "status", "legal_form",
    })

    def __init__(
        self,
        session_factory: Callable[[], AsyncSession],
        embedding_service: Any = None,
        kg_engine: Any = None,
        logger: Any = None,
    ):
        self._session_factory = session_factory
        self._embedding_service = embedding_service
        self._kg_engine = kg_engine
        self._logger = logger
        self.metrics = SearchMetrics()
        self._cache = SearchCache(ttl_seconds=60.0, max_entries=256)

    SEARCH_TIMEOUT: float = 5.0

    async def search(
        self,
        query: str,
        tenant_id: str,
        strategy: SearchStrategy = SearchStrategy.HYBRID,
        filters: Optional[dict] = None,
        limit: int = 20,
        offset: int = 0,
        include_facets: bool = False,
        entity_types: Optional[list[str]] = None,
    ) -> SearchResult:
        """Main search entry point — dispatches to the appropriate strategy."""
        t0 = time.monotonic()
        self.metrics.searches += 1

        # Check cache for non-offset queries (most dashboard queries are page 1)
        if offset == 0:
            cached = self._cache.get(
                query=query, tenant_id=tenant_id, strategy=strategy.value,
                filters=filters, limit=limit, include_facets=include_facets,
                entity_types=entity_types,
            )
            if cached is not None:
                cached.took_ms = (time.monotonic() - t0) * 1000
                return cached

        try:
            if strategy == SearchStrategy.FULLTEXT:
                self.metrics.fulltext_searches += 1
                result = await asyncio.wait_for(
                    self._fulltext_search(query, tenant_id, filters, limit, offset, entity_types),
                    timeout=self.SEARCH_TIMEOUT,
                )
            elif strategy == SearchStrategy.SEMANTIC:
                self.metrics.semantic_searches += 1
                result = await asyncio.wait_for(
                    self._semantic_search(query, tenant_id, limit, offset),
                    timeout=self.SEARCH_TIMEOUT,
                )
            elif strategy == SearchStrategy.GRAPH:
                self.metrics.graph_searches += 1
                result = await asyncio.wait_for(
                    self._graph_search(query, tenant_id, limit),
                    timeout=self.SEARCH_TIMEOUT,
                )
            else:
                self.metrics.hybrid_searches += 1
                result = await asyncio.wait_for(
                    self._hybrid_search(query, tenant_id, filters, limit, offset, entity_types),
                    timeout=self.SEARCH_TIMEOUT,
                )
        except asyncio.TimeoutError:
            self.metrics.errors += 1
            return SearchResult(items=[], total=0, query=query, strategy=strategy, took_ms=(time.monotonic() - t0) * 1000)

        result.took_ms = (time.monotonic() - t0) * 1000
        self.metrics.total_search_ms += result.took_ms

        if include_facets and result.items:
            result.facets = await self._get_facets(query, tenant_id)

        # Cache result (only page 1, non-offset queries)
        if offset == 0:
            self._cache.set(result, query=query, tenant_id=tenant_id, strategy=strategy.value,
                            filters=filters, limit=limit, include_facets=include_facets,
                            entity_types=entity_types)

        return result

    def _safe_col(self, field: str, allowed: frozenset[str]) -> str:
        if field not in allowed:
            raise ValueError(f"Field not allowed: {field}")
        return field

    async def suggest(self, query: str, tenant_id: str, field: str = "name_ar", limit: int = 10) -> list[str]:
        """Auto-complete suggestions for a field."""
        col = self._safe_col(field, self.ALLOWED_SUGGEST_FIELDS)
        self.metrics.searches += 1
        async with self._session_factory() as session:
            rows = await session.execute(
                sa_text(f"""
                    SELECT DISTINCT c.{col} FROM companies c
                    WHERE c.tenant_id = :tid AND c.{col} ILIKE :prefix
                    LIMIT :lim
                """),
                {"tid": tenant_id, "prefix": f"{query}%", "lim": limit},
            )
            return [str(r[0]) for r in rows if r[0]]

    async def similar_to(self, company_id: str, tenant_id: str, limit: int = 10) -> SearchResult:
        """Find companies similar to a given company."""
        t0 = time.monotonic()
        self.metrics.searches += 1
        self.metrics.semantic_searches += 1

        if not self._embedding_service:
            return SearchResult(items=[], total=0, query="similar_to", strategy=SearchStrategy.SEMANTIC, took_ms=0)

        async with self._session_factory() as session:
            row = await session.execute(
                sa_text("SELECT * FROM companies WHERE id = :cid AND tenant_id = :tid"),
                {"cid": company_id, "tid": tenant_id},
            )
            company = row.mappings().one_or_none()
            if not company:
                return SearchResult(items=[], total=0, query="similar_to", strategy=SearchStrategy.SEMANTIC, took_ms=0)

            text = f"{company['name_ar']} {company.get('name_en', '')} {company.get('activity_description', '')} {company.get('city', '')}"
            embedding = await self._embedding_service.embed(text)

            # Find nearest neighbors by L2 distance
            neighbors = await session.execute(
                sa_text("""
                    SELECT c.id, c.name_ar, c.name_en, c.cr_number, c.city, c.industry,
                           1 / (1 + (c.embedding <-> :emb)) as similarity
                    FROM companies c
                    WHERE c.tenant_id = :tid AND c.id != :cid AND c.embedding IS NOT NULL
                    ORDER BY c.embedding <-> :emb
                    LIMIT :lim
                """),
                {"emb": embedding, "tid": tenant_id, "cid": company_id, "lim": limit},
            )
            items = [
                SearchResultItem(
                    id=r["id"], type="company", score=float(r["similarity"]),
                    data={"name_ar": r["name_ar"], "name_en": r["name_en"],
                          "cr_number": r["cr_number"], "city": r["city"],
                          "industry": r["industry"]},
                    matched_fields=["vector_similarity"],
                ) for r in neighbors.mappings().all()
            ]

        took_ms = (time.monotonic() - t0) * 1000
        return SearchResult(items=items, total=len(items), query="similar_to",
                           strategy=SearchStrategy.SEMANTIC, took_ms=took_ms)

    # ── Strategy implementations ───────────────────────────────

    async def _fulltext_search(
        self, query: str, tenant_id: str,
        filters: Optional[dict], limit: int, offset: int,
        entity_types: Optional[list[str]],
    ) -> SearchResult:
        async with self._session_factory() as session:
            await session.execute(sa_text("SET statement_timeout = '5s'"))

            tsq = f"plainto_tsquery('arabic', :q)"
            conditions = [
                "c.tenant_id = :tid",
                f"c.tsv @@ {tsq}",
            ]
            params: dict = {"tid": tenant_id, "q": query, "lim": limit, "off": offset}

            if filters:
                for field, value in filters.items():
                    col = self._safe_col(field, self.ALLOWED_FILTER_FIELDS)
                    conditions.append(f"c.{col} = :{col}")
                    params[col] = value

            where_clause = " AND ".join(conditions)

            # Count
            count_row = await session.execute(
                sa_text(f"SELECT COUNT(*) FROM companies c WHERE {where_clause}"), params
            )
            total = count_row.scalar() or 0

            # Results
            rows = await session.execute(
                sa_text(f"""
                    SELECT c.id, c.name_ar, c.name_en, c.cr_number, c.city,
                           c.region, c.industry, c.status, c.activity_description,
                           ts_rank(c.tsv, {tsq}) AS relevance
                    FROM companies c
                    WHERE {where_clause}
                    ORDER BY
                        CASE
                            WHEN c.name_ar = :q THEN 10
                            WHEN c.cr_number = :q THEN 8
                            ELSE 5
                        END + COALESCE(ts_rank(c.tsv, {tsq}), 0) DESC,
                        c.updated_at DESC
                    LIMIT :lim OFFSET :off
                """),
                params,
            )

            items = [
                SearchResultItem(
                    id=r["id"], type="company",
                    score=float(r["relevance"]) if r["relevance"] else 1.0,
                    data={"name_ar": r["name_ar"], "name_en": r["name_en"],
                          "cr_number": r["cr_number"], "city": r["city"],
                          "region": r["region"], "industry": r["industry"],
                          "status": r["status"]},
                    matched_fields=self._find_matched(query, r),
                ) for r in rows.mappings().all()
            ]

        return SearchResult(items=items, total=total, query=query,
                           strategy=SearchStrategy.FULLTEXT, took_ms=0)

    async def _semantic_search(self, query: str, tenant_id: str, limit: int, offset: int) -> SearchResult:
        if not self._embedding_service:
            return SearchResult(items=[], total=0, query=query,
                               strategy=SearchStrategy.SEMANTIC, took_ms=0)

        embedding = await self._embedding_service.embed(query)
        async with self._session_factory() as session:
            rows = await session.execute(
                sa_text("""
                    SELECT c.id, c.name_ar, c.name_en, c.cr_number, c.city, c.industry,
                           c.activity_description,
                           1 / (1 + (c.embedding <-> :emb)) as similarity
                    FROM companies c
                    WHERE c.tenant_id = :tid AND c.embedding IS NOT NULL
                    ORDER BY c.embedding <-> :emb
                    LIMIT :lim OFFSET :off
                """),
                {"emb": embedding, "tid": tenant_id, "lim": limit, "off": offset},
            )
            items = [
                SearchResultItem(
                    id=r["id"], type="company", score=float(r["similarity"]),
                    data={"name_ar": r["name_ar"], "name_en": r["name_en"],
                          "cr_number": r["cr_number"], "city": r["city"],
                          "industry": r["industry"]},
                    matched_fields=["vector_similarity"],
                ) for r in rows.mappings().all()
            ]

        return SearchResult(items=items, total=len(items), query=query,
                           strategy=SearchStrategy.SEMANTIC, took_ms=0)

    async def _graph_search(self, query: str, tenant_id: str, limit: int) -> SearchResult:
        if not self._kg_engine:
            return SearchResult(items=[], total=0, query=query,
                               strategy=SearchStrategy.GRAPH, took_ms=0)

        nodes = await self._kg_engine.search(query, limit=limit)
        items = [
            SearchResultItem(
                id=n.id, type="company", score=1.0,
                data=n.properties,
                matched_fields=["graph_match"],
            ) for n in nodes
        ]
        return SearchResult(items=items, total=len(items), query=query,
                           strategy=SearchStrategy.GRAPH, took_ms=0)

    async def _hybrid_search(
        self, query: str, tenant_id: str,
        filters: Optional[dict], limit: int, offset: int,
        entity_types: Optional[list[str]],
    ) -> SearchResult:
        # Early termination: run full-text first with a short timeout.
        # If it yields enough high-confidence results, skip semantic search
        # (which is the dominant cost at ~150-400ms per embedding call).
        try:
            ft_result = await asyncio.wait_for(
                self._fulltext_search(query, tenant_id, filters, limit, offset, entity_types),
                timeout=self.SEARCH_TIMEOUT * 0.5,
            )
        except asyncio.TimeoutError:
            ft_result = SearchResult(items=[], total=0, query=query, strategy=SearchStrategy.FULLTEXT, took_ms=0)

        # Early exit: full-text results are good enough — skip semantic
        enough_results = len(ft_result.items) >= limit
        high_confidence = any(item.score >= 0.5 for item in ft_result.items[:3])
        if enough_results and high_confidence and not filters:
            ft_result.strategy = SearchStrategy.HYBRID
            return ft_result

        # Semantic boost — only if embedding service is available and we
        # actually need the extra signal
        sem_result = None
        if self._embedding_service and ft_result.total > 0:
            try:
                sem_result = await asyncio.wait_for(
                    self._semantic_search(query, tenant_id, limit, 0),
                    timeout=self.SEARCH_TIMEOUT * 0.4,
                )
            except asyncio.TimeoutError:
                self.metrics.errors += 1
            except Exception as exc:
                self.metrics.errors += 1
                if self._logger:
                    self._logger.warning("Semantic search error (fallback to fulltext): %s", exc)

        # Semantic boost
        semantic_items: dict[str, float] = {}
        if sem_result:
            for item in sem_result.items:
                semantic_items[item.id] = item.score

        # Combine with weighted scoring
        for item in ft_result.items:
            sem_score = semantic_items.get(item.id, 0)
            item.score = (item.score * 0.4) + (sem_score * 0.6)
            if sem_score > 0:
                item.matched_fields.append("semantic")

        ft_result.items.sort(key=lambda x: -x.score)
        ft_result.strategy = SearchStrategy.HYBRID
        return ft_result

    def _find_matched(self, query: str, row: dict) -> list[str]:
        fields = []
        ql = query.lower()
        for field in ("name_ar", "name_en", "cr_number", "city", "activity_description"):
            val = str(row.get(field, "")).lower()
            if ql in val:
                fields.append(field)
        return fields

    async def _get_facets(self, query: str, tenant_id: str) -> dict[str, dict[str, int]]:
        async def _facet_for_field(field: str) -> tuple[str, dict[str, int]]:
            col = self._safe_col(field, self.ALLOWED_FACET_FIELDS)
            async with self._session_factory() as session:
                rows = await session.execute(
                    sa_text(f"""
                        SELECT c.{col}, COUNT(*) as cnt
                        FROM companies c
                        WHERE c.tenant_id = :tid
                          AND c.tsv @@ plainto_tsquery('arabic', :q)
                          AND c.{col} IS NOT NULL
                        GROUP BY c.{col}
                        ORDER BY cnt DESC
                        LIMIT 20
                    """),
                    {"tid": tenant_id, "q": query},
                )
                data = {str(r[0]): r[1] for r in rows}
                return field, data

        results = await asyncio.gather(
            *[_facet_for_field(f) for f in self.ALLOWED_FACET_FIELDS],
            return_exceptions=True,
        )
        facets: dict[str, dict[str, int]] = {}
        for r in results:
            if isinstance(r, Exception):
                continue
            field, data = r
            if data:
                facets[field] = data
        return facets
