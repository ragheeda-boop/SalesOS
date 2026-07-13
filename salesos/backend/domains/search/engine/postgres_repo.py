"""PostgresSearchRepository — PostgreSQL infrastructure for the Search domain.

Implements the SearchRepository[Any] ABC from contracts/repository.py,
providing full-text search (tsvector/tsquery), faceted aggregation,
prefix suggestions, and filter-based queries against the companies table.

Uses a session_factory (async context manager) for connection lifecycle.

Architecture compliance:
  - Infrastructure layer: lives inside the domain but is the only place
    that touches raw SQL for search.
  - The SearchRuntime delegates to this repo instead of embedding SQL.
  - Implements SearchRepository[Any] ABC — the canonical contract.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from domains.search.contracts.models import SearchQuery, SearchResult
from domains.search.contracts.repository import SearchRepository

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────

SEARCH_TIMEOUT_SECONDS = 10.0
MAX_PAGE_SIZE = 50
FTS_LANGUAGE = "arabic"

ALLOWED_FTS_LANGUAGES = frozenset({"arabic", "english", "simple"})

ALLOWED_FILTER_FIELDS = frozenset({
    "city", "region", "industry", "status", "legal_form",
    "activity", "is_active", "created_at", "updated_at",
    "cr_number", "phone", "email",
})

ALLOWED_FACET_FIELDS = frozenset({
    "city", "region", "industry", "status", "legal_form",
})

ALLOWED_SUGGEST_FIELDS = frozenset({
    "name_ar", "name_en", "cr_number", "city", "email", "phone",
})


class PostgresSearchRepository(SearchRepository[Any]):
    """PostgreSQL-backed search repository for the Search domain.

    Implements the SearchRepository[Any] ABC. Raw SQL methods are
    available for direct use by SearchRuntime and HybridSearchEngine.

    Usage (ABC contract):
        repo = PostgresSearchRepository(session_factory=async_session)
        result = await repo.search(SearchQuery(query="شركات", tenant_id="t1"))

    Usage (raw search):
        rows, total = await repo.search_raw("شركات", tenant_id="t1")
    """

    def __init__(
        self,
        session_factory: Callable[[], AsyncSession],
        fts_language: str = FTS_LANGUAGE,
        timeout_seconds: float = SEARCH_TIMEOUT_SECONDS,
    ):
        self._session_factory = session_factory
        if fts_language not in ALLOWED_FTS_LANGUAGES:
            raise ValueError(f"Invalid FTS language: {fts_language}")
        self._fts_language = fts_language
        self._timeout = timeout_seconds

    # ── SearchRepository[Any] ABC implementation ─────────────────

    async def search(self, query: SearchQuery) -> SearchResult[Any]:
        """Full-text search via the ABC contract.

        Delegates to search_by_filters when structured filters are present,
        otherwise to search_raw for pure full-text queries.
        """
        t0 = time.monotonic()
        filters = query.filters if query.filters else None
        offset = (query.page - 1) * query.page_size

        if filters:
            rows, total = await self.search_by_filters(
                query=query.query,
                tenant_id=query.tenant_id,
                filters=filters,
                limit=query.page_size,
                offset=offset,
            )
        else:
            rows, total = await self.search_raw(
                query=query.query,
                tenant_id=query.tenant_id,
                limit=query.page_size,
                offset=offset,
            )

        took_ms = (time.monotonic() - t0) * 1000

        return SearchResult(
            items=rows,
            total=total,
            page=query.page,
            page_size=query.page_size,
            filters=query.filters,
            query=query.query,
            duration_ms=round(took_ms, 2),
            strategy="postgres",
        )

    async def count(self, query: SearchQuery) -> int:
        """Count companies matching the full-text query + filters (ABC)."""
        return await self.count_raw(
            query=query.query,
            tenant_id=query.tenant_id,
            filters=query.filters if query.filters else None,
        )

    async def facets(self, query: SearchQuery, fields: list[str]) -> dict[str, dict[str, int]]:
        """Aggregate facet counts for the given fields (ABC)."""
        return await self.facets_raw(
            query=query.query,
            tenant_id=query.tenant_id,
            fields=fields,
        )

    async def suggest(self, query: SearchQuery, field: str, prefix: str, limit: int = 10) -> list[str]:
        """Prefix-based auto-complete suggestions (ABC)."""
        return await self.suggest_raw(
            prefix=prefix,
            tenant_id=query.tenant_id,
            field=field,
            limit=limit,
        )

    # ── Raw SQL methods (used by SearchRuntime, HybridSearchEngine) ──

    async def search_raw(
        self,
        query: str,
        tenant_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        """Full-text search using PostgreSQL tsvector/tsquery with GIN index.

        Returns:
            (rows, total_count) — rows are dicts with company fields + rank.
        """
        safe_limit = min(limit, MAX_PAGE_SIZE)
        if not query or not query.strip():
            return [], 0

        async with self._session_factory() as session:
            await session.execute(
                sa_text(f"SET LOCAL statement_timeout = '{int(self._timeout * 1000)}'")
            )

            sql = sa_text(f"""
                SELECT c.id::text, c.name_ar, c.name_en, c.cr_number,
                       c.city, c.region, c.industry, c.status,
                       c.activity_description,
                       ts_rank(c.search_vector, plainto_tsquery('{self._fts_language}', :q)) AS rank,
                       count(*) OVER() AS total_count
                FROM companies c
                WHERE c.tenant_id = :tid
                  AND c.search_vector @@ plainto_tsquery('{self._fts_language}', :q)
                ORDER BY rank DESC, c.updated_at DESC
                LIMIT :lim OFFSET :off
            """)

            result = await session.execute(sql, {
                "q": query.strip(),
                "tid": tenant_id,
                "lim": safe_limit,
                "off": offset,
            })
            rows = [dict(r._mapping) for r in result.fetchall()]
            total = rows[0]["total_count"] if rows else 0
            return rows, total

    async def search_by_filters(
        self,
        query: str,
        tenant_id: str,
        filters: dict[str, str] | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        """Full-text search with structured field filters.

        Args:
            query: Search text (tsquery-compatible)
            tenant_id: Tenant UUID for multi-tenant isolation
            filters: Dict of field=value pairs (city, region, industry, etc.)
            limit: Max results to return
            offset: Pagination offset

        Returns:
            (rows, total_count)
        """
        safe_limit = min(limit, MAX_PAGE_SIZE)
        if not query or not query.strip():
            return [], 0

        conditions = [
            "c.tenant_id = :tid",
            f"c.search_vector @@ plainto_tsquery('{self._fts_language}', :q)",
        ]
        params: dict[str, Any] = {
            "q": query.strip(),
            "tid": tenant_id,
            "lim": safe_limit,
            "off": offset,
        }

        if filters:
            for field_name, value in filters.items():
                if field_name in ALLOWED_FILTER_FIELDS and value is not None:
                    conditions.append(f"c.{field_name} = :fltr_{field_name}")
                    params[f"fltr_{field_name}"] = value

        where_clause = " AND ".join(conditions)

        async with self._session_factory() as session:
            await session.execute(
                sa_text(f"SET LOCAL statement_timeout = '{int(self._timeout * 1000)}'")
            )

            # Count total matching rows
            count_sql = sa_text(f"SELECT count(*) FROM companies c WHERE {where_clause}")
            count_result = await session.execute(count_sql, params)
            total = count_result.scalar() or 0

            # Fetch results
            sql = sa_text(f"""
                SELECT c.id::text, c.name_ar, c.name_en, c.cr_number,
                       c.city, c.region, c.industry, c.status,
                       c.activity_description,
                       ts_rank(c.search_vector, plainto_tsquery('{self._fts_language}', :q)) AS rank
                FROM companies c
                WHERE {where_clause}
                ORDER BY rank DESC, c.updated_at DESC
                LIMIT :lim OFFSET :off
            """)
            result = await session.execute(sql, params)
            rows = [dict(r._mapping) for r in result.fetchall()]
            return rows, total

    async def count_raw(
        self,
        query: str,
        tenant_id: str,
        filters: dict[str, str] | None = None,
    ) -> int:
        """Count companies matching the full-text query + filters."""
        if not query or not query.strip():
            return 0

        conditions = [
            "c.tenant_id = :tid",
            f"c.search_vector @@ plainto_tsquery('{self._fts_language}', :q)",
        ]
        params: dict[str, Any] = {"q": query.strip(), "tid": tenant_id}

        if filters:
            for field_name, value in filters.items():
                if field_name in ALLOWED_FILTER_FIELDS and value is not None:
                    conditions.append(f"c.{field_name} = :fltr_{field_name}")
                    params[f"fltr_{field_name}"] = value

        where_clause = " AND ".join(conditions)

        async with self._session_factory() as session:
            result = await session.execute(
                sa_text(f"SELECT count(*) FROM companies c WHERE {where_clause}"),
                params,
            )
            return result.scalar() or 0

    async def facets_raw(
        self,
        query: str,
        tenant_id: str,
        fields: list[str] | None = None,
    ) -> dict[str, dict[str, int]]:
        """Aggregate facet counts for the given fields in a single round-trip.

        Uses UNION ALL across all requested facet fields to execute one
        SQL statement instead of N sequential queries (N+1 fix).

        Returns:
            {field_name: {value: count, ...}, ...}
        """
        target_fields = [f for f in (fields or []) if f in ALLOWED_FACET_FIELDS]
        if not target_fields or not query or not query.strip():
            return {}

        union_parts = []
        for field in target_fields:
            union_parts.append(
                f"SELECT '{field}' AS facet_field, c.{field} AS facet_value, COUNT(*) AS facet_count "
                f"FROM companies c "
                f"WHERE c.tenant_id = :tid "
                f"AND c.search_vector @@ plainto_tsquery('{self._fts_language}', :q) "
                f"AND c.{field} IS NOT NULL "
                f"GROUP BY c.{field} "
                f"ORDER BY facet_count DESC "
                f"LIMIT 20"
            )

        combined_sql = " UNION ALL ".join(union_parts)

        results: dict[str, dict[str, int]] = {}

        async with self._session_factory() as session:
            rows = await session.execute(
                sa_text(combined_sql),
                {"tid": tenant_id, "q": query.strip()},
            )
            for row in rows:
                field_name = row[0]
                value = str(row[1])
                count = row[2]
                if field_name and value:
                    if field_name not in results:
                        results[field_name] = {}
                    results[field_name][value] = count

        return results

    async def suggest_raw(
        self,
        prefix: str,
        tenant_id: str,
        field: str = "name_ar",
        limit: int = 10,
    ) -> list[str]:
        """Prefix-based auto-complete suggestions for a field."""
        if field not in ALLOWED_SUGGEST_FIELDS or not prefix or not prefix.strip():
            return []

        async with self._session_factory() as session:
            sql = sa_text(f"""
                SELECT DISTINCT c.{field}
                FROM companies c
                WHERE c.tenant_id = :tid
                  AND c.{field} ILIKE :prefix
                ORDER BY c.{field}
                LIMIT :lim
            """)
            result = await session.execute(sql, {
                "tid": tenant_id,
                "prefix": f"{prefix.strip()}%",
                "lim": limit,
            })
            return [str(r[0]) for r in result if r[0] is not None]
