"""Search abstraction for full-text and vector search.

CI-19 Wave 2: PgVectorSearch uses SQLAlchemy Core only (no sqlalchemy.text).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import Column, MetaData, String, Table, bindparam, delete, literal, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import insert as pg_insert

_vector_metadata = MetaData()


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
    async def bulk_index(self, index_name: str, documents: list[dict]) -> None:
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


ALLOWED_COLLECTIONS = frozenset(
    {
        "company_embeddings",
        "contact_embeddings",
        "document_embeddings",
        "companies",
        "contacts",
        "licenses",
        "branches",
        "opportunities",
    }
)


def _validate_collection(name: str) -> None:
    if name not in ALLOWED_COLLECTIONS:
        raise ValueError(f"Unknown collection: {name}")


def _embedding_table(table_name: str) -> Table:
    """Allowlisted Core table for pgvector collections."""
    _validate_collection(table_name)
    return Table(
        table_name,
        _vector_metadata,
        Column("id", String, primary_key=True),
        Column("embedding", String),
        Column("metadata", JSONB),
        extend_existing=True,
    )


class PgVectorSearch(VectorSearch):
    """pgvector-based vector search implementation."""

    _TABLE_MAP: dict[str, str] = {
        "company_embeddings": "company_embeddings",
        "contact_embeddings": "contact_embeddings",
        "document_embeddings": "document_embeddings",
        "companies": "companies",
        "contacts": "contacts",
        "licenses": "licenses",
        "branches": "branches",
        "opportunities": "opportunities",
    }

    def __init__(self, session_factory):
        self._session_factory = session_factory

    def _safe_table(self, collection: str) -> str:
        if collection not in self._TABLE_MAP:
            raise ValueError(f"Unknown collection: {collection}")
        return self._TABLE_MAP[collection]

    async def search(
        self, collection: str, vector: list[float], top_k: int = 10
    ) -> list[SearchResult]:
        tbl = _embedding_table(self._safe_table(collection))
        distance = tbl.c.embedding.op("<=>")(bindparam("vector"))
        score = (literal(1) - distance).label("score")
        stmt = select(tbl.c.id, tbl.c.metadata, score).order_by(distance).limit(top_k)
        async with self._session_factory() as session:
            result = await session.execute(stmt, {"vector": str(vector)})
            rows = result.fetchall()
            return [
                SearchResult(id=str(r.id), score=float(r.score), data=r.metadata or {})
                for r in rows
            ]

    async def upsert(
        self, collection: str, document_id: str, vector: list[float], metadata: dict
    ) -> None:
        tbl = _embedding_table(self._safe_table(collection))
        stmt = pg_insert(tbl).values(
            id=document_id,
            embedding=str(vector),
            metadata=metadata,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[tbl.c.id],
            set_={"embedding": stmt.excluded.embedding, "metadata": stmt.excluded.metadata},
        )
        async with self._session_factory() as session:
            await session.execute(stmt)
            await session.commit()

    async def delete(self, collection: str, document_id: str) -> None:
        tbl = _embedding_table(self._safe_table(collection))
        async with self._session_factory() as session:
            await session.execute(delete(tbl).where(tbl.c.id == document_id))
            await session.commit()
