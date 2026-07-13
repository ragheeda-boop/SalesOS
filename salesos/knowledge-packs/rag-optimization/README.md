# RAG Optimization — Knowledge Pack

> Chunking strategies, embedding model selection, hybrid search tuning, context window management, and citation tracking for SalesOS RAG pipeline.

---

## Chunking Strategies for Business Documents

### Available Strategies (from ChunkingService)

| Strategy | Use Case | Pros | Cons |
|----------|----------|------|------|
| `fixed_size` | Uniform documents | Simple, predictable | May split mid-sentence |
| `semantic` | Structured documents | Respects document structure | May create uneven chunks |
| `hybrid` | Mixed content (default) | Best of both worlds | Slightly more complex |

### Fixed-Size Chunking

```python
# Default: 512 tokens, 128 token overlap
chunk_size = 512
overlap = 128

# Algorithm:
# 1. Tokenize document
# 2. Slide window with (chunk_size - overlap) step
# 3. Create chunk from each window
```

**When to use**:
- Plain text documents without clear structure
- Logs, emails, chat transcripts
- When consistency is more important than semantic accuracy

### Semantic Chunking

```python
# Split by paragraph boundaries (\n\n)
# Then merge paragraphs into chunks ≤ chunk_size
# Large paragraphs get split with fixed-size fallback
```

**When to use**:
- Reports, proposals, contracts
- Documents with clear section headings
- Arabic documents with paragraph structure

### Hybrid Chunking (Default)

```python
# 1. First pass: semantic chunking
# 2. Second pass: merge small semantic chunks into larger ones
# 3. Result: semantically-aware chunks of consistent size
```

**When to use**:
- Mixed content types
- Documents with both structured and unstructured sections
- Default choice for unknown document types

### Arabic Document Considerations

```python
# Arabic text detection
has_arabic = bool(re.search(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]", text))

# Arabic tokenization: word-level
# Long words (>20 chars) split into 20-char segments
# This handles connected Arabic script and compound words
```

**Arabic-specific chunking tips**:
- Use `hybrid` strategy for Arabic documents
- Increase overlap to 25% for Arabic (128 tokens for 512 chunk)
- Preserve paragraph boundaries to maintain meaning
- Keep related Arabic phrases together when possible

---

## Embedding Model Selection Criteria

### Current Implementation (from EmbeddingService)

```python
# Default model: text-embedding-3-large (OpenAI)
# Dimension: 3072 (stored in pgvector)
# Cache: SHA-256 hash of text → embedding vector
# Batch size: configurable via EmbeddingConfig
# Retries: 3 with exponential backoff
```

### Model Selection Matrix

| Model | Dimension | Cost/1M tokens | Multilingual | Business Docs | Recommended |
|-------|-----------|----------------|--------------|---------------|-------------|
| text-embedding-3-large | 3072 | $0.13 | Excellent | Best | ✅ Default |
| text-embedding-3-small | 1536 | $0.02 | Good | Good | Budget option |
| text-embedding-ada-002 | 1536 | $0.10 | Good | Good | Legacy |
| Cohere embed-v3 | 1024 | $0.10 | Excellent | Good | Alternative |
| Sentence-BERT | 768 | Self-hosted | Good | Good | On-premises |

### Selection Criteria

| Factor | Weight | text-embedding-3-large | text-embedding-3-small |
|--------|--------|----------------------|----------------------|
| Multilingual (Arabic) | 0.30 | 0.95 | 0.80 |
| Business domain accuracy | 0.25 | 0.90 | 0.80 |
| Cost efficiency | 0.20 | 0.60 | 0.95 |
| Dimension (storage) | 0.15 | 0.70 | 0.85 |
| Speed | 0.10 | 0.75 | 0.90 |
| **Weighted Score** | | **0.83** | **0.85** |

**Recommendation**: Use `text-embedding-3-large` for accuracy-critical queries, `text-embedding-3-small` for cost-sensitive batch operations.

