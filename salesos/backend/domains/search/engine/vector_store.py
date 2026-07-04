"""Vector store abstraction for semantic search.

Supports both pgvector (production) and in-memory (development/demo).
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


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
        return scored[:top_k]

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
        self._collection = collection

    async def search(self, vector: list[float], top_k: int = 10) -> list[VectorRecord]:
        from sqlalchemy import text

        async with self._session_factory() as session:
            stmt = text(f"""
                SELECT id, metadata, 1 - (embedding <=> :vector::vector) AS score
                FROM {self._collection}
                ORDER BY embedding <=> :vector::vector
                LIMIT :top_k
            """)
            result = await session.execute(stmt, {"vector": vector, "top_k": top_k})
            return [
                VectorRecord(id=str(r.id), vector=[], metadata=r.metadata or {}, score=float(r.score))
                for r in result
            ]

    async def upsert(self, record: VectorRecord) -> None:
        from sqlalchemy import text

        async with self._session_factory() as session:
            await session.execute(
                text(f"""
                    INSERT INTO {self._collection} (id, embedding, metadata)
                    VALUES (:id, :vector::vector, :metadata::jsonb)
                    ON CONFLICT (id) DO UPDATE
                    SET embedding = :vector::vector, metadata = :metadata::jsonb
                """),
                {"id": record.id, "vector": record.vector, "metadata": record.metadata},
            )
            await session.commit()

    async def delete(self, record_id: str) -> None:
        from sqlalchemy import text

        async with self._session_factory() as session:
            await session.execute(
                text(f"DELETE FROM {self._collection} WHERE id = :id"),
                {"id": record_id},
            )
            await session.commit()

    async def count(self) -> int:
        from sqlalchemy import text

        async with self._session_factory() as session:
            result = await session.execute(text(f"SELECT COUNT(*) FROM {self._collection}"))
            return result.scalar() or 0
