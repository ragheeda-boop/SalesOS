# Execution DAG — Current Program State

> **Living classification** of what is READY / BLOCKED / PARALLEL as of records close **2026-08-01** (post DEC-044 Option B).  
> Authority: evidence + `SPRINT_05_DELIVERY_BOARD.md` + `RISK_REGISTER.md` + Sprint plans.  
> Honesty labels: **CI GREEN not met**. **Phase 0 exit = NO-GO** (Railway R-14 / S04-04). STORY-02-01 **DONE** under revised AC (DEC-044 — 47 policies, not literal 72).

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
Security P0 (historical) → RLS / STORY-02-01 (DONE, DEC-044 revised AC @ 47)
                                               ├── Railway R-14 (S04-04) ──► Phase 0 exit
                                               │
                                               └── Adversarial suites (S04-01 LANDED; S04-05 LANDED; S04-06 READY)
                     Category B inventory ──► Sprint 04
                     R-09 / DB-05 (8 tables) ──► schema program
```

Phase 0 exit requires: Railway isolation proof (or formal accept-without-Railway decision), adversarial coverage, and **CI GREEN** (not met). STORY-02-01 story AC is satisfied under **DEC-044** (47) — that does **not** unlock Phase 0 GO. **Current gate: NO-GO.**

---

## BLOCKED

| Item | Class | Blocked on | Notes |
|---|---|---|---|
| **S04-04** Railway R-14 closure | BLOCKED | Credentials / live authorization (DEC-015/016) | Highest Phase 0 gate risk (R-14 score 25) |
| **Phase 0 exit** | BLOCKED | R-14 Railway + CI not green | **NO-GO** — DEC-040 / DEC-044; STORY-02-01 no longer a story-AC blocker |
| **CI-08** GHCR 403 | BLOCKED | Org-level GHCR access | Outside repo scope; R-17 |
| **CI-09** VPS SSH/secrets | BLOCKED | Ops secret provisioning | R-17 |
| **CI GREEN** (overall workflow) | BLOCKED | Residual reds: MyPy (CI-20), pip-audit (CI-16/R-21), npm audit (CI-14), Jest debt, Trivy fs, etc. | Individual gates may be green; **workflow not green** |

---

## READY

| Item | Class | Why ready now | Notes |
|---|---|---|---|
| **S04-06** Adversarial suite (remaining) | READY | S04-01 + S04-05 landed; no credential block | P2 board pending; expect POLICY_COUNT 47 after DEC-044 migration |
| **STORY-02-02** browser/E2E verify (if scoped) | READY | Middleware code LANDED (`3f4b3c8`); status PARTIAL until redirect verified | Not a board CLOSE; validation gap only |
| **CI-19** Semgrep Wave 1 (GHA injection ×8) | READY / IN PROGRESS | Triage done (`CI_19_SEMGREP_TRIAGE.md`); Wave 1 next; R-24 pointer | Waves 2–5 backlog |
| **CI-21** Gitleaks JWT fixture | LANDED (CLOSED) | Fix `b03ffbf` on master | Closed from residual triage |
| **CI-20** Backend Types (MyPy) | READY (phased) | REGISTERED; 308 errors; Backend Lint already green | DEC-038 — not mechanical this sprint |
| **CI-14** Frontend Dependency Modernization | READY (Sprint 06) | REGISTERED; dep CI-13 baseline closed | Majors — R-18 |
| **CI-16** Backend dependency security | READY (backlog pull) | BACKLOG; R-21 | Not part of CI-02 |
| **DB-05** Schema reconciliation program | READY (program) | BACKLOG; R-20 / R-09 | Multi-sprint; unblocks 8 RLS-deferred tables |
| **Sprint 04 Category B RLS + inventory** | READY (planning) | DEC-044 deferred Category B here | Settle canonical count (may be 69/72/other) |

---

## DONE / closed (story AC)

| Item | Class | Notes |
|---|---|---|
| **STORY-02-01** (RLS rollout) | **DONE** (revised AC) | DEC-044 Option B: **47** policies (`065d1d3a466b` + `company_features`). Draft RLS-72 **Superseded**. R-25 Closed-as-accepted-scope. Not Phase 0 GO |

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
| S04-05 write-protection suite | `8699796` | COMPLETE (DEC-039) | **build validated** — Docker pytest **8/8 PASS in 4.88s** |
| CI-21 Gitleaks JWT fixture neutralize | `b03ffbf` | CLOSED | fixture replaced; scanner not weakened |
| STORY-02-03 JWT audience groundwork | `2379e5f` | DONE | **not validated** |
| STORY-02-02 server-side middleware | `3f4b3c8` | PARTIAL | unit helpers present; browser **not validated** |
| STORY-03-04 OpenAPI contract framework | `623077c` | DONE | **not validated** |
| STORY-02-04 §17.2 relabel | `932f722` | DONE | docs-only (already on master) |
| Card primitives (Jest debt related) | `9577c98` | Progress note only | suite recovery aid; **CI GREEN not met** |

---

## Board progress fraction

**18/20** Complete/Closed on `SPRINT_05_DELIVERY_BOARD.md` (S04-05 + CI-21 closed). Pending: S04-06. In progress: CI-19 Wave 1. Blocked: CI-08, S04-04, CI-09.

---

## Update rule

When a story changes READY↔BLOCKED↔COMPLETE, update this file in the same records commit as `SPRINT_05_DELIVERY_BOARD.md` / `DECISION_LOG.md`. Never claim Phase 0 GO or CI GREEN without command evidence.
