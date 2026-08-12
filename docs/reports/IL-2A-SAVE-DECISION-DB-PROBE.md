# IL-2A — live DB probe: `_save_decision` hang (2026-08-12)

**Scope:** Railway `responsible-comfort` / production · API commit under probe `03ca3da` · tenant `326e0825-…172b`  
**Fix (sister):** `69c6e835` — JSONB binds were raw `list`/`dict` (asyncpg `DataError` → ~30s stall).  
**This note:** corroborating read-only Postgres evidence only. No secrets. No redeploy.

## Verdict (matches fix)

Hang was **not** RLS, locks, or idle-in-transaction. It was **asyncpg bind typing** on `evidence` / `supporting_features` / `context_snapshot`.

## Live evidence (SSH → SalesOS → `salesos_app`, rolled back)

| Check | Result |
|-------|--------|
| `decisions` RLS | `relrowsecurity=false`, `relforcerowsecurity=false`, **0 policies** |
| `company_policies` RLS | off (PolicyEngine SELECTs OK without GUC) |
| Locks / blocked / idle-in-xact (idle snapshot) | all **0** |
| INSERT as JSON **strings** (`$10`… as text JSON) | **~1.0 ms**, OK |
| INSERT as native **list/dict** (app-shaped binds) | **`DataError: invalid input for query argument $10: [] (expected str, got list)`** — fails immediately in raw asyncpg; under SQLAlchemy/`command_timeout`/`pool_timeout` path this presented as **~30s** evaluate stall after `step=scored` |
| Row count at probe | `n=2`, newest `2026-08-12 12:33:31Z` (no inserts from hung evaluates) |

## Ruled out for sister

- Missing `apply_tenant_guc` on `_save_decision` — **not** the hang (table has no RLS). Still a hygiene gap vs agent/search runtimes if RLS is enabled later.
- Pool exhaustion / lock waits — no supporting live activity at idle; ContextBuilder + PolicyEngine already checked out sessions successfully (~17–22 ms) before `_save_decision`.

## Working write contrast

Same API process: `get_db` / agent paths that JSON-serialize or use ORM JSONB codecs succeed quickly; DIE `_save_decision` passed Python objects into `text()` INSERT without codec/cast.

**Validation of fix:** **PASS** on live prod HTTP gate — see [`IL-2A-HTTP-PRODUCTION-GATE.md`](./IL-2A-HTTP-PRODUCTION-GATE.md) (deploy `9304265`, light validated).
