# DEC-102 — CI-19 Wave 2 Slice 5 COMPLETE: activity_runtime + kg + memory Core honesty

> **Status:** **Accepted**  
> **Date:** 2026-08-01  
> **Story:** CI-19 — Semgrep findings remediation (Wave 2 SQL honesty)  
> **Prior:** Wave 2 Slice 4 COMPLETE (DEC-101 / land `9ab3516`)  
> **Validation label:** **light validated** (narrow pytest **58 passed** — DEC-085 guard + `test_postgres_memory` + `knowledge_graph_runtime/tests`) — **not** whole-pipeline CI GREEN  
> **DEC-085:** `get_db()` untouched — still `SELECT set_config('app.tenant_id', :tenant_id, true)`  
> **Conflict note:** Parallel Backend Unit pytest-fix agent owns Wave2/bind/RLS/ER / activity_intelligence / company service clusters. This slice does **not** touch those files.

---

## Decision

Accept **CI-19 Wave 2 Slice 5** as **COMPLETE**. Eliminate `sqlalchemy.text` on densest non-alembic remainder after Slice 4:

| File | Approach | Expected alerts cleared |
|---|---|---|
| `runtime/activity_runtime/__init__.py` | Allowlisted Core `Table` + `insert` / filter `and_` / stats aggregates | **3** |
| `runtime/knowledge_graph_runtime/repository/sql_repository.py` | Core `Table` + joins / `pg_insert` ON CONFLICT / `update`+`exists` merge | (local density; next SARIF) |
| `runtime/knowledge_graph_runtime/service.py` | Core selects; f-string dynamic `OR` → typed `or_(*conds)` | **2** |
| `intelligence/memory/postgres_store.py` | Core `pg_insert` / filter `and_` / `delete` / TTL `make_interval` | **2** |

**Expected clear this slice (CS densest non-stale inventory):** **7** `avoid-sqlalchemy-text` Code Scanning alerts.

**Alembic RLS migrations:** intentionally **not** touched (residual package / Slice 6 decision — churn risks DEC-085 / RLS).

**Do not** mark CI-19 CLOSED. **Do not** weaken Semgrep ERROR/WARNING gates or SARIF upload. **Do not** use `nosemgrep` / severity drop.

---

## Evidence

- Narrow pytest (`docker compose exec backend`): `tests/unit/test_dec085_set_config_guard.py` + `tests/unit/intelligence/memory/test_postgres_memory.py` + `runtime/knowledge_graph_runtime/tests.py` → **58 passed**
- `app/database.py` `get_db()` still uses `set_config` for tenant GUC (DEC-085 hard stop intact)
- No `SET LOCAL app.tenant_id` reintroduced

---

## Remainder (Slice 6 / residual)

~**11** after Slice 4+5 (prior ~18 − 7), excluding stale Slice 4 SARIF lag: alembic RLS (**7** — residual / out-of-scope for app honesty), `database.py` init_db DDL (**1**), benchmark (**2**), mcp_server (**1**). Optional: other runtime `text()` if field Semgrep resurfaces (nba/feature_store/pipeline_analytics/etc.).

**Wave 2 NOT CLOSED.** **CI-19 NOT CLOSED.**

---

## Honesty

- Does **not** claim whole-pipeline **CI GREEN**.
- Does **not** claim Production GO or External pilot.
- Does **not** modify `app/database.py` / tenant GUC path.
- Does **not** claim Backend Unit field green (parallel pytest-fix agent owns prior Wave 2 fallout).
