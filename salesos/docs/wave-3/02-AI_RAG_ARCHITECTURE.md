# AI RAG Architecture

> **الهدف:** تصميم RAG pipeline لـ Wave 3 — من استيعاب الوثائق إلى التوليد مع الاستشهادات
>
> **تاريخ:** 2026-07-11
> **المرحلة:** Wave 3 — Sprint 10

---

## 1. RAG Pipeline Overview

```
Document Ingestion
      │  PDF, DOCX, HTML, Email, Meeting Notes, Signals
      ▼
Document Processing
      │  OCR, format detection, language detection
      │  Metadata extraction (author, date, source, type)
      ▼
Chunking
      │  Semantic chunking with overlap (10-20%)
      │  Arabic-aware segmentation
      ▼
Embedding
      │  Multi-lingual embedding model (Arabic + English)
      │  Cache hit? → reuse cached embedding
      ▼
Vector Store (pgvector)
      │  HNSW index, partitioned by tenant
      │  Store: embedding + text + metadata + source
      ▼
Retrieval
      │  Hybrid search: semantic + keyword (BM25)
      │  Reranking for relevance
      ▼
Context Assembly
      │  Token-aware context window management
      │  Priority: high-relevance chunks first
      ▼
Generation
      │  LLM with citations
      │  Output: response + source list
      ▼
Citation Verification
      │  Verify each citation against source
      │  Confidence score per citation
```

---

## 2. Document Ingestion

### Supported Formats

| Format | Parser | Notes |
|--------|--------|-------|
| PDF | PyMuPDF / pdfminer | Table extraction, Arabic OCR |
| DOCX | python-docx | Preserve headings, lists |
| HTML | BeautifulSoup | Strip markup, extract main content |
| Plain Text | Direct | UTF-8 with Arabic normalization |
| Email (EML) | email parser | Extract body + attachments |
| Meeting Notes | Markdown | From Meeting Intelligence output |
| Signals | JSON | From Signal Runtime |

### Ingestion Pipeline

```python
class DocumentIngestionService:
    async def ingest(self, document: DocumentInput) -> DocumentId:
        # 1. Detect format and language
        fmt = detect_format(document.content)
        lang = detect_language(document.content)

        # 2. Parse based on format
        parsed = await self.parsers[fmt].parse(document.content)

        # 3. Normalize Arabic text
        if lang == 'ar':
            parsed = normalize_arabic(parsed)

        # 4. Extract metadata
        metadata = self.extract_metadata(document, parsed)

        # 5. Store raw document
        doc_id = await self.store.save(parsed, metadata)

        # 6. Trigger chunking pipeline
        await self.event_bus.emit(Event(
            type="document.processed",
            data={"document_id": doc_id, "language": lang}
        ))

        return doc_id
```

### Arabic Text Normalization

```python
def normalize_arabic(text: str) -> str:
    """Normalize Arabic text for consistent embedding."""
    text = re.sub('[إأآا]', 'ا', text)     # Normalize Alef
    text = re.sub('ة', 'ه', text)          # Taa Marbuta → Ha
    text = re.sub('ى', 'ي', text)          # Alif Maqsura → Ya
    text = re.sub('[ًٌٍَُِّْ]', '', text)   # Remove diacritics (Tashkeel)
    text = re.sub('ـ', '', text)            # Remove Tatweel/Kashida
    return text.strip()
```

---

## 3. Chunking Strategy

### Chunking Methods

| Method | Use Case | Chunk Size | Overlap |
|--------|----------|------------|---------|
| **Semantic** | General documents | 512 tokens | 10% |
| **Heading-based** | Structured docs (reports, specs) | Per-section | None |
| **Sentence-based** | Emails, short notes | 3-5 sentences | 1 sentence |
| **Fixed-size** | Fallback | 512 tokens | 20% |

### Chunk Architecture

