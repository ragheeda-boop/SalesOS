# DEC-130 — DB-05 criterion 7.6: live `alembic check` re-baseline + phased plan

> **Status:** **Accepted** — Slice **5a** COMPLETE · Slice **5b** COMPLETE ([DEC-130b](DEC-130b-DB-05-SLICE-5B-METADATA-CLASSIFY.md)) · Slice **5c** COMPLETE ([DEC-130c](DEC-130c-DB-05-SLICE-5C-ADMIN-GLOBAL-CREATE.md)) · Slice **5d** COMPLETE ([DEC-130d](DEC-130d-DB-05-SLICE-5D-INDEX-TYPE-NULLABLE.md)) · Slice **5e** COMPLETE ([DEC-130e](DEC-130e-DB-05-SLICE-5E-COMPANIES-RESIDUAL-KEEP.md)) · Slice **5f** COMPLETE ([DEC-130f](DEC-130f-DB-05-SLICE-5F-ORPHAN-KEEP-REGISTER.md)) · Slice **5g** COMPLETE ([DEC-130g](DEC-130g-DB-05-SLICE-5G-INDEX-FK-COMMENT.md) — live `alembic check` **exit 0**) · Criterion **7.6 VERIFIED/CLOSED** via [DEC-130h](../DECISION_LOG.md) (Arch+Val PASS @ `250bcb5`)  
> **Date:** 2026-08-01  
> **Board:** Backend Platform / Database (SalesOS)  
> **Story / risk:** DB-05 / R-20 / Phase 0 Exit Criterion **7.6**  
> **Authority:** DEC-111 Slice 0 · DEC-113–123 · DEC-129 KEEP · DEC-085 `set_config` · DEC-107 swarm READY  
> **Out of scope this land:** production / Railway migrate · Prisma · DEC-085 edits · Production GO / CI GREEN

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
| Criterion 7.6 | **CLOSED** (DEC-130h) — phased residual cleared |

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
| **5d** | Index / type / nullable residual batches (additive rename/create only; SET NOT NULL only with null inventory) ([DEC-130d](DEC-130d-DB-05-SLICE-5D-INDEX-TYPE-NULLABLE.md)) | `added_index` **37 → 0**; type **13 → 1**; NOT NULL **33 → 0** | **No** (COMPLETE / READY FOR REVIEW) |
| **5e** | Companies residual columns (`do_not_contact`, `embedding_vector`) — KEEP + ORM or explicit DROP DEC | Column DROP proposals gone | **No** |
| **5f** | Orphan KEEP metadata register + vectors residual columns ([DEC-130f](DEC-130f-DB-05-SLICE-5F-ORPHAN-KEEP-REGISTER.md)) | `remove_table` **15 → 0**; `remove_column` **2 → 0** | **No** |
| **5g** | Residual index/FK/comment/type metadata + twin KEEP + expression `include_object` ([DEC-130g](DEC-130g-DB-05-SLICE-5G-INDEX-FK-COMMENT.md)) | **`alembic check` exit 0** | **Yes** (after Arch+Val + Orchestrator CLOSE) |

**Slice 5f landed (DEC-130f):** orphan KEEP metadata register — `remove_table` **15→0**; vectors residual columns — `remove_column` **2→0**; check still FAILED; next **5g**.

**Slice 5g landed (DEC-130g):** residual index/FK/comment/type metadata register + rename-twin KEEP + `include_object` KEEP for `ix_graph_nodes_search` — live Docker `alembic check` **exit 0**; head unchanged `a4f7c29e1b80`.

**Orchestrator CLOSE (DEC-130h):** Arch PASS + Validation PASS @ `250bcb5` → criterion **7.6 VERIFIED/CLOSED**; Phase 0 **25/54**; DB Schema **6/6**. Residual KEEP `ix_graph_nodes_search` non-blocking. **Production GO not claimed. CI GREEN not met.**

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

**Production GO not claimed. CI GREEN not met. Criterion 7.6 CLOSED via DEC-130h.**

---

## 5. Records

- Phase 0 criterion **7.6** → **VERIFIED/CLOSED** (DEC-130h; Slices 5a–5g)  
- Board DB-05 → **COMPLETE**; residual KEEP documented  
- `DECISION_LOG.md` DEC-130…DEC-130h  
- R-20 → **Closed — mitigating residual KEEP**  
- **Not claimed:** Production GO · CI GREEN

---

## 6. Architecture next?

Closed path complete. Residual `ix_graph_nodes_search` KEEP stands until a dedicated DROP+CREATE DEC (not required for 7.6). Swarm: next PARALLEL READY = ADR Drift / Capability Drift / EOS / contract tests — do **not** claim Phase 0 GO.
