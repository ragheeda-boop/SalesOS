"""CompanySearchRepository — SearchRepository[Company] implementation.

This is the bridge between the Company module and the Search Domain.
Every company-specific search concern lives here, not in the service or router.
"""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from domains.search.contracts.models import SearchQuery, SearchResult, SearchSort
from domains.search.contracts.repository import SearchRepository


class CompanySearchRepository(SearchRepository[Any]):

    def __init__(self, db: AsyncSession):
        from app.modules.company.models import Company

        self._Company = Company
        self.db = db

    def _build_base(self, query: SearchQuery):
        Company = self._Company
        stmt = select(Company).where(Company.tenant_id == uuid.UUID(query.tenant_id))

        parsed = query.context.get("parsed")
        if parsed:
            if parsed.tokens:
                token_conditions = []
                for token in parsed.tokens:
                    token_conditions.append(
                        or_(
                            Company.name_ar.ilike(f"%{token}%"),
                            Company.name_en.ilike(f"%{token}%"),
                            Company.cr_number.ilike(f"%{token}%"),
                            Company.city.ilike(f"%{token}%"),
                            Company.activity_description.ilike(f"%{token}%"),
                        )
                    )
                if token_conditions:
                    stmt = stmt.where(or_(*token_conditions))

            if parsed.phrases:
                for phrase in parsed.phrases:
                    stmt = stmt.where(
                        or_(
                            Company.name_ar.ilike(f"%{phrase}%"),
                            Company.name_en.ilike(f"%{phrase}%"),
                        )
                    )

            ff = parsed.field_filters
            if "cr" in ff or "cr_number" in ff:
                cr_val = ff.get("cr") or ff["cr_number"]
                stmt = stmt.where(Company.cr_number.ilike(f"%{cr_val}%"))
            if "city" in ff:
                stmt = stmt.where(Company.city.ilike(f"%{ff['city']}%"))
            if "region" in ff:
                stmt = stmt.where(Company.region.ilike(f"%{ff['region']}%"))
            if "status" in ff:
                stmt = stmt.where(Company.status == ff["status"])
            if "activity" in ff:
                stmt = stmt.where(Company.activity_description.ilike(f"%{ff['activity']}%"))
            if "legal_form" in ff:
                stmt = stmt.where(Company.legal_form.ilike(f"%{ff['legal_form']}%"))

        for field, value in query.filters.items():
            if hasattr(Company, field):
                if isinstance(value, dict):
                    if "eq" in value:
                        stmt = stmt.where(getattr(Company, field) == value["eq"])
                    if "in" in value:
                        stmt = stmt.where(getattr(Company, field).in_(value["in"]))
                    if "gte" in value:
                        stmt = stmt.where(getattr(Company, field) >= value["gte"])
                    if "lte" in value:
                        stmt = stmt.where(getattr(Company, field) <= value["lte"])
                else:
                    stmt = stmt.where(getattr(Company, field) == value)

        return stmt

    def _apply_sort(self, stmt, query: SearchQuery):
        Company = self._Company
        sort = query.sort or SearchSort(field="created_at", direction="desc")

        sort_map = {
            "name": Company.name_ar,
            "name_ar": Company.name_ar,
            "name_en": Company.name_en,
            "cr_number": Company.cr_number,
            "cr": Company.cr_number,
            "status": Company.status,
            "city": Company.city,
            "region": Company.region,
            "created_at": Company.created_at,
            "updated_at": Company.updated_at,
            "confidence_score": Company.confidence_score,
        }

        col = sort_map.get(sort.field, Company.created_at)
        if sort.direction == "asc":
            stmt = stmt.order_by(col.asc().nullslast())
        else:
            stmt = stmt.order_by(col.desc().nullslast())
        return stmt

    async def search(self, query: SearchQuery) -> SearchResult[Any]:
        base = self._build_base(query)
        cq = select(func.count()).select_from(base.subquery())
        tr = await self.db.execute(cq)
        total = tr.scalar() or 0

        fq = self._apply_sort(base, query)
        fq = fq.offset((query.page - 1) * query.page_size).limit(query.page_size)
        r = await self.db.execute(fq)
        companies = list(r.scalars().all())

        return SearchResult(
            items=companies,
            total=total,
            page=query.page,
            page_size=query.page_size,
            filters=query.filters,
            query=query.query,
        )

    async def count(self, query: SearchQuery) -> int:
        base = self._build_base(query)
        cq = select(func.count()).select_from(base.subquery())
        r = await self.db.execute(cq)
        return r.scalar() or 0

    async def facets(self, query: SearchQuery, fields: list[str]) -> dict[str, dict[str, int]]:
        Company = self._Company
        base = self._build_base(query)
        result: dict[str, dict[str, int]] = {}

        for field in fields:
            if hasattr(Company, field):
                col = getattr(Company, field)
                sub = base.subquery()
                fq = select(col, func.count().label("cnt")).select_from(sub).group_by(col).order_by(text("cnt desc")).limit(20)
                r = await self.db.execute(fq)
                result[field] = {str(row[0] or "unknown"): row[1] for row in r}

        return result

    async def suggest(self, query: SearchQuery, field: str, prefix: str, limit: int = 10) -> list[str]:
        Company = self._Company
        if not hasattr(Company, field):
            return []

        col = getattr(Company, field)
        stmt = (
            select(col)
            .where(Company.tenant_id == uuid.UUID(query.tenant_id), col.ilike(f"{prefix}%"))
            .distinct()
            .limit(limit)
        )
        r = await self.db.execute(stmt)
        return [str(row[0]) for row in r if row[0]]
