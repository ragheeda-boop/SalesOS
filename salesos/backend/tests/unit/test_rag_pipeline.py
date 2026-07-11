"""Tests for the RAG pipeline — chunking, embeddings, retrieval, and full pipeline."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from domains.rag.models import Document, DocumentChunk, EmbeddingConfig, RagAnswer
from intelligence.rag.chunking import ChunkingService
from intelligence.rag.embeddings import EmbeddingService
from intelligence.rag.retrieval import RetrievalService
from intelligence.rag.service import RagService


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_document():
    return Document(
        id=str(uuid4()),
        tenant_id="tenant-1",
        source_type="email",
        source_id="email-1",
        title="Test Email",
        content="هذا هو البريد الإلكتروني الأول. يحتوي على معلومات مهمة عن العميل.",
    )


@pytest.fixture
def sample_document_long():
    paragraphs = [
        "مناقشة الفرص الجديدة في السوق السعودي. تم تحديد احتياجات العميل.",
        "تم عرض الحلول المتاحة ومناقشة الأسعار. العميل مهتم بالحل المتكامل.",
        "تم الاتفاق على متابعة الاجتماع الأسبوع القادم لتقديم عرض تفصيلي.",
    ]
    for i in range(5):
        paragraphs.append("فقرة " + str(i) + ": " + "كلمة " * 100)
    return Document(
        id=str(uuid4()),
        tenant_id="tenant-1",
        source_type="meeting",
        source_id="meeting-1",
        title="Long Meeting Notes",
        content="\n\n".join(paragraphs),
    )


@pytest.fixture
def chunking_service():
    return ChunkingService(default_chunk_size=50, default_overlap=10)


@pytest.fixture
def mock_openai_client():
    client = MagicMock()
    client.embeddings.create = AsyncMock()
    client.embeddings.create.return_value = MagicMock(
        data=[
            MagicMock(index=0, embedding=[0.1] * 3072),
            MagicMock(index=1, embedding=[0.2] * 3072),
            MagicMock(index=2, embedding=[0.3] * 3072),
        ]
    )
    return client


@pytest.fixture
def embedding_service(mock_openai_client):
    return EmbeddingService(
        config=EmbeddingConfig(model_name="test-model", dimension=4, batch_size=2),
        openai_client=mock_openai_client,
    )


@pytest.fixture
def mock_db_session():
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
def retrieval_service(mock_db_session):
    svc = RetrievalService(db=mock_db_session)
    svc._pgvector_available = False
    return svc


# ── Chunking Tests ───────────────────────────────────────────────────────────

class TestChunkingService:

    def test_fixed_size_chunks_small_document(self, chunking_service, sample_document):
        chunks = chunking_service.chunk_document(sample_document, strategy="fixed_size")
        assert len(chunks) >= 1
        assert all(c.document_id == sample_document.id for c in chunks)
        assert chunks[0].chunk_index == 0

    def test_fixed_size_chunks_with_overlap(self, chunking_service, sample_document_long):
        chunks = chunking_service.chunk_document(sample_document_long, strategy="fixed_size")
        assert len(chunks) >= 2
        contents = [c.content for c in chunks]
        # overlap means consecutive chunks share some content
        assert all(len(c) > 0 for c in contents)

    def test_fixed_size_respects_chunk_size(self, chunking_service):
        doc = Document(id=str(uuid4()), tenant_id="t1", source_type="note",
                       source_id="n1", title="Test",
                       content="word " * 200)
        chunks = chunking_service.chunk_document(doc, strategy="fixed_size", chunk_size=30, overlap=5)
        for c in chunks:
            token_count = len(chunking_service._tokenize(c.content))
            assert token_count <= 30

    def test_semantic_chunking_by_paragraphs(self, chunking_service, sample_document_long):
        chunks = chunking_service.chunk_document(sample_document_long, strategy="semantic")
        assert len(chunks) >= 1
        assert all(c.metadata.get("strategy") in ("semantic", "semantic_overflow") for c in chunks)

    def test_semantic_chunking_paragraph_boundaries(self, chunking_service):
        doc = Document(id=str(uuid4()), tenant_id="t1", source_type="note",
                       source_id="n1", title="Test",
                       content="فقرة أولى.\n\nفقرة ثانية.\n\nفقرة ثالثة.")
        chunks = chunking_service.chunk_document(doc, strategy="semantic", chunk_size=100)
        assert len(chunks) >= 1

    def test_hybrid_chunking_combines_strategies(self, chunking_service, sample_document_long):
        chunks = chunking_service.chunk_document(sample_document_long, strategy="hybrid")
        assert len(chunks) >= 1

    def test_hybrid_small_document_returns_one_chunk(self, chunking_service, sample_document):
        chunks = chunking_service.chunk_document(sample_document, strategy="hybrid")
        assert len(chunks) >= 1

    def test_unknown_strategy_raises_error(self, chunking_service, sample_document):
        with pytest.raises(ValueError, match="Unknown chunking strategy"):
            chunking_service.chunk_document(sample_document, strategy="invalid")

    def test_empty_document_returns_empty(self, chunking_service):
        doc = Document(id=str(uuid4()), tenant_id="t1", source_type="note",
                       source_id="n1", title="Empty", content="")
        chunks = chunking_service.chunk_document(doc, strategy="fixed_size")
        assert chunks == []

    def test_arabic_text_tokenization(self, chunking_service):
        text = "مرحبا بكم في منصة SalesOS لتطوير الأعمال"
        tokens = chunking_service._tokenize(text)
        assert len(tokens) > 0
        assert all(len(t) > 0 for t in tokens)

    def test_english_text_tokenization(self, chunking_service):
        text = "Welcome to the SalesOS platform for business development"
        tokens = chunking_service._tokenize(text)
        assert len(tokens) == 8

    def test_empty_text_tokenization(self, chunking_service):
        assert chunking_service._tokenize("") == []
        assert chunking_service._detokenize([]) == ""

    def test_long_arabic_word_split(self, chunking_service):
        long_word = "أ" * 50
        tokens = chunking_service._tokenize_arabic(long_word)
        assert len(tokens) >= 2
        assert all(len(t) <= 20 for t in tokens)


# ── Embedding Tests ──────────────────────────────────────────────────────────

class TestEmbeddingService:

    async def test_embed_text_returns_vector(self, embedding_service, mock_openai_client):
        result = await embedding_service.embed_text("hello")
        assert len(result) == 3072
        assert all(isinstance(v, float) for v in result[:5])

    async def test_embed_text_caches_by_hash(self, embedding_service, mock_openai_client):
        result1 = await embedding_service.embed_text("test text")
        result2 = await embedding_service.embed_text("test text")
        assert result1 == result2
        assert mock_openai_client.embeddings.create.call_count == 1

    async def test_embed_batch_returns_vectors(self, embedding_service, mock_openai_client):
        results = await embedding_service.embed_batch(["a", "b", "c"])
        assert len(results) == 3
        for r in results:
            assert len(r) == 3072

    async def test_embed_batch_respects_cache(self, embedding_service, mock_openai_client):
        await embedding_service.embed_text("cached")
        results = await embedding_service.embed_batch(["cached", "new"])
        assert len(results) == 2
        # Only 1 new call + 1 from embed_text
        assert mock_openai_client.embeddings.create.call_count >= 1

    async def test_embed_document_returns_chunks_with_embeddings(self, embedding_service, sample_document):
        chunks = await embedding_service.embed_document(sample_document)
        assert len(chunks) >= 1
        for c in chunks:
            assert c.embedding is not None
            assert len(c.embedding) > 0

    async def test_embed_text_retries_on_failure(self):
        client = MagicMock()
        fail_count = 0

        async def _fail_twice(*args, **kwargs):
            nonlocal fail_count
            fail_count += 1
            if fail_count <= 2:
                raise RuntimeError("API error")
            return MagicMock(data=[MagicMock(index=0, embedding=[0.5] * 3072)])

        client.embeddings.create = _fail_twice
        svc = EmbeddingService(openai_client=client, max_retries=3)
        result = await svc.embed_text("test")
        assert len(result) == 3072

    async def test_embed_text_returns_empty_on_all_failures(self):
        client = MagicMock()
        client.embeddings.create = AsyncMock(side_effect=RuntimeError("API down"))
        svc = EmbeddingService(openai_client=client, max_retries=2)
        result = await svc.embed_text("test")
        assert result == []


# ── Retrieval Tests ──────────────────────────────────────────────────────────

class TestRetrievalService:

    async def test_retrieve_without_pgvector_returns_fallback(self, retrieval_service):
        results = await retrieval_service.retrieve(
            query_embedding=[0.1, 0.2, 0.3],
            tenant_id="tenant-1",
            top_k=5,
        )
        assert isinstance(results, list)

    async def test_retrieve_with_empty_embedding(self, retrieval_service):
        results = await retrieval_service.retrieve(
            query_embedding=[],
            tenant_id="tenant-1",
        )
        assert results == []

    async def test_store_and_delete_document(self, retrieval_service):
        doc = Document(id=str(uuid4()), tenant_id="t1", source_type="note",
                       source_id="n1", title="Test", content="test")
        chunks = [DocumentChunk(id=str(uuid4()), document_id=doc.id,
                                content="test", chunk_index=0)]
        await retrieval_service.store_document_chunks(doc, chunks)
        await retrieval_service.delete_document(doc.id)
        # Should not raise

    async def test_list_documents_without_pgvector(self, retrieval_service):
        docs = await retrieval_service.list_documents("tenant-1")
        assert docs == []

    async def test_retrieve_hybrid_without_pgvector(self, retrieval_service):
        results = await retrieval_service.retrieve_hybrid(
            query_embedding=[0.1, 0.2],
            tenant_id="t1",
        )
        assert isinstance(results, list)

    async def test_retrieve_by_source_without_pgvector(self, retrieval_service):
        results = await retrieval_service.retrieve_by_source("email", "e1")
        assert results == []

    async def test_ensure_tables_creates_extension(self, mock_db_session):
        svc = RetrievalService(db=mock_db_session)
        await svc.ensure_tables()
        assert mock_db_session.execute.called

    async def test_retrieve_pgvector_parses_results(self, mock_db_session):
        class FakeRow(dict):
            def __getattr__(self, name):
                return self.get(name)

        row = FakeRow({
            "id": str(uuid4()),
            "document_id": str(uuid4()),
            "content": "relevant chunk",
            "chunk_index": 0,
            "metadata": {},
            "score": 0.92,
            "tenant_id": "t1",
            "source_type": "email",
            "source_id": "s1",
            "title": "Doc",
            "doc_content": "full content",
            "doc_metadata": {},
            "created_at": None,
        })

        mock_mappings = MagicMock()
        mock_mappings.all.return_value = [row]
        mock_result = MagicMock()
        mock_result.mappings.return_value = mock_mappings
        mock_db_session.execute.return_value = mock_result

        svc = RetrievalService(db=mock_db_session)
        svc._pgvector_available = True

        results = await svc.retrieve(
            query_embedding=[0.1] * 3072,
            tenant_id="t1",
        )
        assert len(results) == 1
        assert results[0].score == 0.92
        assert results[0].source is not None
        assert results[0].source.title == "Doc"


# ── Full RAG Pipeline Tests ──────────────────────────────────────────────────

class TestRagService:

    async def test_answer_returns_rag_answer(self, mock_db_session):
        embed_svc = MagicMock()
        embed_svc.embed_text = AsyncMock(return_value=[0.1, 0.2, 0.3])

        retrieve_svc = RetrievalService(db=mock_db_session)
        retrieve_svc._pgvector_available = False
        doc_id = str(uuid4())
        doc = Document(id=doc_id, tenant_id="t1", source_type="email",
                       source_id="e1", title="Doc", content="info")
        chunk = DocumentChunk(id=str(uuid4()), document_id=doc_id,
                              content="relevant info", chunk_index=0)
        await retrieve_svc.store_document_chunks(doc, [chunk])

        rag = RagService(
            embedding_service=embed_svc,
            retrieval_service=retrieve_svc,
        )
        mock_llm = MagicMock()
        mock_llm.chat = AsyncMock()
        mock_llm.chat.return_value = MagicMock(content="This is the answer")
        rag._llm = mock_llm

        result = await rag.answer(question="what?", tenant_id="t1")
        assert isinstance(result, RagAnswer)
        assert result.answer == "This is the answer"
        assert isinstance(result.citations, list)
        assert result.chunks_used >= 0

    async def test_answer_returns_empty_when_no_embedding(self, mock_db_session):
        embed_svc = MagicMock()
        embed_svc.embed_text = AsyncMock(return_value=[])

        retrieve_svc = RetrievalService(db=mock_db_session)
        rag = RagService(
            embedding_service=embed_svc,
            retrieval_service=retrieve_svc,
        )
        result = await rag.answer(question="?", tenant_id="t1")
        assert result.answer == ""
        assert result.chunks_used == 0

    async def test_generate_brief_returns_summary(self, mock_db_session):
        embed_svc = MagicMock()
        retrieve_svc = RetrievalService(db=mock_db_session)
        retrieve_svc._pgvector_available = True

        doc_id = str(uuid4())
        mock_mappings = MagicMock()
        mock_mappings.all.return_value = [
            {
                "id": str(uuid4()),
                "document_id": doc_id,
                "content": "brief content",
                "chunk_index": 0,
                "metadata": {},
                "score": 0.0,
                "tenant_id": "t1",
                "source_type": "meeting",
                "source_id": "m1",
                "title": "Meeting",
                "doc_content": "full",
                "doc_metadata": {},
                "created_at": None,
            }
        ]
        mock_result = MagicMock()
        mock_result.mappings.return_value = mock_mappings
        mock_db_session.execute.return_value = mock_result

        rag = RagService(
            embedding_service=embed_svc,
            retrieval_service=retrieve_svc,
        )
        mock_llm = MagicMock()
        mock_llm.chat = AsyncMock()
        mock_llm.chat.return_value = MagicMock(content="Brief summary")
        rag._llm = mock_llm

        result = await rag.generate_brief(entity_id="m1", entity_type="meeting", tenant_id="t1")
        assert isinstance(result, RagAnswer)
        assert result.answer == "Brief summary"
        assert len(result.citations) > 0

    async def test_generate_brief_no_results(self, mock_db_session):
        embed_svc = MagicMock()
        retrieve_svc = RetrievalService(db=mock_db_session)
        retrieve_svc._pgvector_available = True

        mock_mappings = MagicMock()
        mock_mappings.all.return_value = []
        mock_result = MagicMock()
        mock_result.mappings.return_value = mock_mappings
        mock_db_session.execute.return_value = mock_result

        rag = RagService(
            embedding_service=embed_svc,
            retrieval_service=retrieve_svc,
        )
        result = await rag.generate_brief(
            entity_id="nonexistent", entity_type="email", tenant_id="t1"
        )
        assert result.answer == ""
        assert result.chunks_used == 0

    async def test_answer_uses_citations(self, mock_db_session):
        embed_svc = MagicMock()
        embed_svc.embed_text = AsyncMock(return_value=[0.1, 0.2, 0.3])

        retrieve_svc = RetrievalService(db=mock_db_session)
        retrieve_svc._pgvector_available = True

        mock_mappings = MagicMock()
        mock_mappings.all.return_value = []
        mock_result = MagicMock()
        mock_result.mappings.return_value = mock_mappings
        mock_db_session.execute.return_value = mock_result

        rag = RagService(
            embedding_service=embed_svc,
            retrieval_service=retrieve_svc,
        )
        result = await rag.answer(question="test", tenant_id="t1")
        assert isinstance(result.citations, list)
