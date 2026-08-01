# DEC-103 — CI-19 Wave 2 Slice 6 COMPLETE: residual package (app clear + alembic RLS accepted)

> **Status:** **Accepted**  
> **Date:** 2026-08-01  
> **Story:** CI-19 — Semgrep findings remediation (Wave 2 SQL honesty)  
> **Prior:** Wave 2 Slice 5 COMPLETE (DEC-102 / land `179a477` + crumb `460d0a7`)  
> **Land SHA:** `3d49ae1` (`3d49ae1`)  
> **Validation label:** **light validated** (narrow pytest DEC-085 guard **2 passed**; AST/import of touched modules; py_compile) — **not** whole-pipeline CI GREEN  
> **DEC-085:** `get_db()` **untouched** — still `SELECT set_config('app.tenant_id', :tenant_id, true)` (init_db DDL only changed)  
> **Conflict note:** Parallel pytest-fix may own company/entity_resolution/workflow/activity_intelligence — this slice does **not** touch those paths.

---

## Decision

Accept **CI-19 Wave 2 Slice 6** as **COMPLETE** and formalize the **Wave 2 residual package**.

### In-scope app / runtime fixes (expected clear **4** live CS `avoid-sqlalchemy-text`)

| File | Approach | Expected alerts |
|---|---|---|
| `app/database.py` `init_db` | Allowlisted `exec_driver_sql` for `CREATE EXTENSION` / `CREATE SCHEMA`; Core `select` for `alembic_version` | **1** (#513) |
| `benchmark/run.py` | Fixed PG/SQLite DDL constants + `exec_driver_sql`; Core `count` | **1** (#523) |
| `benchmark/runner.py` | Allowlisted SQL via `exec_driver_sql` (named→positional binds); no `sqlalchemy.text` | **1** (#524) |
| `mcp_server/salesos_client.py` | Core aggregate for market intelligence (removes f-string `text`) | **1** (#542) |

**Also cleared locally (not required by CS densest list):** `mcp_server/resources.py` search_log Core; `benchmark/data_generator.py` Core `insert`; mcp decision-history Core over `CompanyFeatureModel`.

### Alembic residual package — **ACCEPTED** (do not churn)

| Path | Live CS (approx) | Disposition |
|---|---|---|
| `0afbf3e6ae53_enable_rls_all_tenant_tables.py` | **4** `avoid-sqlalchemy-text` | **Accepted residual** — RLS policy DDL; rewrite churn risks DEC-085 / tenant isolation |
| `065d1d3a466b_enable_rls_company_features.py` | **3** `avoid-sqlalchemy-text` | **Accepted residual** — same RLS class |
| `0020_add_tenant_id.py` | **4** raw/formatted SQL (not `avoid-sqlalchemy-text`) | **Accepted residual** — historical tenant migration; out of Wave 2 app honesty |

**Rationale:** Zero-risk Core rewrite of historical Alembic RLS/tenant DDL is not available without replaying policy SQL. Prior slices already established `exec_driver_sql` for **new** allowlisted DDL; rewriting shipped RLS migrations is **out of scope** for Semgrep clearance and risks R-14 / DEC-085 regressions.

**Do not** mark CI-19 CLOSED on this land alone — leave **OPEN** until Security Scan / Code Scanning field-verify shows in-scope app `avoid-sqlalchemy-text` at **0** (alembic residual only), or an executive residual-close DEC. **Do not** weaken Semgrep ERROR/WARNING gates or SARIF upload. **Do not** use `nosemgrep` / severity drop. **Do not** churn alembic RLS migrations in Slice 7 for Semgrep cosmetics.

---

## Wave 2 status

| Slice | DEC | Scope | Status |
|---|---|---|---|
| 1 | DEC-091 | outbox / revenue / audit | COMPLETE |
| 2 | DEC-097 | data_quality / pgvector_migration | COMPLETE |
| 3 | DEC-099 | postgres_repo / timeline | COMPLETE |
| 4 | DEC-101 | search_runtime / vector / tasks | COMPLETE |
| 5 | DEC-102 | activity_runtime / kg / memory | COMPLETE |
| 6 | **DEC-103** | init_db + benchmark + mcp + **alembic residual accept** | **COMPLETE** |

**Wave 2 app-honesty track: COMPLETE** (remaining SQL Semgrep = documented alembic residual only).  
**CI-19 story: still OPEN** pending residual field-verify / executive park. **No Slice 7 required** for in-scope app text unless field Semgrep resurfaces non-alembic findings.

---

## Evidence

- Narrow pytest (`docker compose exec backend`): `tests/unit/test_dec085_set_config_guard.py` → **2 passed**
- `get_db()` body unchanged (DEC-085 hard stop intact); only `init_db` / `_run_migrations_if_needed` DDL/head-check paths changed
- py_compile + `SalesOSClient` import OK on touched modules
- **Field-verify (2026-08-01):** Security Scan run [`30686789458`](https://github.com/ragheeda-boop/SalesOS/actions/runs/30686789458) @ tip `abaae85` (`abaae852b45719bbefb59350c72f86a5ca3130fc`; includes land `3d49ae1`) — workflow **SUCCESS**; `sast-scan` job `91334080531` **SUCCESS**. Live Code Scanning: app `avoid-sqlalchemy-text` **0** (alerts #513/#523/#524/#542 **fixed** at `2026-08-01T05:58:15Z`); alembic residual **7** + `0020` raw/formatted **4**. Validation label upgraded for Wave 2 park: **build validated** (field CS). Semgrep CLI total on tip = **19** blocking (includes non-Wave-2 rules) — **not** whole-pipeline / finding-zero GREEN.

---

## Residual package summary (program board)

**Cleared this slice (app):** **4** (field-confirmed fixed)  
**Remaining accepted residual (alembic):** **7** `avoid-sqlalchemy-text` (RLS) + **4** raw/formatted on `0020`  
**Wave 2:** **PARKED COMPLETE** (app-complete with alembic residual; field-verified)  
**CI-19:** OPEN (not falsely closed — executive residual-close still required)  
**CI GREEN:** not met  
**Slice 7:** **not required** (field Semgrep residual-only)

---

## Honesty

- Does **not** claim whole-pipeline **CI GREEN**.
- Does **not** claim Production GO or External pilot.
- Does **not** modify `get_db()` tenant GUC path.
- Does **not** claim Backend Unit field green (parallel pytest-fix agent).
- Live Code Scanning may still show Slice 5 paths until SARIF catches tip — expected lag, not a reopen of Slice 5.
