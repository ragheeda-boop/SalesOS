# DEC-130 — DB-05 criterion 7.6: live `alembic check` re-baseline + phased plan

> **Status:** **Accepted** — Slice **5a** COMPLETE · Slice **5b** COMPLETE ([DEC-130b](DEC-130b-DB-05-SLICE-5B-METADATA-CLASSIFY.md)) · Slice **5c** COMPLETE ([DEC-130c](DEC-130c-DB-05-SLICE-5C-ADMIN-GLOBAL-CREATE.md) READY FOR REVIEW) · Criterion **7.6 remains OPEN** (clean check **not** met) · do **not** CLOSE 7.6  
> **Date:** 2026-08-01  
> **Board:** Backend Platform / Database (SalesOS / AQLIYA)  
> **Story / risk:** DB-05 / R-20 / Phase 0 Exit Criterion **7.6**  
> **Authority:** DEC-111 Slice 0 · DEC-113–123 · DEC-129 KEEP · DEC-085 `set_config` · DEC-107 swarm READY  
> **Out of scope this land:** Full `alembic check` clean · DROP companies / orphan tables · production / Railway migrate · Prisma · DEC-085 edits · Production GO / CI GREEN · Criterion VERIFIED/CLOSED

---

## 1. Decision

**Honest path:** criterion **7.6 cannot close in one Cursor COMPLETE package**. Ship **Slice 5a** = live Docker `alembic check` re-baseline + multi-slice reconciliation plan. Keep 7.6 **OPEN**. Prefer additive migrations; **7.4 KEEP stands** (no reckless DROPs).

| Pin | Value |
|---|---|
| Alembic head (local compose) | **`d1a8c35e7f09`** (single head; unchanged this land) |
| `alembic check` | **FAILED** (exit **255**) — not clean |
| Historic CI-15 claim | “~300 drift lines” — **superseded by live counts below** |
| Base.metadata size | **70** tables registered via `app/database.py` import side-effects |
| DEC-085 | **Intact** (not touched) |
| Criterion 7.6 | **OPEN** — phased residual |

### Alternatives considered

| Option | Result |
|---|---|
| (a) Claim 7.6 CLOSED / `alembic check` clean | **Rejected** — live check FAILED |
| (b) Autogenerate one mega-migration to clear all ops | **Rejected** — includes `remove_table`×28 + `remove_column` (destructive; false positives from metadata gaps) |
| (c) Slice 5a live re-baseline + phased plan only | **Approved** — only honest Cursor COMPLETE package |

---

## 2. Live evidence (Docker compose, 2026-08-01)

**Commands (local non-prod):**

```text
docker compose exec -T backend alembic current   → d1a8c35e7f09 (head)
docker compose exec -T backend alembic heads     → d1a8c35e7f09 (head)
docker compose exec -T backend alembic check     → FAILED exit 255
```

**Detected summary (INFO lines + FAILED op blob):**

| Class | Approx count | Notes |
|---|---:|---|
| `Detected added table` | **3** | `admin_plans`, `admin_feature_flags`, `admin_health_snapshots` (ORM present; **no** CREATE in DB — DEC-111 P2 global admin) |
| `Detected removed table` | **28** | Mix of **metadata-not-registered** (e.g. `company_features`, `decision_center_*`, `scoring_scorecards`, `revenue_analytics_snapshots`) and **CREATE-without-ORM / legacy** (intent, rag, graph, marketplace, …) — **do not DROP** without dedicated DEC |
| `Detected removed index` | **~100** | Naming / composite vs single-column residual (contacts, commercial, companies trgm, …) |
| `Detected added index` | **~37** | ORM wants indexes DB lacks (or rename twins) |
| Type changes | **4** | e.g. `api_keys.permissions` JSONB↔JSON; `audit_logs.id` BIGINT↔Integer; `contacts.name`/`name_ar` length |
| `Detected removed column` | **2** | `companies.do_not_contact`, `companies.embedding_vector` — **KEEP-adjacent**; extend DEC-129 pattern (no DROP this phase) |
| `modify_nullable` (FAILED blob) | **~27** | workflow / notifications / scheduled_jobs / feature_* — DEC-122 deferred (needs prod null inventory) |
| Raw check log lines | **~1083** | Captured locally as `.tmp-alembic-check-7-6.txt` (not committed) |

**Root cause (primary):** `app/alembic/env.py` uses `Base.metadata` from `app/database.py`, which registers a **partial** model set (~70). Tables that exist in Postgres but are absent from that metadata show as `remove_table` — **autogenerate false DROP proposals**, not proof the tables are dead.

---

## 3. Phased plan (subsequent lands; not this land)

| Slice | Scope | Exit for that slice | Closes 7.6? |
|---|---|---|---|
| **5a** | *(this DEC)* Live re-baseline + plan | Evidence pinned; 7.6 stays OPEN | **No** |
| **5b** | Metadata completeness — classify 28 `remove_table`; register FPs ([DEC-130b](DEC-130b-DB-05-SLICE-5B-METADATA-CLASSIFY.md)) | `remove_table` **28 → 15**; **no DROP** | **No** (COMPLETE / READY FOR REVIEW) |
| **5c** | Additive **CREATE** for global admin trio (`admin_plans`, `admin_feature_flags`, `admin_health_snapshots`) — no RLS ([DEC-130c](DEC-130c-DB-05-SLICE-5C-ADMIN-GLOBAL-CREATE.md)) | `add_table` **3 → 0** | **No** (COMPLETE / READY FOR REVIEW) |
| **5d** | Index / type / nullable residual batches (additive rename/create only; SET NOT NULL only with null inventory) | Index/type/null noise ↓ | **No** |
| **5e** | Companies residual columns (`do_not_contact`, `embedding_vector`) — KEEP + ORM or explicit DROP DEC | Column DROP proposals gone | **No** |
| **5f+** | Remaining orphan/legacy table policy + final `alembic check` | **exit 0** | **Yes** (only then) |

**Hard stops (all slices):** no production migrate · no Prisma · no DEC-085 edits · no DROP of FTS/KEEP columns (7.4) · no blind DROP of the 28 “removed” tables.

---

## 4. Validation

| Check | Result |
|---|---|
| Docker `alembic current` / `heads` | `d1a8c35e7f09` |
| Docker `alembic check` | **FAILED** (exit 255) — expected |
| New Alembic revision | **None** |
| Production / Railway migrate | **Not run** |
| DEC-085 | Untouched |
| Label | **light validated** (Docker alembic check + metadata count) |

**Production GO not claimed. CI GREEN not met. Criterion 7.6 not CLOSED.**

---

## 5. Records

- Phase 0 criterion **7.6** → **OPEN** (phased; Slice 5a COMPLETE) — checklist evidence refreshed from live check  
- Board DB-05 → Slice 5a COMPLETE; residual = 7.6 clean check  
- `DECISION_LOG.md` DEC-130  
- R-20 next-action → Slice 5b metadata / classify remove_table  
- **Not claimed:** Production GO · CI GREEN · `alembic check` clean · 7.6 VERIFIED/CLOSED

---

## 6. Architecture next?

Architecture Reviewer: confirm (1) phased plan is the honest path vs mega-migration, (2) KEEP / no-DROP stance for false `remove_table` + companies residual columns, (3) Slice 5b metadata registration is safe scope for next Backend land. Validation: corroborate Docker check FAILED + head pin only — do **not** treat this DEC as 7.6 close evidence.
