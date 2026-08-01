# DEC-145 — Agent coordination protocol exercised (Phase 0 criterion 8.2)

> **Status:** **Accepted** — Cursor packaging **COMPLETE** · Criterion 8.2 = **VERIFIED/CLOSED CONDITIONAL** (DEC-145a; Arch PASS_CONDITIONAL + Val PASS_CONDITIONAL). Residual: *at-scale live soak at `max_parallel_workers=8` concurrent writers not field-proven*.  
> **Date:** 2026-08-01  
> **Board:** Backend Lead / Engineering Stability (SalesOS / AQLIYA) — api-worker land  
> **Story / risk:** Phase 0 Exit Criterion **8.2** · Agent coordination protocol exercised  
> **Authority:** PHASE_0_EXIT_CHECKLIST §8.2 · DEC-107 · DEC-144 residual · `.engineering/26_AGENT_COORDINATION.md` · ARB-2026-08-01-003 (`.ai/` baseline)  
> **Out of scope this land:** inventing Agent OS scheduler · EOS **4.1/4.8** ARB · CI-08/CI-09 ops · auth/CSRF weaken · DEC-085 · Production GO · CI GREEN · Phase 0 exit · unconditional CLOSED · VERIFIED/CLOSED (Orchestrator only)

---

## 1. Decision

Resolve criterion **8.2** by landing an **honest coordination protocol evidence package** (max agents, namespacing, conflict rules) and committing the previously untracked `.ai/` organization baseline. Do **not** claim multi-agent soak “at scale.”

| Gate element | As-built |
|---|---|
| Max permanent roles | **4** (ARB freeze) |
| Max parallel temporary workers | **8** (`runtime-spec.yaml` → `max_parallel_workers`; was `auto`) |
| Min / prefer READY while ops wait | **2** / **3** (DEC-107) |
| Max agents total | **12** (≤4 + ≤8) |
| Namespacing | Mandatory `parent-domain/task` (`.ai/docs/WORKER_EXECUTION.md`) |
| Conflict rules | Locks (`22`), one-path ownership, TenantList/security leave-alone, Orchestrator serialize on cap breach (`.engineering/26_AGENT_COORDINATION.md` + `.ai/docs/PARALLEL_EXECUTION.md`) |
| Org contracts committed | `.ai/` tree (roles, bindings, runtime-spec, lifecycle, workers, parallel docs) |

### Gate definition (honest)

| Check | Pass? |
|---|---|
| Explicit `max_agents` / worker caps in repo | **Yes** — closes DEC-107 “no max_agents cap” diagnosis gap |
| Namespaced worker protocol documented | **Yes** |
| Conflict / lock / ownership rules documented | **Yes** |
| `.ai/` org baseline tracked (not only local) | **Yes** this land |
| Light exercise evidence (parallel Phase 0 + namespaced workers in `21`) | **Yes** — light |
| Multi-agent parallel work **at scale** (soak at cap) | **No** — residual CONDITIONAL |
| Full Agent OS scheduler / queue | **No** — still DEFERRED (9.3) |
| Production GO / CI GREEN / VERIFIED/CLOSED | **No** |

**Not claimed:** Production GO · CI GREEN · Phase 0 exit · unconditional CLOSED · closing 4.1 / 4.8 · inventing ARB PASS.

---

## 2. Alternatives considered

| Option | Verdict |
|---|---|
| (a) Docs-only checklist note without caps / without committing `.ai/` | Rejected — leaves DEC-107 gap + protocol untracked |
| (b) Claim VERIFIED/CLOSED / “tested at scale” | Rejected — no soak evidence at worker ceiling |
| (c) Invent running scheduler / fifth permanent role | Rejected — ADR-036 / ARB freeze / 9.3 |
| (d) Pin caps + conflict rules + commit `.ai/`; READY FOR REVIEW CONDITIONAL | **Approved** |

---

## 3. Validation

