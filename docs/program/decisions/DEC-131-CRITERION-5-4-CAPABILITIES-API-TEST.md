# DEC-131 — Capability decorator API contract test (Phase 0 criterion 5.4)

> **Status:** **Accepted** — Cursor implementation **COMPLETE** · Criterion **5.4 VERIFIED/CLOSED** via DEC-131a (Arch PASS + Validation PASS @ `65e82cc`)  
> **Date:** 2026-08-01  
> **Board:** Backend Lead / Capability Drift (SalesOS / AQLIYA)  
> **Story / risk:** Phase 0 Exit Criterion **5.4** · DEBT-ARC-003 / E-21 (partial — test gap only)  
> **Authority:** PHASE_0_EXIT_CHECKLIST §5.4 · `.engineering/29_CAPABILITY_REGISTRY.md` §4 drift #6 · ARB review protocol (Cursor ≠ CLOSED)  
> **Out of scope this land:** Criterion **5.1** SoT designation · **5.2** CAP-### mapping · **5.3** `validate_capability_registries.py` exit 0 · auth/CSRF weaken · DEC-085 `set_config` · Production GO · CI GREEN

---

## 1. Decision

Accept HTTP ASGI contract coverage for the decorator capability registry as **Cursor COMPLETE** for criterion **5.4**.

| Pin | Value |
|---|---|
| Gap | Checklist 5.4 / EOS §4#6 — no test exercised `GET /api/v1/capabilities` |
| This land | `tests/contract/test_capabilities_api.py` — auth gate, list (≥13 core kebab IDs), by-id 200/404, status filter + invalid status 400 |
| App code | **Unchanged** (router already live: `runtime/capability_framework/router.py`) |
| DEC-085 | **Intact** (`get_db` / `set_config` not touched) |
| Criterion state | **CLOSED** (DEC-131a) |

---

## 2. Validation

| Check | Result |
|---|---|
| Narrow Docker pytest (4 tests) | **4 passed** in 6.75s |
| Command | `docker compose exec -T backend …/bin/python -m pytest tests/contract/test_capabilities_api.py -q --tb=short` |
| Production / Railway | **Not run** |
| Label | **build validated** (narrow Docker pytest) |

**Production GO not claimed. CI GREEN not met.**

**Orchestrator CLOSE (DEC-131a):** Arch PASS + Validation PASS @ `65e82cc` → criterion **5.4 VERIFIED/CLOSED**; Phase 0 **26/54**; Capability Drift **1/4**. Residuals **5.1–5.3** OPEN. **Production GO not claimed. CI GREEN not met.**

---

## 3. Records

- Phase 0 criterion **5.4** → **VERIFIED/CLOSED** (DEC-131a)
- Residual Capability Drift **5.1–5.3** remain OPEN (4-way registry drift unchanged)
- **Not claimed:** Production GO · CI GREEN · 5.1 SoT · Phase 0 exit

---

## 4. Evidence Package

| ID | Artifact | Location / command |
|----|----------|-------------------|
| EV-001 | Router under test | `runtime/capability_framework/router.py` (`prefix=/api/v1/capabilities`, `Depends(verify_token)`) |
| EV-002 | Contract suite | `tests/contract/test_capabilities_api.py` |
| EV-003 | pytest output | **4 passed**, 1 warning (passlib/crypt), 6.75s |
| EV-004 | Core IDs asserted | identity, company, data-fabric, search, timeline, knowledge-graph, feature-store, decision-engine, event-runtime, activity-intelligence, workflow, marketplace, capability-framework |
| EV-005 | CI artifacts | Field CI PENDING (OpenCode / Validator) |

---

## 5. Rollback

| Step | Action |
|------|--------|
| 1 | Revert land commit containing `test_capabilities_api.py` + DEC-131 docs |
| 2 | No app behavior change to undo |
| Expected impact | Lose HTTP contract coverage only |

---

## 6. Risk

| Surface | Level | Note |
|---------|-------|------|
| Registry drift | HIGH unchanged | 5.1–5.3 still open; this land only closes the “no test” gap for review |
| Auth | LOW | Auth override mirrors other contract suites; unauthenticated path asserts 401 |
| Route ordering | LOW residual | Static paths under `/{capability_id}` (e.g. `/nav/sidebar`) may shadow — not asserted this land |
