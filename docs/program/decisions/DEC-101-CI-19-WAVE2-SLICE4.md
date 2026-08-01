# DEC-101 — CI-19 Wave 2 Slice 4 COMPLETE: search_runtime + vector/search/tasks Core honesty

> **Status:** **Accepted**  
> **Date:** 2026-08-01  
> **Story:** CI-19 — Semgrep findings remediation (Wave 2 SQL honesty)  
> **Prior:** Wave 2 Slice 3 COMPLETE (DEC-099 / land `1f53dce`)  
> **Validation label:** **light validated** (narrow pytest **14 passed** — `test_search_runtime` + DEC-085 guard) — **not** whole-pipeline CI GREEN  
> **DEC-085:** `get_db()` untouched — still `SELECT set_config('app.tenant_id', :tenant_id, true)`  
> **Note:** DEC-100 reserved by CI-14 Jest STOP — this slice is **DEC-101**.  
> **Conflict note:** Parallel agent remediating Backend Unit ~85 pytest failures from earlier Wave 2 Core (to_jsonb / timeline CM). This slice does **not** touch outbox/timeline; no file overlap.

---

## Decision

Accept **CI-19 Wave 2 Slice 4** as **COMPLETE**. Eliminate `sqlalchemy.text` on the densest remainder after Slice 3:

| File | Approach | Expected alerts cleared |
|---|---|---|
| `runtime/search_runtime/__init__.py` | Core FTS (`plainto_tsquery`/`ts_rank`/`@@`); allowlisted filters/facets/suggest; pgvector `<->`; timeout via `set_config` | **4** |
| `sdk/search.py` | Allowlisted Core `Table` + `<=>` / `pg_insert` / `delete` | **3** |
| `domains/search/engine/vector_store.py` | Allowlisted Core `Table` + `<=>` / `pg_insert` / `delete` / `count` | **3** |
| `app/tasks.py` | Allowlisted Core `select`/`update` for companies/contacts helpers | **3** |
| `app/modules/contact/search_repository.py` | `set_config` timeout + Core `order_by(cnt.desc())` | **1** |

**Also cleared locally (not in prior CS densest list):** `runtime/admin_router.py` metrics/health counts → Core `select(func.count())` / `select(literal(1))`.

**Expected clear this slice (CS densest inventory):** **14** `avoid-sqlalchemy-text` Code Scanning alerts.

**Do not** mark CI-19 CLOSED. **Do not** weaken Semgrep ERROR/WARNING gates or SARIF upload. **Do not** use `nosemgrep` / severity drop.

---

## Evidence

- Narrow pytest (fresh `docker compose run --no-deps`): `tests/unit/test_search_runtime.py` + `tests/unit/test_dec085_set_config_guard.py` → **14 passed**
- `app/database.py` `get_db()` still uses `set_config` for tenant GUC (DEC-085 hard stop intact)
- Search / contact statement timeout uses `func.set_config("statement_timeout", …, True)` — not `SET LOCAL`

---

## Remainder (not this slice)

~**18** `avoid-sqlalchemy-text` after Slice 1–4 (prior ~32 − 14): alembic RLS/tenant migrations, `activity_runtime`, kg `service`/`sql_repository`, integration-test helpers, `database.py` non-GUC DDL paths (leave `get_db` alone), etc. + non-SQL residuals.

**Wave 2 NOT CLOSED.** **CI-19 NOT CLOSED.**

---

## Honesty

- Does **not** claim whole-pipeline **CI GREEN**.
- Does **not** claim Production GO or External pilot.
- Does **not** modify `app/database.py` / tenant GUC path.
- Does **not** claim Backend Unit field green (parallel pytest-fix agent owns prior Wave 2 fallout).
