"""Vector store abstraction for semantic search.

Supports both pgvector (production) and in-memory (development/demo).

CI-19 Wave 2: PgVectorStore uses SQLAlchemy Core only (no sqlalchemy.text).
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import (
    Column,
    DateTime,
    Index,
    MetaData,
    String,
    Table,
    Text,
    bindparam,
    delete,
    func,
    literal,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB, insert as pg_insert

_ALLOWED_COLLECTIONS = frozenset({
    "vectors", "company_embeddings", "contact_embeddings",
    "document_embeddings",
})

_vector_store_metadata = MetaData()


def _validate_collection(name: str) -> str:
    """Validate table/collection name against allowlist to prevent SQL injection."""
    if name not in _ALLOWED_COLLECTIONS:
        raise ValueError(f"Invalid collection name: {name}")
    return name


def _collection_table(name: str) -> Table:
    """Core Table for PgVectorStore collections.

    DEC-130f: include live ``created_at`` / ``updated_at`` so alembic check does
    not propose ``remove_column`` DROP (columns from migration 0010).
    """
    table_name = _validate_collection(name)
    return Table(
        table_name,
        _vector_store_metadata,
        Column("id", Text, primary_key=True),
        Column("embedding", String, nullable=False),
        Column("metadata", JSONB, nullable=False),
        Column("created_at", DateTime(timezone=True)),
        Column("updated_at", DateTime(timezone=True)),
        Index("ix_vectors_created_at", "created_at"),
        extend_existing=True,
    )


@dataclass
class VectorRecord:
    id: str
    vector: list[float]
    metadata: dict[str, Any] = field(default_factory=dict)
    score: float = 0.0


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class VectorStore(ABC):

    @abstractmethod
    async def search(self, vector: list[float], top_k: int = 10) -> list[VectorRecord]: ...

    @abstractmethod
    async def upsert(self, record: VectorRecord) -> None: ...

    @abstractmethod
    async def delete(self, record_id: str) -> None: ...

    @abstractmethod
    async def count(self) -> int: ...


class InMemoryVectorStore(VectorStore):
    """Simple in-memory vector store for development/demo.

    Uses brute-force cosine similarity. NOT for production.
    Swap with PgVectorStore when pgvector extension is available.
    """

    def __init__(self):
        self._records: dict[str, VectorRecord] = {}

    async def search(self, vector: list[float], top_k: int = 10) -> list[VectorRecord]:
        scored = []
        for r in self._records.values():
            score = cosine_similarity(vector, r.vector)
            scored.append(VectorRecord(id=r.id, vector=r.vector, metadata=r.metadata, score=score))

        scored.sort(key=lambda x: x.score, reverse=True)
        return [r for r in scored[:top_k] if r.score > 0]

    async def upsert(self, record: VectorRecord) -> None:
        self._records[record.id] = record

    async def delete(self, record_id: str) -> None:
        self._records.pop(record_id, None)

    async def count(self) -> int:
        return len(self._records)

    async def clear(self) -> None:
        self._records.clear()


class PgVectorStore(VectorStore):
    """pgvector-backed store for production.

    Requires PostgreSQL with pgvector extension installed.
    CREATE EXTENSION vector;
    """

    def __init__(self, session_factory, collection: str = "vectors"):
        self._session_factory = session_factory
        self._collection = _validate_collection(collection)
        self._table = _collection_table(self._collection)

    async def search(self, vector: list[float], top_k: int = 10) -> list[VectorRecord]:
        tbl = self._table
        distance = tbl.c.embedding.op("<=>")(bindparam("vector"))
        score = (literal(1) - distance).label("score")
        stmt = select(tbl.c.id, tbl.c.metadata, score).order_by(distance).limit(top_k)
        async with self._session_factory() as session:
            result = await session.execute(stmt, {"vector": str(vector)})
            return [
                VectorRecord(id=str(r.id), vector=[], metadata=r.metadata or {}, score=float(r.score))
                for r in result
            ]

    async def upsert(self, record: VectorRecord) -> None:
        tbl = self._table
        stmt = pg_insert(tbl).values(
            id=record.id,
            embedding=str(record.vector),
            metadata=record.metadata,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[tbl.c.id],
            set_={"embedding": stmt.excluded.embedding, "metadata": stmt.excluded.metadata},
        )
        async with self._session_factory() as session:
            await session.execute(stmt)
            await session.commit()

    async def delete(self, record_id: str) -> None:
        async with self._session_factory() as session:
            await session.execute(delete(self._table).where(self._table.c.id == record_id))
            await session.commit()

    async def count(self) -> int:
        async with self._session_factory() as session:
            result = await session.execute(select(func.count()).select_from(self._table))
            return result.scalar() or 0
