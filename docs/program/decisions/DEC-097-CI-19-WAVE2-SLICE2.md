# DEC-097 — CI-19 Wave 2 Slice 2 COMPLETE: data_quality + pgvector_migration Core honesty

> **Status:** **Accepted**  
> **Date:** 2026-08-01  
> **Story:** CI-19 — Semgrep findings remediation (Wave 2 SQL honesty)  
> **Land SHA:** `5686d4d` (`5686d4d4b76829affa36ec80d36665b0b00baa8d`) — note: commit subject was mislabeled as DEC-094 SHA record; payload is Wave 2 Slice 2 + this DEC  
> **Prior:** Wave 2 Slice 1 COMPLETE (decision-log id DEC-091 / lands `844548e` + `5fb7dc5`)  
> **Validation label:** **light validated** (AST parse of rewritten modules) — **not** whole-pipeline CI GREEN  
> **DEC-085:** `get_db()` untouched — still `SELECT set_config('app.tenant_id', :tenant_id, true)`

---

## Decision

Accept **CI-19 Wave 2 Slice 2** as **COMPLETE**. Eliminate `sqlalchemy.text` on the next densest pair after Slice 1:

| File | Approach | Expected alerts cleared |
|---|---|---|
| `app/application/admin/data_quality.py` | SQLAlchemy Core (`Table`/`select`/`case`/`func`) over allowlisted `companies` columns | **8** |
| `runtime/knowledge_graph_runtime/pgvector_migration.py` | Core for `information_schema` + allowlisted DDL via `exec_driver_sql` (ident allowlist) | **8** |

**Expected clear this slice:** **16** `avoid-sqlalchemy-text` Code Scanning alerts.

**Out of this slice (still OPEN):** `domains/search/engine/postgres_repo.py`, `timeline_runtime`, `search_runtime`, alembic RLS/tenant migrations, etc.

**Do not** mark CI-19 CLOSED. **Do not** weaken Semgrep ERROR/WARNING gates or SARIF upload. **Do not** use `nosemgrep` / severity drop.

---

## Remainder (not this slice)

~**43** `avoid-sqlalchemy-text` after Slice 1+2 (prior ~59 − 16): densest next — `domains/search/engine/postgres_repo.py` (6), `timeline_runtime` (5), `search_runtime` (4), alembic RLS/tenant migrations, `sdk/search.py`, `tasks.py`, etc. + non-SQL residuals.

**Wave 2 NOT CLOSED.** **CI-19 NOT CLOSED.**

---

## Honesty

- Does **not** claim whole-pipeline **CI GREEN**.
- Does **not** claim Production GO or External pilot.
- Does **not** modify `app/database.py` / tenant GUC path.
- Backend Lint remains a separate residual (lint agent in flight on tip).
- Earlier draft board text claiming Slice 2 covered postgres_repo/timeline (**27**) was **incorrect** and is corrected here to **16**.
