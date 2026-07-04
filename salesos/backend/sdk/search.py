"""Search abstraction for full-text and vector search."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SearchResult:
    id: str
    score: float
    data: dict
    highlights: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class SearchQuery:
    query: str
    filters: dict[str, Any] | None = None
    page: int = 1
    page_size: int = 20
    sort_by: str | None = None
    sort_order: str = "desc"
    fuzzy: bool = False
    language: str = "arabic"
    min_score: float = 0.0


class FullTextSearch(ABC):
    """Full-text search abstraction.

    Implementations: PostgreSQL full-text, Elasticsearch, Meilisearch.
    """

    @abstractmethod
    async def search(self, query: SearchQuery) -> tuple[list[SearchResult], int]:
        """Execute a full-text search. Returns (results, total_count)."""

    @abstractmethod
    async def index(self, index_name: str, document_id: str, document: dict) -> None:
        """Index or update a document."""

    @abstractmethod
    async def bulk_index(
        self, index_name: str, documents: list[dict]
    ) -> None:
        """Bulk index multiple documents."""

    @abstractmethod
    async def delete_index(self, index_name: str) -> None:
        """Remove an entire index."""


class VectorSearch(ABC):
    """Vector search abstraction for semantic similarity.

    Implementations: pgvector, Pinecone, Weaviate, Qdrant.
    """

    @abstractmethod
    async def search(
        self, collection: str, vector: list[float], top_k: int = 10
    ) -> list[SearchResult]:
        """Search for nearest neighbors."""

    @abstractmethod
    async def upsert(
        self, collection: str, document_id: str, vector: list[float], metadata: dict
    ) -> None:
        """Insert or update a vector embedding."""

    @abstractmethod
    async def delete(self, collection: str, document_id: str) -> None:
        """Delete a vector embedding."""


ALLOWED_COLLECTIONS = frozenset({
    "company_embeddings", "contact_embeddings", "document_embeddings",
    "companies", "contacts", "licenses", "branches", "opportunities",
})


def _validate_collection(name: str) -> None:
    if name not in ALLOWED_COLLECTIONS:
        raise ValueError(f"Unknown collection: {name}")


class PgVectorSearch(VectorSearch):
    """pgvector-based vector search implementation."""

    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def search(
        self, collection: str, vector: list[float], top_k: int = 10
    ) -> list[SearchResult]:
        _validate_collection(collection)
        from sqlalchemy import text

        async with self._session_factory() as session:
            stmt = text(f"""
                SELECT id, metadata, 1 - (embedding <=> :vector::vector) AS score
                FROM {collection}
                ORDER BY embedding <=> :vector::vector
                LIMIT :top_k
            """)
            result = await session.execute(
                stmt, {"vector": vector, "top_k": top_k}
            )
            rows = result.fetchall()
            return [
                SearchResult(id=str(r.id), score=float(r.score), data=r.metadata or {})
                for r in rows
            ]

    async def upsert(
        self, collection: str, document_id: str, vector: list[float], metadata: dict
    ) -> None:
        _validate_collection(collection)
        from sqlalchemy import text

        async with self._session_factory() as session:
            stmt = text(f"""
                INSERT INTO {collection} (id, embedding, metadata)
                VALUES (:id, :vector::vector, :metadata::jsonb)
                ON CONFLICT (id)
                DO UPDATE SET embedding = :vector::vector, metadata = :metadata::jsonb
            """)
            await session.execute(
                stmt, {"id": document_id, "vector": vector, "metadata": metadata}
            )
            await session.commit()

    async def delete(self, collection: str, document_id: str) -> None:
        _validate_collection(collection)
        from sqlalchemy import text

        async with self._session_factory() as session:
            await session.execute(
                text(f"DELETE FROM {collection} WHERE id = :id"),
                {"id": document_id},
            )
            await session.commit()