```python
class ChunkingPipeline:
    def __init__(self, strategies: dict[str, ChunkingStrategy]):
        self.strategies = strategies

    async def chunk(self, document: ParsedDocument) -> list[Chunk]:
        strategy = self._select_strategy(document)
        chunks = strategy.split(document.content)

        # Enrich each chunk with metadata
        enriched = []
        for i, chunk in enumerate(chunks):
            enriched.append(Chunk(
                document_id=document.id,
                index=i,
                text=chunk.text,
                tokens=count_tokens(chunk.text),
                metadata={
                    **document.metadata,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "section": chunk.heading,
                    "language": document.language,
                },
                embedding=None,  # Computed by embedding service
            ))
        return enriched

    def _select_strategy(self, doc: ParsedDocument) -> ChunkingStrategy:
        if doc.format in ('pdf', 'docx') and doc.has_headings:
            return self.strategies['heading']
        if doc.format == 'email':
            return self.strategies['sentence']
        if doc.token_count < 300:
            return self.strategies['sentence']
        return self.strategies['semantic']
```

---

## 4. Embedding Strategy

### Model Selection

| Model | Dimensions | Languages | Cost | Quality |
|-------|-----------|-----------|------|---------|
| **intfloat/multilingual-e5-large** | 1024 | 100+ (AR + EN) | Free (self-host) | ★★★★★ |
| **Cohere embed-multilingual-v3.0** | 1024 | 100+ | $0.10/1K tokens | ★★★★★ |
| **OpenAI text-embedding-3-large** | 3072 | EN (weak AR) | $0.13/1K tokens | ★★★★☆ |
| **LaBSE** | 768 | 100+ | Free (self-host) | ★★★☆☆ |

**Recommendation:** `intfloat/multilingual-e5-large` self-hosted for cost + quality.

### Embedding Service

```python
class EmbeddingService:
    def __init__(self, model_name: str = "intfloat/multilingual-e5-large"):
        self.model = self._load_model(model_name)
        self.cache = EmbeddingCache()

    async def embed(self, texts: list[str], language: str = "ar") -> list[list[float]]:
        # Check cache first
        uncached = []
        cached_embeddings = []

        for text in texts:
            cached = await self.cache.get(text)
            if cached:
                cached_embeddings.append(cached)
            else:
                uncached.append(text)

        # Embed uncached texts
        if uncached:
            # Add instruction prefix per E5 convention
            prefixed = [f"query: {t}" if language == "en" else f"استعلام: {t}" for t in uncached]
            new_embeddings = self.model.encode(prefixed, normalize_embeddings=True)
            for text, emb in zip(uncached, new_embeddings):
                await self.cache.set(text, emb.tolist())
            cached_embeddings.extend(new_embeddings.tolist())

        return cached_embeddings
```

### Cache Strategy

| Cache Level | Storage | TTL | Hit Rate Target |
|-------------|---------|-----|-----------------|
| **L1: In-memory** | RAM (Redis) | 24 hours | 60% |
| **L2: Disk** | pgvector | 7 days | 30% |
| **Total** | | | **> 90%** |

---

## 5. Vector Store (pgvector)

### Architecture

```sql
-- Enable pgvector extension
CREATE EXTENSION vector;

-- Main vectors table
CREATE TABLE document_vectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    chunk_id UUID NOT NULL REFERENCES chunks(id),
    document_id UUID NOT NULL REFERENCES documents(id),
    embedding vector(1024),           -- multilingual-e5-large
    text TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    language VARCHAR(10) NOT NULL,
    token_count INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- HNSW index for fast similarity search
    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

-- Create HNSW index (tuned for 1024 dimensions)
CREATE INDEX idx_document_vectors_embedding 
    ON document_vectors 
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 32, ef_construction = 200);

-- Partition by tenant for multi-tenant isolation
-- (applied via table inheritance or schema per tenant)
```

### Hybrid Search

