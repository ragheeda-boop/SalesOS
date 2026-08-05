"""PostgresSearchRepository - PostgreSQL infrastructure for the Search domain.

CI-19 Wave 2 Core (no sqlalchemy.text)

Implements the SearchRepository[Any] ABC from contracts/repository.py,
providing full-text search (tsvector/tsquery), faceted aggregation,
prefix suggestions, and filter-based queries against the companies table.

Uses a session_factory (async context manager) for connection lifecycle.

Architecture compliance:
  - Infrastructure layer: lives inside the domain but is the only place
    that touches raw SQL for search.
  - The SearchRuntime delegates to this repo instead of embedding SQL.
  - Implements SearchRepository[Any] ABC - the canonical contract.
"""

from __future__ import annotations

import base64
import json
import logging
import time
from collections.abc import Callable
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    MetaData,
    String,
    Table,
    and_,
    cast,
    func,
    literal,
    or_,
    select,
    union_all,
)
from sqlalchemy import text as sa_text
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession

from domains.search.contracts.models import SearchQuery, SearchResult
from domains.search.contracts.repository import SearchRepository

logger = logging.getLogger(__name__)

SEARCH_TIMEOUT_SECONDS = 10.0
MAX_PAGE_SIZE = 50
# Must match companies.search_vector generation (to_tsvector('simple', ...)).
FTS_LANGUAGE = "simple"

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

_search_metadata = MetaData()

companies = Table(
    "companies",
    _search_metadata,
    Column("id", PGUUID(as_uuid=True), primary_key=True),
    Column("tenant_id", PGUUID(as_uuid=True)),
    Column("name_ar", String),
    Column("name_en", String),
    Column("cr_number", String),
    Column("city", String),
    Column("region", String),
    Column("industry", String),
    Column("status", String),
    Column("legal_form", String),
    Column("activity", String),
    Column("is_active", Boolean),
    Column("phone", String),
    Column("email", String),
    Column("activity_description", String),
    Column("created_at", DateTime(timezone=True)),
    Column("updated_at", DateTime(timezone=True)),
    Column("search_vector", TSVECTOR),
)


def _filter_column(field_name: str):
    if field_name not in ALLOWED_FILTER_FIELDS:
        raise ValueError(f"Invalid filter field: {field_name}")
    return companies.c[field_name]


def _facet_column(field_name: str):
    if field_name not in ALLOWED_FACET_FIELDS:
        raise ValueError(f"Invalid facet field: {field_name}")
    return companies.c[field_name]


def _suggest_column(field_name: str):
    if field_name not in ALLOWED_SUGGEST_FIELDS:
        raise ValueError(f"Invalid suggest field: {field_name}")
    return companies.c[field_name]


def _fts_tsquery(query: str, fts_language: str):
    return func.plainto_tsquery(fts_language, query.strip())


def _fts_rank(query: str, fts_language: str):
    tsq = _fts_tsquery(query, fts_language)
    return func.ts_rank(companies.c.search_vector, tsq), tsq


def _parse_cursor_updated_at(value: str | None) -> datetime | str | None:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return value


async def _apply_statement_timeout(session: AsyncSession, timeout_seconds: float) -> None:
    await session.execute(
        select(
            func.set_config(
                "statement_timeout",
                str(int(timeout_seconds * 1000)),
                True,
            )
        )
    )


async def _set_tenant_guc(session: AsyncSession, tenant_id: str) -> None:
    """DEC-085: set app.tenant_id so companies RLS does not fail-closed."""
    await session.execute(
        sa_text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
        {"tenant_id": str(tenant_id)},
    )


def _cursor_predicate(
    rank_expr,
    cursor_rank: float,
    cursor_updated_at: str | None,
    cursor_id: str,
):
    cursor_uat = _parse_cursor_updated_at(cursor_updated_at)
    cursor_uuid: UUID | str = cursor_id
    try:
        cursor_uuid = UUID(cursor_id)
    except ValueError:
        pass
    return or_(
        rank_expr < cursor_rank,
        and_(rank_expr == cursor_rank, companies.c.updated_at < cursor_uat),
        and_(
            rank_expr == cursor_rank,
            companies.c.updated_at == cursor_uat,
            companies.c.id < cursor_uuid,
        ),
    )


def _search_select_columns(rank_expr):
    return [
        cast(companies.c.id, String).label("id"),
        companies.c.name_ar,
        companies.c.name_en,
        companies.c.cr_number,
        companies.c.city,
        companies.c.region,
        companies.c.industry,
        companies.c.status,
        companies.c.activity_description,
        companies.c.updated_at,
        rank_expr.label("rank"),
        func.count().over().label("total_count"),
    ]


