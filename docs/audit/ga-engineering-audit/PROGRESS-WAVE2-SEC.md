# PROGRESS — Wave 2 Security P0 (PROD-W2)

**Date:** 2026-07-22  
**Owner:** Backend security agent  
**Scope:** Decision Center IDOR, Webhook SSRF + Postgres wiring, KG SQL tenant / prod fallback, Forecast demo gate, DIE by-ID tenant checks  
**Classification:** light validated (targeted unit tests). Not production-ready claim.

---

## Findings status

| Program ID | GA ID | Status | Notes |
|------------|-------|--------|-------|
| PROD-W2-001 | GA-P0-SEC-01 | **FIXED** | `get_decision` / audit / feedback require `(id, tenant_id)`; 404 on mismatch |
| PROD-W2-002 | GA-P0-SEC-02 | **FIXED** (with residual) | HTTPS + private/metadata IP block + DNS rebinding check; Postgres repos + Alembic `0039`; router wired to Postgres |
| PROD-W2-003 | GA-P0-SEC-03 | **FIXED** (partial residual) | SQL fallback tenant predicates; prod disables SQL fallback unless `KG_ALLOW_SQL_FALLBACK`; DIE by-ID ops require tenant |
| PROD-W2-004 | GA-P0-05 | **FIXED** | `DEMO_MODE=false` loads tenant open opportunities; no `demo-1`; 400 if empty |

Wave 5 P1 items (CSRF API-key, Bearer rate-limit, 401) **not in scope** for this wave.

---

## Files changed

### Decision Center IDOR
- `salesos/backend/domains/decision_center/repository.py`
- `salesos/backend/domains/decision_center/postgres_repo.py`
- `salesos/backend/domains/decision_center/service.py`
- `salesos/backend/domains/decision_center/router.py`
- `salesos/backend/domains/decision_center/tests/test_decision_center.py` (+ cross-tenant IDOR test)

### DIE memory by-ID tenant
- `salesos/backend/runtime/decision_runtime/__init__.py`
- `salesos/backend/runtime/decision_runtime/router.py`

### Webhooks SSRF + persistence
- `salesos/backend/app/modules/webhooks/url_safety.py` (new)
- `salesos/backend/app/modules/webhooks/service.py`
- `salesos/backend/app/modules/webhooks/repository.py` (Postgres models/repos)
- `salesos/backend/app/modules/webhooks/router.py` (Postgres factory)
- `salesos/backend/app/alembic/versions/0039_webhook_tables.py` (new; **not applied** in this session)
- `salesos/backend/tests/unit/test_webhooks.py` (SSRF cases)

### Knowledge graph
- `salesos/backend/app/config.py` (`kg_allow_sql_fallback` / `is_kg_sql_fallback_allowed`)
- `salesos/backend/runtime/knowledge_graph_runtime/service.py`
- `salesos/backend/runtime/knowledge_graph_runtime/repository.py`
- `salesos/backend/runtime/knowledge_graph_runtime/router.py`

### Forecast
- `salesos/backend/app/routers/commercial.py`
- `salesos/backend/tests/unit/test_forecast_demo_gate.py` (new)

### This report
- `docs/audit/ga-engineering-audit/PROGRESS-WAVE2-SEC.md`

---

## Validation evidence

Commands run (targeted; not full suite):

```text
cd salesos/backend
python -m pytest domains/decision_center/tests/test_decision_center.py tests/unit/test_webhooks.py tests/unit/test_forecast_demo_gate.py -q --tb=line
```

**Result:** `96 passed in 3.54s` (2026-07-22)  
**Honest label:** **light validated** (targeted unit tests green). Not build/integration/staging validated.

Not run (require approval / heavy): full `pytest tests/unit`, `alembic upgrade`, docker rebuild, browser E2E.

---

## Residual risk

1. **Alembic 0039 not applied** — Postgres webhook tables exist in code/migration only. Until `alembic upgrade` on target env, webhook API will fail at DB layer. InMemory still used by unit tests only.
2. **DIE still memory-primary** — tenant checks on by-ID ops close IDOR for in-process cache; durable source-of-truth still dual (memory + optional `decisions` SQL). Full Postgres-primary DIE is larger than this wave.
3. **`graph_edges` has no `tenant_id` column** — SQL fallback joins `companies` for tenant scope; edges without matching company rows may be invisible rather than leak. Prod SQL fallback default-off reduces exposure.
4. **DNS rebinding race** — validate-then-connect window remains (TOCTOU); no pinned IP connect yet.
5. **Analytics demo inputs** in `commercial.py` (`AnalyticsInput` static values) were **out of Wave 2 scope** (only Forecast GA-P0-05).
6. **Decision templates** remain global (no tenant column) — not flagged as P0 in register; left unchanged.

---

## Acceptance checklist (from PRODUCTION_PLAN §3.c)

- [x] Decision Center by-ID filters `(id, tenant_id)` → 404 mismatch  
- [x] Webhooks: SSRF block RFC1918/metadata + HTTPS; Postgres wiring present  
- [x] KG SQL fallback disabled in prod by default + tenant predicates when allowed  
- [x] Forecast: no `demo-1` when `DEMO_MODE=false`  
- [ ] Staging smoke / pentest — **not validated**