---

## Hybrid Search Tuning Parameters

### Current Implementation (from RetrievalService)

```python
# Hybrid search combines vector similarity + full-text search
# SQL fusion formula:
score = vector_score * 0.7 + text_score * 0.3

# Vector similarity: cosine distance (1 - cosine_distance)
# Text search: ts_rank with 'simple' text configuration
```

### Tuning Parameters

| Parameter | Current Value | Range | Impact |
|-----------|---------------|-------|--------|
| vector_weight | 0.7 | 0.5-0.9 | Higher = more semantic matching |
| text_weight | 0.3 | 0.1-0.5 | Higher = more keyword matching |
| min_score | 0.7 | 0.5-0.9 | Lower = more results, higher noise |
| top_k | 5 | 3-20 | More results = more context, higher cost |
| pgvector_lists | 100 | 50-200 | Higher = faster search, more memory |

### Tuning Scenarios

**Scenario 1: Semantic-heavy (recommended for Arabic)**
```python
vector_weight = 0.8  # Boost semantic matching
text_weight = 0.2
min_score = 0.6      # Lower threshold for Arabic
top_k = 7
```

**Scenario 2: Keyword-heavy (technical documents)**
```python
vector_weight = 0.5
text_weight = 0.5    # Equal weight
min_score = 0.75
top_k = 5
```

**Scenario 3: Broad discovery (market research)**
```python
vector_weight = 0.6
text_weight = 0.4
min_score = 0.5      # Very low threshold
top_k = 10
```

### Fallback Strategy

```
pgvector available? ──Yes──▶ Vector search (pgvector)
       │
       No
       │
       ▼
  Fallback store (in-memory dict)
  No similarity scoring, returns all chunks
```

---

## Context Window Management

### Token Budget Planning

```
Total context window: 128K tokens (GPT-4o)
├── System prompt: ~500 tokens
├── Schema guide: ~200 tokens
├── Grounding context: ~2000 tokens
├── RAG context: ~2000 tokens (5 chunks × ~400 tokens)
├── User query: ~500 tokens
├── Response buffer: ~1000 tokens
└── Safety margin: ~500 tokens
Total estimated: ~6700 tokens (well within budget)
```

### Context Window Strategies

| Strategy | When to Use | Implementation |
|----------|------------|----------------|
| Priority truncation | Limited context | Keep most relevant chunks only |
| Summarization | Long documents | Summarize before injecting |
| Sliding window | Sequential analysis | Process in overlapping windows |
| Map-reduce | Very long docs | Process chunks independently, merge results |

### Grounding Context Structure (from AgentContext)

```python
@dataclass
class AgentContext:
    company_info: dict    # ~200 tokens
    contacts: list        # ~500 tokens (top 5)
    opportunities: list   # ~500 tokens (top 5)
    relationships: list   # ~300 tokens (top 5)
    signals: list         # ~500 tokens (top 5)
    recent_activity: list # ~500 tokens (top 5)

# Total: ~2500 tokens max
# Truncation: top 5 items per category
```

### Context Assembly Order

```python
# 1. System prompt (role, instructions, output format)
# 2. Grounding context (company data from DB/Neo4j)
# 3. RAG context (relevant document chunks)
# 4. User query (the actual question)
# 5. Schema guide (JSON output format)
```

### Context Overflow Handling

| Overflow Type | Detection | Mitigation |
|--------------|-----------|------------|
| Too many chunks | len(chunks) > top_k | Take top_k by score |
| Large context | token_count > budget | Priority truncation |
| Mixed languages | Arabic + English | Separate language blocks |
| Special characters | Unicode issues | Sanitize before injection |

---

## Citation Tracking Implementation

### Citation Schema (from RagService)

