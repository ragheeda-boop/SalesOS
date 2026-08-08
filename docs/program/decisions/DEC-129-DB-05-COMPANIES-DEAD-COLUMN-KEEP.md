# DEC-129 — DB-05 companies dead-column DROP disposition (Phase 0 criterion 7.4)

> **Status:** **Accepted** — Cursor implementation **COMPLETE** · Criterion 7.4 = **VERIFIED/CLOSED** (DEC-129a; Architecture PASS · Validation PASS @ `4aacd6d`).  
> **Date:** 2026-08-01  
> **Board:** Backend Platform / Database (SalesOS)  
> **Story / risk:** DB-05 / R-20 / Phase 0 Exit Criterion **7.4**  
> **Authority:** DEC-122 STOP · DEC-111 P1 companies cluster · DEC-085 `set_config` · DEC-107 swarm READY · DEC-129a Orchestrator  
> **Out of scope this land:** DROP any companies column · full `alembic check` (7.6) · production / Railway migrate · Prisma · DEC-085 edits · Production GO / CI GREEN

---

## 1. Decision

**KEEP** the companies columns DEC-122 refused to DROP. They are **not dead**. Record the disposition and restore them on the `Company` ORM so autogenerate cannot propose DROP again.

| Pin | Value |
|---|---|
| Disposition | **KEEP** (no DROP migration this phase) |
| Alembic head | **unchanged** — `d1a8c35e7f09` (no new revision) |
| FTS authority | `search_vector` remains **GENERATED ALWAYS AS … STORED** (Alembic 0023); `tsv` remains trigger-backed (0006/0025) |
| DEC-085 | **Intact** |
| Criterion state | **VERIFIED/CLOSED** (DEC-129a) |

### Column disposition (Docker `information_schema` @ local compose)

| Column | Live DB | Runtime use | Action |
|---|---|---|---|
| `search_vector` | tsvector **GENERATED ALWAYS** | `search_runtime`, `domains/search` FTS `@@` / `ts_rank` | **KEEP** + ORM `Computed(persisted=True)` |
| `tsv` | tsvector + GIN `ix_companies_tsv` | Trigger refresh (0025); backward-compat FTS | **KEEP** + ORM + GIN index |
| `parent_company_id` | uuid FK | `company/service.py`, `feature_store` subsidiary SQL | **KEEP** + ORM FK |
| `branch_count` | int default 0 | `feature_store` scoring | **KEEP** + ORM |
| `revenue_prev_year` | float | `feature_store` / `context_runtime` growth | **KEEP** + ORM |
| `annual_revenue`, `revenue_2yr_ago`, `employee_count_prev_year`, `linkedin_url`, `country` | present (0002) | feature-store / enrichment dict paths | **KEEP** + ORM (same cluster) |

### Alternatives considered

| Option | Result |
|---|---|
| (a) DROP “dead” columns this land | **Rejected** — `search_vector` is live FTS; `parent_company_id` / feature columns still referenced; local row counts ≠ prod safety |
| (b) Docs-only KEEP without ORM restore | **Rejected** — leaves autogenerate DROP noise; reopens accidental DROP risk |
| (c) KEEP + restore ORM columns (no DDL) | **Approved** |

---

## 2. Validation

| Check | Result |
|---|---|
| Docker live column inventory | PASS — all KEEP columns present; `search_vector.is_generated=ALWAYS` |
| Narrow unit tests | Docker `pytest tests/unit/test_dec129_companies_keep_columns.py tests/unit/test_dec085_set_config_guard.py` (see land commit) |
| New Alembic revision | **None** |
| Production / Railway migrate | **Not run** |
| Full `alembic check` | **Out of scope** (criterion **7.6**) |
| Label | **build validated** (narrow Docker pytest + live column probe) |

**Production GO not claimed. CI GREEN not met. R-14 GO not claimed.**

---

## 3. Records

- Phase 0 criterion **7.4** → **VERIFIED/CLOSED** (DEC-129a; Phase 0 **24/54**).
- DB-05 residual after this land = **7.6** `alembic check` (companies KEEP cluster mitigated; systemic drift remains).
- `DECISION_LOG.md` DEC-129 / DEC-129a
- **Not claimed:** Production GO · CI GREEN · `alembic check` clean

---

## 4. Evidence Package

| ID | Artifact | Location / command |
|----|----------|-------------------|
| EV-001 | Live column probe | Docker `information_schema.columns` for KEEP set |
| EV-002 | Index probe | `idx_companies_search_vector` (GIN), `ix_companies_tsv` (GIN), `ix_companies_parent_company_id` |
| EV-003 | ORM restore | `app/modules/company/models.py` (DEC-129 KEEP columns) |
| EV-004 | Unit guard | `tests/unit/test_dec129_companies_keep_columns.py` |
| EV-005 | DEC-085 intact | `tests/unit/test_dec085_set_config_guard.py` (run with land) |
| EV-006 | Screenshots | N/A (backend schema/docs) |

---

## 5. Rollback

| Step | Action |
|------|--------|
| 1 | Revert ORM columns + unit guard from land commit |
| 2 | Revert program docs (checklist / board / DEC-129) |
| Expected impact | Autogenerate may again propose DROP of live FTS/feature columns; FTS runtime unchanged (DDL never altered) |

---

## 6. Risk

| Surface | Level | Note |
|---------|-------|------|
| Database | LOW | No DDL; KEEP only |
| Search / FTS | LOW | Preserves generated `search_vector` |
| Auth / RLS / DEC-085 | NONE | Untouched |
| Residual | MED | Full ORM↔DB clean remains **7.6** |
