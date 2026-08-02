# Post–Phase 0 Parallel Execution Plan

> **Status:** **ACTIVE** — TRIGGER_POST_PHASE0_PLAN fired 2026-08-02 on tip checklist **54/54** (DEC-155 3.7 CLOSED).  
> **Authority:** `PHASE_0_EXIT_CHECKLIST.md` · `EXECUTION_DAG.md` · `SPRINT_05_DELIVERY_BOARD.md` · `ENGINEERING_ROADMAP.md` · `PRODUCT_ROADMAP.md` · DEC-151 freeze · Continuous Autonomous Mode.  
> **Prepared:** 2026-08-02 (Sprint Program Planner)  
> **Honesty:** This plan does **not** invent 54/54, does **not** close criterion **3.7**, and does **not** claim Production GO / GA GO / Stages 1–7 whole-pipeline green. Phase 0 COMPLETE requires tip score **54/54**. Production GA remains governed by `docs/audit/ga-engineering-audit/` (**production no-go** until GA criteria are independently met).

---

## 0. Launch posture

| Field | Value |
|-------|--------|
| Operating state (now) | `PHASE 1 PARALLEL EXECUTION ACTIVE` |
| Phase 0 tip pin | **54/54 COMPLETE** evidence @ `53a4aa7` (DEC-155 3.7 @ `909230d` / run 30726085801; DEC-154 2.3); Watchdog confirmed; withdraw `a08d7c0` reversed |
| Hard OPEN ⬜ | **none** |
| Sprint 05 delivery board | **26/26** stories Complete/Closed/Governance Completed (**S04-04 CLOSED CONDITIONAL** DEC-154) |
| This plan | **ACTIVE** — Phase 1 parallel streams A/B/C/D launched |
| Production GO | **Not claimed** by this document |

### 0.1 Orchestrator trigger protocol

| Step | Action |
|------|--------|
| Arm | Remain **ARMED** while Score &lt; **54/54**; continue Stream B (**3.7**) chase |
| Gate | Trigger **only** on true tip checklist **54/54** (all hard ⬜ closed + Open cells **0** with evidence — see §0 Trigger + §5). **No fake 54/54.** |
| Fire | On gate pass: Orchestrator **immediately** spawns Backend / Frontend / DevOps / Validation streams per §4 **without waiting for human approval** |
| Records | Same wave: board + DAG + checklist crumbs; this file ARMED → **ACTIVE**; launch crumb *“Phase 0 COMPLETE — post-54/54 parallel execution STARTED”* |
| Hold | Abort if invent CLOSE, Open cells remain, or Production GO language appears in exit crumbs |

**Trigger (all must be true):**

1. Tip `PHASE_0_EXIT_CHECKLIST.md` Operating State `Score = 54/54` with evidence crumbs.  
2. Criterion **3.7** = ✅ VERIFIED/CLOSED (tip Stage 7 / Playwright E2E SUCCESS with real backend services — not local-only green).  
3. Scoreboard Open cells = **0** (including **2.3** residual disposition — see §3).  
4. Orchestrator / Validation records land on board + DAG + checklist in the same records wave.  
5. Explicit launch crumb: *“Phase 0 COMPLETE — post-54/54 parallel execution STARTED”* (this file flips ARMED → **ACTIVE**).

