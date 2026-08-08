# DEC-130e — DB-05 Slice 5e: companies residual columns KEEP (ORM)

> **Status:** **Accepted** — Cursor implementation **COMPLETE** · Criterion **7.6 remains OPEN** (clean check **not** met) · Package = **READY FOR REVIEW** (Architecture / Validation: companies KEEP honesty + evidence only; do **not** CLOSE 7.6)  
> **Date:** 2026-08-01  
> **Board:** Backend Platform / Database (SalesOS)  
> **Story / risk:** DB-05 / R-20 / Phase 0 Exit Criterion **7.6**  
> **Authority:** DEC-130 Slice 5a plan · DEC-130d Slice 5d · DEC-129 KEEP pattern · DEC-085 `set_config` · DEC-107 swarm READY  
> **Out of scope this land:** DROP any column/table · new Alembic revision (columns already live) · orphan KEEP DROPs (5f+) · vectors Core Table residual · production / Railway migrate · Prisma · DEC-085 edits · Production GO / CI GREEN · Criterion VERIFIED/CLOSED

---

## 1. Decision

Ship **Slice 5e** = restore live companies residual columns on `Company` ORM / metadata so `alembic check` stops proposing `remove_column` DROP. Disposition **KEEP** (DEC-129 pattern). **No DROP. No DDL.** Criterion **7.6 stays OPEN**.

| Pin | Value |
|---|---|
| Alembic head (local compose) | **unchanged** — **`a4f7c29e1b80`** (no new revision) |
| Live columns | `companies.do_not_contact` BOOLEAN NOT NULL default false; `companies.embedding_vector` vector(3072) NULL |
| `alembic check` | **FAILED** (exit **255**) — expected (residual noise remains) |
| `Detected removed column` | **4 → 2** (companies pair cleared; residual = `vectors.created_at` / `vectors.updated_at`) |
| Companies `remove_column` | **`do_not_contact` + `embedding_vector` gone** |
| DEC-085 | **Intact** (not touched) |
| Criterion 7.4 | **KEEP stands** (DEC-129a CLOSED; unchanged) |
| Criterion 7.6 | **OPEN** — phased residual (next **5f+** orphan KEEP / vectors) |

### Alternatives considered

| Option | Result |
|---|---|
| (a) DROP `do_not_contact` / `embedding_vector` | **Rejected** — live runtime/search paths; DEC-129 KEEP posture |
| (b) Additive CREATE migration | **Rejected** — columns already live in Docker Postgres |
| (c) KEEP + ORM restore (no DDL) | **Approved** |

---

## 2. Scope

### ORM / metadata (no DDL)

| Column | Live DB | ORM action |
|---|---|---|
| `do_not_contact` | boolean NOT NULL default false (0003) | `Boolean` + `server_default="false"` on `Company` |
| `embedding_vector` | `vector(3072)` NULL (0006) | `_PgVector(3072)` UserDefinedType with `compare_against_backend → True` (no pgvector package; silences DROP/ALTER) |

### Unit guard

- Extended `tests/unit/test_dec129_companies_keep_columns.py` KEEP set with `do_not_contact` + `embedding_vector`.

---

## 3. Live evidence (Docker compose, 2026-08-01)

```text
information_schema: do_not_contact bool NOT NULL default false; embedding_vector vector NULL
alembic_version: a4f7c29e1b80 (head unchanged)
alembic check: FAILED exit 255
```

| Class | Before (5d @ `a4f7c29e1b80`) | After (5e ORM @ `a4f7c29e1b80`) | Notes |
|---|---:|---:|---|
| `Detected removed column` | **4** | **2** | companies KEEP cleared |
| companies `do_not_contact` remove_column | present | **absent** | KEEP |
| companies `embedding_vector` remove_column | present | **absent** | KEEP (`Couldn't determine database type` warning only) |
| vectors `created_at` / `updated_at` remove_column | present | present | **5f+** / Core Table residual |
| DEC-085 `set_config` | intact | intact | untouched |

---

## 4. Validation

| Check | Result |
|---|---|
| Docker `alembic_version` | `a4f7c29e1b80` |
| Docker `alembic check` | **FAILED** (exit 255) — expected |
| `remove_column` delta | **4 → 2** (companies pair cleared) |
| New Alembic revision | **None** |
| Production / Railway migrate | **Not run** |
| DEC-085 | Untouched |
| Label | **light validated** (Docker column probe + alembic check counts + ORM KEEP guard) |

**Production GO not claimed. CI GREEN not met. Criterion 7.6 not CLOSED.**

---

## 5. Records

- Phase 0 criterion **7.6** → **OPEN** (phased; Slice 5e COMPLETE / READY FOR REVIEW)
- Board DB-05 → Slice 5e COMPLETE; residual = 7.6 clean check (5f+ orphan KEEP / vectors cols)
- `DECISION_LOG.md` DEC-130e
- R-20 next-action → Slice **5f+** orphan KEEP / vectors residual
- **Not claimed:** Production GO · CI GREEN · `alembic check` clean · 7.6 VERIFIED/CLOSED

---

## 6. Architecture next?

Architecture Reviewer: confirm (1) KEEP disposition for live `do_not_contact` + `embedding_vector` matches DEC-129 pattern (no DROP), (2) ORM-only restore with head pin `a4f7c29e1b80` unchanged is correct (columns already live), (3) `_PgVector` compare-against-backend stand-in is acceptable metadata hygiene without adding pgvector dependency, (4) residual `vectors.*` remove_column + orphan KEEP tables remain for **5f+**. Validation: corroborate `remove_column` **4→2** + companies pair absent + FAILED check — do **not** treat as 7.6 close evidence.