```python
@dataclass
class Citation:
    document_id: str      # UUID of source document
    title: str            # Document title
    source_type: str      # "crm", "document", "email", etc.
    source_id: str        # Original source identifier
    score: float          # Retrieval relevance score (0-1)
```

### Citation Deduplication

```python
seen_sources: set[str] = set()

for result in retrieval_results:
    source_id = result.source.id
    if source_id not in seen_sources:
        seen_sources.add(source_id)
        citations.append({
            "document_id": result.source.id,
            "title": result.source.title,
            "source_type": result.source.source_type,
            "source_id": result.source.source_id,
            "score": round(result.score, 4),
        })
```

### Citation Display Formats

**Inline (Arabic)**:
```
التحليل مبني على تقارير المبيعات (score: 0.92) وتقارير السوق (score: 0.85)
```

**Footnote style**:
```
تشهد الشركة نموًا مستقرًا[1] مع توسع في السوق السعودي[2].

[1] تقرير المبيعات Q3 2026 (score: 0.92)
[2] تقرير السوق الشهري (score: 0.85)
```

**JSON (API response)**:
```json
{
  "answer": "التحليل النصي...",
  "citations": [
    {
      "document_id": "doc_uuid_1",
      "title": "تقرير المبيعات Q3 2026",
      "source_type": "crm",
      "source_id": "report_123",
      "score": 0.92
    }
  ],
  "chunks_used": 5,
  "confidence": 0.85
}
```

### Citation Quality Metrics

| Metric | Definition | Target |
|--------|-----------|--------|
| Source diversity | Unique sources / total chunks | > 0.6 |
| Score average | Mean retrieval score | > 0.75 |
| Coverage | Chunks from different doc types | > 2 types |
| Freshness | Most recent source age | < 30 days |

### Citation Storage (PostgreSQL)

```sql
-- Document table
CREATE TABLE rag_documents (
    id UUID PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    source_type VARCHAR(50) NOT NULL,  -- crm, document, email, etc.
    source_id VARCHAR(255) NOT NULL,   -- original source ID
    title TEXT NOT NULL DEFAULT '',
    content TEXT NOT NULL DEFAULT '',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Chunk table with embeddings
CREATE TABLE rag_document_chunks (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES rag_documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding vector(3072),            -- pgvector column
    chunk_index INTEGER NOT NULL DEFAULT 0,
    metadata JSONB DEFAULT '{}'
);

-- Indexes for performance
CREATE INDEX idx_rag_chunks_document ON rag_document_chunks (document_id);
CREATE INDEX idx_rag_chunks_tenant ON rag_documents (tenant_id);
CREATE INDEX idx_rag_chunks_vector ON rag_document_chunks
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

---

## RAG Pipeline Optimization Checklist

### Pre-Deployment

- [ ] Chunk size tuned for document types (512 default, adjust for Arabic)
- [ ] Embedding model selected and tested (text-embedding-3-large)
- [ ] Hybrid search weights tuned (vector: 0.7, text: 0.3)
- [ ] min_score threshold validated (0.7 default)
- [ ] pgvector index created with appropriate lists (100)
- [ ] Citation deduplication working correctly
- [ ] Fallback store functional (in-memory)
- [ ] Context window budget calculated

### Performance Monitoring

| Metric | Threshold | Alert |
|--------|-----------|-------|
| Retrieval latency (p95) | < 200ms | > 300ms |
| Embedding latency (p95) | < 500ms | > 1000ms |
| Cache hit rate | > 80% | < 60% |
| Chunks per query | 3-7 | > 10 |
| Citation diversity | > 0.6 | < 0.4 |

### Cost Optimization

| Strategy | Savings | Trade-off |
|----------|---------|-----------|
| Embedding cache | 30-50% | Memory usage |
| Batch embedding | 20-30% | Slight latency |
| Smaller model for drafts | 80% | Lower quality |
| Chunk deduplication | 10-15% | Storage overhead |

---

*Last updated: 2026-07-13*
*Version: 1.0*
