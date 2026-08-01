# Execution DAG — Current Program State

> **Living classification** of what is READY / BLOCKED / PARALLEL as of records close **2026-08-01** (post DEC-044 Option B; human confirmed critical-path posture).  
> Authority: evidence + `SPRINT_05_DELIVERY_BOARD.md` + `RISK_REGISTER.md` + Sprint plans.  
> Honesty labels: **CI GREEN not met**. **Phase 0 exit = NO-GO** — sole critical-path gate: **S04-04 Railway R-14** (human). STORY-02-01 **DONE** under revised AC (DEC-044 — 47 policies, not literal 72). **Do not reopen STORY-02-01.**

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
Security P0 (historical) → RLS / STORY-02-01 (DONE, DEC-044 revised AC @ 47) ──► closed
                                               │
                                               └── Railway R-14 (S04-04) ──► Phase 0 exit
                                                     ▲
                                                     │ sole remaining critical-path gate (human)
```

**Phase 0 exit critical path = S04-04 only.** STORY-02-01 story AC is satisfied under **DEC-044** (47) and is **not** on the critical path. CI residual work and Sprint 05/06 READY items continue **in parallel** — they are independent of the Human Gate on S04-04 and do **not** reopen STORY-02-01. S04-06 adversarial remaining suite is **COMPLETE** (DEC-045). Closing S04-04 (or a formal accept-without-Railway decision) is the Phase 0 exit blocker. **Current gate: NO-GO.**

---

## BLOCKED

| Item | Class | Blocked on | Notes |
|---|---|---|---|
| **S04-04** Railway R-14 closure | BLOCKED | Credentials / live authorization (DEC-015/016) | **Sole Phase 0 exit critical-path gate** (R-14 score 25); Human Gate — independent of Sprint 05/06 READY work |
| **Phase 0 exit** | BLOCKED | **S04-04 only** (critical path) | **NO-GO** — DEC-040 / DEC-044; STORY-02-01 closed; do not reopen |
| **CI-08** GHCR 403 | BLOCKED | Org-level GHCR access | Outside repo scope; R-17 — not Phase 0 critical path |
| **CI-09** VPS SSH/secrets | BLOCKED | Ops secret provisioning | R-17 — not Phase 0 critical path |
| **CI GREEN** (overall workflow) | BLOCKED | Residual reds: MyPy (CI-20), pip-audit (R-21; starlette → CI-22; ecdsa accepted residual DEC-057), npm audit (CI-14), Jest debt, Trivy fs, etc. | Parallel honesty track; **not** the Phase 0 critical-path gate |

---

## READY (parallel — continue while S04-04 Human Gate is open)

| Item | Class | Why ready now | Notes |
|---|---|---|---|
| **CI-20** Backend Types (MyPy) | IN PROGRESS / PARALLEL (phased) | Phase 1–9 COMPLETE through demo_mode (`821aad5`; ~100 expected; field-verify `30677025355` **104**); Phase 10 COMPLETE at `ca76f9c` (communication_hub 11→0; ~100→~89 / field **93**); Phase 11 COMPLETE at `86b4094` (work_intelligence 5→0; ~89→~84 / field **88**); Phase 12 COMPLETE at `e44b7f3` (boot/startup 7→0 + database 7→0; ~84→~70 / field ~74 expected); story OPEN; Backend Lint already green | DEC-038 register; DEC-046–050 Phases 1–5; DEC-053 Phase 6; DEC-055 Phase 7; DEC-058 Phase 8; DEC-059 Phase 9; DEC-060 Phase 10; DEC-061 Phase 11; DEC-064 Phase 12 — **not CLOSED** |
| **CI-19** Semgrep Waves 2–5 | READY / PARALLEL | Wave 1 COMPLETE (`d5c9b57`); Waves 2–5 REGISTERED | SQL honesty, SHA pins, noise excludes, residual; R-24 |
| **CI-16** Backend dependency security | CLOSED | Slice 1 COMPLETE (`1e73a2f` multipart); Slice 2 → **CI-22** (DEC-052/054); Slice 3 COMPLETE (`d3f1eef` strawberry); **ecdsa** Accepted residual **Option A** (DEC-057); R-21 mitigating (starlette open) | Not part of CI-02; story **CLOSED** (slice scope) |
| **CI-22** FastAPI / Starlette / Pydantic modernization | REGISTERED / PARALLEL | DEC-054; DEC-052 follow-on; scoped cascade (FastAPI ~0.135+, pydantic ≥2.9, starlette ≥1.3.1); **NOT** CI-16 slice work | No package bumps at registration; R-21 starlette leg |
| **CI-14** Frontend Dependency Modernization | IN PROGRESS / PARALLEL (Sprint 06) | **plan DEC-062**; **Slice 1 COMPLETE DEC-063** (sharp **0.35.3** under next **15.5.22**); dep CI-13 closed; Slice 2–3 pending | Majors — R-18 mitigating; STOP silent Next/React/ESLint/Jest / Next↓14 |
| **Jest-debt** (Sprint 01 suite remediation) | READY / PARALLEL | FE-only; Card primitives `9577c98` progress only | 33 failing suites; does not close via Card primitives alone |
| **STORY-02-02** browser/E2E verify (if scoped) | READY / PARALLEL | Middleware code LANDED (`3f4b3c8`); status PARTIAL until redirect verified | Not a board CLOSE; validation gap only |
| **DB-05** Schema reconciliation program | READY (program) | BACKLOG; R-20 / R-09 | Multi-sprint; unblocks 8 RLS-deferred tables |
| **Sprint 04 Category B RLS + inventory** | READY (planning) | DEC-044 deferred Category B here | Settle canonical count (may be 69/72/other) |
| **CI-21** Gitleaks JWT fixture | LANDED (CLOSED) | Fix `b03ffbf` on master | Closed from residual triage |

---

## DONE / closed (story AC)

| Item | Class | Notes |
|---|---|---|
| **STORY-02-01** (RLS rollout) | **DONE** (revised AC) | DEC-044 Option B: **47** policies (`065d1d3a466b` + `company_features`). Draft RLS-72 **Superseded**. R-25 Closed-as-accepted-scope. **Do not reopen.** Not Phase 0 GO |
| **S04-06** Adversarial suite (remaining) | **COMPLETE** | DEC-045; commit `119df9e`; Docker **15/15 PASS** (**build validated**); POLICY_COUNT 47 intact; inventory not reopened |
| **CI-16** Backend dependency security | **CLOSED** | DEC-057 Option A: ecdsa accepted residual; Slices 1+3 complete; starlette → CI-22. **CI GREEN not met** |

---

## PARALLEL (safe alongside blocked Railway / Phase 0 Human Gate)

| Track | Class | Justification |
|---|---|---|
| **CI-20**, **CI-19 Waves 2–5**, **CI-22**, **CI-14**, **Jest-debt** | PARALLEL / READY | Explicitly unblocked for Sprint 05/06 execution while S04-04 waits on human auth |
| Contract tests expansion (post STORY-03-04) | PARALLEL | Framework LANDED (`623077c`); more endpoints can add without Railway |
| JWT audience **consumption** (EPIC-04 / Sprint 04 STORY-02-03 consume) | PARALLEL | Groundwork DONE (`2379e5f`); consumption is separate story |
| Owner Admin / commercial FE that does not claim Phase 0 GO | PARALLEL | Must not weaken auth/CSRF/RBAC; must not market Phase 0 complete |

---

## LANDED (master) — Sprint 03 / Sprint 05 adjacency

| Story / item | SHA | Records status | Validation |
|---|---|---|---|
| S04-05 write-protection suite | `8699796` | COMPLETE (DEC-039) | **build validated** — Docker pytest **8/8 PASS in 4.88s** |
| S04-06 adversarial RLS remaining | `119df9e` | COMPLETE (DEC-045) | **build validated** — Docker pytest **15/15 PASS**; POLICY_COUNT 47 intact |
| CI-21 Gitleaks JWT fixture neutralize | `b03ffbf` | CLOSED | fixture replaced; scanner not weakened |
| STORY-02-03 JWT audience groundwork | `2379e5f` | DONE | **not validated** |
| STORY-02-02 server-side middleware | `3f4b3c8` | PARTIAL | unit helpers present; browser **not validated** |
| STORY-03-04 OpenAPI contract framework | `623077c` | DONE | **not validated** |
| STORY-02-04 §17.2 relabel | `932f722` | DONE | docs-only (already on master) |
| Card primitives (Jest debt related) | `9577c98` | Progress note only | suite recovery aid; **CI GREEN not met** |

---

## Board progress fraction

**19/20** Complete/Closed on `SPRINT_05_DELIVERY_BOARD.md` (S04-06 closed DEC-045). Pending: none. In progress: CI-19 Wave 1 done / Waves 2–5 READY. Blocked (critical path): **S04-04 only**. Also blocked (non-critical-path ops): CI-08, CI-09.

---

## Update rule

When a story changes READY↔BLOCKED↔COMPLETE, update this file in the same records commit as `SPRINT_05_DELIVERY_BOARD.md` / `DECISION_LOG.md`. Never claim Phase 0 GO or CI GREEN without command evidence. Never reopen STORY-02-01 after DEC-044.
