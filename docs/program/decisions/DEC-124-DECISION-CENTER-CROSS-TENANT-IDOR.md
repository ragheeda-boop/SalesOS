# DEC-124 — Decision Center cross-tenant IDOR (Phase 0 criterion 1.1)

> **Status:** **Accepted** — Cursor implementation **COMPLETE** · Criterion 1.1 = **READY FOR REVIEW** (Architecture PENDING · Validation PENDING). Only Execution Orchestrator may mark VERIFIED/CLOSED.  
> **Date:** 2026-08-01  
> **Board:** Backend Lead / Security P0 (SalesOS / AQLIYA)  
> **Story / risk:** GA-P0-SEC-01 / PROD-W2-001 / R-01 / Phase 0 Exit Criterion **1.1**  
> **Authority:** PHASE_0_EXIT_CHECKLIST §1.1 · PRODUCTION_PLAN PROD-W2-001 · DEC-085 `set_config` · ARB review protocol (Cursor ≠ CLOSED)  
> **Out of scope this land:** Webhook SSRF (1.2) · CSRF X-API-Key (1.3) · Railway R-14 (2.3) · frontend · `.ai/` org design · Criterion CLOSED/VERIFIED claims · Production GO

---

## 1. Decision

Accept Decision Center by-ID tenant isolation as **Cursor COMPLETE** for criterion **1.1**, with HTTP-layer regression added.

| Pin | Value |
|---|---|
| Finding | GA-P0-SEC-01 — `get_decision` by ID without tenant filter |
| App fix (prior Sprint 01 / Wave 2) | `PostgresDecisionCenterRepository.get_decision` filters `(id, tenant_id)`; router passes `Depends(get_current_tenant_id)`; audit/feedback gated via `get_decision` |
| This land | HTTP ASGI contract regression proving cross-tenant GET/audit/feedback → **404** / empty |
| DEC-085 | **Intact** (`get_db` still `set_config`; not touched) |
| Criterion state | **READY FOR REVIEW** (not CLOSED / not VERIFIED) |

---

## 2. Validation

| Check | Result |
|---|---|
| Narrow Docker pytest (9 tests) | **9 passed** |
| Nodes | service IDOR · postgres get/audit/feedback · harness demo · HTTP contract (3) |
| Command | `poetry run pytest` … (see Evidence Package) |
| Production / Railway | **Not run** |
| Label | **build validated** (narrow Docker pytest) |

**Production GO not claimed. CI GREEN not met. Criterion CLOSED not claimed.**

---

## 3. Records

- Phase 0 criterion **1.1** → **READY FOR REVIEW** (Cursor COMPLETE)
- Assigned next: Architecture Reviewer (independent review sign)
- Prior Wave 2 note: `PROGRESS-WAVE2-SEC.md` already marked PROD-W2-001 FIXED — checklist 1.1 remained ⬜ pending review + HTTP proof
- **Not claimed:** Criterion CLOSED · VERIFIED · Production GO · CI GREEN · Railway migrate

---

## 4. Evidence Package

| ID | Artifact | Location / command |
|----|----------|-------------------|
| EV-001 | App isolation | `domains/decision_center/postgres_repo.py` `get_decision` + `router.py` tenant Depends |
| EV-002 | pytest output | **9 passed** (Docker `poetry run pytest` narrow suite) |
| EV-003 | New regression | `tests/contract/test_decision_center_cross_tenant_idor.py` |
| EV-004 | Prior regressions | `test_decision_center.py::test_cross_tenant_idor_blocked`, `test_postgres_repo.py`, `test_decision_center_harness_demo.py` |
| EV-005 | Screenshots | N/A |
| EV-006 | CI artifacts | Field CI PENDING (OpenCode / Validator) |

---

## 5. Rollback

| Step | Action |
|------|--------|
| 1 | Revert land commit containing `test_decision_center_cross_tenant_idor.py` + DEC-124 docs |
| 2 | App tenant filters remain (pre-existing); do not remove `(id, tenant_id)` predicates |
| Expected impact | Lose HTTP contract coverage only; isolation behavior unchanged |

---

## 6. Risk

| Surface | Level | Note |
|---------|-------|------|
| Database | MEDIUM | App-layer filter is primary; RLS Category A on `decision_center_decisions` helps only when role lacks BYPASSRLS (R-14 Railway still OPEN) |
| Application | LOW | Templates with `tenant_id IS NULL` remain readable/mutable as shared globals — not GA-P0-SEC-01 class; residual |
| Runtime | LOW | In-memory contract path + Postgres unit path covered; full e2e multi-JWT not re-run this land |
