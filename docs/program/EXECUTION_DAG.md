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
| **CI-08** GHCR 403 | BLOCKED | Org-level GHCR access (DEC-104 Option A) | Outside repo scope; R-17 — remaining board **P0**; Stage 6 build proven / push 403; not Phase 0 RLS gate |
| **CI-09** VPS SSH/secrets | BLOCKED | Ops secret provisioning | R-17 — P2; not Phase 0 RLS gate |
| **CI GREEN (full incl. publish)** | BLOCKED | Stage 6 GHCR push (CI-08) + Stage 7 + any residual non-publish reds | DEC-104 Option D: do **not** equate Stages 1–5 green with full publish GREEN; **blocks production GO**, not DEC-008 Phase 0 exit |
| **CI GREEN (code path)** | REPORTING ONLY | Stages 1–5 (+ non-publish gates) on a named run | DEC-104 interim honesty — **not** a closed production gate; claim only with run IDs |

---

## READY (Sprint 05 / 06+ — post Railway close)

| Item | Class | Why ready now | Notes |
|---|---|---|---|
| **DB-05** Schema reconciliation program | IN PROGRESS | Slice 0 CLOSED (DEC-111); R-20 / R-09 | Next Slice 1: additive CREATE for 8 deferred tables; no RLS yet |
| **Optional Jest 30 evidence** | BACKLOG (not CI-14) | DEC-108 deferred; authorize dedicated package | STOP silent major; Stage 3 **0**-fail gate |
| **STORY-02-02** browser/E2E verify (if scoped) | **CLOSED** (DEC-095) | Live Next redirect: `/dashboard` → **307** `/login?callbackUrl=%2Fdashboard`; `/`+`/login` **200** | Optional authenticated `smoke-ui.ps1` not run; **CI GREEN not met** |
| **Sprint 04 Category B RLS execution (B1–B7)** | READY (execution) | DEC-110 planning CLOSED | Inventory pinned: A=47, B=12, A-deferred=8; slices B1–B7; no SQL until slice land |
| **JWT audience consumption** | **CLOSED** (DEC-093) | Owner admin deps wire `decode_owner_*` via `owner_auth.py`; **14/14** unit PASS | Tenant `verify_token` unchanged (`salesos-api`); groundwork `2379e5f` |
| **Contract tests expansion** | IN PROGRESS / PARALLEL | Slice 1–4 LANDED (DEC-094 + DEC-106): probes + health/ready + auth list + **401/422** | Optional further typed endpoints; park OK |

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
| **CI-19** Semgrep findings / **R-24** | **CLOSED** | DEC-105 residual-close (alembic residual accepted) |
| **CI-22** FastAPI / Starlette / Pydantic / R-21 starlette | **CLOSED** | DEC-109 executive close; Phase 1 DEC-081 @ `442af64`; field pip-audit clear of starlette |
| **CI-14** Frontend Dependency Modernization / **R-18** | **CLOSED** | DEC-108 executive AC (sharp + eslint 10 + audit 0; Jest 30 backlog) |

---

## PARALLEL (safe; no Phase 0 RLS Human Gate)

| Track | Class | Justification |
|---|---|---|
| Contract tests, optional Jest 30 backlog, DB-05 Slice 1+, Category B B1–B7 | PARALLEL / READY | Unblocked Sprint 05/06 execution. Railway gate closed. CI-14/CI-19/CI-20/CI-22 CLOSED. DB-05 Slice 0 inventory CLOSED (DEC-111). |
| Contract tests expansion (post STORY-03-04) | PARALLEL | Slice 1–4 DEC-094/106 (probes + health/ready + auth list + 401/422); framework `623077c` |
| JWT audience **consumption** | **CLOSED** (DEC-093) | Owner Platform admin consumes `salesos-owner-platform`; tenant path untouched |
| Owner Admin / commercial FE | PARALLEL | Must not weaken auth/CSRF/RBAC; must **not** market production GO |

**Category B (DEC-110):** planning CLOSED; execution slices B1–B7 READY (join-policy SQL not this land). Do not reopen STORY-02-01.

**Swarm dispatch (DEC-107):** While waiting on ops (CI-08 GHCR, CI-09 VPS), keep agents on independent PARALLEL READY ownership — do **not** idle solely because those ops leaves are BLOCKED. CI-14 preferred path during that wait was **DEC-108** executive AC close (not silent Jest 30); swarm policy = DEC-107. Honesty: DEC-104 **code path** vs **full incl. publish**.

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
| Contract tests expansion slice 2 (DEC-094) | `0ac07bc` | LANDED | `/health` + `/health/ready` + honest DB/cache fixtures |
| Contract tests expansion slice 3 (DEC-094) | `bdc6fd2` | LANDED | Auth list `GET /api/v1/decisions` OpenAPI contract |
| Contract tests expansion slice 4 (DEC-106) | `448c301` | LANDED | 401 `DetailStringError` + 422 `HTTPValidationError` on decisions list |
| DB-05 Slice 0 drift inventory (DEC-111) | *(this land)* | **CLOSED** (inventory) | Alembic head `065d1d3a466b`; 8 R-09 missing CREATE; emails/meetings type drift; **docs / light validated** |
| Category B RLS planning (DEC-110) | `4889ac7` | **CLOSED** (planning) | docs inventory + slices B1–B7; POLICY_COUNT 47 intact; **docs / light validated** |
| CI-22 executive close (DEC-109) | `a3e4bee` | **CLOSED** | docs close; field pip-audit + Unit corroboration |
| CI-14 executive AC close (DEC-108) | `278b0d4`+follow-up | **CLOSED** | docs-only; security AC met without Jest major |
| STORY-02-04 §17.2 relabel | `932f722` | DONE | docs-only |
| Card primitives (Jest debt related) | `9577c98` | Progress note only | **CI GREEN not met** |

---

## Board progress fraction

**25/25** Complete/Closed on tracked Sprint 05 board fraction (includes **S04-04** / **CI-16** / **CI-20** / **CI-19** / **CI-14** / **CI-22**). Adjacent closed: **Jest-debt / R-23**. Pending: none. In progress: none. Blocked (critical path Phase 0): **none**. Also blocked (ops): CI-08 (P0), CI-09 (P2).

---

## Update rule

When a story changes READY↔BLOCKED↔COMPLETE, update this file in the same records commit as `SPRINT_05_DELIVERY_BOARD.md` / `DECISION_LOG.md`. Never claim **production GO** or **CI GREEN** without command evidence. Never reopen STORY-02-01 after DEC-044. Phase 0 (DEC-008) **GO** ≠ production GA GO.
