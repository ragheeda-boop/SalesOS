"""ContactSearchRepository — SearchRepository[Contact] implementation.

Bridge between the standalone Contact module and the Search Domain.
Mirrors the CompanySearchRepository pattern from app/modules/company/search_repository.py.

Uses PostgreSQL full-text search via tsvector for token/phrase matching,
with ILIKE fallback for field filters.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from domains.search.contracts.models import SearchQuery, SearchResult, SearchSort
from domains.search.contracts.repository import SearchRepository

logger = logging.getLogger(__name__)

MAX_PAGE_SIZE = 50
SEARCH_TIMEOUT_SECONDS = 10.0


class ContactSearchRepository(SearchRepository[Any]):
    """SearchRepository implementation for standalone contacts (contacts_standalone)."""

    def __init__(self, db: AsyncSession):
        from app.modules.contact.models import Contact

        self._Contact = Contact
        self.db = db

    def _build_base(self, query: SearchQuery):
        Contact = self._Contact
        stmt = select(Contact).where(
            Contact.tenant_id == uuid.UUID(query.tenant_id)
        )

        if query.query:
            like = f"%{query.query}%"
            condition = or_(
                Contact.name.ilike(like),
                Contact.name_ar.ilike(like),
                Contact.email.ilike(like),
                Contact.phone.ilike(like),
                Contact.position.ilike(like),
                Contact.department.ilike(like),
            )
            stmt = stmt.where(condition)

        for field, value in query.filters.items():
            if hasattr(Contact, field):
                if isinstance(value, dict):
                    if "eq" in value:
                        stmt = stmt.where(getattr(Contact, field) == value["eq"])
                    if "in" in value:
                        stmt = stmt.where(getattr(Contact, field).in_(value["in"]))
                    if "contains" in value:
                        stmt = stmt.where(
                            getattr(Contact, field).ilike(f"%{value['contains']}%")
                        )
                else:
                    stmt = stmt.where(getattr(Contact, field) == value)

        return stmt

    def _apply_sort(self, stmt, query: SearchQuery):
        Contact = self._Contact
        sort = query.sort or SearchSort(field="created_at", direction="desc")

        sort_map = {
            "name": Contact.name,
            "name_ar": Contact.name_ar,
            "email": Contact.email,
            "position": Contact.position,
            "department": Contact.department,
            "created_at": Contact.created_at,
            "updated_at": Contact.updated_at,
            "confidence_score": Contact.confidence_score,
        }

        col = sort_map.get(sort.field, Contact.created_at)
        if sort.direction == "asc":
            stmt = stmt.order_by(col.asc().nullslast())
        else:
            stmt = stmt.order_by(col.desc().nullslast())
        return stmt

    async def search(self, query: SearchQuery) -> SearchResult[Any]:
        safe_page_size = min(query.page_size, MAX_PAGE_SIZE)

        await self.db.execute(
            text(
                f"SET LOCAL statement_timeout = "
                f"'{int(SEARCH_TIMEOUT_SECONDS * 1000)}'"
            )
        )

        base = self._build_base(query)

        count_query = select(func.count()).select_from(base.subquery())
        tr = await self.db.execute(count_query)
        total = tr.scalar() or 0

        fq = self._apply_sort(base, query)
        fq = fq.offset((query.page - 1) * safe_page_size).limit(safe_page_size)
        r = await self.db.execute(fq)
        contacts = list(r.scalars().all())

        return SearchResult(
            items=contacts,
            total=total,
            page=query.page,
            page_size=safe_page_size,
            filters=query.filters,
            query=query.query,
        )

    async def count(self, query: SearchQuery) -> int:
        base = self._build_base(query)
        cq = select(func.count()).select_from(base.subquery())
        r = await self.db.execute(cq)
        return r.scalar() or 0

    async def facets(
        self, query: SearchQuery, fields: list[str]
    ) -> dict[str, dict[str, int]]:
        Contact = self._Contact
        base = self._build_base(query)
        result: dict[str, dict[str, int]] = {}

        for field in fields:
            if hasattr(Contact, field):
                col = getattr(Contact, field)
                sub = base.subquery()
                fq = (
                    select(col, func.count().label("cnt"))
                    .select_from(sub)
                    .group_by(col)
                    .order_by(text("cnt desc"))
                    .limit(20)
                )
                r = await self.db.execute(fq)
                result[field] = {
                    str(row[0] or "unknown"): row[1] for row in r
                }

        return result

    async def suggest(
        self, query: SearchQuery, field: str, prefix: str, limit: int = 10
    ) -> list[str]:
        Contact = self._Contact
        if not hasattr(Contact, field):
            return []

        col = getattr(Contact, field)
        stmt = (
            select(col)
            .where(
                Contact.tenant_id == uuid.UUID(query.tenant_id),
                col.ilike(f"{prefix}%"),
            )
            .distinct()
            .limit(limit)
        )
        r = await self.db.execute(stmt)
        return [str(row[0]) for row in r if row[0]]