def _finalize_search_rows(
    rows_raw: list[dict[str, Any]],
    safe_limit: int,
) -> tuple[list[dict[str, Any]], int, str | None]:
    total = rows_raw[0]["total_count"] if rows_raw else 0
    has_next = len(rows_raw) > safe_limit
    rows = rows_raw[:safe_limit]

    next_cursor = None
    if has_next and rows:
        last = rows[-1]
        next_cursor = encode_search_cursor(
            float(last["rank"]) if last["rank"] else 0.0,
            last.get("updated_at"),
            last["id"],
        )

    for row in rows:
        row.pop("total_count", None)
        row.pop("updated_at", None)

    return rows, total, next_cursor


def encode_search_cursor(rank: float, updated_at: Any, row_id: str) -> str:
    """Encode a keyset cursor from (rank, updated_at, id)."""
    raw: dict[str, Any] = {"id": row_id, "r": round(rank, 10)}
    if updated_at is not None:
        raw["u"] = updated_at.isoformat() if hasattr(updated_at, "isoformat") else str(updated_at)
    return base64.urlsafe_b64encode(json.dumps(raw, separators=(",", ":")).encode()).decode()


def decode_search_cursor(cursor: str) -> tuple[float, str | None, str]:
    """Decode a keyset cursor into (rank, updated_at_str, id)."""
    raw = json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
    return float(raw["r"]), raw.get("u"), str(raw["id"])


