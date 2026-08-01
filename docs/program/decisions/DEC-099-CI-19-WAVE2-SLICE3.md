# DEC-099 — CI-19 Wave 2 Slice 3 COMPLETE: postgres_repo + timeline_runtime Core honesty

> **Status:** **Accepted**  
> **Date:** 2026-08-01  
> **Story:** CI-19 — Semgrep findings remediation (Wave 2 SQL honesty)  
> **Prior:** Wave 2 Slice 2 COMPLETE (DEC-097 / land `5686d4d`)  
> **Validation label:** **light validated** (narrow pytest **50 passed**) — **not** whole-pipeline CI GREEN  
> **DEC-085:** `get_db()` untouched — still `SELECT set_config('app.tenant_id', :tenant_id, true)`  
> **Note:** DEC-098 number reserved by parallel Trivy ecdsa named-ignore work — this slice is **DEC-099**.

---

## Decision

Accept **CI-19 Wave 2 Slice 3** as **COMPLETE**. Eliminate `sqlalchemy.text` on the next densest pair after Slice 2:

| File | Approach | Expected alerts cleared |
|---|---|---|
| `domains/search/engine/postgres_repo.py` | Core FTS (`plainto_tsquery`/`ts_rank`/`@@`); allowlisted filters/facets/suggest; timeout via `set_config` (not `SET LOCAL`) | **6** |
| `runtime/timeline_runtime/__init__.py` | Core `insert`/`select` over `TimelineEventModel` | **5** |

**Expected clear this slice:** **11** `avoid-sqlalchemy-text` Code Scanning alerts.

**Do not** mark CI-19 CLOSED. **Do not** weaken Semgrep ERROR/WARNING gates or SARIF upload. **Do not** use `nosemgrep` / severity drop.

---

## Evidence

- Narrow pytest: `domains/search/tests/test_search_postgres_repo.py` + `domains/timeline/tests/test_timeline.py` + `tests/unit/test_dec085_set_config_guard.py` → **50 passed**
- `app/database.py` `get_db()` still uses `set_config` for tenant GUC (DEC-085 hard stop intact)
- Search statement timeout uses `func.set_config("statement_timeout", …, True)` — not `SET LOCAL`

---

## Remainder (not this slice)

~**32** `avoid-sqlalchemy-text` after Slice 1+2+3 (prior ~43 − 11): densest next — `search_runtime` (4), alembic RLS/tenant migrations, `sdk/search.py`, `tasks.py`, etc. + non-SQL residuals.

**Wave 2 NOT CLOSED.** **CI-19 NOT CLOSED.**

---

## Honesty

- Does **not** claim whole-pipeline **CI GREEN**.
- Does **not** claim Production GO or External pilot.
- Does **not** modify `app/database.py` / tenant GUC path.
