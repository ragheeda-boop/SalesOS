# PROGRESS — Wave 2 Security Residuals (code-fixable closeout)

**Date:** 2026-07-22  
**Product:** SalesOS — local Docker API `:8000`  
**Related:** [PROGRESS-WAVE2-LOAD.md](./PROGRESS-WAVE2-LOAD.md), [PROGRESS-WAVE2-SEC.md](./PROGRESS-WAVE2-SEC.md)  
**Validation class:** **light validated** (focused smoke + local defensive re-probe)  
**Production secure claim:** **false**

---

## Closed this pass (code-fixable)

### 1. KG `StructuredLogger.error` arity → CLOSED

| Item | Detail |
|------|--------|
| Symptom | `/api/v1/graph/competitors|network/{id}` → **500** `StructuredLogger.error() takes 2 positional arguments but 5 were given` |
| Root cause | `StructuredLogger` rejected stdlib printf `*args`; KG `_run` used `%s` formatting |
| Fix | `salesos/backend/sdk/telemetry.py` — accept `*args`, format safely; add `warning` alias |
| Tests | `tests/unit/test_structured_logger.py` (written); full pytest blocked by container **OOM** on conftest import |
| Smoke | In-container: `LOGGER_OK` with printf error/warning |
| Re-probe `T125056Z` | Logger arity string **absent**; competitors/network **500** now show `graph_edges` missing (different residual) |

### 2. Webhook SSRF DNS TOCTOU → REDESIGNED (code) / pentest OPEN

| Item | Detail |
|------|--------|
| Before | Validate DNS then optional hostname dial; pin first IP only |
| Fix (2026-07-28) | Delivery always `resolve_dns=True`; refuse empty `allowed_ips`; multi-IP `_PinnedIPBackend` failover |
| Files | `url_safety.py`, `service.py`; [PROGRESS-WAVE2-SSRF-REDESIGN.md](./PROGRESS-WAVE2-SSRF-REDESIGN.md) |
| Still OPEN | Staging pentest [runbooks/staging-ssrf-pentest.md](./runbooks/staging-ssrf-pentest.md); httpx `_pool` private API coupling |

### 3. KG `graph_edges` missing / SQL fallback 500 → CLOSED (local schema repair)

| Item | Detail |
|------|--------|
| Symptom | With Neo4j unavailable/flaky, SQL fallback queried `graph_edges` → **500** `UndefinedTableError` |
| Root cause | Migration **0004** defined `graph_edges`/`graph_nodes`, but local DB at **0039** head had **no** `graph_*` relations (stamp/recreate drift) |
| Fix | Idempotent Alembic **0040** creates tables/indexes if missing (schema intended, not empty-gate); SQL joins cast `companies.id::text` to match varchar edge IDs; insights competitor/partner queries also filter `c.tenant_id` |
| Applied | **Local only** `alembic upgrade head` → **0040**; **not** prod migrate |
| Re-probe `T131010Z` | competitors **200** `[]`; network **200** `[]`; insights **200** not-found; metrics **200** (`neo4j_available: false` still — fallback path exercised) |
| Approach | **Table created** (preferred) — not gated empty/503 |

---

## Still OPEN

1. ~~**`graph_edges` missing**~~ — **CLOSED** local (0040); staging/prod DBs still need migrate when approved.  
2. **KG SQL fallback policy** — non-prod allows fallback; prod default-off (prior Wave 2).  
3. **`graph_edges` lacking `tenant_id` column** — scope via company joins + `tenant_id` filters; orphan edges invisible vs leak.  
4. **SSRF residuals** — multi-IP pin + refuse unpinned delivery **CLOSED in code**; staging pentest still **OPEN**.  
5. **Staging / pentest** — checklist ready; not run.  
6. **RBAC nuance** — webhook create without `workflow.read` list permission.  
7. **Full pytest** — not validated here (OOM / memory).  
8. **Neo4j flakiness** — metrics still show `neo4j_available: false` after probes; SQL fallback is the resilience path.

---

## Evidence

| Path | Role |
|------|------|
| `evidence/wave2-load/kg-graph-edges-2026-07-22T131010Z.json` | Post-0040 + cast fix — competitors/network **200** |
| `evidence/wave2-load/kg-graph-edges-2026-07-22T130534Z.json` | Mid-fix: competitors OK; network 500 uuid≠varchar |
| `evidence/wave2-load/probe-summary-2026-07-22T125056Z.json` | Prior rollup (graph_edges still missing then) |
| `evidence/wave2-load/kg-tenant-2026-07-22T125056Z.json` | KG probes — logger arity gone; graph_edges 500 |
| `evidence/wave2-load/ssrf-denied-2026-07-22T125056Z.json` | SSRF denies still 400; allow 201 |
| `evidence/wave2-load/burst-2026-07-22T125056Z.json` | Light burst |

---

## Commands run

```powershell
docker compose exec -T backend alembic current   # was 0039; no graph_*
docker compose exec -T backend alembic upgrade head   # 0039 → 0040 LOCAL ONLY
docker compose exec -T postgres psql -U salesos -d salesos -c "\dt graph_*"
docker compose restart backend
# focused register + competitors/network/insights/metrics probe → OVERALL PASS @ T131010Z
```

---

## Honesty

- **Label:** light validated  
- **Not claimed:** production-secure, GO, browser pass, full pytest green, pentest complete, staging/prod migrate done  
- **GA decision remains:** **NO-GO**
