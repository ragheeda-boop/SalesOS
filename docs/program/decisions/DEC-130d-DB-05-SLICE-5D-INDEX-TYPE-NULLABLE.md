# DEC-130d — DB-05 Slice 5d: index / type / nullable alignments

> **Status:** **Accepted** — Cursor implementation **COMPLETE** · Criterion **7.6 remains OPEN** (clean check **not** met) · Package = **READY FOR REVIEW** (Architecture / Validation: index+type+null honesty + evidence only; do **not** CLOSE 7.6)  
> **Date:** 2026-08-01  
> **Board:** Backend Platform / Database (SalesOS / AQLIYA)  
> **Story / risk:** DB-05 / R-20 / Phase 0 Exit Criterion **7.6**  
> **Authority:** DEC-130 Slice 5a plan · DEC-130c Slice 5c · DEC-122 Slice 3 pattern · DEC-085 `set_config` · DEC-107 swarm READY  
> **Out of scope this land:** DROP TABLE · DROP of KEEP companies columns (`do_not_contact`, `embedding_vector` = **5e**) · SET NOT NULL without null inventory · orphan KEEP DROPs (5f+) · production / Railway migrate · Prisma · DEC-085 edits · Production GO / CI GREEN · Criterion VERIFIED/CLOSED

---

## 1. Decision

Ship **Slice 5d** = additive **CREATE INDEX** (37 ORM-missing) + safe **contacts** VARCHAR widen + ORM→metadata type/nullable/index-register alignments. **No DROP.** Criterion **7.6 stays OPEN**.

| Pin | Value |
|---|---|
| Alembic head (local compose) | **`a4f7c29e1b80`** (down **`e2b9d46f8a10`**) |
| `alembic check` | **FAILED** (exit **255**) — expected (residual noise remains) |
| `Detected added index` | **37 → 0** |
| `Detected type change` | **13 → 1** (residual: `vectors.id` TEXT↔String — pgvector Core Table) |
| `Detected NOT NULL` | **33 → 0** (ORM loosened to match DB nullability) |
| `Detected NULL` | **5 → 2** (residual: `vectors.embedding` / `vectors.metadata`) |
| `Detected removed index` | **84 → 61** (live-table register + orphan KEEP residual) |
| `Detected removed table` | **15** (unchanged — orphan KEEP / 5f+) |
| Companies KEEP columns | **untouched** (`do_not_contact`, `embedding_vector` still remove_column — **5e**) |
| DEC-085 | **Intact** (not touched) |
| Criterion 7.6 | **OPEN** — phased residual (next **5e**) |

### Alternatives considered

| Option | Result |
|---|---|
| (a) DROP legacy rename-twin indexes | **Rejected** — keep twins until dedicated rename/DROP DEC |
| (b) SET NOT NULL on workflow/marketplace/admin | **Rejected** — DB allows NULL; needs null inventory |
| (c) Additive CREATE INDEX + ORM align to live DB | **Approved** |

---

## 2. Scope

### Migration `a4f7c29e1b80`

- Idempotent `_index_exists` CREATE for **37** ORM-declared indexes (commercial, companies, contacts, emails, meetings, entity resolution, golden_records, DLQ, device_sessions, licenses, marketplace, token_blacklist, audit outcome)
- `ALTER COLUMN contacts.name` / `name_ar` VARCHAR(255) → VARCHAR(500) when shorter
- Downgrade: drop created indexes + narrow contacts (local/compose only)

### ORM / metadata (no DDL)

| Area | Fix |
|---|---|
| `api_keys.permissions` | `JSON` → `JSONB`; register `ix_api_keys_prefix` / `ix_api_keys_user` |
| `audit_logs.id` | `Integer` → `BigInteger`; register tenant composites |
| `company_features` | `signals` → `JSONB`; timestamps `nullable=False`; unique index name = live `ix_company_features_lookup` |
| Decision Center | `Text` + `DateTime(timezone=True)`; register `ix_dcd_*` / `ix_dcf_decision`; `_aware_utc` (DB is TIMESTAMPTZ) |
| admin / marketplace / workflow / notifications / feature_* | `nullable=True` where DB allows NULL |
| `dead_letter_queue.created_at` | ORM `nullable=True` (no SET NOT NULL) |
| `graph_edges.created_at` | Core Table `nullable=False` |
| activity_records / domain_events / graph_edges | Register live indexes on Core Tables |

---

## 3. Live evidence (Docker compose, 2026-08-01)

```text
docker compose exec -T backend alembic upgrade head   → a4f7c29e1b80
docker compose exec -T backend alembic current        → a4f7c29e1b80 (head)
docker compose exec -T backend alembic check          → FAILED exit 255
```

| Class | Before (5c @ `e2b9d46f8a10`) | After (5d @ `a4f7c29e1b80`) | Notes |
|---|---:|---:|---|
| `Detected added index` | **37** | **0** | CREATE INDEX landed |
| `Detected type change` | **13** | **1** | vectors residual |
| `Detected NOT NULL` | **33** | **0** | ORM→DB nullable |
| `Detected NULL` | **5** | **2** | vectors residual |
| `Detected removed index` | **84** | **61** | register + orphan KEEP |
| `Detected removed table` | **15** | **15** | orphan KEEP (5f+) |
| `Detected removed column` | **4** | **4** | companies KEEP + vectors cols (5e+) |
| DEC-085 `set_config` | intact | intact | untouched |

---

## 4. Validation

| Check | Result |
|---|---|
| Docker `alembic current` / `heads` | `a4f7c29e1b80` |
| Docker `alembic check` | **FAILED** (exit 255) — expected |
| `added_index` delta | **37 → 0** |
| Production / Railway migrate | **Not run** |
| DEC-085 | Untouched |
| Label | **light validated** (Docker upgrade + alembic check counts) |

**Production GO not claimed. CI GREEN not met. Criterion 7.6 not CLOSED.**

---

## 5. Records

- Phase 0 criterion **7.6** → **OPEN** (phased; Slice 5d COMPLETE / READY FOR REVIEW)
- Board DB-05 → Slice 5d COMPLETE; residual = 7.6 clean check (5e+)
- `DECISION_LOG.md` DEC-130d
- R-20 next-action → Slice **5e** companies residual columns KEEP/ORM
- **Not claimed:** Production GO · CI GREEN · `alembic check` clean · 7.6 VERIFIED/CLOSED

---

## 6. Architecture next?

Architecture Reviewer: confirm (1) additive CREATE INDEX + contacts widen are safe and match ORM, (2) ORM nullable/type align to live DB (no SET NOT NULL / no DROP) is correct, (3) KEEP companies columns and orphan tables remain untouched for **5e** / **5f+**, (4) down-revision pin `e2b9d46f8a10` → `a4f7c29e1b80` is sound. Validation: corroborate count deltas + head pin + FAILED check — do **not** treat as 7.6 close evidence.
