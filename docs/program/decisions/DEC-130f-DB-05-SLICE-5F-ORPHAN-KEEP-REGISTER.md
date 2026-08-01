# DEC-130f — DB-05 Slice 5f: orphan KEEP metadata register + vectors residual columns

> **Status:** **Accepted** — Cursor implementation **COMPLETE** · Criterion **7.6 remains OPEN** (clean check **not** met) · Package = **READY FOR REVIEW** (Architecture / Validation: orphan KEEP honesty + evidence only; do **not** CLOSE 7.6)  
> **Date:** 2026-08-01  
> **Board:** Backend Platform / Database (SalesOS / AQLIYA)  
> **Story / risk:** DB-05 / R-20 / Phase 0 Exit Criterion **7.6**  
> **Authority:** DEC-130 Slice 5a plan · DEC-130b orphan KEEP residual · DEC-130e Slice 5e · DEC-129 KEEP pattern · DEC-085 `set_config` · DEC-107 swarm READY  
> **Out of scope this land:** DROP any orphan table/column · dedicated DROP DEC · production / Railway migrate · Prisma · DEC-085 edits · Production GO / CI GREEN · Criterion VERIFIED/CLOSED

---

## 1. Decision

Ship **Slice 5f** = (1) classify residual `remove_table`×15 as **KEEP-document / metadata-register** (default KEEP; **true DROP DEC = 0**), (2) register Core `Table` stubs onto `Base.metadata` for live orphan tables (no ORM), (3) restore `vectors.created_at` / `vectors.updated_at` on Core `_collection_table`. **No DROP. No DDL.** Criterion **7.6 stays OPEN**.

| Pin | Value |
|---|---|
| Alembic head (local compose) | **unchanged** — **`a4f7c29e1b80`** (no new revision) |
| `alembic check` | **FAILED** (exit **255**) — expected (index/FK/comment residual) |
| `Detected removed table` | **15 → 0** |
| `Detected removed column` | **2 → 0** (vectors timestamps cleared) |
| `Base.metadata` size | **83 → 98** (+15 orphan KEEP stubs) |
| True DROP DEC | **0** — any future DROP needs dedicated DEC |
| DEC-085 | **Intact** (not touched) |
| Criterion 7.6 | **OPEN** — phased residual (next **5g+** index/FK/comment noise) |

### Alternatives considered

| Option | Result |
|---|---|
| (a) DROP the 15 orphan tables | **Rejected** — live enrichment / decision / RAG / graph paths; no dedicated DROP DEC |
| (b) Document-only KEEP inventory (leave remove_table×15) | **Rejected** — honest progress toward exit 0 prefers metadata KEEP register |
| (c) Metadata KEEP register + vectors Core columns (no DDL) | **Approved** |

---

## 2. Classification (15 orphans)

| Table | Class | Action |
|---|---|---|
| `company_funding_events` | KEEP-document → **metadata register** | Core stub in `app/db05_orphan_keep.py` |
| `company_payments` | same | same |
| `company_job_postings` | same | same |
| `company_intent_contacts` | same | same |
| `company_intent_visits` | same | same |
| `company_intent_rfps` | same | same |
| `company_intent_content` | same | same |
| `company_products` | same | same |
| `company_deals` | same | same |
| `company_policies` | KEEP (policy_runtime raw SQL) | same |
| `decisions` | KEEP (decision_runtime raw SQL) | same |
| `decision_feedback_loop` | KEEP (feedback raw SQL) | same |
| `rag_documents` | KEEP (intelligence/rag raw SQL) | same |
| `rag_document_chunks` | KEEP (+ `_PgVector` embedding stand-in) | same |
| `graph_nodes` | KEEP (migration cache; companion to registered `graph_edges`) | same |
| **True DROP DEC** | — | **None** |

### Vectors residual columns

| Column | Live DB | Core action |
|---|---|---|
| `created_at` | timestamptz (0010) | added to `_collection_table` |
| `updated_at` | timestamptz (0010) | added to `_collection_table` |
| `ix_vectors_created_at` | present | Index registered on Core Table |

---

## 3. Live evidence (Docker compose, 2026-08-01)

```text
alembic_version: a4f7c29e1b80 (head unchanged)
Base.metadata: 98 tables; orphan KEEP missing = []
vectors cols: id, embedding, metadata, created_at, updated_at
alembic check: FAILED exit 255
```

| Class | Before (5e @ `a4f7c29e1b80`) | After (5f metadata @ `a4f7c29e1b80`) | Notes |
|---|---:|---:|---|
| `Detected removed table` | **15** | **0** | orphan KEEP stubs |
| `Detected removed column` | **2** | **0** | vectors timestamps |
| `Detected removed index` | **~61** (5d pin) | **36** | incidental ↓; residual noise remains |
| DEC-085 `set_config` | intact | intact | untouched |

Log capture (local, not committed): `.tmp-alembic-check-7-6-slice5f-after.txt`

---

## 4. Validation

| Check | Result |
|---|---|
| Docker `alembic_version` | `a4f7c29e1b80` |
| Docker `alembic check` | **FAILED** (exit 255) — expected |
| `remove_table` delta | **15 → 0** |
| `remove_column` delta | **2 → 0** |
| New Alembic revision | **None** |
| Production / Railway migrate | **Not run** |
| DEC-085 | Untouched |
| Label | **light validated** (Docker metadata probe + alembic check counts + unit KEEP guard) |

**Production GO not claimed. CI GREEN not met. Criterion 7.6 not CLOSED.**

---

## 5. Records

- Phase 0 criterion **7.6** → **OPEN** (phased; Slice 5f COMPLETE / READY FOR REVIEW)
- Board DB-05 → Slice 5f COMPLETE; residual = index/FK/comment / type noise toward clean check
- `DECISION_LOG.md` DEC-130f
- R-20 next-action → Slice **5g+** residual index/FK/comment (still no blind DROP)
- **Not claimed:** Production GO · CI GREEN · `alembic check` clean · 7.6 VERIFIED/CLOSED

---

## 6. Architecture next?

Architecture Reviewer: confirm (1) metadata KEEP stubs for the 15 live orphan tables (no DROP) is sound vs inventing ORM models, (2) vectors Core timestamp restore matches DEC-129/130e KEEP posture, (3) head pin `a4f7c29e1b80` unchanged (no DDL) is correct, (4) residual `remove_index` / FK / comment noise is the honest next Backend land (**5g+**) — do **not** treat as 7.6 close evidence. Validation: corroborate `remove_table` **15→0** + `remove_column` **2→0** + FAILED check.
