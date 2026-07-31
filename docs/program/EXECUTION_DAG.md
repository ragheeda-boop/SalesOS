# Execution DAG — Current Program State

> **Living classification** of what is READY / BLOCKED / PARALLEL as of records close **2026-08-01** (post DEC-039 / DEC-040).  
> Authority: evidence + `SPRINT_05_DELIVERY_BOARD.md` + `RISK_REGISTER.md` + Sprint plans.  
> Honesty labels: **CI GREEN not met**. **Phase 0 exit = NO-GO** (Railway R-14 / STORY-02-01 incomplete).

---

## Legend

| Class | Meaning |
|---|---|
| **READY** | Unblocked for execution; next eligible work |
| **BLOCKED** | Cannot proceed without named external/authorization dependency or unfinished gate |
| **PARALLEL** | May run alongside critical-path work; disjoint files / no shared gate ownership |
| **LANDED** | Code/docs on `origin/master`; may still need validation evidence |

---

## Critical path (Phase 0 → Phase 1)

```
Security P0 (historical) → RLS / STORY-02-01 ──┬── Railway R-14 (S04-04) ──► Phase 0 exit
                                               │
                                               └── Adversarial suites (S04-01 LANDED; S04-05 LANDED; S04-06 READY)
```

Phase 0 exit requires: STORY-02-01 complete **including** Railway isolation proof (or formal accept-without-Railway decision), adversarial coverage, and **CI GREEN** (not met). **Current gate: NO-GO.**

---

## BLOCKED

| Item | Class | Blocked on | Notes |
|---|---|---|---|
| **S04-04** Railway R-14 closure | BLOCKED | Credentials / live authorization (DEC-015/016) | Highest Phase 0 gate risk (R-14 score 25) |
| **STORY-02-01** (Railway portion / full AC) | BLOCKED | S04-04 / R-14 Railway | Local/CI/staging/prod-template remediated; Railway open |
| **Phase 0 exit** | BLOCKED | R-14 Railway + STORY-02-01 incomplete + CI not green | **NO-GO** — DEC-040 |
| **CI-08** GHCR 403 | BLOCKED | Org-level GHCR access | Outside repo scope; R-17 |
| **CI-09** VPS SSH/secrets | BLOCKED | Ops secret provisioning | R-17 |
| **CI GREEN** (overall workflow) | BLOCKED | Residual reds: MyPy (CI-20), pip-audit (CI-16/R-21), npm audit (CI-14), Jest debt, Trivy fs, etc. | Individual gates may be green; **workflow not green** |

---

## READY

| Item | Class | Why ready now | Notes |
|---|---|---|---|
| **S04-06** Adversarial suite (remaining) | READY | S04-01 + S04-05 landed; no credential block | P2 board pending |
| **STORY-02-02** browser/E2E verify (if scoped) | READY | Middleware code LANDED (`3f4b3c8`); status PARTIAL until redirect verified | Not a board CLOSE; validation gap only |
| **CI-19** Semgrep findings remediation | READY (triage first) | REGISTERED; Security Scan green; 253 findings need triage | Not mechanical |
| **CI-20** Backend Types (MyPy) | READY (phased) | REGISTERED; 308 errors; Backend Lint already green | DEC-038 — not mechanical this sprint |
| **CI-14** Frontend Dependency Modernization | READY (Sprint 06) | REGISTERED; dep CI-13 baseline closed | Majors — R-18 |
| **CI-16** Backend dependency security | READY (backlog pull) | BACKLOG; R-21 | Not part of CI-02 |
| **DB-05** Schema reconciliation program | READY (program) | BACKLOG; R-20 | Multi-sprint |

---

## PARALLEL (safe alongside blocked Railway / Phase 0 gate)

| Track | Class | Justification |
|---|---|---|
| Jest suite remediation (Sprint 01 debt) | PARALLEL | FE-only; Card primitives `9577c98` are related progress, not closure of 33 failing suites |
| Contract tests expansion (post STORY-03-04) | PARALLEL | Framework LANDED (`623077c`); more endpoints can add without Railway |
| JWT audience **consumption** (EPIC-04 / Sprint 04 STORY-02-03 consume) | PARALLEL | Groundwork DONE (`2379e5f`); consumption is separate story |
| Owner Admin / commercial FE that does not claim Phase 0 GO | PARALLEL | Must not weaken auth/CSRF/RBAC; must not market Phase 0 complete |

---

## LANDED (master) — Sprint 03 / Sprint 05 adjacency

| Story / item | SHA | Records status | Validation |
|---|---|---|---|
| S04-05 write-protection suite | `8699796` | COMPLETE (DEC-039) | **not validated** |
| STORY-02-03 JWT audience groundwork | `2379e5f` | DONE | **not validated** |
| STORY-02-02 server-side middleware | `3f4b3c8` | PARTIAL | unit helpers present; browser **not validated** |
| STORY-03-04 OpenAPI contract framework | `623077c` | DONE | **not validated** |
| STORY-02-04 §17.2 relabel | `932f722` | DONE | docs-only (already on master) |
| Card primitives (Jest debt related) | `9577c98` | Progress note only | suite recovery aid; **CI GREEN not met** |

---

## Board progress fraction

**17/19** Complete/Closed on `SPRINT_05_DELIVERY_BOARD.md` (S04-05 closed). Pending: S04-06. Blocked: CI-08, S04-04, CI-09.

---

## Update rule

When a story changes READY↔BLOCKED↔COMPLETE, update this file in the same records commit as `SPRINT_05_DELIVERY_BOARD.md` / `DECISION_LOG.md`. Never claim Phase 0 GO or CI GREEN without command evidence.
