"""Search Runtime — unified search orchestrator combining full-text, semantic, and graph search.

Search strategies:
  1. Full-Text (PostgreSQL ILIKE + tsvector) — fast, exact, structured filters
  2. Semantic (pgvector + OpenAI embeddings) — meaning-based similarity
  3. Graph (Neo4j) — relationship-based discovery
  4. Hybrid — weighted combination of all three with ranking
"""

from __future__ import annotations

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

        if strategy == SearchStrategy.FULLTEXT:
            self.metrics.fulltext_searches += 1
            result = await self._fulltext_search(query, tenant_id, filters, limit, offset, entity_types)
        elif strategy == SearchStrategy.SEMANTIC:
            self.metrics.semantic_searches += 1
            result = await self._semantic_search(query, tenant_id, limit, offset)
        elif strategy == SearchStrategy.GRAPH:
            self.metrics.graph_searches += 1
            result = await self._graph_search(query, tenant_id, limit)
        else:
            self.metrics.hybrid_searches += 1
            result = await self._hybrid_search(query, tenant_id, filters, limit, offset, entity_types)

        result.took_ms = (time.monotonic() - t0) * 1000
        self.metrics.total_search_ms += result.took_ms

        if include_facets and result.items:
            result.facets = await self._get_facets(query, tenant_id)

        return result

    async def suggest(self, query: str, tenant_id: str, field: str = "name_ar", limit: int = 10) -> list[str]:
        """Auto-complete suggestions for a field."""
        if field not in self.ALLOWED_SUGGEST_FIELDS:
            raise ValueError(f"Suggest field not allowed: {field}")
        self.metrics.searches += 1
        async with self._session_factory() as session:
            rows = await session.execute(
                sa_text(f"""
                    SELECT DISTINCT {field} FROM companies
                    WHERE tenant_id = :tid AND {field} ILIKE :prefix
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
        like = f"%{query}%"
        async with self._session_factory() as session:
            conditions = [
                "c.tenant_id = :tid",
                "(c.name_ar ILIKE :q OR c.name_en ILIKE :q OR c.cr_number ILIKE :q "
                "OR c.city ILIKE :q OR c.activity_description ILIKE :q)",
            ]
            params: dict = {"tid": tenant_id, "q": like, "lim": limit, "off": offset}

            if filters:
                for field, value in filters.items():
                    if field not in self.ALLOWED_FILTER_FIELDS:
                        raise ValueError(f"Filter field not allowed: {field}")
                    conditions.append(f"c.{field} = :{field}")
                    params[field] = value

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
                           c.region, c.industry, c.status, c.activity_description
                    FROM companies c
                    WHERE {where_clause}
                    ORDER BY
                        CASE
                            WHEN c.name_ar ILIKE :exact THEN 10
                            WHEN c.name_ar ILIKE :q THEN 5
                            WHEN c.cr_number ILIKE :exact THEN 8
                            ELSE 1
                        END DESC,
                        c.updated_at DESC
                    LIMIT :lim OFFSET :off
                """),
                {**params, "exact": query},
            )

            items = [
                SearchResultItem(
                    id=r["id"], type="company",
                    score=5.0 if r["name_ar"] == query else 1.0,
                    data={"name_ar": r["name_ar"], "name_en": r["name_en"],
                          "cr_number": r["cr_number"], "city": r["city"],
                          "region": r["region"], "industry": r["industry"],
                          "status": r["status"]},
                    matched_fields=self._find_matched(query, r),
                ) for r in rows.mappings().all()
            ]

        return SearchResult(items=items, total=total, query=query,
                           strategy=SearchStrategy.FULLTEXT, took_ms=0,
                           suggestions=await self.suggest(query, tenant_id))

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
        # Full-text base
        ft_result = await self._fulltext_search(query, tenant_id, filters, limit, offset, entity_types)

        # Semantic boost
        semantic_items: dict[str, float] = {}
        if self._embedding_service:
            try:
                sem_result = await self._semantic_search(query, tenant_id, limit, 0)
                for item in sem_result.items:
                    semantic_items[item.id] = item.score
            except Exception as exc:
                self.metrics.errors += 1
                if self._logger:
                    self._logger.warning("Semantic search error (fallback to fulltext): %s", exc)

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
        async with self._session_factory() as session:
            facets = {}
            for field in self.ALLOWED_FACET_FIELDS:
                rows = await session.execute(
                    sa_text(f"""
                        SELECT {field}, COUNT(*) as cnt
                        FROM companies
                        WHERE tenant_id = :tid
                          AND (name_ar ILIKE :q OR name_en ILIKE :q OR cr_number ILIKE :q)
                          AND {field} IS NOT NULL
                        GROUP BY {field}
                        ORDER BY cnt DESC
                        LIMIT 20
                    """),
                    {"tid": tenant_id, "q": f"%{query}%"},
                )
                facet_data = {str(r[0]): r[1] for r in rows}
                if facet_data:
                    facets[field] = facet_data
            return facets
