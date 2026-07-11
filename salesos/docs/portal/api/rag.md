# RAG Pipeline API

> **RAG — الاسترجاع المعزز بالتوليد للإجابة على أسئلة الشركات**

Base path: `/api/v1/rag`

---

## Query RAG

```
POST /api/v1/rag/query
```

**Permissions:** Requires AI feature flag

```bash
curl -X POST "https://api.salesos.sa/api/v1/rag/query" \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-Id: <tenant_id>" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "ما هي أحدث تراخيص شركة المملكة للتقنية؟",
    "company_id": "comp_mamlaka_123",
    "max_chunks": 5
  }'
```

**Response (200):**

```json
{
  "answer": "شركة المملكة للتقنية لديها ترخيص ساري المفعول من وزارة الاتصالات وتقنية المعلومات (رقم الترخيص: 852147963) صادر في 2025-03-15 وينتهي في 2028-03-14 [1]. كما لديها ترخيص إضافي من هيئة الاتصالات والفضاء والتقنية (رقم: 741258) [2].",
  "citations": [
    {
      "id": 1,
      "source": "وزارة الاتصالات — سجل التراخيص",
      "text": "الترخيص رقم 852147963 — شركة المملكة للتقنية — ساري حتى 2028-03-14",
      "score": 0.94,
      "is_accurate": true
    },
    {
      "id": 2,
      "source": "هيئة الاتصالات — سجل التراخيص",
      "text": "الترخيص رقم 741258 — شركة المملكة للتقنية",
      "score": 0.87,
      "is_accurate": true
    }
  ],
  "pipeline_trace": {
    "retrieval_ms": 145,
    "generation_ms": 890,
    "total_ms": 1035
  }
}
```

---

## Ingest Document

```
POST /api/v1/rag/documents
```

**Permissions:** Requires AI feature flag

Supports: PDF, DOCX, HTML, TXT, EML (max 10MB)

```bash
curl -X POST "https://api.salesos.sa/api/v1/rag/documents" \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-Id: <tenant_id>" \
  -F "file=@contract.pdf" \
  -F "company_id=comp_mamlaka_123"
```

---

## Get Document Status

```
GET /api/v1/rag/documents/{id}
```

Returns processing status: `pending`, `processing`, `ready`, `failed`.

---

## RAG Pipeline Stages

```
Document Upload
      │
      ▼
┌─────────────────┐
│ Parse & Chunk    │  PDF/DOCX → semantic chunks
└────────┬────────┘
         ▼
┌─────────────────┐
│ Embed (E5)      │  multilingual-e5-large → 1024d vector
└────────┬────────┘
         ▼
┌─────────────────┐
│ Store in pgvector│  HNSW index, tenant-partitioned
└────────┬────────┘
         ▼
┌─────────────────┐
│ Hybrid Search   │  Semantic + BM25 + RRF fusion
└────────┬────────┘
         ▼
┌─────────────────┐
│ Context Assembly │  Token-aware, max 6000 tokens
└────────┬────────┘
         ▼
┌─────────────────┐
│ LLM Generation  │  GPT-4o-mini with citations
└────────┬────────┘
         ▼
┌─────────────────┐
│ Citation Verify │  Verify each citation against source
└─────────────────┘
```

## Related

| Resource | Link |
|----------|------|
| RAG Architecture | [Wave 3 RAG](../../docs/wave-3/02-AI_RAG_ARCHITECTURE.md) |
| Embedding RAG Guide | [Guide](../guides/embedding-rag.md) |