**TRIGGER_POST_PHASE0_PLAN FIRED (2026-08-02):** Watchdog confirmed. Evidence Stage 7 [https://github.com/ragheeda-boop/SalesOS/actions/runs/30726085801](https://github.com/ragheeda-boop/SalesOS/actions/runs/30726085801) SUCCESS @ `909230d`. Phase 0 checklist **54/54** @ `53a4aa7`. Operating State → **PHASE 1 PARALLEL EXECUTION ACTIVE**. Launch crumb [`PHASE1_STREAM_LAUNCH_CRUMB.md`](PHASE1_STREAM_LAUNCH_CRUMB.md). Streams A/B/C/D ACTIVE. Premature withdraw `a08d7c0` reversed. **Production GO still not claimed.**

---

## 1. Sprint map summary (inventory)

Two naming systems coexist — do not conflate them.

### 1.1 Calendar program (26 sprints) — `docs/program/SPRINT_PLAN/`

| Sprint | Phase | Goal (abbrev.) | Status | Evidence |
|--------|-------|----------------|--------|----------|
| **01** | 0 | P0 security bleed stop; CI groundwork | **DONE** | `SPRINT_PLAN/Sprint-01.md` CLOSED 2026-07-30; closure report under ga-engineering-audit |
| **02** | 0 | Remaining P0 + regression harness | **DONE** | `Sprint-02.md` CLOSED 2026-07-31 |
| **03** | 0 | RLS / middleware / JWT / contracts | **DONE (stories)** / Phase 0 exit **BLOCKED** | `Sprint-03.md`: STORY-02-01..03-04 DONE; Phase 0 critical path still NO-GO |
| **04** | 1 | Tenant extension + provisioning | **NOT STARTED** (feature) | `Sprint-04.md`: STORY-04-01/04-02 not implemented; S04-02 CI triage only |
| **05** | 1 | Suspend/delete + subscription SM | **NOT STARTED** | `Sprint-05.md` (calendar — not the delivery board) |
| **06** | 1 | Stripe sandbox + metering | **NOT STARTED** | `Sprint-06.md` |
| **07** | 1 | Dunning / entitlements / Alpha gate | **NOT STARTED** | `Sprint-07.md` |
| **08–11** | 2 | Integration Hub + Odoo | **NOT STARTED** | `Sprint-08.md`…`Sprint-11.md` |
| **12–15** | 3 | Tenant Studio | **NOT STARTED** | `Sprint-12.md`…`Sprint-15.md` |
| **16–19** | 4 | GTM Intelligence | **NOT STARTED** | `Sprint-16.md`…`Sprint-19.md` |
| **20–22** | 5 | AI Studio + Marketplace | **NOT STARTED** | `Sprint-20.md`…`Sprint-22.md` |
| **23–25** | 6 | Hardening / RC | **NOT STARTED** | `Sprint-23.md`…`Sprint-25.md` |
| **26** | 7 | GA cutover (terminal) | **NOT STARTED** | `Sprint-26.md` |

Index: `ENGINEERING_ROADMAP.md` (Phase 0 = S01–03; Phase 1 = S04–07 → Alpha).

### 1.2 Sprint 05 Enterprise Delivery Board (operational Phase 0 package)

Canonical living board: `docs/program/SPRINT_05_DELIVERY_BOARD.md`.

| Class | IDs | Status |
|-------|-----|--------|
| Complete / Closed | CI-01…CI-07, CI-10…CI-22, S04-01, S04-05, S04-06, DB-05, compose prod name, Jest-debt (adjacent) | **DONE** |
| Governance Completed | CI-08 (DEC-150 B) | **DONE (governance)** — field GHCR 403 legacy/non-blocking |
| Closed Conditional | CI-09 (DEC-149a) | **DONE CONDITIONAL** |
| Reopened residual | **S04-04** Railway R-14 | **REOPENED** (DEC-120) — maps to checklist **2.3 CLOSED CONDITIONAL** multi-tenant residual; board fraction still **26/26** |

**Rule:** Sprint success for Phase 0 exit = checklist criteria CLOSED (**54/54**), **not** board story count. Board **26/26 ≠ Phase 0 COMPLETE**.

### 1.3 Execution DAG + PRODUCTION_PLAN waves

| Artifact | Role | Status vs Phase 0 |
|----------|------|-------------------|
| `EXECUTION_DAG.md` | READY / BLOCKED / PARALLEL classification | Hard OPEN chase = **3.7**; Phase 0 **53/54 NO-GO** |
| `PHASE_0_EXIT_CHECKLIST.md` | Authoritative 54-criterion scoreboard | Tip pin **53/54** |
| `docs/audit/ga-engineering-audit/PRODUCTION_PLAN.md` Waves 0–14 | GA engineering remediation waves | **Orthogonal** — does not auto-clear on 54/54; Production GO still audit-governed |
| Wave 0–2 (build/security) | Partially absorbed into Phase 0 / CI board | Do not re-open closed Security P0 without evidence |
| Waves 3–14 | Test green → hypercare | Resume as Phase 1+ / GA track after 54/54 — **no Production GO claim from Phase 0 exit alone** |

---

## 2. Where we stopped (stop point)

Pinned from tip checklist / board / DAG (2026-08-02):

```
STATE   = CONTINUOUS AUTONOMOUS MODE — FREEZE COMPLIANT
         + ARMED FOR POST-54/54 PARALLEL SPRINT EXECUTION
Score   = 51/54 NO-GO (tip 8600f68; NOT 54/54)
Hard ⬜ = 3.7 Stage 7 E2E (sole hard OPEN)
Freeze  = DEC-151 (Architecture FROZEN · Governance FROZEN · AI Runtime DEFERRED)
Deploy  = DEC-149 Railway+Vercel · DEC-150 B Stage 6 GHCR retired
Streams = A 3.9 CLOSED CONDITIONAL (DEC-152)
          B 3.7 ACTIVE chase
          C 4.1/4.8 CLOSED (DEC-153 ARB PASS)
          D QUEUED freeze-compliant backlog
Post54  = ARMED (this plan — trigger ≠ fire)
Board   = 26/26 stories (S04-04 REOPENED residual)
```

Evidence paths:

- Checklist: `docs/program/PHASE_0_EXIT_CHECKLIST.md` (Operating State + Summary **51** Complete / **2** Open / **54** total)  
- Board: `docs/program/SPRINT_05_DELIVERY_BOARD.md` (Progress crumbs DEC-151…153)  
- DAG: `docs/program/EXECUTION_DAG.md`  
- DEC-153: `docs/program/decisions/DEC-153-CRITERION-4-1-4-8-ARB-REAUDIT-PASS.md`  
- DEC-152: `docs/program/decisions/DEC-152-CRITERION-3-9-CI-GREEN-TOPOLOGY-FIELD-VERIFY.md`  
- DEC-151: `docs/program/decisions/DEC-151-PHASE-0-GOVERNANCE-FREEZE.md`  
- Stage 7 chase: standalone `.github/workflows/e2e-stage7.yml` + harden crumbs (`d973cba` / tip series)

**Start method (current, pre-54/54):** Continuous Autonomous loop under DEC-151 — identify next hard OPEN → assign DevOps/Backend → field-verify tip Stage 7 → land crumbs → push. **Do not invent CLOSE.**

---

## 3. Gap to 54/54 (scoreboard math)

| Item | Tip status | Counts as Complete? | Action to reach 54/54 |
|------|------------|---------------------|------------------------|
| **3.7** Stage 7 E2E | ⬜ **OPEN** (hard) | **No** | **Must CLOSE** with tip Stage 7 SUCCESS + real services |
| **2.3** R-14 Railway multi-tenant residual | ✅ CLOSED **CONDITIONAL** but scoreboard **Open** | **No** (special case) | Dispose Open cell: (a) multi-tenant live re-proof → unconditional, **or** (b) ARB/Orchestrator accept CONDITIONAL as Complete for Phase 0 exit with residual logged |
| Other CLOSED CONDITIONAL (1.5, 3.5, 3.8, 3.9, 3.11, 8.2, 8.3) | ✅ | **Yes** (already in Complete) | Residuals non-blocking; do **not** reopen as hard ⬜ |
| 3.6 / 3.10 SUPERSEDED | ✅ | **Yes** | Leave retired (DEC-150 B) |
| 4.1 / 4.8 | ✅ CLOSED | **Yes** | DEC-153 — do not reopen |

**Arithmetic honesty:** Summary row pins Complete **51** + Open **2** (= **53**) against denominator **54**. Cluster column sum of Completes = **52** + Open **2** = **54**. On exit, Validation **must reconcile** TOTAL Complete to **54** with Open **0** — do not invent a point; fix counting when 3.7 and 2.3 Open dispositions land.

**What still must CLOSE (minimum):**

1. Hard: **3.7** tip Stage 7 E2E green.  
2. Scoreboard: **2.3** Open cell disposition (upgrade or ARB accept).  
3. Records: flip Operating State Score → **54/54**, Open → **0**, Phase 0 COMPLETE crumb — **without** Production GO language unless GA audit criteria separately pass.

---

## 4. Post-54/54 Parallel Execution Plan (first 48–72h)

Activate only after §0 trigger. Goal: start **Phase 1 — Owner Platform Core** (calendar Sprint **04**) with continuous parallel streams and no idle capacity (DEC-107 swarm).

### 4.1 Workstreams

#### A — Backend (Owner Platform core)

| # | First 48–72h task | Depends |
|---|-------------------|---------|
| A1 | Pre-task package for **STORY-04-01** Tenant extension (`plan_id` / `region` / `data_residency` / `provisioning_status` / `trial_ends_at`) | Phase 0 COMPLETE |
| A2 | Alembic migration draft + local Docker upgrade/downgrade proof (non-prod) | A1 approved |
| A3 | Pre-task package for **STORY-04-02** idempotent provisioning workflow skeleton | A1 schema direction stable |
| A4 | Confirm JWT owner-audience consumption still green (DEC-093) after tenant schema touch | A2 |
| A5 | Parked contract expansion (DEC-094/106) only if disjoint files | None (parallel) |

**Do not:** weaken RLS / DEC-085 `set_config` / CSRF / RBAC. New tenant-adjacent tables inherit Category-A RLS pattern before merge.

#### B — Frontend

| # | First 48–72h task | Depends |
|---|-------------------|---------|
| B1 | Inventory Owner Console / admin surfaces touching Tenant model | Phase 0 COMPLETE |
| B2 | Minimal FE read-path stubs for new tenant fields (no fake GA AI) | A1 field contract |
| B3 | Keep `feature_ai_copilot` default **False**; Decision package remains STUB | Standing rule |
| B4 | Optional: PRODUCTION_PLAN Wave 0 FE lint/tsc holdouts **only if** already blocking Sprint 04 FE — separate story, explicit approval for heavy npm | Human approval |

#### C — DevOps / CI

| # | First 48–72h task | Depends |
|---|-------------------|---------|
| C1 | Keep DEC-149 Railway+Vercel deploy green on tip after Phase 0 exit land | Tip push |
| C2 | Protect Stage 7 E2E from docs-push cancel (standalone workflow retention) | Standing |
| C3 | Staging remains deferred (single-env DEC-149) unless ARB unfreezes topology | DEC-151 lift |
| C4 | Legacy GHCR 403 = tech debt backlog — **not** Phase 1 blocker | — |

#### D — Validation

| # | First 48–72h task | Depends |
|---|-------------------|---------|
| D1 | Field-verify Phase 0 COMPLETE records (54/54, 3.7 CLOSED, Open 0) | Trigger fire |
| D2 | Baseline tip CI Stages 1–5 + Deploy Prod after exit land | Tip SHA |
| D3 | Adversarial RLS suites still PASS after tenant schema migration | A2 |
| D4 | Honest labels only: build validated / light validated / not validated | Standing |

#### E — Docs / Program

| # | First 48–72h task | Depends |
|---|-------------------|---------|
| E1 | Flip this plan ARMED → **ACTIVE**; board + DAG + checklist crumbs | Trigger |
| E2 | Open calendar Sprint 04 delivery tracking (or extend board with S04-calendar stories — do not overload Phase 0 board semantics) | E1 |
| E3 | RISK_REGISTER: open Phase 1 risks (billing R-05, etc.) as READY | E1 |
| E4 | DECISION_LOG: Phase 0 COMPLETE accepted + Phase 1 start authorized | D1 |

### 4.2 Dependencies / order

```text
[54/54 tip evidence]
        │
        ▼
 Validation D1 ──► Docs E1/E4 (Phase 0 COMPLETE records)
        │
        ├──────────────┬────────────────┬─────────────────
        ▼              ▼                ▼
   Backend A1     Frontend B1      DevOps C1 (observe tip)
        │              │
        ▼              ▼
   Backend A2 ◄── contract with FE B2
        │
        ▼
   Backend A3 (provisioning) + Validation D3 (RLS)
        │
        ▼
   Continuous DEC-107 parallel READY (≥2–3 agents) on Sprint 04/05 backlog
```

**Critical path after exit:** A1 → A2 → A3 (Tenant → provision). FE/DevOps/Docs run **parallel** once E1 fires.

### 4.3 Freeze vs unfreeze after Phase 0 exit

| Remains frozen / deferred | Unfrozen on 54/54 |
|---------------------------|-------------------|
| Production GA / External pilot GO claims (audit still **no-go** until GA criteria) | Phase 1 Owner Platform stories (calendar S04+) |
| AI Runtime / Agent OS (`.ai/` runtime) until DEC-146 triggers | Feature work gated only by Phase 0 before |
| Reopening GHCR as mandatory gate without ARB | Continuous Autonomous → **Phase 1 delivery mode** (rename Operating State) |
| Deploy topology superseding DEC-149 without ARB | Field work on Railway+Vercel under DEC-149 |
| Weakening auth/CSRF/RBAC/RLS/audit | Normal bugfix + evidence crumbs |
| Claiming Stages 1–7 green without tip evidence | Closing CONDITIONAL residuals that become Phase 1 tech debt |

**DEC-151:** Governance freeze intent was Phase 0 residual closure. On 54/54, freeze **lifts for Phase 1 delivery**; architecture still requires ADR/ARB for topology or org redesign. Do not treat freeze lift as Production GO.

### 4.4 Explicit non-claims

- Phase 0 COMPLETE ≠ Production GO ≠ GA GO ≠ External pilot GO.  
- Board 26/26 ≠ Phase 0 COMPLETE.  
- CLOSED CONDITIONAL residuals may remain as Phase 1 tech debt without upgrading to unconditional.  
- ga-engineering-audit `PRODUCTION_PLAN` Waves continue as a **separate** GA track.

---

## 5. Launch trigger checklist (when 54/54 fires)

Copy/paste for Orchestrator. **On gate pass: spawn streams immediately — do not wait for human.**

- [x] Tip Stage 7 job **SUCCESS** (named run URL + SHA) → close **3.7**  
- [x] Checklist **3.7** cell = ✅ VERIFIED/CLOSED with evidence  
- [x] **2.3** Open cell disposed (unconditional **or** ARB accept CONDITIONAL as Complete)  
- [x] Summary: Complete **54** / Open **0** / Blocked **0** (arithmetic reconciled)  
- [x] Operating State Score = **54/54**; Phase 0 = COMPLETE (NO Production GO language)  
- [x] Board + DAG + DECISION_LOG crumbs landed + pushed  
- [x] This file status → **ACTIVE**; first crumbs for STORY-04-01 pre-task package  
- [x] Spawn Backend / Frontend / DevOps / Validation streams per §4 (≥2–3 PARALLEL READY: A1, B1, C1 observe, D2) **without human wait**  
- [x] Confirm DEC-085 / auth / CSRF / RLS untouched by exit land  
- [x] Confirm AI copilot flag still default False  

**Abort / hold:** If 3.7 flips without tip evidence, or Open cells remain, or Production GO language appears in exit crumbs — **do not** start Phase 1 under this plan.

---

## 6. References

| Doc | Path |
|-----|------|
| Phase 0 checklist | `docs/program/PHASE_0_EXIT_CHECKLIST.md` |
| Delivery board | `docs/program/SPRINT_05_DELIVERY_BOARD.md` |
| Execution DAG | `docs/program/EXECUTION_DAG.md` |
| Sprint plans | `docs/program/SPRINT_PLAN/Sprint-01.md` … `Sprint-26.md` |
| Engineering roadmap | `docs/program/ENGINEERING_ROADMAP.md` |
| Product roadmap | `docs/program/PRODUCT_ROADMAP.md` |
| GA production plan | `docs/audit/ga-engineering-audit/PRODUCTION_PLAN.md` |
| Freeze | `docs/program/decisions/DEC-151-PHASE-0-GOVERNANCE-FREEZE.md` |

---

*Plan ACTIVE. Phase 1 parallel execution authorized. No Production GO.*
