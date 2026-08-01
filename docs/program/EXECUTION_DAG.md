# Execution DAG — Current Program State

> **Living classification** of what is READY / BLOCKED / PARALLEL as of records close **2026-08-01** (post **DEC-120** Railway R-14 reopen).  
> Authority: evidence + `SPRINT_05_DELIVERY_BOARD.md` + `RISK_REGISTER.md` + Sprint plans + `docs/audit/ga-engineering-audit/` + Principal Audit.  
> Honesty labels: **CI GREEN not met**. **Phase 0 (DEC-008 RLS / R-14) exit = NO-GO** (DEC-086 GO **withdrawn** by DEC-120). **Production GA / External pilot = NO-GO**. STORY-02-01 **DONE** under revised AC (DEC-044 — 47 policies). **Do not reopen STORY-02-01.**

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
                                               └── Railway R-14 (S04-04) ──► REOPENED (DEC-120)
                                                     │
                                                     ▼
                                          Phase 0 (DEC-008) exit = NO-GO
                                          (production GA still NO-GO)
```

**Phase 0 (DEC-008 tenant-isolation / R-14) critical-path gate = NO-GO residual (multi-tenant).** DEC-120 A–E + tip RLS align on Railway prod (`9664e9fc`, `salesos_app`, alembic `d1a8c35e7f09`, policies **67**, E bare/wrong-tenant **0** vs owner **141221**, single-tenant caveat). Criterion **2.3 CLOSED CONDITIONAL** (DEC-126; residual *multi-tenant live split not re-proven*). Tip-align does not upgrade 2.3. STORY-02-01 **CLOSED** (DEC-044). Local/CI/compose R-14 remediations retained.

**Does not equal production GO.** ga-engineering-audit executive summary remains **production no-go**. **CI GREEN not met.**

---

## Architecture Validation verdict (2026-08-01; amended DEC-120)

| Gate | Verdict | Evidence |
|---|---|---|
| Phase 0 (DEC-008 RLS / R-14) | **NO-GO** (DEC-086 GO withdrawn) | DEC-120; Principal Audit; S04-04 REOPENED; R-14 Railway REOPENED |
| Production GA | **NO-GO** | Audit `00-EXECUTIVE-SUMMARY.md`; PRODUCTION_PLAN DoD incomplete; **CI GREEN not met** |
| External pilot | **NO-GO** | Same; no soak/browser/GA DoD evidence |
| Pilot-ready with conditions | **Not claimed** | Conditions unmet |

---

## BLOCKED

| Item | Class | Blocked on | Notes |
|---|---|---|---|
| **S04-04 / Railway R-14** | BLOCKED (critical path) | Remediation slices A–E + live re-proof (DEC-120) | Dual honesty: env ≠ runtime RLS; password rotate human/ops |
| **CI-08** GHCR 403 | BLOCKED | Org-level GHCR access (DEC-104 Option A) | Also blocks primary image promote path for Railway; alternate = Railway build-from-GitHub |
| **CI-09** VPS SSH/secrets | BLOCKED | Ops secret provisioning | R-17 — P2 |
| **CI GREEN (full incl. publish)** | BLOCKED | Stage 6 GHCR push (CI-08) + Stage 7 + residual reds | Blocks production GO |
| **CI GREEN (code path)** | REPORTING ONLY | Stages 1–5 on a named run | DEC-104 interim honesty |

---

## READY (Sprint 05 / 06+ — parallel; Phase 0 still NO-GO)

| Item | Class | Why ready now | Notes |
|---|---|---|---|
| **S04-04 remediation A** | READY | Wiring commit identified | `5e7023f` introduced `app_database_url` / `APP_POSTGRES_*` consumption |
| **S04-04 remediation B** | READY (path choice) | Image promote | GHCR path BLOCKED (CI-08); alternate Railway GitHub build/redeploy |
| **S04-04 remediation A–E** | **Evidence landed** | Prod `9664e9fc` / `salesos_app` / alembic `d1a8` / policies **67** / E bare=0 | Single-tenant caveat residual; tip RLS align via owner SSH |
| **DB-05** Schema reconciliation | IN PROGRESS | Slice 0–3 CLOSED; Slice 4 / criterion 7.5 **CLOSED** (DEC-123a); prod tip `d1a8` / POLICY_COUNT **67** | Residual 7.4 / 7.6; prior “prod on 59” residual cleared (`c842245`) |
| **Optional Jest 30 evidence** | BACKLOG | DEC-108 deferred | STOP silent major |
| **STORY-02-02** browser/E2E | **CLOSED** (DEC-095) | Redirect AC | **CI GREEN not met** |
| **Sprint 04 Category B (B1–B7)** | **CLOSED** (COMPLETE) | DEC-110; B1–B7 CLOSED (DEC-112/114/115/116/117/118/119); live policies **59** | Does not restore Phase 0 GO (DEC-120) |
| **JWT audience consumption** | **CLOSED** (DEC-093) | 14/14 unit PASS | |
| **Contract tests expansion** | IN PROGRESS / PARALLEL | DEC-094 + DEC-106 | Park OK |

---

## DONE / closed (story AC)

| Item | Class | Notes |
|---|---|---|
| **S04-04** Railway R-14 | **REOPENED** (DEC-120) | Was CLOSED DEC-016; contradicted by Tier-1 audit |
| **R-14** Railway | **REOPENED** | Local/CI/compose retained; Railway live isolation not proven |
| **STORY-02-01** (RLS rollout) | **DONE** (revised AC) | DEC-044 @ **47**. **Do not reopen.** |
| **S04-01 / S04-05 / S04-06** | **COMPLETE** | Adversarial suites |
| **CI-16 / CI-20 / CI-19 / CI-22 / CI-14** | **CLOSED** | As previously recorded |
| **Jest-debt** / **R-23** | **CLOSED** | DEC-077 |
| **Security P0 1.3** CSRF X-API-Key | **CLOSED** (DEC-127a) | Arch+Val PASS @ `5db0756`; Phase 0 **22/54**; Security OPEN residual **1.5** |

---

## PARALLEL (safe; Phase 0 still blocked on S04-04)

| Track | Class | Justification |
|---|---|---|
| Contract tests, optional Jest 30, DB-05 7.4/7.6 | PARALLEL / READY | DEC-107 swarm — do not idle on CI-08 alone; Category B B1–B7 COMPLETE (DEC-119); deferred-8 RLS DEC-123; do **not** claim Phase 0 GO |
| Owner Admin / commercial FE | PARALLEL | Must not weaken auth/CSRF/RBAC; must **not** market production GO |

**Swarm dispatch (DEC-107):** Keep agents on independent PARALLEL READY ownership while S04-04 remediation / CI-08/09 ops proceed.

---

## LANDED (master) — adjacency crumbs

| Story / item | SHA | Records status | Validation |
|---|---|---|---|
| DEC-120 Railway R-14 reopen + Principal Audit | *(this land)* | **Accepted / REOPENED** | **docs / light validated** (encodes Tier-1 audit) |
| S04-04 / DEC-016 Railway R-14 (historical close) | `7232979` | **Superseded consequence** | Infra verified; security closure contradicted |
| S04-05 / S04-06 / Category B B1–B7 COMPLETE / CI closes | tip | As prior | See board; Cat B = DEC-119 POLICY_COUNT **59** |

---

## Board progress fraction

**24/25** Complete/Closed on tracked Sprint 05 board fraction (**S04-04 REOPENED**). Adjacent closed: **Jest-debt / R-23**. **Phase 0 critical path blocked:** **S04-04 / Railway R-14**. Also blocked (ops): CI-08 (P0), CI-09 (P2).

---

## Update rule

When a story changes READY↔BLOCKED↔COMPLETE, update this file in the same records commit as `SPRINT_05_DELIVERY_BOARD.md` / `DECISION_LOG.md`. Never claim **production GO** or **CI GREEN** without command evidence. Never reopen STORY-02-01 after DEC-044. Phase 0 (DEC-008) **GO** ≠ production GA GO — and Phase 0 GO is currently **withdrawn** (DEC-120).
