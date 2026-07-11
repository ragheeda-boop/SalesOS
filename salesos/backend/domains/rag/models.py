from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Document:
    id: str
    tenant_id: str
    source_type: str  # email | meeting | note | company_profile
    source_id: str
    title: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None


@dataclass
class DocumentChunk:
    id: str
    document_id: str
    content: str
    embedding: list[float] | None = None
    chunk_index: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EmbeddingConfig:
    model_name: str = "text-embedding-3-large"
    dimension: int = 3072
    batch_size: int = 20


@dataclass
class RetrievalResult:
    chunk: DocumentChunk
    score: float
    source: Document | None = None


@dataclass
class RagAnswer:
    answer: str
    citations: list[dict[str, Any]] = field(default_factory=list)
    chunks_used: int = 0
    confidence: float = 0.0
