# DEC-156 — MetaData residual Base merge (DRIFT-01)

> **Status:** **Proposal — not Accepted / not CLOSED**  
> **Date:** 2026-08-13  
> **Board:** Backend Platform / Database (SalesOS)  
> **Finding:** EAB-001-P1-DRIFT-01  
> **Authority:** METADATA-ISLAND-FREEZE.md · DEC-130b/f (KEEP + `to_metadata`) · freeze rule: no live Base merge without a DEC  
> **Out of scope this proposal:** DROP any table/column · Alembic head bump · `feature_ai_copilot` flip · Production GO / CI GREEN · claiming DRIFT-01 Fixed

---

## 1. Decision (proposed — do not execute until Accepted)

Authorize constructing the **six residual** private `MetaData()` islands onto canonical `sdk.database.Base.metadata` (or keep them as KEEP stubs already copied there), then delete the private `MetaData()` constructors.

This land (2026-08-13) already converted **seven query/DML stubs** to `table()`/`column()` without Base merge (ceiling **13→6**). That work does **not** require this DEC. This DEC is only for the remaining schema-owning / KEEP-register islands.

| Pin | Value |
|---|---|
| FF-09 ceiling after `table()` land (this session) | **6** (not this DEC) |
| Residual islands needing this DEC | **6** |
| Alembic head | **unchanged** unless a tiny additive migration is proven required (prefer avoid) |
| Criterion / DRIFT-01 | stays **Partial** until residual islands are gone **and** freeze + fitness updated |

### Alternatives considered

| Option | Result |
|---|---|
| (a) Convert remaining six to `table()`/`column()` | **Rejected** — they own `Index()` KEEP registers, `to_metadata(Base)`, and/or `create_all()` |
| (b) Leave ceiling at 6 forever | **Rejected** as Fixed claim; acceptable as freeze hold |
| (c) Construct residual `Table(...)` on `sdk.database.Base.metadata`; drop private `MetaData()` | **Proposed** |
| (d) New Alembic DROP / rewrite | **Rejected** — DEC-130f no-DROP posture |

---

## 2. Residual islands (blocked without this DEC)

| Path | Why not `table()` | Proposed merge |
|---|---|---|
| `app/db05_orphan_keep.py` | KEEP register; `to_metadata(Base)` | Construct stubs on `Base.metadata` directly (same KEEP; no DROP) |
| `runtime/activity_runtime/__init__.py` | `Index()` KEEP; copied in `app/database.py` | `Table(..., Base.metadata)` via `sdk.database.Base` (avoid `app.database` cycle) |
| `sdk/events/store.py` | `domain_events` Index KEEP; copied in `app/database.py` | same |
| `runtime/knowledge_graph_runtime/repository/sql_repository.py` | `graph_edges` Index KEEP; query stubs for companies/contacts | `graph_edges` on Base; leftover query stubs → `table()` in same land |
| `domains/search/engine/vector_store.py` | `_PgVector` + Index KEEP; `vectors` copied in `app/database.py` | construct on Base; keep `_PgVector` stand-in |
| `sdk/events/outbox.py` | `Index()` + **`create_all()`** runtime DDL | register on Base; retire `ensure_table()` `create_all` in favor of existing/additive migration **only if** table is not already live |

**Do not** merge search_runtime + domains/search postgres_repo into one Base table — those are already `table()` stubs as of the 2026-08-13 land.

---

## 3. Acceptance criteria (when Arch+Val accept)

1. `rg MetaData(` under `salesos/backend *.py` ≤ new freeze ceiling (expected **0–1** if KEEP file still needs a private md; prefer **0**).  
2. `app/database.py` `to_metadata` copy loop removed or no-ops.  
3. Live Docker `alembic check` still **exit 0** (or no worse than current); **no DROP**.  
4. Freeze + FF-09 ceiling updated in the same land.  
5. `feature_ai_copilot` remains **False**.

---

## 4. Explicit non-claims

- This file is a **proposal**. It is **not** Accepted, **not** CLOSED, **not** Arch PASS.  
- DRIFT-01 remains **Partial**.  
- Production / GA **GO** — **NO**.
