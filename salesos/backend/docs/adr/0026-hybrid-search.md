# ADR-026: Hybrid Search with RRF Fusion (Full-Text + Semantic)

**Status:** Accepted  
**Date:** 2026-07-12  
**Deciders:** CTO, Chief Architect, Search Engineer  
**Tags:** architecture, search, hybrid, semantic, full-text, arabic, pgvector

## Context

SalesOS search needs to serve multiple use cases:

- **Keyword search** — users searching for exact company names, CR numbers, emails
- **Semantic search** — users searching by concept ("companies in fintech", "contacts who work in sales")
- **Arabic search** — the primary language for many users, with diacritics, transliteration variations, and right-to-left text

Previous approaches:
- PostgreSQL full-text search (`tsvector`/`tsquery`) handles keywords well but misses semantic intent
- Pure vector search (pgvector) captures semantics but fails on exact matches and is slower for simple lookups
- External search services (Elasticsearch, Algolia) add operational complexity and latency

Neither full-text nor semantic alone provides acceptable recall and precision.

## Decision

Implement **Hybrid Search** combining PostgreSQL `tsvector` full-text search with `pgvector` semantic embeddings, fused via **Reciprocal Rank Fusion (RRF)**.

### Architecture

```
┌──────────────────────────────────────────────────────────┐
│                     Search Query                          │
│              (Arabic or English, any text)                │
└──────────────────┬───────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
┌───────────────┐    ┌────────────────┐
│  tsvector    │    │  pgvector      │
│  Full-Text   │    │  Semantic      │
│  Search      │    │  Search        │
│              │    │                │
│  ts_config:  │    │  Embedding:    │
│  'arabic'    │    │  1536-dim      │
│  for Arabic  │    │  cosine sim    │
└──────┬───────┘    └───────┬────────┘
       │                    │
       ▼                    ▼
┌──────────────────────────────────────┐
│       Reciprocal Rank Fusion (RRF)   │
│                                      │
│  score(d) = Σ 1/(k + rank_i(d))     │
│  k = 60 (standard constant)         │
└──────────────────┬───────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
┌───────────────┐    ┌────────────────┐
│  Timeout      │    │  Max Results   │
│  Guard        │    │  Limit         │
│  (500ms)      │    │  (100/page)    │
└──────┬────────┘    └───────┬────────┘
       │                     │
       ▼                     ▼
┌──────────────────────────────────────┐
│          Ranked Results              │
│  (with highlights, snippets, scores) │
└──────────────────────────────────────┘
```

### Full-Text Search (tsvector)

```sql
-- Arabic-optimized full-text search
ALTER TABLE companies ADD COLUMN search_vector tsvector;

CREATE INDEX idx_companies_search ON companies USING GIN(search_vector);

-- Populate with Arabic config
UPDATE companies SET search_vector =
    setweight(to_tsvector('arabic', COALESCE(name, '')), 'A') ||
    setweight(to_tsvector('arabic', COALESCE(name_ar, '')), 'A') ||
    setweight(to_tsvector('arabic', COALESCE(industry, '')), 'B') ||
    setweight(to_tsvector('arabic', COALESCE(description, '')), 'C');
```

### Semantic Search (pgvector)

```sql
-- Embedding storage
ALTER TABLE companies ADD COLUMN embedding vector(1536);

CREATE INDEX idx_companies_embedding ON companies
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
```

### Reciprocal Rank Fusion

```python
def reciprocal_rank_fusion(
    full_text_results: list[SearchResult],
    semantic_results: list[SearchResult],
    k: int = 60
) -> list[SearchResult]:
    """
    Fuse two ranked lists using RRF.

    RRF score for document d = sum over each list:
        1 / (k + rank_of_d_in_list_i)

    k=60 is the standard constant from the original RRF paper.
    """
    scores: dict[str, float] = defaultdict(float)
    result_map: dict[str, SearchResult] = {}

    for rank, result in enumerate(full_text_results, start=1):
        scores[result.id] += 1.0 / (k + rank)
        result_map[result.id] = result

    for rank, result in enumerate(semantic_results, start=1):
        scores[result.id] += 1.0 / (k + rank)
        if result.id not in result_map:
            result_map[result.id] = result

    # Sort by combined RRF score descending
    return sorted(
        [result_map[doc_id] for doc_id in scores],
        key=lambda r: scores[r.id],
        reverse=True
    )
```

