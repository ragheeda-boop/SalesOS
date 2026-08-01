# Execution DAG — Current Program State

> **Living classification** of what is READY / BLOCKED / PARALLEL as of records close **2026-08-01** (post **DEC-016** Railway R-14 Option A + Architecture Validation reassessment).  
> Authority: evidence + `SPRINT_05_DELIVERY_BOARD.md` + `RISK_REGISTER.md` + Sprint plans + `docs/audit/ga-engineering-audit/`.  
> Honesty labels: **CI GREEN not met**. **Phase 0 (DEC-008 RLS / R-14) exit = GO** (critical-path gate cleared under DEC-016 @ `7232979`). **Production GA / External pilot = NO-GO** (unchanged). STORY-02-01 **DONE** under revised AC (DEC-044 — 47 policies). **Do not reopen STORY-02-01.**

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
Security P0 (historical) → RLS / STORY-02-01 (DONE, DEC-044 @ 47) ──► closed
                                               │
                                               └── Railway R-14 (S04-04) ──► CLOSED (DEC-016)
                                                     │
                                                     ▼
                                          Phase 0 (DEC-008) exit = GO
                                          (production GA still NO-GO)
```

**Phase 0 (DEC-008 tenant-isolation / R-14) critical-path gate = CLEARED.** Evidence: S04-04 **CLOSED** under **DEC-016** Option A (Railway staging→prod bypass-probe PASS; `APP_POSTGRES_*` set; health 200; **no app image promote**; docs SHA `7232979`); STORY-02-01 **CLOSED** (DEC-044); R-14 **CLOSED**; S04-01/S04-05/S04-06 adversarial coverage **COMPLETE**.

**Does not equal production GO.** ga-engineering-audit executive summary remains **production no-go**. **CI GREEN not met.** CI-08/CI-09 remain ops-blocked (non–Phase-0-critical-path). Program Phase 1 commercial sequencing may proceed per DEC-008; marketing / GA claims stay **NO-GO**.

---

## Architecture Validation verdict (2026-08-01)

| Gate | Verdict | Evidence |
|---|---|---|
| Phase 0 (DEC-008 RLS / R-14) | **GO** (gate cleared) | DEC-016; S04-04 CLOSED; R-14 CLOSED; STORY-02-01 CLOSED |
| Production GA | **NO-GO** | Audit `00-EXECUTIVE-SUMMARY.md`; PRODUCTION_PLAN DoD incomplete; **CI GREEN not met** |
| External pilot | **NO-GO** | Same; no soak/browser/GA DoD evidence |
| Pilot-ready with conditions | **Not claimed** | Conditions for product pilot still unmet (CI red; deploy ops gaps) |

---

## BLOCKED

| Item | Class | Blocked on | Notes |
|---|---|---|---|
| **CI-08** GHCR 403 | BLOCKED | Org-level GHCR access | Outside repo scope; R-17 — remaining board **P0**; not Phase 0 RLS gate |
| **CI-09** VPS SSH/secrets | BLOCKED | Ops secret provisioning | R-17 — P2; not Phase 0 RLS gate |
| **CI GREEN** (overall workflow) | BLOCKED | Residual reds: Backend Lint, pip-audit/Secrets Scan residuals, npm audit (CI-14), Trivy fs, Semgrep residual (CI-19 Wave 2), etc. (**CI-20 / Backend Types CLOSED** DEC-096 field **0**; **Jest-debt / R-23 CLOSED** DEC-077) | Parallel honesty track; **blocks production GO**, not DEC-008 Phase 0 exit |

---

## READY (Sprint 05 / 06+ — post Railway close)

| Item | Class | Why ready now | Notes |
|---|---|---|---|
| **CI-19** Semgrep Wave 2 residual | IN PROGRESS / READY | Waves 1/3/4/5 COMPLETE; Wave 2 deferred (~108 `avoid-sqlalchemy-text`) | R-24; authorize Wave 2 when ready |
| **CI-22** FastAPI / Starlette / Pydantic | IN PROGRESS / READY | Phase 1 COMPLETE (DEC-081 @ `442af64`); further phases | R-21 starlette / pip-audit path |
| **CI-14** Frontend Dependency Modernization | IN PROGRESS / READY (Sprint 06) | Slice 1 COMPLETE; Slice 2 STOP; Slice 3 pending | R-18; STOP silent majors |
| **STORY-02-02** browser/E2E verify (if scoped) | **CLOSED** (DEC-095) | Live Next redirect: `/dashboard` → **307** `/login?callbackUrl=%2Fdashboard`; `/`+`/login` **200** | Optional authenticated `smoke-ui.ps1` not run; **CI GREEN not met** |
| **DB-05** Schema reconciliation program | READY (program) | BACKLOG; R-20 / R-09 | Multi-sprint; unblocks 8 RLS-deferred tables |
| **Sprint 04 Category B RLS + inventory** | READY (planning) | DEC-044 deferred Category B | Settle canonical count |
| **JWT audience consumption** | **CLOSED** (DEC-093) | Owner admin deps wire `decode_owner_*` via `owner_auth.py`; **14/14** unit PASS | Tenant `verify_token` unchanged (`salesos-api`); groundwork `2379e5f` |
| **Contract tests expansion** | IN PROGRESS / PARALLEL | Slice 1+2 LANDED (DEC-094): `/ping`+`/health/live`+csrf; `/health`+`/health/ready` (DB fixtures) | Next: 401/422 (honest OpenAPI error shapes), one auth list |
| **CI-16** Backend dependency security | CLOSED | Slices 1+3 + ecdsa Option A; starlette → CI-22 | Story closed; residual via CI-22 |
| **Jest-debt** | CLOSED (DEC-077) | Stage 3 field 0 failures | R-23 Closed |

---

## DONE / closed (story AC)

| Item | Class | Notes |
|---|---|---|
| **S04-04** Railway R-14 | **CLOSED** | DEC-016 Option A; SHA `7232979`; staging+prod bypass-probe PASS; health 200; no image promote |
| **R-14** | **CLOSED** | Local/CI/compose + Railway staging + Railway production |
| **STORY-02-01** (RLS rollout) | **DONE** (revised AC) | DEC-044 Option B @ **47** policies. **Do not reopen.** |
| **S04-01 / S04-05 / S04-06** | **COMPLETE** | Adversarial read / write / remaining suites |
| **CI-16** Backend dependency security | **CLOSED** | DEC-057 ecdsa residual; starlette → CI-22 |
| **Jest-debt** / **R-23** | **CLOSED** | DEC-077; Stage 3 **0** failing suites |
| **CI-20** Backend Types (MyPy) / **R-22** | **CLOSED** | DEC-096; field Types **0** on `220d91a` (run `30684023356` / job `91326366120`); tip `af4835f` (`30684308678` / `91327119501`) |

---

## PARALLEL (safe; no Phase 0 RLS Human Gate)

| Track | Class | Justification |
|---|---|---|
| **CI-19 Wave 2**, **CI-22**, **CI-14** | PARALLEL / READY | Unblocked Sprint 05/06 execution. Railway gate closed. CI-20 CLOSED (DEC-096). |
| Contract tests expansion (post STORY-03-04) | PARALLEL | Slice 1+2 DEC-094 (`/ping`+`/health/live`+`/health`+`/health/ready`); framework `623077c` |
| JWT audience **consumption** | **CLOSED** (DEC-093) | Owner Platform admin consumes `salesos-owner-platform`; tenant path untouched |
| Owner Admin / commercial FE | PARALLEL | Must not weaken auth/CSRF/RBAC; must **not** market production GO |

---

## LANDED (master) — Sprint 03 / Sprint 05 adjacency

| Story / item | SHA | Records status | Validation |
|---|---|---|---|
| S04-04 / DEC-016 Railway R-14 | `7232979` | CLOSED | Ops evidence: bypass-probe + health (secrets redacted in DEC-016) |
| S04-05 write-protection suite | `8699796` | COMPLETE (DEC-039) | **build validated** — Docker pytest **8/8 PASS** |
| S04-06 adversarial RLS remaining | `119df9e` | COMPLETE (DEC-045) | **build validated** — Docker pytest **15/15 PASS** |
| CI-21 Gitleaks JWT fixture neutralize | `b03ffbf` | CLOSED | fixture replaced; scanner not weakened |
| STORY-02-03 JWT audience groundwork | `2379e5f` | DONE | **light validated** — host pytest **7/7** (DEC-091); prior Docker **15** w/ write-protection (`deae7de`) |
| STORY-02-02 server-side middleware | `3f4b3c8` | **DONE** (DEC-095) | Jest **14/14** (DEC-088) + live redirect probe **browser-validated** (DEC-095) |
| STORY-03-04 OpenAPI contract framework | `623077c` | DONE | Framework land; pytest via DEC-093 |
| Contract tests expansion slice 1 (DEC-094) | `93a00d7` | LANDED | `/ping` + `/health/live` typed + OpenAPI HTTP contracts |
| Contract tests expansion slice 2 (DEC-094) | (this land) | IN PROGRESS | `/health` + `/health/ready` + honest DB/cache fixtures; next: 401/422, auth list |
| STORY-02-04 §17.2 relabel | `932f722` | DONE | docs-only |
| Card primitives (Jest debt related) | `9577c98` | Progress note only | **CI GREEN not met** |

---

## Board progress fraction

**22/22** Complete/Closed on tracked Sprint 05 board fraction (includes **S04-04** / **CI-16** / **CI-20**). Adjacent closed: **Jest-debt / R-23**. Pending: none. In progress: CI-19 (Wave 2 Slice 1 COMPLETE / remainder OPEN), CI-14, CI-22. Blocked (critical path Phase 0): **none**. Also blocked (ops): CI-08 (P0), CI-09 (P2).

---

## Update rule

When a story changes READY↔BLOCKED↔COMPLETE, update this file in the same records commit as `SPRINT_05_DELIVERY_BOARD.md` / `DECISION_LOG.md`. Never claim **production GO** or **CI GREEN** without command evidence. Never reopen STORY-02-01 after DEC-044. Phase 0 (DEC-008) **GO** ≠ production GA GO.