```python
class HybridSearchEngine:
    def __init__(self, vector_weight: float = 0.7, keyword_weight: float = 0.3):
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight

    async def search(
        self,
        query: str,
        tenant_id: str,
        top_k: int = 10,
        filters: dict = None,
    ) -> list[SearchResult]:
        # 1. Embed query
        query_vector = await self.embedding_service.embed([query])

        # 2. Vector search (cosine similarity)
        vector_results = await self._vector_search(
            query_vector[0], tenant_id, top_k * 2, filters
        )

        # 3. Keyword search (BM25 via PostgreSQL full-text)
        keyword_results = await self._keyword_search(
            query, tenant_id, top_k * 2, filters
        )

        # 4. Reciprocal Rank Fusion (RRF)
        fused = self._rrf_fusion(vector_results, keyword_results, k=60)

        # 5. Rerank with cross-encoder
        reranked = await self._rerank(query, fused[:top_k * 2])

        return reranked[:top_k]

    def _rrf_fusion(
        self,
        vector_results: list[ScoredResult],
        keyword_results: list[ScoredResult],
        k: int = 60,
    ) -> list[ScoredResult]:
        """Reciprocal Rank Fusion combines two ranked lists."""
        scores = {}
        for rank, result in enumerate(vector_results):
            scores[result.chunk_id] = scores.get(result.chunk_id, 0) + 1 / (k + rank + 1)
        for rank, result in enumerate(keyword_results):
            scores[result.chunk_id] = scores.get(result.chunk_id, 0) + 1 / (k + rank + 1)

        combined = []
        for chunk_id, score in sorted(scores.items(), key=lambda x: -x[1]):
            result = next(
                (r for r in vector_results + keyword_results if r.chunk_id == chunk_id),
                None
            )
            if result:
                combined.append(result.with_score(score))
        return combined
```

---

## 6. Context Window Management

### Strategy

```python
class ContextWindowManager:
    MAX_TOKENS = 8000  # GPT-4 context window reserve

    async def build_context(
        self,
        query: str,
        retrieved_chunks: list[SearchResult],
        max_tokens: int = 6000,  # Leave room for response
    ) -> Context:
        # 1. Sort by relevance score (descending)
        sorted_chunks = sorted(retrieved_chunks, key=lambda c: c.score, reverse=True)

        # 2. Token-aware packing
        context_parts = []
        total_tokens = 0
        used_chunks = []

        for chunk in sorted_chunks:
            chunk_tokens = count_tokens(chunk.text)
            if total_tokens + chunk_tokens > max_tokens:
                continue  # Skip; context window full
            context_parts.append(chunk.text)
            used_chunks.append(chunk)
            total_tokens += chunk_tokens

        # 3. Assemble context with metadata
        context = Context(
            text="\n\n---\n\n".join(context_parts),
            sources=[ChunkSource(
                document_id=c.document_id,
                chunk_id=c.chunk_id,
                text=c.text,
                score=c.score,
                metadata=c.metadata,
            ) for c in used_chunks],
            total_tokens=total_tokens,
            used_chunks=len(used_chunks),
            available_chunks=len(retrieved_chunks),
        )

        return context
```

---

## 7. Generation with Citations

### Prompt Template

```python
RAG_PROMPT = """You are a sales intelligence assistant for SalesOS. Answer based on the provided context.

Context:
{context}

Question: {query}

Instructions:
1. Answer using ONLY the provided context
2. If the context doesn't contain enough information, say "لا توجد معلومات كافية" / "Insufficient information"
3. Cite sources using [1], [2], etc. corresponding to the context sections
4. Provide answers in the same language as the question (Arabic or English)
5. If the question mentions specific numbers or dates, verify them in the context

Answer:
"""
```

### Citation Verification