### Timeout Guard

```python
async def search_with_timeout(
    query: str,
    tenant_id: UUID,
    timeout_ms: int = 500,
    max_results: int = 100
) -> SearchResponse:
    """
    Execute hybrid search with timeout protection.
    Falls back to full-text only if semantic search exceeds timeout.
    """
    try:
        full_text, semantic = await asyncio.wait_for(
            asyncio.gather(
                search_full_text(query, tenant_id),
                search_semantic(query, tenant_id),
            ),
            timeout=timeout_ms / 1000
        )
        return SearchResponse(
            results=reciprocal_rank_fusion(full_text, semantic)[:max_results],
            strategy="hybrid"
        )
    except asyncio.TimeoutError:
        # Degrade gracefully to full-text only
        full_text = await search_full_text(query, tenant_id)
        return SearchResponse(
            results=full_text[:max_results],
            strategy="full-text-only",
            degraded=True
        )
```

### Arabic Text Normalization

```python
def normalize_arabic(text: str) -> str:
    """
    Normalize Arabic text before indexing and querying.
    - Remove diacritics (tashkeel)
    - Normalize alef variants (أ, إ, آ → ا)
    - Normalize teh marbuta (ة → ه)
    - Normalize yeh (ى → ي)
    """
    text = re.sub(r'[\u0610-\u061A\u064B-\u065F\u0670]', '', text)  # Remove diacritics
    text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
    text = text.replace('ة', 'ه').replace('ى', 'ي')
    return text
```

### Search API

```python
class SearchRequest(BaseModel):
    query: str
    entity_types: list[str] = ["company", "contact"]
    filters: dict = {}
    page: int = 1
    page_size: int = 20  # max 100

class SearchResponse(BaseModel):
    results: list[SearchResult]
    total: int
    strategy: str  # 'hybrid', 'full-text-only', 'semantic-only'
    degraded: bool = False
    latency_ms: float
```

## Consequences

### Positive
1. **No external search service** — PostgreSQL handles everything, no Elasticsearch/Algolia dependency
2. **Arabic text normalization built-in** — diacritics, alef variants, teh marbuta handled at index time
3. **Graceful degradation** — timeout guard ensures search never hangs; falls back to full-text only
4. **Consistent ranking** — RRF combines signals without requiring score calibration between different scoring systems
5. **Existing infrastructure** — uses PostgreSQL extensions already in the stack (pg_trgm, pgvector)

### Negative
1. **RRF is simpler than learning-to-rank** — may not suit all use cases where feature-based ranking is needed
2. **Embedding generation adds latency** — semantic search requires embedding the query (mitigated by timeout guard)
3. **IVFFlat index tuning** — `lists` parameter needs tuning based on data volume
4. **No real-time indexing** — embedding updates are asynchronous (mitigated by batch refresh)

### Mitigations
- Timeout guard ensures p95 latency stays within budget (500ms)
- Full-text search is always available as fallback
- IVFFlat index can be rebuilt online as data grows
- Future: replace RRF with learning-to-rank if needed (ADR would be required per Material 3.1)

## Compliance

- [x] Uses repository pattern — `SearchRepository` interface in domain, PostgreSQL implementation in infrastructure
- [x] Tenant isolation — all searches scoped by `tenant_id`
- [x] No cross-domain imports — search is self-contained within Search domain
- [x] Rate limiting — search endpoint uses standard API rate limits
- [x] Input validation — query length, page_size bounds, entity_type whitelist
- [x] Automated checks:
  - `pgvector` extension exists: `SELECT * FROM pg_extension WHERE extname = 'vector'`
  - Search vector index exists: `SELECT * FROM pg_indexes WHERE indexname LIKE '%search%'`
  - Embedding dimension validation: `SELECT vector_dims(embedding) FROM companies LIMIT 1`
  - Timeout configuration: `SEARCH_TIMEOUT_MS` environment variable present
  - Max page size enforced: `PAGE_SIZE <= 100` in request validation
