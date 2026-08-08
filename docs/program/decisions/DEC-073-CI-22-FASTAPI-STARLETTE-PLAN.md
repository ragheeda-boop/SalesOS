# DEC-073 — CI-22 FastAPI / Starlette / Pydantic modernization: planning evidence (no package bump)

> **Status:** **Accepted** — plan COMPLETE; **Phase 1 EXECUTED** under DEC-081 (fastapi 0.141.1 / starlette 1.3.1 / pydantic 2.13.4)  
> **Date:** 2026-08-01  
> **Board:** Backend / Deps (SalesOS)  
> **Story / risk:** CI-22 / R-21 starlette leg  
> **Authority:** DEC-052 STOP · DEC-054 register · DEC-057 ecdsa residual · board REGISTERED READY/PARALLEL  
> **Out of scope this land:** Poetry lock bumps · production migrate · Railway · CI-14 · silent FastAPI major mid-flight

---

## 1. Why plan-first

CI-16 Slice 2 proved: under `fastapi ^0.111` / `pydantic <2.9`, **no** pip-audit-clean `starlette` exists that clears the advisory floor (**≥1.3.1**). Clearance requires a **scoped cascade**:

| Package | Current (approx lock) | Target floor | Risk |
|---|---|---|---|
| `starlette` | below audit-clean under FastAPI 0.111 | **≥1.3.1** | Transitive via FastAPI |
| `fastapi` | **^0.111** | **~0.115+ / ~0.135+** (solver-proven) | Request/response, Depends, middleware |
| `pydantic` | **<2.9** constraint historically | **≥2.9** | Schema / validation edge cases |

Blind mid-flight bump without DEC evidence is forbidden (session contract).

---

## 2. Execution slices (when authorized)

| Slice | Scope | Evidence gate |
|---|---|---|
| **C0** | Inventory lock versions + `pip-audit` starlette findings (this DEC) | Docs only |
| **C1** | Raise pydantic floor to ≥2.9 **if** FastAPI target requires it; narrow smoke | `poetry update` + import `app.main` + GraphQL smoke |
| **C2** | FastAPI → solver-clean line that pulls starlette ≥1.3.1 | `pip-audit` **NO starlette**; unit smoke; no security-gate weaken |
| **C3** | Residual app fixes if API breakages surface | Targeted tests only |

**STOP if:** cascade forces unrelated majors; audit still red on starlette after C2; test blast beyond smoke without executive OK.

---

## 3. Decision

Accept CI-22 **plan/evidence**. Keep story **REGISTERED / READY**. Do **not** bump packages in this land. Next executable requires a Phase-1 package naming exact version pins + smoke commands (C1 or C2).

---

## 4. Validation

| Check | Result |
|---|---|
| Package / lock changes | **None** |
| Label | **not validated** (docs-only plan) |

**CI GREEN not met.** `pip-audit` remains red on starlette (± ecdsa accepted residual).
