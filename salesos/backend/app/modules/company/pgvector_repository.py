"""PgVectorCompanyRepository — semantic search executor using VectorStore.

Implements SearchRepository[Company] for semantic/similarity search.
Uses VectorStore abstraction (InMemoryVectorStore for dev, PgVectorStore for prod).

Does NOT replace CompanySearchRepository. Adds semantic capability.
All SDK imports are lazy (inside methods) to avoid eager __init__.py chain.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domains.search.contracts.models import SearchQuery, SearchResult
from domains.search.contracts.repository import SearchRepository
from domains.search.engine.vector_store import InMemoryVectorStore, VectorRecord, VectorStore


class PgVectorCompanyRepository(SearchRepository[Any]):

    def __init__(
        self,
        db: AsyncSession,
        vector_store: VectorStore | None = None,
        embedding_service: Any = None,
    ):
        self.db = db
        self._store = vector_store or InMemoryVectorStore()
        self._embedding_service = embedding_service

    @property
    def store(self) -> VectorStore:
        return self._store

    async def _embed_query(self, query: SearchQuery) -> list[float]:
        if not self._embedding_service:
            from sdk.vector import OpenAIEmbeddingService
            self._embedding_service = OpenAIEmbeddingService()
        return await self._embedding_service.embed(query.query)

    async def _vector_search(
        self, embedding: list[float], query: SearchQuery
    ) -> SearchResult[Any]:
        records = await self._store.search(embedding, top_k=query.page_size)
        if not records:
            return SearchResult(
                items=[],
                total=0,
                page=query.page,
                page_size=query.page_size,
                query=query.query,
                strategy=self._store.__class__.__name__,
                ranking_version="1.0",
            )

        from app.modules.company.models import Company

        company_ids = [r.id for r in records]
        stmt = select(Company).where(Company.id.in_(company_ids))
        result = await self.db.execute(stmt)
        companies = {str(c.id): c for c in result.scalars().all()}

        items = [companies[cid] for cid in company_ids if cid in companies]
        ranking = [
            {"field": "vector_similarity", "score": r.score, "id": r.id}
            for r in records
            if r.id in companies
        ]

        return SearchResult(
            items=items,
            total=len(items),
            page=query.page,
            page_size=query.page_size,
            ranking=ranking,
            query=query.query,
            strategy=self._store.__class__.__name__,
            ranking_version="1.0",
        )

    async def search(self, query: SearchQuery) -> SearchResult[Any]:
        embedding = await self._embed_query(query)
        return await self._vector_search(embedding, query)

    async def similar_to(self, company_id: str, top_k: int = 10) -> SearchResult[Any]:
        if hasattr(self._store, "_records") and company_id in self._store._records:
            source = self._store._records[company_id]
            query = SearchQuery(query="", page_size=top_k + 1)  # +1 because source may appear
            result = await self._vector_search(source.vector, query)
            result.items = [item for item in result.items if str(item.id) != company_id][:top_k]
            result.total = len(result.items)
            return result
        return SearchResult(items=[], total=0)

    async def seed_from_database(self) -> int:
        """Index all companies from the database into the vector store.

        Call this once when setting up semantic search.
        """
        from app.modules.company.models import Company

        result = await self.db.execute(select(Company))
        companies = result.scalars().all()

        count = 0
        for company in companies:
            text = f"{company.name_ar} {company.name_en or ''} {company.activity_description or ''} {company.city or ''}"
            embedding = await self._embed_query(SearchQuery(query=text))
            await self._store.upsert(VectorRecord(
                id=str(company.id),
                vector=embedding,
                metadata={
                    "name_ar": company.name_ar,
                    "name_en": company.name_en,
                    "cr_number": company.cr_number,
                    "city": company.city,
                    "activity": company.activity_description,
                },
            ))
            count += 1

        return count

    async def count(self, query: SearchQuery) -> int:
        return await self._store.count()

    async def facets(self, query: SearchQuery, fields: list[str]) -> dict[str, dict[str, int]]:
        return {}

    async def suggest(self, query: SearchQuery, field: str, prefix: str, limit: int = 10) -> list[str]:
        return []
