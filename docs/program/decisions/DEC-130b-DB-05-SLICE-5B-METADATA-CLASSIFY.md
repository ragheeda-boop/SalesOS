# DEC-130b — DB-05 Slice 5b: classify `remove_table` + register false positives

> **Status:** **Accepted** — Cursor implementation **COMPLETE** · Criterion **7.6 remains OPEN** (clean check **not** met) · Package = **READY FOR REVIEW** (Architecture / Validation: metadata honesty + evidence only; do **not** CLOSE 7.6)  
> **Date:** 2026-08-01  
> **Board:** Backend Platform / Database (SalesOS)  
> **Story / risk:** DB-05 / R-20 / Phase 0 Exit Criterion **7.6**  
> **Authority:** DEC-130 Slice 5a plan · DEC-129 KEEP · DEC-085 `set_config` · DEC-107 swarm READY  
> **Out of scope this land:** DROP any table/column · admin CREATE (5c) · index/type/null batches (5d) · companies residual columns (5e) · production / Railway migrate · Prisma · DEC-085 edits · Production GO / CI GREEN · Criterion VERIFIED/CLOSED

---

## 1. Decision

Ship **Slice 5b** = classify each of the Slice 5a **28** `remove_table` proposals as **FP (register)** vs **orphan KEEP** vs **true DROP DEC**, and register false positives into `Base.metadata` only. **No DROP.** Criterion **7.6 stays OPEN**.

| Pin | Value |
|---|---|
| Alembic head (local compose) | **`d1a8c35e7f09`** (unchanged; no new revision) |
| `alembic check` | **FAILED** (exit **255**) — expected |
| `remove_table` | **28 → 15** |
| `Base.metadata` size | **70 → 83** |
| DEC-085 | **Intact** (not touched) |
| Criterion 7.6 | **OPEN** — phased residual (next **5d**) |

### Alternatives considered

| Option | Result |
|---|---|
| (a) DROP the 28 “removed” tables | **Rejected** — false positives + live GA paths |
| (b) Mega-migration from autogenerate | **Rejected** — destructive; DEC-130 |
| (c) Classify + register FPs only (no DROP) | **Approved** |

---

## 2. Classification (28 → 13 FP registered + 15 orphan KEEP)

### FP — register (13) — done this land

| Table | Registration |
|---|---|
| `decision_center_decisions` | import `domains.decision_center.postgres_repo` |
| `decision_center_audits` | same |
| `decision_center_feedback` | same |
| `decision_center_templates` | same |
| `marketplace_plugins` | import `domains.marketplace.db_models` |
| `marketplace_lifecycle_events` | same (+ rename ORM attr `metadata` → `event_metadata` mapped to column `"metadata"` — Declarative reserved name blocked import) |
| `scoring_scorecards` | import `domains.scoring.infrastructure.postgres_repository` |
| `revenue_analytics_snapshots` | import `domains.revenue.analytics.postgres_repo` |
| `company_features` | `FeatureBase` → shared `sdk.database.Base`; drop explicit `schema="public"`; import `runtime.feature_store` |
| `activity_records` | Core `Table` → `to_metadata(Base.metadata)` |
| `domain_events` | Core `Table` → `to_metadata(Base.metadata)` |
| `graph_edges` | Core `Table` → `to_metadata(Base.metadata)` |
| `vectors` | Core `_collection_table("vectors")` → `to_metadata(Base.metadata)` |

### Orphan KEEP (15) — residual `remove_table`; **no DROP**

| Table | Why KEEP |
|---|---|
| `company_funding_events` | Enrichment / feature SQL (no Base ORM) |
| `company_payments` | same |
| `company_job_postings` | same |
| `company_intent_contacts` | same |
| `company_intent_visits` | same |
| `company_intent_rfps` | same |
| `company_intent_content` | same |
| `company_products` | same |
| `company_deals` | same |
| `company_policies` | Decision-engine policy store (raw SQL) |
| `decisions` | `decision_runtime` raw SQL |
| `decision_feedback_loop` | feedback_loop raw SQL |
| `rag_documents` | `intelligence/rag` raw SQL |
| `rag_document_chunks` | same |
| `graph_nodes` | Migration-created cache; no live `Table`/`__tablename__` |

### True DROP DEC (0 this land)

None. Any future DROP requires a dedicated DEC (Slice **5f+**).

---

## 3. Live evidence (Docker compose, 2026-08-01)

```text
docker compose exec -T backend alembic current   → d1a8c35e7f09 (head)
docker compose exec -T backend alembic check     → FAILED exit 255
```

| Class | Before (5a) | After (5b) | Notes |
|---|---:|---:|---|
| `Detected removed table` | **28** | **15** | FPs cleared; orphans remain |
| `Detected added table` | **3** | **3** | admin trio — Slice **5c** |
| `Detected removed index` | **~100** | **84** | noise ↓ incidental |
| `Detected added index` | **~37** | **38** | Slice **5d** |
| `Detected removed column` | **2** | **4** | companies KEEP-adjacent (`do_not_contact`, `embedding_vector`) + `vectors.created_at`/`updated_at` (Core Table incomplete) — **no DROP** |
| New Alembic revision | — | **None** | metadata-only land |

Log capture (local, not committed): `.tmp-alembic-check-7-6-slice5b.txt`

---

## 4. Validation

| Check | Result |
|---|---|
| Docker `alembic current` / `heads` | `d1a8c35e7f09` |
| Docker `alembic check` | **FAILED** (exit 255) — expected |
| `remove_table` delta | **28 → 15** |
| DEC-085 `set_config` | Untouched |
| Production / Railway migrate | **Not run** |
| Label | **light validated** (Docker alembic check + metadata count 83) |

**Production GO not claimed. CI GREEN not met. Criterion 7.6 not CLOSED.**

---

## 5. Records

- Phase 0 criterion **7.6** → **OPEN** (phased; Slice 5b COMPLETE / READY FOR REVIEW)
- Board DB-05 → Slice 5b COMPLETE; residual = 7.6 clean check (5c+)
- `DECISION_LOG.md` DEC-130b
- R-20 next-action → Slice **5c** admin CREATE trio → **landed DEC-130c**
- **Not claimed:** Production GO · CI GREEN · `alembic check` clean · 7.6 VERIFIED/CLOSED

---

## 6. Architecture next?

Architecture Reviewer: confirm (1) FP registration / orphan KEEP / no-DROP classification is sound, (2) marketplace `event_metadata` rename is safe (column name unchanged), (3) Core `to_metadata` copies are acceptable for alembic discovery without changing runtime MetaData ownership, (4) Slice **5c** additive CREATE for `admin_plans` / `admin_feature_flags` / `admin_health_snapshots` is the correct next Backend land. Validation: corroborate `remove_table` **28→15** + head pin + FAILED check — do **not** treat as 7.6 close evidence.
