# DEC-096 — CI-20 Backend Types (MyPy) CLOSED

> **Status:** **Accepted**  
> **Date:** 2026-08-01  
> **Story:** CI-20 — Backend Types remediation (DEC-038 → Phases 1–21)  
> **Close SHA:** `220d91a` (`220d91aeeb4eafc07174b62e7468b98fbf1002c2`)  
> **Field evidence:** CI run `30684023356` — Stage 2 Backend Types job `91326366120` **SUCCESS** — mypy error count **0**  
> **Tip corroboration:** `af4835f` — CI run `30684308678` — Backend Types job `91327119501` **SUCCESS** (also `844548e` `30684181874` / `91326794076`)  
> **Validation label:** **build validated** (field CI Backend Types) — **not** whole-pipeline CI GREEN

---

## Decision

Close **CI-20**. Stage 2 Backend Types is field-verified **0** errors on the close SHA and on later tip.

| Evidence | Result |
|---|---|
| Baseline (DEC-038) | Run `30670339985` — **308** mypy errors |
| Phase 21 (DEC-092) | `17c1eee` — host CI-equivalent **0**; field pending at that DEC |
| Syntax residual | `5588bb7` — `pg_repositories.list_transactions` `Expected ':'` |
| DEC-093 import residual | `a636c69` — audit routers → `get_owner_scoped_tenant_id` (field **1** left: `domain_events`) |
| Final residual clear | `220d91a` — `EVENT_REGISTRY` uses `getattr(cls, "event_type")` |
| Field verify close SHA | Run `30684023356` / job `91326366120` — Backend Types **SUCCESS** / **0** `error:` lines |
| Tip corroboration | `af4835f` run `30684308678` / job `91327119501` — Backend Types **SUCCESS** |
| DEC-085 `get_db()` | Still `SELECT set_config('app.tenant_id', :tenant_id, true)` on tip — **not** `SET LOCAL` |

**Story status:** **CLOSED**.

---

## Honesty

- Closes the **Backend Types** gate story only.
- Does **not** claim whole-pipeline **CI GREEN** (Backend Lint / Secrets Scan / other Stage 5 / Deploy paths may still fail on the same run).
- Does **not** claim Production GO or External pilot.
- Does **not** weaken DEC-085 (`set_config` only for tenant GUC).
