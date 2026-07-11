from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_tenant_id, get_db_session, verify_token
from domains.rag.models import Document, EmbeddingConfig
from intelligence.rag.embeddings import EmbeddingService
from intelligence.rag.retrieval import RetrievalService
from intelligence.rag.service import RagService
from sdk.permissions import PermissionAction

router = APIRouter()


class AskRequest(BaseModel):
    question: str
    top_k: int = 5
    min_score: float = 0.7


class IngestRequest(BaseModel):
    source_type: str
    source_id: str
    title: str
    content: str
    metadata: dict = {}


class DocumentResponse(BaseModel):
    id: str
    source_type: str
    source_id: str
    title: str
    metadata: dict
    created_at: str | None = None


class AskResponse(BaseModel):
    answer: str
    citations: list[dict]
    chunks_used: int
    confidence: float


def get_rag_service(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
):
    embedding_service = EmbeddingService()
    retrieval_service = RetrievalService(db=db)
    return RagService(
        embedding_service=embedding_service,
        retrieval_service=retrieval_service,
    )


@router.post("/rag/ask", response_model=AskResponse)
async def ask_rag(
    body: AskRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    rag: RagService = Depends(get_rag_service),
    _token: dict = Depends(verify_token),
):
    result = await rag.answer(
        question=body.question,
        tenant_id=tenant_id,
        top_k=body.top_k,
        min_score=body.min_score,
    )
    return AskResponse(
        answer=result.answer,
        citations=result.citations,
        chunks_used=result.chunks_used,
        confidence=result.confidence,
    )


@router.post("/rag/ingest")
async def ingest_document(
    body: IngestRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _token: dict = Depends(verify_token),
):
    document = Document(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        source_type=body.source_type,
        source_id=body.source_id,
        title=body.title,
        content=body.content,
        metadata=body.metadata,
        created_at=datetime.now(timezone.utc),
    )

    embedding_service = EmbeddingService()
    retrieval = RetrievalService(db=db)
    chunks = await embedding_service.embed_document(document)
    await retrieval.store_document_chunks(document, chunks)

    return {
        "document_id": document.id,
        "chunks": len(chunks),
        "status": "ingested",
    }


@router.get("/rag/documents", response_model=list[DocumentResponse])
async def list_documents(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _token: dict = Depends(verify_token),
):
    retrieval = RetrievalService(db=db)
    docs = await retrieval.list_documents(tenant_id)
    return [
        DocumentResponse(
            id=d.id,
            source_type=d.source_type,
            source_id=d.source_id,
            title=d.title,
            metadata=d.metadata,
            created_at=d.created_at.isoformat() if d.created_at else None,
        )
        for d in docs
    ]


@router.delete("/rag/documents/{document_id}")
async def delete_document(
    document_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _token: dict = Depends(verify_token),
):
    retrieval = RetrievalService(db=db)
    await retrieval.delete_document(document_id)
    return {"status": "deleted", "document_id": document_id}
