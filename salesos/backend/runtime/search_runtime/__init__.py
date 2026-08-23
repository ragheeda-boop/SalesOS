"""Search Runtime — unified search orchestrator combining full-text, semantic, and graph search.

CI-19 Wave 2 Core (no sqlalchemy.text)

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
from enum import Enum
from typing import Any, Callable, ClassVar, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    String,
    bindparam,
    case,
    cast,
    column,
    func,
    literal,
    or_,
    select,
    table,
)
from sqlalchemy import text as sa_text
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession

# Lightweight table()/column() — avoid private MetaData island (EAB-001-P1-DRIFT-01).
# companies already lives on shared Base; this is a query stub only.
companies = table(
    "companies",
    column("id", PGUUID(as_uuid=True)),
    column("tenant_id", PGUUID(as_uuid=True)),
    column("name_ar", String),
    column("name_en", String),
    column("cr_number", String),
    column("city", String),
    column("region", String),
    column("industry", String),
    column("status", String),
    column("legal_form", String),
    column("activity", String),
    column("is_active", Boolean),
    column("phone", String),
    column("email", String),
    column("activity_description", String),
    column("created_at", DateTime(timezone=True)),
    column("updated_at", DateTime(timezone=True)),
    column("search_vector", TSVECTOR),
    column("embedding", String),  # pgvector column; String avoids dialect dependency
)


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


async def _apply_statement_timeout(session: AsyncSession) -> None:
    await session.execute(
        select(func.set_config("statement_timeout", "5000", True))
    )


async def _set_tenant_guc(session: AsyncSession, tenant_id: str) -> None:
    """DEC-085: set app.tenant_id so companies RLS does not fail-closed."""
    await session.execute(
        sa_text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
        {"tenant_id": str(tenant_id)},
    )


class SearchRuntime:
    """Unified search engine — coordinates full-text, semantic, and graph search.

    When a PostgresSearchRepository is provided, full-text search delegates
    to it instead of embedding raw SQL (architecture compliance — VIO-103).

    Usage:
        rt = SearchRuntime(session_factory, kg_engine, search_repo=repo)
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
        search_repo: Any = None,
    ):
        self._session_factory = session_factory
        self._embedding_service = embedding_service
        self._kg_engine = kg_engine
        self._logger = logger
        self._search_repo = search_repo
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
                try:
                    result = await asyncio.wait_for(
                        self._semantic_search(query, tenant_id, limit, offset),
                        timeout=self.SEARCH_TIMEOUT,
                    )
                except Exception:
                    self.metrics.errors += 1
                    result = await asyncio.wait_for(
                        self._fulltext_search(query, tenant_id, filters, limit, offset, entity_types),
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
        col_name = self._safe_col(field, self.ALLOWED_SUGGEST_FIELDS)
        self.metrics.searches += 1

        # Delegate to PostgresSearchRepository when available (VIO-103 compliance)
        if self._search_repo is not None:
            return await self._search_repo.suggest_raw(
                prefix=query, tenant_id=tenant_id, field=field, limit=limit,
            )

        col = companies.c[col_name]
        stmt = (
            select(col)
            .distinct()
            .where(
                companies.c.tenant_id == tenant_id,
                col.ilike(f"{query}%"),
            )
            .limit(limit)
        )
        async with self._session_factory() as session:
            await _set_tenant_guc(session, tenant_id)
            rows = await session.execute(stmt)
            return [str(r[0]) for r in rows if r[0]]

    async def similar_to(self, company_id: str, tenant_id: str, limit: int = 10) -> SearchResult:
        """Find companies similar to a given company."""
        t0 = time.monotonic()
        self.metrics.searches += 1
        self.metrics.semantic_searches += 1

        if not self._embedding_service:
            return SearchResult(items=[], total=0, query="similar_to", strategy=SearchStrategy.SEMANTIC, took_ms=0)

        async with self._session_factory() as session:
            await _set_tenant_guc(session, tenant_id)
            row = await session.execute(
                select(companies).where(
                    companies.c.id == company_id,
                    companies.c.tenant_id == tenant_id,
                )
            )
            company = row.mappings().one_or_none()
            if not company:
                return SearchResult(items=[], total=0, query="similar_to", strategy=SearchStrategy.SEMANTIC, took_ms=0)

            text = f"{company['name_ar']} {company.get('name_en', '')} {company.get('activity_description', '')} {company.get('city', '')}"
            embedding = await self._embedding_service.embed(text)

            distance = companies.c.embedding.op("<->")(bindparam("emb"))
            similarity = (literal(1.0) / (literal(1.0) + distance)).label("similarity")
            neighbors_stmt = (
                select(
                    cast(companies.c.id, String).label("id"),
                    companies.c.name_ar,
                    companies.c.name_en,
                    companies.c.cr_number,
                    companies.c.city,
                    companies.c.industry,
                    similarity,
                )
                .where(
                    companies.c.tenant_id == tenant_id,
                    companies.c.id != company_id,
                    companies.c.embedding.is_not(None),
                )
                .order_by(distance)
                .limit(limit)
            )
            neighbors = await session.execute(neighbors_stmt, {"emb": embedding})
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
        # Delegate to PostgresSearchRepository when available (VIO-103 compliance)
        if self._search_repo is not None:
            rows, total, _cursor = await self._search_repo.search_by_filters(
                query=query,
                tenant_id=tenant_id,
                filters=filters,
                limit=limit,
                offset=offset,
            )
            items = [
                SearchResultItem(
                    id=r["id"], type="company",
                    score=float(r.get("rank", 0)) or 1.0,
                    data={"name_ar": r.get("name_ar", ""), "name_en": r.get("name_en", ""),
                          "cr_number": r.get("cr_number", ""), "city": r.get("city", ""),
                          "region": r.get("region", ""), "industry": r.get("industry", ""),
                          "status": r.get("status", "")},
                    matched_fields=self._find_matched(query, r),
                ) for r in rows
            ]
            return SearchResult(items=items, total=total, query=query,
                               strategy=SearchStrategy.FULLTEXT, took_ms=0)

        # Fallback: SQLAlchemy Core (legacy path).
        # search_vector is generated with to_tsvector('simple', …) — must match.
        tsq = func.plainto_tsquery("simple", query)
        rank_expr = func.ts_rank(companies.c.search_vector, tsq)
        pattern = f"%{query.strip()}%"
        ilike_match = or_(
            companies.c.name_ar.ilike(pattern),
            companies.c.name_en.ilike(pattern),
            companies.c.cr_number.ilike(pattern),
            companies.c.city.ilike(pattern),
            companies.c.email.ilike(pattern),
        )
        conditions = [
            companies.c.tenant_id == tenant_id,
            or_(companies.c.search_vector.op("@@")(tsq), ilike_match),
        ]

        if filters:
            for field_name, value in filters.items():
                col_name = self._safe_col(field_name, self.ALLOWED_FILTER_FIELDS)
                conditions.append(companies.c[col_name] == value)

        boost = case(
            (companies.c.name_ar == query, 10),
            (companies.c.cr_number == query, 8),
            else_=5,
        )
        order_score = boost + func.coalesce(rank_expr, 0)

        count_stmt = (
            select(func.count())
            .select_from(companies)
            .where(*conditions)
        )
        results_stmt = (
            select(
                cast(companies.c.id, String).label("id"),
                companies.c.name_ar,
                companies.c.name_en,
                companies.c.cr_number,
                companies.c.city,
                companies.c.region,
                companies.c.industry,
                companies.c.status,
                companies.c.activity_description,
                rank_expr.label("relevance"),
            )
            .where(*conditions)
            .order_by(order_score.desc(), companies.c.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )

        async with self._session_factory() as session:
            await _set_tenant_guc(session, tenant_id)
            await _apply_statement_timeout(session)

            count_row = await session.execute(count_stmt)
            total = count_row.scalar() or 0

            rows = await session.execute(results_stmt)
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
        distance = companies.c.embedding.op("<->")(bindparam("emb"))
        similarity = (literal(1.0) / (literal(1.0) + distance)).label("similarity")
        stmt = (
            select(
                cast(companies.c.id, String).label("id"),
                companies.c.name_ar,
                companies.c.name_en,
                companies.c.cr_number,
                companies.c.city,
                companies.c.industry,
                companies.c.activity_description,
                similarity,
            )
            .where(
                companies.c.tenant_id == tenant_id,
                companies.c.embedding.is_not(None),
            )
            .order_by(distance)
            .limit(limit)
            .offset(offset)
        )
        async with self._session_factory() as session:
            await _set_tenant_guc(session, tenant_id)
            rows = await session.execute(stmt, {"emb": embedding})
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
        for field_name in ("name_ar", "name_en", "cr_number", "city", "activity_description"):
            val = str(row.get(field_name, "")).lower()
            if ql in val:
                fields.append(field_name)
        return fields

    async def _get_facets(self, query: str, tenant_id: str) -> dict[str, dict[str, int]]:
        async def _facet_for_field(field_name: str) -> tuple[str, dict[str, int]]:
            col_name = self._safe_col(field_name, self.ALLOWED_FACET_FIELDS)
            col = companies.c[col_name]
            tsq = func.plainto_tsquery("simple", query)
            pattern = f"%{query.strip()}%"
            ilike_match = or_(
                companies.c.name_ar.ilike(pattern),
                companies.c.name_en.ilike(pattern),
                companies.c.cr_number.ilike(pattern),
                companies.c.city.ilike(pattern),
                companies.c.email.ilike(pattern),
            )
            stmt = (
                select(col, func.count().label("cnt"))
                .where(
                    companies.c.tenant_id == tenant_id,
                    or_(companies.c.search_vector.op("@@")(tsq), ilike_match),
                    col.is_not(None),
                )
                .group_by(col)
                .order_by(func.count().desc())
                .limit(20)
            )
            async with self._session_factory() as session:
                await _set_tenant_guc(session, tenant_id)
                rows = await session.execute(stmt)
                data = {str(r[0]): r[1] for r in rows}
                return field_name, data

        results = await asyncio.gather(
            *[_facet_for_field(f) for f in self.ALLOWED_FACET_FIELDS],
            return_exceptions=True,
        )
        facets: dict[str, dict[str, int]] = {}
        for r in results:
            if isinstance(r, Exception):
                continue
            field_name, data = r
            if data:
                facets[field_name] = data
        return facets

    async def clear_cache(self) -> None:
        """Drop in-process search result cache (call after company create/update)."""
        self._cache.clear()

    async def close(self) -> None:
        """Release held resources."""
        self._cache.clear()
        if self._kg_engine and hasattr(self._kg_engine, "close"):
            await self._kg_engine.close()
        self._kg_engine = None
        self._session_factory = None  # type: ignore
        self._embedding_service = None  # type: ignore
        self._search_repo = None  # type: ignore
