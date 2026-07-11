# Tutorial: Using RAG for Company Documents

> **RAG — إجابة الأسئلة عن الشركات باستخدام الذكاء الاصطناعي مع الاستشهادات**

This tutorial shows how to use the RAG pipeline to query company documents with citations.

---

## Step 1: Upload Documents

Upload company documents (contracts, reports, licenses) via the API:

```bash
curl -X POST "https://api.salesos.sa/api/v1/rag/documents" \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-Id: <tenant_id>" \
  -F "file=@contract_123.pdf" \
  -F "company_id=comp_mamlaka_123"
```

**Response:**

```json
{
  "id": "doc_uuid",
  "status": "processing",
  "filename": "contract_123.pdf",
  "file_size": 2450000,
  "created_at": "2026-07-11T10:00:00Z"
}
```

---

## Step 2: Check Processing Status

```bash
curl -X GET "https://api.salesos.sa/api/v1/rag/documents/doc_uuid" \
  -H "Authorization: Bearer <token>"
```

Status: `pending` → `processing` → `ready` (typically 10-30s per document).

---

## Step 3: Query the Document

```python
import httpx

response = httpx.post(
    "https://api.salesos.sa/api/v1/rag/query",
    headers={
        "Authorization": "Bearer sos_your_key",
        "X-Tenant-Id": "tenant_xyz",
        "Content-Type": "application/json",
    },
    json={
        "query": "ما هي شروط العقد مع شركة المملكة للتقنية؟",
        "company_id": "comp_mamlaka_123",
    }
)

data = response.json()
print(f"Answer: {data['answer']}")
for citation in data['citations']:
    print(f"[{citation['id']}] {citation['source']} — accuracy: {citation['score']}")
```

**Output:**

```
Answer: وفقًا للعقد الموقع في 2025-01-15، تشمل الشروط: مدة العقد 3 سنوات (تنتهي في 2028-01-14)،
قيمة العقد 2,500,000 ريال سعودي، وتجديد تلقائي لمدة سنة إضافية [1]. تتضمن بنود الخدمة
مستوى اتفاقية الخدمة (SLA) بنسبة 99.5% [2].

[1] contract_123.pdf — accuracy: 0.94
[2] contract_123.pdf — accuracy: 0.89
```

---

## Step 4: Use RAG with the SDK

```typescript
import { RAGClient } from '@salesos/decision-platform'

const rag = new RAGClient({
  apiKey: 'sos_your_key',
  tenantId: 'tenant_xyz',
})

const result = await rag.query({
  query: 'ما هي شروط العقد؟',
  companyId: 'comp_mamlaka_123',
  maxChunks: 5,
})

console.log(result.answer)
result.citations.forEach(c => {
  console.log(`[${c.id}] ${c.source} (${(c.score * 100).toFixed(0)}%)`)
})
```

---

## RAG Pipeline Components

| Component | Technology | Role |
|-----------|-----------|------|
| Document Parser | PyMuPDF, python-docx | Extract text from PDF/DOCX |
| Chunker | Custom (semantic/heading/sentence) | Split text into searchable chunks |
| Embedder | multilingual-e5-large (self-hosted) | Convert text to 1024-dim vectors |
| Vector Store | pgvector (HNSW index) | Store and search embeddings |
| Retriever | Hybrid (semantic + BM25) | Find relevant chunks |
| Generator | GPT-4o-mini | Generate answer with citations |
| Verifier | Custom NLP | Verify citations against sources |

---

## Best Practices

1. **Upload clear documents** — Scanned PDFs with OCR work but have lower quality
2. **Use specific queries** — "What is the contract value?" works better than "Tell me about the company"
3. **Verify citations** — Always check the source text for critical information
4. **Arabic queries work** — RAG handles bilingual input natively

---

## Related

| Resource | Link |
|----------|------|
| RAG Architecture | [Wave 3 RAG](../../docs/wave-3/02-AI_RAG_ARCHITECTURE.md) |
| RAG API Reference | [API](../api/rag.md) |