class PostgresSearchRepository(SearchRepository[Any]):
    """PostgreSQL-backed search repository for the Search domain."""

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

    async def search(self, query: SearchQuery) -> SearchResult[Any]:
        t0 = time.monotonic()
        filters = query.filters if query.filters else None
        cursor_rank: float | None = None
        cursor_updated_at: str | None = None
        cursor_id: str | None = None

        if query.cursor:
            cursor_rank, cursor_updated_at, cursor_id = decode_search_cursor(query.cursor)

        if filters:
            rows, total, next_cursor = await self.search_by_filters(
                query=query.query,
                tenant_id=query.tenant_id,
                filters=filters,
                limit=query.page_size,
                offset=(query.page - 1) * query.page_size if not query.cursor else 0,
                cursor_rank=cursor_rank,
                cursor_updated_at=cursor_updated_at,
                cursor_id=cursor_id,
            )
        else:
            rows, total, next_cursor = await self.search_raw(
                query=query.query,
                tenant_id=query.tenant_id,
                limit=query.page_size,
                offset=(query.page - 1) * query.page_size if not query.cursor else 0,
                cursor_rank=cursor_rank,
                cursor_updated_at=cursor_updated_at,
                cursor_id=cursor_id,
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
            next_cursor=next_cursor,
        )

    async def count(self, query: SearchQuery) -> int:
        return await self.count_raw(
            query=query.query,
            tenant_id=query.tenant_id,
            filters=query.filters if query.filters else None,
        )

    async def facets(self, query: SearchQuery, fields: list[str]) -> dict[str, dict[str, int]]:
        return await self.facets_raw(
            query=query.query,
            tenant_id=query.tenant_id,
            fields=fields,
        )

    async def suggest(self, query: SearchQuery, field: str, prefix: str, limit: int = 10) -> list[str]:
        return await self.suggest_raw(
            prefix=prefix,
            tenant_id=query.tenant_id,
            field=field,
            limit=limit,
        )

    async def search_raw(
        self,
        query: str,
        tenant_id: str,
        limit: int = 20,
        offset: int = 0,
        cursor_rank: float | None = None,
        cursor_updated_at: str | None = None,
        cursor_id: str | None = None,
    ) -> tuple[list[dict[str, Any]], int, str | None]:
        safe_limit = min(limit, MAX_PAGE_SIZE)
        if not query or not query.strip():
            return [], 0, None

        rank_expr, tsq = _fts_rank(query, self._fts_language)
        fts_match = companies.c.search_vector.op("@@")(tsq)
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
            or_(fts_match, ilike_match),
        ]
        use_cursor = cursor_rank is not None and cursor_id is not None
        if use_cursor:
            conditions.append(
                _cursor_predicate(rank_expr, cursor_rank, cursor_updated_at, cursor_id)
            )

        stmt = (
            select(*_search_select_columns(rank_expr))
            .where(and_(*conditions))
            .order_by(rank_expr.desc(), companies.c.updated_at.desc(), companies.c.id.desc())
        )

        if use_cursor:
            stmt = stmt.limit(safe_limit + 1)
        else:
            stmt = stmt.limit(safe_limit).offset(offset)

        async with self._session_factory() as session:
            await _set_tenant_guc(session, tenant_id)
            await _apply_statement_timeout(session, self._timeout)
            result = await session.execute(stmt)
            rows_raw = [dict(r._mapping) for r in result.fetchall()]

        return _finalize_search_rows(rows_raw, safe_limit)

    async def search_by_filters(
        self,
        query: str,
        tenant_id: str,
        filters: dict[str, str] | None = None,
        limit: int = 20,
        offset: int = 0,
        cursor_rank: float | None = None,
        cursor_updated_at: str | None = None,
        cursor_id: str | None = None,
    ) -> tuple[list[dict[str, Any]], int, str | None]:
        safe_limit = min(limit, MAX_PAGE_SIZE)
        if not query or not query.strip():
            return [], 0, None

        rank_expr, tsq = _fts_rank(query, self._fts_language)
        fts_match = companies.c.search_vector.op("@@")(tsq)
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
            or_(fts_match, ilike_match),
        ]

        if filters:
            for field_name, value in filters.items():
                if field_name in ALLOWED_FILTER_FIELDS and value is not None:
                    conditions.append(_filter_column(field_name) == value)

        use_cursor = cursor_rank is not None and cursor_id is not None
        if use_cursor:
            conditions.append(
                _cursor_predicate(rank_expr, cursor_rank, cursor_updated_at, cursor_id)
            )

        stmt = (
            select(*_search_select_columns(rank_expr))
            .where(and_(*conditions))
            .order_by(rank_expr.desc(), companies.c.updated_at.desc(), companies.c.id.desc())
        )

        if use_cursor:
            stmt = stmt.limit(safe_limit + 1)
        else:
            stmt = stmt.limit(safe_limit).offset(offset)

        async with self._session_factory() as session:
            await _set_tenant_guc(session, tenant_id)
            await _apply_statement_timeout(session, self._timeout)
            result = await session.execute(stmt)
            rows_raw = [dict(r._mapping) for r in result.fetchall()]

        return _finalize_search_rows(rows_raw, safe_limit)

    async def count_raw(
        self,
        query: str,
        tenant_id: str,
        filters: dict[str, str] | None = None,
    ) -> int:
        if not query or not query.strip():
            return 0

        _, tsq = _fts_rank(query, self._fts_language)
        fts_match = companies.c.search_vector.op("@@")(tsq)
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
            or_(fts_match, ilike_match),
        ]

        if filters:
            for field_name, value in filters.items():
                if field_name in ALLOWED_FILTER_FIELDS and value is not None:
                    conditions.append(_filter_column(field_name) == value)

        stmt = select(func.count()).select_from(companies).where(and_(*conditions))

        async with self._session_factory() as session:
            await _set_tenant_guc(session, tenant_id)
            result = await session.execute(stmt)
            return result.scalar() or 0

    async def facets_raw(
        self,
        query: str,
        tenant_id: str,
        fields: list[str] | None = None,
    ) -> dict[str, dict[str, int]]:
        target_fields = [f for f in (fields or []) if f in ALLOWED_FACET_FIELDS]
        if not target_fields or not query or not query.strip():
            return {}

        _, tsq = _fts_rank(query, self._fts_language)
        fts_match = companies.c.search_vector.op("@@")(tsq)
        pattern = f"%{query.strip()}%"
        ilike_match = or_(
            companies.c.name_ar.ilike(pattern),
            companies.c.name_en.ilike(pattern),
            companies.c.cr_number.ilike(pattern),
            companies.c.city.ilike(pattern),
            companies.c.email.ilike(pattern),
        )
        text_match = or_(fts_match, ilike_match)
        union_parts = []
        for field in target_fields:
            col = _facet_column(field)
            union_parts.append(
                select(
                    literal(field).label("facet_field"),
                    col.label("facet_value"),
                    func.count().label("facet_count"),
                )
                .where(
                    companies.c.tenant_id == tenant_id,
                    text_match,
                    col.is_not(None),
                )
                .group_by(col)
                .order_by(func.count().desc())
                .limit(20)
            )

        stmt = union_all(*union_parts)
        results: dict[str, dict[str, int]] = {}

        async with self._session_factory() as session:
            await _set_tenant_guc(session, tenant_id)
            rows = await session.execute(stmt)
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
        if field not in ALLOWED_SUGGEST_FIELDS or not prefix or not prefix.strip():
            return []

        col = _suggest_column(field)
        stmt = (
            select(col)
            .distinct()
            .where(
                companies.c.tenant_id == tenant_id,
                col.ilike(f"{prefix.strip()}%"),
            )
            .order_by(col)
            .limit(limit)
        )

        async with self._session_factory() as session:
            await _set_tenant_guc(session, tenant_id)
            result = await session.execute(stmt)
            return [str(r[0]) for r in result if r[0] is not None]
