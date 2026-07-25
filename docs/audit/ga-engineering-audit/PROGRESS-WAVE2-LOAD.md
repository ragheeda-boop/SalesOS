# PROGRESS — Wave 2 Security Residuals Under Load (PROD-W2 load)

**Date:** 2026-07-22  
**Product:** SalesOS (AQLIYA) — local Docker API `:8000`  
**Scope:** Defensive verification of webhook SSRF guards + KG tenant / SQL-fallback gates under light concurrent load  
**Validation class:** **light validated** (local runtime probes + code review)  
**Overall probe matrix:** **PASS** (26/26 on CSRF-aware runs `2026-07-22T103720Z` and re-probe `2026-07-22T125056Z`)  
**Production secure claim:** **false** — do not treat as GO / pentest complete  
**Code closeout:** [PROGRESS-WAVE2-RESIDUALS.md](./PROGRESS-WAVE2-RESIDUALS.md)

---

## Code review (guards present)

### Webhook SSRF (`app/modules/webhooks/url_safety.py` + service)

| Control | Present | Notes |
|---------|---------|-------|
| HTTPS-only | Yes | Non-HTTPS → `UnsafeWebhookURLError` |
| Block localhost / metadata hostnames | Yes | `localhost`, `*.localhost`, `metadata.google.internal`, … |
| Block private / loopback / link-local / reserved IPs | Yes | Via `ipaddress` flags |
| DNS resolve check | Yes | `socket.getaddrinfo` when hostname is not literal IP |
| Re-validate on delivery | Yes | `_attempt_delivery` calls `analyze_webhook_url` again |
| Redirect follow disabled | Yes | `httpx.AsyncClient(..., follow_redirects=False)` |
| CSRF on create/update POST | Yes | Middleware requires cookie + `X-CSRF-Token` |
| Pinned-IP connect | **Yes (2026-07-22)** | `_PinnedIPBackend` dials first validated public IP; TLS SNI keeps URL hostname. Residual: first-IP only; `resolve_dns=False` skips pin |

Create/update raise HTTP **400** on `UnsafeWebhookURLError` (`webhooks/router.py`).

### KG tenant + SQL fallback (`config.is_kg_sql_fallback_allowed`, `knowledge_graph_runtime`)

| Control | Present | Notes |
|---------|---------|-------|
| Router requires `verify_token` + `get_current_tenant_id` | Yes | All `/api/v1/graph/*` and KG insights |
| Tenant mismatch header | Yes | Live probe: **403** “Tenant ID in header does not match…” |
| SQL fallback default-off in prod | Yes | Allowed when `env` not production/prod unless `KG_ALLOW_SQL_FALLBACK` / `kg_allow_sql_fallback` set |
| SQL queries join/filter `tenant_id` | Yes (Wave 2) | Edge table still has **no** `tenant_id` column; scoped via company joins |
| Neo4j path | Observed | Re-probe `/health` `graph: connected`; metrics `neo4j_available: true` |
| Logger arity on error path | **Fixed** | See residuals doc; competitors/network no longer 500 on StructuredLogger |

---

## Live probe results (local `:8000`)

Script: `evidence/wave2-load/probe-wave2-load.ps1`  
Primary summaries: `probe-summary-2026-07-22T103720Z.json`, `probe-summary-2026-07-22T125056Z.json`

### Pass / fail matrix (CSRF-aware re-probe `T125056Z`)

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| `GET /health` | 200 | 200 (`graph: connected`) | **PASS** |
| Register disposable tenants A/B | token+tenant | ok | **PASS** |
| `GET /api/v1/identity/csrf-token` | 200 | 200 | **PASS** |
| Webhooks / graph / KG unauth | 401 | 401 | **PASS** |
| Webhooks list auth (no `workflow.read`) | 403 RBAC | 403 | **PASS** |
| SSRF deny: http / localhost / 127.0.0.1 / 10.x / 192.168 / 169.254 / metadata host / URL creds | 400 | 400 each | **PASS** |
| SSRF allow: `https://example.com/webhook-sink` | not SSRF-blocked | **201** created | **PASS** |
| KG metrics / search / insights | 200 scoped / empty / not-found | as expected | **PASS** |
| KG competitors / network (fake id) | no cross-tenant leak | Prior `T125056Z`: **500** missing table; post-0040 `T131010Z`: **200** empty | **PASS*** |
| KG cross-tenant `X-Tenant-Id` mismatch | 401/403 | **403** | **PASS** |
| Burst ×12 `/health` | all 200 | 200=12 | **PASS** |
| Burst ×12 `/identity/users/me` | 200 or 429 | 429=9, 200=3 | **PASS** |
| Burst ×12 `/companies` | 200 or 429 | 200=12 | **PASS** |