```python
class CitationVerifier:
    async def verify(self, response: str, context: Context) -> CitationReport:
        """Verify each citation references a real source in the context."""
        citations = self._extract_citations(response)
        verified = []
        errors = []

        for citation in citations:
            source = self._find_source(citation.id, context)
            if source:
                # Verify the claim matches the source text
                similarity = await self._check_claim_match(
                    citation.claim, source.text
                )
                verified.append(VerifiedCitation(
                    id=citation.id,
                    source_id=source.chunk_id,
                    source_text=source.text[:200],
                    match_score=similarity,
                    is_accurate=similarity > 0.7,
                ))
                if similarity < 0.7:
                    errors.append(f"Citation [{citation.id}] has low accuracy: {similarity}")
            else:
                errors.append(f"Citation [{citation.id}] references non-existent source")

        return CitationReport(
            citations=verified,
            errors=errors,
            total=len(citations),
            accurate=sum(1 for c in verified if c.is_accurate),
        )
```

---

## 8. Cost Optimization

### Tiered Model Strategy

| Task | Primary Model | Fallback | Cost/Request |
|------|--------------|----------|-------------|
| Embedding | multilingual-e5 (self-host) | — | $0.0001 |
| RAG Generation | GPT-4o-mini | GPT-4o | $0.002 |
| Complex Analysis | GPT-4o | Claude 3.5 | $0.01 |
| Arabic Generation | GPT-4o | Claude 3 Haiku | $0.005 |
| Keyword Search | PostgreSQL FTS | — | $0 (free) |

### Optimization Techniques

1. **Embedding Cache** — 80%+ hit rate via Redis L1 + pgvector L2
2. **Query Caching** — Identical queries return cached responses (TTL: 1 hour)
3. **Batch Processing** — Embed chunks in batches of 32
4. **Selective AI** — Use AI only when rule-based scoring is insufficient
5. **Chunk Pruning** — Pre-filter chunks by metadata before embedding search
6. **Token Budgeting** — Dynamic context window: smaller for simple queries

---

## 9. Integration with Wave 2

### NBA + RAG

```python
class NBARAGEnhancer:
    """Enhances NBA recommendations with RAG context."""

    async def enhance(self, nba: NBAOutput, opportunity: Opportunity) -> EnhancedNBA:
        # 1. Build RAG query from opportunity context
        query = self._build_query(opportunity)

        # 2. Retrieve relevant documents
        chunks = await self.rag.retrieve(query, opportunity.tenant_id)

        # 3. Build context window
        context = await self.context_manager.build_context(query, chunks)

        # 4. Generate enhanced recommendation with citations
        enhanced = await self.rag.generate(
            prompt=self._build_nba_prompt(nba, context),
        )

        return EnhancedNBA(
            original=nba,
            rag_context=context,
            rag_recommendation=enhanced,
            citations=enhanced.citations,
            confidence_adjustment=self._compute_confidence_boost(context),
        )
```

### Meeting Intelligence + RAG

```python
class MeetingRAGEnhancer:
    """Enhances Meeting Intelligence with previous interactions."""

    async def prepare(self, meeting: Meeting, company: Company) -> MeetingBrief:
        # Retrieve all documents related to this company + opportunity
        query = f"Company: {company.name_ar}. Prepare for meeting about {meeting.title}"
        chunks = await self.rag.retrieve(query, company.tenant_id)

        return MeetingBrief(
            company_summary=self._extract_company_summary(chunks),
            recent_signals=self._extract_signals(chunks),
            previous_meetings=self._extract_meeting_history(chunks),
            competitor_mentions=self._extract_competitors(chunks),
            suggested_questions=self._generate_questions(chunks),
        )
```

---

## 10. Monitoring & Observability

| Metric | Instrumentation | Alert Threshold |
|--------|----------------|-----------------|
| RAG pipeline latency | Histogram (normalize_ms, chunk_ms, embed_ms, retrieve_ms, generate_ms) | p95 > 2s |
| Embedding cache hit rate | Gauge | < 60% |
| Citation accuracy | Counter (accurate / total) | < 85% |
| Context window utilization | Gauge | > 90% (warning) |
| Embedding API cost | Counter ($/day) | > $50/day |
| Retrieval relevance score | Gauge (avg score) | < 0.5 |

---

*AI RAG Architecture complete. Ready for Sprint 10 implementation.*
