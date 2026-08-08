# Remediation — Structural Partials — EAB-2026-08-06-003

**Date:** 2026-08-06  
**Trigger:** User «التالي» after OPS-01 advancement (OPS-01 remains **Deferred**)  
**Scope:** Agent-executable structural Partials from EAB-003 FINDINGS-RECHECK  
**Production GA:** **NO-GO** (unchanged)  
**OPS-01:** Still **Deferred** — launch rows 1–5 BLOCKED-HUMAN; do not fake-close  
**Commit:** none

---

## Mandate

Advance Still Partial findings without claiming Production GO:

| ID | Prior (EAB-003 recheck) | This pack target |
|----|-------------------------|------------------|
| DUP-01 | Still Partial | Push SoT / quarantine twins; Fixed only if collisions truly gone |
| AIGOV-01 | Still Partial | Strengthen honesty gates |
| DRIFT-01 | Still Partial | Reduce count or freeze+migrate with measurable progress |
| DUP-02 | Still Partial | Resolve or quarantine top duplicates |
| FIT-01 | Still Partial (minimal) | Wire/document closer to Fixed |

---

## Dispositions (new)

| ID | New disposition | Residual |
|----|-----------------|----------|
| **EAB-001-P0-DUP-01** | **Partial (narrowed)** | ≥3 BE engines retained (honest); HTTP SoT tags strengthened; lab twin **renamed** `@salesos/decision-platform-lab`; FE STUB remains resolve target. Not Fixed — engines not deleted; hybrid FE history/accept residual |
| **EAB-001-P1-AIGOV-01** | **Partial (narrowed)** | `/ai/generate` + `/ai/evaluate` gated on `feature_ai_copilot`; decisions honesty banner + Experimental badge; CopilotPanel defense-in-depth gate; FF-07 extended. Residual: Arabic/telemetry paths; multi-engine transparency |
| **EAB-001-P1-DRIFT-01** | **Partial (narrowed)** | MetaData **19→18**; MCP ephemeral `table()` rewrite; ranked migrate plan; freeze ceiling **18**. Live islands remain |
| **EAB-001-P1-DUP-02** | **Partial (narrowed)** | Workflow webhooks remounted → `/api/v1/workflow/webhooks*` (**prefix collision Fixed**); search experimental OpenAPI-deprecated. Prompt multi-registry residual |
| **EAB-001-P2-FIT-01** | **Partial (narrowed / closer to Fixed)** | Root workflow already discoverable; FF-07 extended (stub pkg + lab rename + light FF-14); FF-09 ceiling 18. Not full FF catalog / remote GH Actions green not validated |
| **EAB-001-P0-OPS-01** | **Deferred** (unchanged) | Launch blocker — human rows 1–5 |

**Regressions:** none claimed without suite evidence below.

---

## Work performed (high level)

### DUP-01
- OpenAPI tags: Decision Center (SoT) / Platform (alternate) / Runtime (remounted; deprecated aliases)
- Decision Center router SoT docstring
- Lab package rename `@salesos/decision-platform` → `@salesos/decision-platform-lab`
- FE STUB README/package.json twin pointers updated
- QUARANTINE.md + DECISION-API-SOT cross-links

### AIGOV-01
- `app/routers/ai.py`: generate + evaluate require `feature_ai_copilot`
- `/decisions` honesty banner + `ExperimentalAiBadge`
- `CopilotPanel` returns null unless `useAiCopilotEnabled` passes (tests mock enabled)
- AI_HONESTY §8 updated for twin rename

### DRIFT-01
- `mcp_server/resources.py`: `MetaData()` → `table()`/`column()` (−1)
- METADATA-ISLAND-FREEZE.md remeasure + migrate backlog
- FF-09 ceiling **18**

### DUP-02
- Workflow webhook paths `/webhooks` → `/workflow/webhooks` (+ tests + capability map note)
- `app/routers/search.py`: `deprecated=True` + boot tag Search (experimental)
- CAPABILITY-DUP-REGISTER updated

### FIT-01
- Fitness scripts: FF-07 twin/stub/FF-14 greps; ceiling 18
- Workflow `.github/workflows/fitness-ci-subset.yml` already at repo root (discoverable)
- FITNESS-CI-SUBSET-PLAN.md updated

---

## Test evidence

| Check | Result | Label |
|-------|--------|-------|
| Host `fitness-ci-subset.ps1` | **exit 0** (FF-07/09/10/12 + light FF-14; MetaData count=18) | light validated |
| MetaData count | **18** ≤ ceiling 18 | light validated |
| Docker BE `test_webhook_ssrf` + workflow webhook creates/lists | **20 passed** | build validated (targeted) |
| Docker BE `test_feature_ai_copilot_remains_false` | **1 passed** | light validated |
| Docker BE `require_ai_copilot_enabled` on `app.routers.ai` | raises **403** | light validated |
| FE jest `copilot-panel.test.tsx` | **13/13 passed** | build validated (targeted) |
| Full FE lint 528 | **Not run** (out of scope) | — |
| Remote GitHub Actions fitness job | **Not validated** | — |

---

## EAB-004 Verification Run?

**Warranted: yes (narrow)** — structural deltas landed on routers, AI gates, MetaData ceiling, fitness greps. Prefer a focused EAB-004 recheck of the five Partials + suite spot-checks — **not** a full Production GO board, and **not** as OPS-01 closure.

---

## Files changed (summary)

| Area | Paths |
|------|-------|
| BE routers / SoT | `boot/routers.py`, `domains/decision_center/router.py`, `app/routers/workflows.py`, `app/routers/search.py`, `app/routers/ai.py` |
| DRIFT | `mcp_server/resources.py`, `METADATA-ISLAND-FREEZE.md` |
| FE / packages | `decisions/page.tsx`, `copilot-panel.tsx` + test, FE + lab decision `package.json`/`README`, lab jest/tsconfig |
| DUP register / capability | `CAPABILITY-DUP-REGISTER.md`, `capability_framework/__init__.py` |
| Tests | `domains/workflow/tests/test_router.py`, `tests/contract/test_webhook_ssrf.py` |
| Fitness | `fitness-ci-subset.sh`, `.ps1`, `FITNESS-CI-SUBSET-PLAN.md` |
| Docs | this file, `REMEDIATION-PROGRAM-STATUS.md`, `AI_HONESTY.md`, `QUARANTINE.md`, `DECISION-API-SOT.md` |

---

*Structural remediation — EAB-2026-08-06-003 — **build validated with gaps** — production no-go — OPS-01 Deferred — no commit*