\*Prior residual was schema 500 (no cross-tenant leak). After local **0040** + `id::text` casts, competitors/network return **200** empty on SQL fallback — see [PROGRESS-WAVE2-RESIDUALS.md](./PROGRESS-WAVE2-RESIDUALS.md).

Earlier incomplete run (`T103036Z`) failed SSRF checks with **403 CSRF missing** (probe bug, not SSRF bypass). Manual CSRF confirm (`~T103505Z`): `https://127.0.0.1/hook` → **400** private/link-local.

---

## Evidence paths

| Path | Role |
|------|------|
| `docs/audit/ga-engineering-audit/evidence/wave2-load/kg-graph-edges-2026-07-22T131010Z.json` | Post-0040 competitors/network **200** |
| `docs/audit/ga-engineering-audit/evidence/wave2-load/probe-summary-2026-07-22T125056Z.json` | Prior rollup (graph_edges still missing then) |
| `docs/audit/ga-engineering-audit/evidence/wave2-load/ssrf-denied-2026-07-22T125056Z.json` | Denied SSRF target responses |
| `docs/audit/ga-engineering-audit/evidence/wave2-load/kg-tenant-2026-07-22T125056Z.json` | KG tenant / cross-header probes |
| `docs/audit/ga-engineering-audit/evidence/wave2-load/burst-2026-07-22T125056Z.json` | Concurrent light burst |
| `docs/audit/ga-engineering-audit/evidence/wave2-load/probe-wave2-load.ps1` | Repeatable local probe script |
| Prior | `…T103720Z` artifacts (logger arity still present then) |

Related: [PROGRESS-WAVE2-SEC.md](./PROGRESS-WAVE2-SEC.md), [PROGRESS-WAVE2-RESIDUALS.md](./PROGRESS-WAVE2-RESIDUALS.md).

---

## Residual risks (still open)

1. **SSRF pin residuals** — first validated IP only; `resolve_dns=False` skips pin; httpx `_pool` private coupling; no staging pentest.  
2. ~~**KG SQL fallback / `graph_edges` missing**~~ — **CLOSED** local via Alembic **0040** (table created) + uuid/text join casts; staging/prod migrate still pending approval.  
3. **`graph_edges` lacking `tenant_id`** — join-based scope (+ insights now filter `c.tenant_id`); orphan edges invisible vs leak (as Wave 2 notes).  
4. ~~**KG `StructuredLogger.error()` arity bug**~~ — **CLOSED** 2026-07-22 (see residuals doc).  
5. **No staging/pentest** — local only; not production hardening proof.  
6. **RBAC nuance** — disposable user cannot **list** webhooks (`workflow.read`) but **create** succeeded (201) after SSRF pass — permission matrix inconsistency worth tracking (not SSRF bypass).  
7. **Neo4j flakiness** — local metrics often `neo4j_available: false`; SQL fallback is required for availability.

---

## Commands run

```powershell
# Local stack on :8000; backend restarted after volume-mounted patches
curl.exe -s http://127.0.0.1:8000/health

powershell -NoProfile -ExecutionPolicy Bypass -File `
  docs\audit\ga-engineering-audit\evidence\wave2-load\probe-wave2-load.ps1 `
  -BaseUrl http://127.0.0.1:8000 `
  -EvidenceDir docs\audit\ga-engineering-audit\evidence\wave2-load
# OVERALL PASS 26/26 @ 2026-07-22T125056Z
```

Not run (by design / low-load / OOM): full pytest suite, pentest tooling, production deploy, exploit PoCs.

---

## Honesty

- **Label:** light validated  
- **Not claimed:** production secure, GO, browser pass, full security sign-off  
- **GA decision remains:** **NO-GO**