| Check | Result |
|---|---|
| Caps present in `runtime-spec.yaml` | `max_parallel_workers: 8`, `min_parallel_ready: 2`, `prefer_parallel_ready: 3`, `max_agents_total: 12` |
| Namespacing docs | `.ai/docs/WORKER_EXECUTION.md` + PARALLEL_EXECUTION caps section |
| Conflict protocol | `.engineering/26_AGENT_COORDINATION.md` §0–§5 |
| Light exercise | DEC-107 swarm through Phase 0 parallel closes; `21_RUNTIME_STATE.json` lists namespaced workers; this land = `backend/api-worker` |
| At-scale soak | **not validated** |
| Auth / DEC-085 | **Untouched** |
| Label | **light validated** (docs + tree commit evidence); at-scale **not validated** |

**Production GO not claimed. CI GREEN not met.**

---

## 4. Records

- Phase 0 criterion **8.2** → **VERIFIED/CLOSED CONDITIONAL** (DEC-145a; Phase 0 **41/54 → 42/54**)
- Eng Stability: Complete **3 → 4** / Open **1 → 0** (cluster **COMPLETE 4/4**)
- Residual (non-blocking for CONDITIONAL close): *at-scale live soak at `max_parallel_workers=8` concurrent writers not field-proven*
- Cluster residuals: EOS **4.1** / **4.8** ARB · CI-08/CI-09 ops · 8.3 tip `test-architecture` PENDING push
- **Not claimed:** Production GO · CI GREEN · Phase 0 exit · unconditional CLOSED

---

## 5. Evidence Package

| ID | Artifact | Location |
|----|----------|----------|
| EV-001 | Caps + parallel policy | `.ai/runtime/runtime-spec.yaml` |
| EV-002 | Worker namespacing | `.ai/docs/WORKER_EXECUTION.md` |
| EV-003 | Parallel + conflict rules | `.ai/docs/PARALLEL_EXECUTION.md` |
| EV-004 | Engineering coordination | `.engineering/26_AGENT_COORDINATION.md` |
| EV-005 | Swarm always-on READY | `docs/program/decisions/DEC-107-SWARM-ALWAYS-ON-PARALLEL-READY.md` |
| EV-006 | Role contracts + bindings | `.ai/roles/` · `.ai/runtime/agent-bindings.yaml` |
| EV-007 | This DEC | `docs/program/decisions/DEC-145-CRITERION-8-2-AGENT-COORDINATION.md` |
| EV-008 | Checklist / board / DAG crumbs | `PHASE_0_EXIT_CHECKLIST.md` · `SPRINT_05_DELIVERY_BOARD.md` · `EXECUTION_DAG.md` · `DECISION_LOG.md` |

---

## 6. Rollback

| Step | Action |
|------|--------|
| 1 | Revert land commit (`.ai/` + docs/protocol crumbs) |
| 2 | Criterion 8.2 returns OPEN / “Not tested at scale” |
| Expected impact | Caps/`max_agents` gap reopens; org contracts untracked again |

---

## 7. Risk

| Surface | Level | Note |
|---------|-------|------|
| At-scale soak residual | MED | CONDITIONAL close only; do not auto-upgrade on docs alone |
| Overclaim scheduler live | LOW | runtime-spec status remains SPECIFICATION; 9.3 deferred intact |
| Overclaim Production GO / CI GREEN | LOW | Explicitly excluded |
| Bridge wording vs 9.3 | LOW | Org baseline vs full runtime distinguished in layer bridges |

---

## 8. Architecture next?

| Question | Recommendation |
|---|---|
| Close 8.2? | **CLOSED CONDITIONAL** via DEC-145a (at-scale soak residual retained) |
| Next PARALLEL | EOS **4.1/4.8** ARB (only if executable without inventing ARB) · optional 8.3 tip field-verify after push · ops CI-08/09 |
| Do not | Claim Phase 0 GO · CI GREEN · unconditional CLOSED · invent Agent OS runtime · weaken auth / DEC-085 |
