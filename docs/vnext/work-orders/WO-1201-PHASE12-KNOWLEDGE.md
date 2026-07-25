# Work Order WO-1201 — Phase 12: Knowledge

> **Issued by**: SalesOS Engineering OS
> **Date**: 2026-07-16
> **Status**: Active
> **Dependency**: Phase 0 ✅, Phase 3 ✅
> **Priority**: P0

---

## Scope

Knowledge platform: decompose KG runtime, PGVector native, embedding cache, hybrid retrieval, Data Fabric connectors.

## Tasks

### Backend

| # | Task | Effort |
|---|------|--------|
| B-1 | **Decompose KG runtime** — split 1,087-line `knowledge_graph_runtime/` into service + repository + router (< 500 lines each) | 3d |
| B-2 | **PGVector native type** — migrate `ARRAY(FLOAT)` to `VECTOR(n)`, add HNSW index | 2d |
| B-3 | **Embedding cache** — LRU cache for embeddings, hit rate > 40% target | 1.5d |
| B-4 | **Hybrid retrieval** — vector similarity + BM25 with RRF fusion, F1 > 0.85 | 2d |
| B-5 | **Data Fabric connectors** — 3+ real connectors (CRM, ERP, market feeds) replacing mocks | 3d |

### Frontend

| # | Task | Effort |
|---|------|--------|
| F-1 | **Knowledge graph viewer** — visualize entities and relationships | 2d |
| F-2 | **Data Fabric connectors UI** — list, status, last sync | 1.5d |

## Acceptance Criteria

| Gate | Criteria |
|------|----------|
| G-12.1 | KG runtime split into modules < 500 lines each |
| G-12.2 | PGVector query speed ~50x improvement |
| G-12.3 | Embedding cache hit rate > 40% |
| G-12.4 | Hybrid retrieval F1 > 0.85 |
| G-12.5 | 3+ real Data Fabric connectors |

---

**Engineering OS**: ✅ Approved
