# DEC-127 — CSRF X-API-Key bypass (Phase 0 criterion 1.3)

> **Status:** **Accepted** — Cursor implementation **COMPLETE** · Criterion 1.3 = **READY FOR REVIEW** (Architecture PENDING · Validation PENDING). Only Execution Orchestrator may mark VERIFIED/CLOSED.  
> **Date:** 2026-08-01  
> **Board:** Backend Lead / Security P0 (SalesOS)  
> **Story / risk:** GA-P1-SEC-01 / PROD-W5-001 / STORY-01-03 / Phase 0 Exit Criterion **1.3**  
> **Authority:** PHASE_0_EXIT_CHECKLIST §1.3 · PRODUCTION_PLAN PROD-W5-001 · DEC-085 `set_config` · ARB review protocol (Cursor ≠ CLOSED)  
> **Out of scope this land:** Security 1.5 (pip-audit residual) · Railway R-14 · frontend · `.ai/` org design · Criterion CLOSED/VERIFIED claims · Production GO

---

## 1. Decision

Accept CSRF enforcement without `X-API-Key` / API-key-auth bypass as **Cursor COMPLETE** for criterion **1.3**, with HTTP ASGI regression added.

| Pin | Value |
|---|---|
| Finding | GA-P1-SEC-01 / PROD-W5-001 — CSRF skipped on non-empty `X-API-Key` (later: also on `api_key_authenticated`) |
| App fix (prior Sprint 01) | `CsrfEnforcementMiddleware` no longer skips for bare `X-API-Key` or `request.state.api_key_authenticated` |
| This land | (1) Correct stale docstring that still claimed API-key skip; (2) HTTP contract regressions for bare + authenticated API-key → **403** |
| DEC-085 | **Intact** (`get_db` still `set_config`; not touched) |
| Criterion state | **READY FOR REVIEW** (not CLOSED / not VERIFIED) |

**Semantics enforced:** state-changing methods require matching `X-CSRF-Token` + `csrf_token` cookie. API-key presence or successful API-key auth does **not** waive CSRF. Testing mode (`SALESOS_TESTING=true`) and listed public identity paths remain the only intentional skips.

---

## 2. Validation

| Check | Result |
|---|---|
| Narrow Docker pytest | **11 passed** |
| Nodes | `TestCsrfMiddleware` (8) · HTTP contract bare/auth API-key + matching CSRF (3) |
| Command | `docker compose exec -T backend poetry run pytest tests/unit/test_middleware.py::TestCsrfMiddleware tests/contract/test_csrf_x_api_key_bypass.py -q` |
| Production / Railway | **Not run** |
| Label | **build validated** (narrow Docker pytest) |

**Production GO not claimed. CI GREEN not met. Criterion CLOSED not claimed.**

---

## 3. Records

- Phase 0 criterion **1.3** → **READY FOR REVIEW** (Cursor COMPLETE)
- Assigned next: Architecture Reviewer (independent review sign)
- Prior Sprint 01/02: STORY-01-03 already verified in audit reports — checklist 1.3 remained ⬜ pending Phase 0 packaging + fresh evidence
- **Not claimed:** Criterion CLOSED · VERIFIED · Production GO · CI GREEN

---

## 4. Evidence Package

| ID | Artifact | Location / command |
|----|----------|-------------------|
| EV-001 | CSRF middleware | `app/common/middleware.py` `CsrfEnforcementMiddleware` (no API-key skip) |
| EV-002 | Docstring honesty | Same class — docstring no longer claims API-key waiver |
| EV-003 | Unit regressions | `tests/unit/test_middleware.py::TestCsrfMiddleware` (incl. bare + authenticated API-key → 403) |
| EV-004 | New HTTP contract | `tests/contract/test_csrf_x_api_key_bypass.py` |
| EV-005 | pytest output | **11 passed** (Docker `poetry run pytest` narrow CSRF suite) |
| EV-006 | Screenshots | N/A |
| EV-007 | CI artifacts | Field CI PENDING (OpenCode / Validator) |

---

## 5. Rollback

| Step | Action |
|------|--------|
| 1 | Revert land commit (docstring + HTTP contract + DEC-127 docs) |
| 2 | Core CSRF no-bypass behavior remains (pre-existing Sprint 01); do not reintroduce API-key skip |
| Expected impact | Lose HTTP contract coverage + docstring honesty; enforcement behavior unchanged |

---

## 6. Risk

| Surface | Level | Note |
|---------|-------|------|
| Application | LOW | Machine clients using API keys on cookie/browser-style state-changing paths must send CSRF (or use non-browser integration patterns) — intentional |
| Runtime | LOW | `SALESOS_TESTING=true` still skips CSRF in test/CI processes — not a production waiver |
| Rate-limit order | LOW | RateLimit runs before CSRF (known P2; budget consumed before 403) — out of 1.3 scope |
| Database | N/A | No schema / DEC-085 / R-14 changes |
