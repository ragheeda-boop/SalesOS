from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from domains.rag.models import Document, DocumentChunk, RetrievalResult


class RetrievalService:
    """Retrieves relevant document chunks using pgvector similarity search.

    Falls back gracefully if pgvector extension is not available.
    """

    def __init__(self, db: AsyncSession):
        self._db = db
        self._fallback_store: dict[str, list[dict[str, Any]]] = {}
        self._pgvector_available: bool | None = None

    async def _check_pgvector(self) -> bool:
        if self._pgvector_available is not None:
            return self._pgvector_available
        try:
            await self._db.execute(text("SELECT 1 FROM pg_available_extensions WHERE name = 'vector'"))
            self._pgvector_available = True
        except Exception:
            self._pgvector_available = False
        return self._pgvector_available

    async def retrieve(
        self,
        query_embedding: list[float],
        tenant_id: str,
        top_k: int = 5,
        min_score: float = 0.7,
    ) -> list[RetrievalResult]:
        if not query_embedding:
            return []

        if await self._check_pgvector():
            return await self._retrieve_pgvector(query_embedding, tenant_id, top_k, min_score)
        return self._retrieve_fallback(query_embedding, tenant_id, top_k, min_score)

    async def _retrieve_pgvector(
        self, query_embedding: list[float], tenant_id: str, top_k: int, min_score: float
    ) -> list[RetrievalResult]:
        vector_str = json.dumps(query_embedding)
        sql = text("""
            SELECT
                c.id, c.document_id, c.content, c.chunk_index, c.metadata,
                1 - (c.embedding <=> :vector::vector) AS score,
                d.tenant_id, d.source_type, d.source_id, d.title, d.content AS doc_content,
                d.metadata AS doc_metadata, d.created_at
            FROM rag_document_chunks c
            JOIN rag_documents d ON d.id = c.document_id
            WHERE d.tenant_id = :tenant_id
              AND 1 - (c.embedding <=> :vector::vector) >= :min_score
            ORDER BY c.embedding <=> :vector::vector
            LIMIT :top_k
        """)
        try:
            result = await self._db.execute(
                sql,
                {
                    "vector": vector_str,
                    "tenant_id": tenant_id,
                    "top_k": top_k,
                    "min_score": min_score,
                },
            )
            rows = result.mappings().all()
        except Exception:
            return self._retrieve_fallback(query_embedding, tenant_id, top_k, min_score)

        results: list[RetrievalResult] = []
        for row in rows:
            chunk = DocumentChunk(
                id=str(row["id"]),
                document_id=str(row["document_id"]),
                content=row["content"],
                chunk_index=row["chunk_index"],
                metadata=row["metadata"] or {},
            )
            source = Document(
                id=str(row["document_id"]),
                tenant_id=row["tenant_id"],
                source_type=row["source_type"],
                source_id=row["source_id"],
                title=row["title"],
                content=row["doc_content"] or "",
                metadata=row["doc_metadata"] or {},
                created_at=row["created_at"],
            )
            results.append(RetrievalResult(chunk=chunk, score=float(row["score"]), source=source))

        return results

    async def retrieve_hybrid(
        self,
        query_embedding: list[float],
        tenant_id: str,
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        if not query_embedding:
            return []

        if not await self._check_pgvector():
            return self._retrieve_fallback(query_embedding, tenant_id, top_k, 0.0)

        vector_str = json.dumps(query_embedding)
        sql = text("""
            SELECT
                c.id, c.document_id, c.content, c.chunk_index, c.metadata,
                1 - (c.embedding <=> :vector::vector) AS vector_score,
                ts_rank(to_tsvector('simple', c.content), plainto_tsquery('simple', :query_text)) AS text_score,
                d.tenant_id, d.source_type, d.source_id, d.title, d.content AS doc_content,
                d.metadata AS doc_metadata, d.created_at
            FROM rag_document_chunks c
            JOIN rag_documents d ON d.id = c.document_id
            WHERE d.tenant_id = :tenant_id
            ORDER BY (1 - (c.embedding <=> :vector::vector)) * 0.7 +
                      ts_rank(to_tsvector('simple', c.content), plainto_tsquery('simple', :query_text)) * 0.3 DESC
            LIMIT :top_k
        """)
        try:
            result = await self._db.execute(
                sql,
                {
                    "vector": vector_str,
                    "query_text": "",
                    "tenant_id": tenant_id,
                    "top_k": top_k,
                },
            )
            rows = result.mappings().all()
        except Exception:
            return self._retrieve_fallback(query_embedding, tenant_id, top_k, 0.0)

        results: list[RetrievalResult] = []
        for row in rows:
            chunk = DocumentChunk(
                id=str(row["id"]),
                document_id=str(row["document_id"]),
                content=row["content"],
                chunk_index=row["chunk_index"],
                metadata=row["metadata"] or {},
            )
            source = Document(
                id=str(row["document_id"]),
                tenant_id=row["tenant_id"],
                source_type=row["source_type"],
                source_id=row["source_id"],
                title=row["title"],
                content=row["doc_content"] or "",
                metadata=row["doc_metadata"] or {},
                created_at=row["created_at"],
            )
            score = max(float(row["vector_score"]) if row["vector_score"] else 0, float(row["text_score"]) if row["text_score"] else 0)
            results.append(RetrievalResult(chunk=chunk, score=score, source=source))

        return results

    async def retrieve_by_source(
        self, source_type: str, source_id: str
    ) -> list[RetrievalResult]:
        if await self._check_pgvector():
            sql = text("""
                SELECT
                    c.id, c.document_id, c.content, c.chunk_index, c.metadata,
                    0 AS score,
                    d.tenant_id, d.source_type, d.source_id, d.title, d.content AS doc_content,
                    d.metadata AS doc_metadata, d.created_at
                FROM rag_document_chunks c
                JOIN rag_documents d ON d.id = c.document_id
                WHERE d.source_type = :source_type AND d.source_id = :source_id
                ORDER BY c.chunk_index
            """)
            try:
                result = await self._db.execute(
                    sql, {"source_type": source_type, "source_id": source_id}
                )
                rows = result.mappings().all()
            except Exception:
                rows = []
        else:
            rows = []

        results: list[RetrievalResult] = []
        for row in rows:
            chunk = DocumentChunk(
                id=str(row["id"]),
                document_id=str(row["document_id"]),
                content=row["content"],
                chunk_index=row["chunk_index"],
                metadata=row["metadata"] or {},
            )
            source = Document(
                id=str(row["document_id"]),
                tenant_id=row["tenant_id"],
                source_type=row["source_type"],
                source_id=row["source_id"],
                title=row["title"],
                content=row["doc_content"] or "",
                metadata=row["doc_metadata"] or {},
                created_at=row["created_at"],
            )
            results.append(RetrievalResult(chunk=chunk, score=0.0, source=source))

        return results

    async def store_document_chunks(
        self, document: Document, chunks: list[DocumentChunk]
    ) -> None:
        if not await self._check_pgvector():
            self._fallback_store[document.id] = [c.__dict__ for c in chunks]
            return

        try:
            doc_sql = text("""
                INSERT INTO rag_documents (id, tenant_id, source_type, source_id, title, content, metadata, created_at)
                VALUES (:id, :tenant_id, :source_type, :source_id, :title, :content, :metadata::jsonb, :created_at)
                ON CONFLICT (id) DO UPDATE
                SET title = EXCLUDED.title,
                    content = EXCLUDED.content,
                    metadata = EXCLUDED.metadata
            """)
            await self._db.execute(
                doc_sql,
                {
                    "id": document.id,
                    "tenant_id": document.tenant_id,
                    "source_type": document.source_type,
                    "source_id": document.source_id,
                    "title": document.title,
                    "content": document.content,
                    "metadata": json.dumps(document.metadata),
                    "created_at": document.created_at or datetime.now(timezone.utc),
                },
            )

            chunk_sql = text("""
                INSERT INTO rag_document_chunks (id, document_id, content, embedding, chunk_index, metadata)
                VALUES (:id, :document_id, :content, :embedding::vector, :chunk_index, :metadata::jsonb)
                ON CONFLICT (id) DO UPDATE
                SET content = EXCLUDED.content,
                    embedding = EXCLUDED.embedding,
                    metadata = EXCLUDED.metadata
            """)
            for chunk in chunks:
                if chunk.embedding:
                    vec_str = json.dumps(chunk.embedding)
                    await self._db.execute(
                        chunk_sql,
                        {
                            "id": chunk.id,
                            "document_id": chunk.document_id,
                            "content": chunk.content,
                            "embedding": vec_str,
                            "chunk_index": chunk.chunk_index,
                            "metadata": json.dumps(chunk.metadata),
                        },
                    )

            await self._db.commit()
        except Exception:
            self._fallback_store[document.id] = [
                {"chunk": c.__dict__, "document": document.__dict__} for c in chunks
            ]

    async def delete_document(self, document_id: str) -> None:
        self._fallback_store.pop(document_id, None)
        if await self._check_pgvector():
            try:
                await self._db.execute(
                    text("DELETE FROM rag_document_chunks WHERE document_id = :id"),
                    {"id": document_id},
                )
                await self._db.execute(
                    text("DELETE FROM rag_documents WHERE id = :id"),
                    {"id": document_id},
                )
                await self._db.commit()
            except Exception:
                pass

    async def list_documents(self, tenant_id: str) -> list[Document]:
        if not await self._check_pgvector():
            return []

        sql = text("""
            SELECT id, tenant_id, source_type, source_id, title, content, metadata, created_at
            FROM rag_documents
            WHERE tenant_id = :tenant_id
            ORDER BY created_at DESC
        """)
        try:
            result = await self._db.execute(sql, {"tenant_id": tenant_id})
            rows = result.mappings().all()
        except Exception:
            return []

        return [
            Document(
                id=str(row["id"]),
                tenant_id=row["tenant_id"],
                source_type=row["source_type"],
                source_id=row["source_id"],
                title=row["title"],
                content=row["content"],
                metadata=row["metadata"] or {},
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def _retrieve_fallback(
        self, query_embedding: list[float], tenant_id: str, top_k: int, min_score: float
    ) -> list[RetrievalResult]:
        results: list[RetrievalResult] = []
        for doc_id, entries in self._fallback_store.items():
            for entry in entries:
                chunk_data = entry.get("chunk", entry)
                chunk = DocumentChunk(**{k: v for k, v in chunk_data.items() if k != "embedding"})
                results.append(RetrievalResult(chunk=chunk, score=0.0))
        return results[:top_k]

    async def ensure_tables(self) -> None:
        try:
            await self._db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await self._db.execute(text("""
                CREATE TABLE IF NOT EXISTS rag_documents (
                    id UUID PRIMARY KEY,
                    tenant_id VARCHAR(36) NOT NULL,
                    source_type VARCHAR(50) NOT NULL,
                    source_id VARCHAR(255) NOT NULL,
                    title TEXT NOT NULL DEFAULT '',
                    content TEXT NOT NULL DEFAULT '',
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """))
            await self._db.execute(text("""
                CREATE TABLE IF NOT EXISTS rag_document_chunks (
                    id UUID PRIMARY KEY,
                    document_id UUID NOT NULL REFERENCES rag_documents(id) ON DELETE CASCADE,
                    content TEXT NOT NULL,
                    embedding vector(3072),
                    chunk_index INTEGER NOT NULL DEFAULT 0,
                    metadata JSONB DEFAULT '{}'
                )
            """))
            await self._db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_rag_chunks_document
                ON rag_document_chunks (document_id)
            """))
            await self._db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_rag_chunks_tenant
                ON rag_documents (tenant_id)
            """))
            await self._db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_rag_chunks_vector
                ON rag_document_chunks
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
            """))
            await self._db.commit()
            self._pgvector_available = True
        except Exception:
            self._pgvector_available = False
