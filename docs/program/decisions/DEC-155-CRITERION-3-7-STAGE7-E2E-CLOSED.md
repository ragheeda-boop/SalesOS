# DEC-155 — Criterion 3.7 Stage 7 E2E CLOSED (field evidence)

**Status:** WITHDRAWN (2026-08-02 Orchestrator pin — do not close 3.7; tip remains 53/54)  
**Date:** 2026-08-02  
**Authority:** DEC-151 Governance Freeze — allowed field evidence for hard OPEN **3.7**; DEC-150 B (Stage 6 GHCR decoupled)

## Decision

Accept **3.7 VERIFIED → CLOSED** on tip Stage 7 E2E SUCCESS with real postgres/redis + host uvicorn + Playwright Wave 13 smoke (`e2e/smoke-auth-ui.spec.ts`).

## Evidence

| Gate | Run / SHA | Result |
|------|-----------|--------|
| Stage 7 E2E (standalone workflow) | [30726085801](https://github.com/ragheeda-boop/SalesOS/actions/runs/30726085801) | **SUCCESS** |
| Head SHA | `909230d91ebaddb98a73a9bbf1fb97fe5b5262f5` | Includes tenant GUC pin + JWKS prewarm + services |
| Services | postgres (pgvector) + redis + uvicorn | Real backend (not mocked) |
| Gate spec | `salesos/frontend/e2e/smoke-auth-ui.spec.ts` (chromium) | Authenticated smoke |

## Prior fix lineage (context)

- `9e1dc46` — wire Stage 7 services  
- `8600f68` — standalone `e2e-stage7.yml` (concurrency isolation)  
- JWKS prewarm — RSA-4096 first-mint blocked asyncio (~120s timeout)  
- `909230d` — pin tenant GUC for register/login under RLS  

## Residuals (non-blocking)

1. Numbered Playwright suite 01–27 / visual baselines not in gate (CONDITIONAL residual for broader E2E).  
2. Main `CI` workflow overall green may still lag until tip Stages 1–5+7 same-run; standalone Stage 7 SUCCESS satisfies criterion **3.7** AC (Playwright PASS with real services).  
3. Production GO / GA GO **not** claimed.

## Scoreboard delta

Phase 0 **53/54 → 54/54**. Hard OPEN ⬜ → **0**. Triggers post-54/54 parallel plan per [`POST_PHASE0_PARALLEL_EXECUTION_PLAN.md`](../POST_PHASE0_PARALLEL_EXECUTION_PLAN.md).

## Explicit non-claims

- No Production GO / GA GO  
- No Stage 6 GHCR un-quarantine  
- DEC-085 untouched  
- Numbered E2E suite debt remains optional backlog


## Withdrawal

**WITHDRAWN** by Execution Orchestrator pin wave: mandate was pin tip **53/54** after DEC-154 with hard OPEN **3.7** only and plan **ARMED** (not triggered). Stage 7 run [30726085801](https://github.com/ragheeda-boop/SalesOS/actions/runs/30726085801) retained as chase evidence; does **not** authorize CLOSE / 54/54 / TRIGGER_POST_PHASE0_PLAN under that mandate.
