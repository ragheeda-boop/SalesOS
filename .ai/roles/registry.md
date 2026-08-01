# Role Registry

> **Purpose:** Central index of all **permanent roles** in the SalesOS engineering organization.
> **Reads with:** Individual role contracts under [`./`](./) and runtime bindings in [`../runtime/agent-bindings.yaml`](../runtime/agent-bindings.yaml).
> **Governed by:** ADR-036 (Layer Separation), EEC-001 (Execution Contract), `21_RUNTIME_STATE.json`.
> **Migration:** Engine-named contracts under `.ai/agents/` were replaced by role-named contracts (2026-08-01). Engines are assigned **only** via `agent-bindings.yaml`.

---

## Permanent roles (exactly four)

| Role | ID | Layer | Owner of | Contract | Execution Cycle |
|------|-----|-------|----------|----------|-----------------|
| Backend Lead | `backend-lead` | Implementation | `salesos/backend/` | [`backend-lead.md`](backend-lead.md) | Implement |
| Architecture Reviewer | `architecture-reviewer` | Review | Architecture review + `salesos/frontend/` | [`architecture-reviewer.md`](architecture-reviewer.md) | Review |
| Engineering Validator | `engineering-validator` | Validation + Infrastructure + Engineering Spec | `.github/workflows/`, `salesos/infra/`, `.engineering/` | [`engineering-validator.md`](engineering-validator.md) | Validate |
| Execution Orchestrator | `execution-orchestrator` | Coordination | Coordination records only (`21_RUNTIME_STATE.json`, `22_FILE_LOCKS.json`, `20_NEXT_READY.md`, `EXECUTION_DAG.md`) | [`execution-orchestrator.md`](execution-orchestrator.md) | Coordinate |

Engine assignment for each role is **not** listed here. See [`.ai/runtime/agent-bindings.yaml`](../runtime/agent-bindings.yaml).

The **Execution Orchestrator** is coordination-only: it drives the execution loop and the Execution State Machine, but never writes production code, reviews architecture, validates evidence, or overrides another role's domain authority.

**No additional permanent roles may be created.** Temporary workers are unlimited and disposable — see [`../docs/WORKER_EXECUTION.md`](../docs/WORKER_EXECUTION.md).

---

## Role Capability Matrix

| Capability | Backend Lead | Architecture Reviewer | Engineering Validator | Orchestrator | Human |
|------------|--------------|----------------------|----------------------|--------------|-------|
| Backend code (modules, domains, runtime) | **Owner** | — | — | — | Approve |
| Frontend code (pages, features, packages) | — | **Owner** | — | — | Approve |
| CI/CD workflows | — | — | **Owner** | — | Approve |
| Infrastructure (k8s, terraform, compose) | — | — | **Owner** | — | Approve |
| DB migrations | **Owner** | — | Consult | — | Approve |
| E2E tests | — | **Owner** | — | — | — |
| Security fixes | **Implement** | — | Scan | — | **Approve** |
| Architecture decisions (ADRs) | Consult | Consult | Consult | Escalate | **Owner** |
| GA posture / release approval | — | — | — | — | **Owner** |
| Capability registry | Shared | Shared | Index | — | **Approve** |
| Implement Code | ✅ | ❌ | ❌ | ❌ | — |
| Review Architecture | ❌ | ✅ | ❌ | ❌ | — |
| Validate Evidence | ❌ | ❌ | ✅ | ❌ | — |
| Select Next Criterion | ❌ | ❌ | ❌ | ✅ | — |
| Detect Blockers | ⚠️ | ⚠️ | ⚠️ | ✅ | — |
| Update Runtime State | ❌ | ❌ | ❌ | ✅ | — |
| Coordinate Execution | ❌ | ❌ | ❌ | ✅ | — |
| Spawn temporary workers | ⚠️ | ⚠️ | ⚠️ | ✅ | — |
| Override Decisions | ❌ | ❌ | ❌ | ❌ | — |

---

## State Authority (official reference)

Official mapping of which **role** owns each execution state. No role may change a state outside its authority. States match the Execution State Machine in [`execution-orchestrator.md`](execution-orchestrator.md).

| State | Authority |
|-------|-----------|
| OPEN | Execution Orchestrator |
| QUEUED | Execution Orchestrator |
| ASSIGNED | Execution Orchestrator |
| IN_PROGRESS | Backend Lead |
| READY_FOR_REVIEW | Backend Lead |
| ARCHITECTURE_PASS | Architecture Reviewer |
| VALIDATION_PASS | Engineering Validator |
| VERIFIED | Execution Orchestrator |
| CLOSED | Execution Orchestrator |
| BLOCKED | Execution Orchestrator |

> Mapping note: `READY_FOR_REVIEW`, `ARCHITECTURE_PASS`, and `VALIDATION_PASS` are the review/validation stages of the state machine (`UNDER_ARCHITECTURE_REVIEW` → `UNDER_VALIDATION`). This table is the authoritative owner-of-state reference.

---

## Operating Constraints (from EEC-001)

All roles (and their temporary workers) are bound by:

1. **Exit Traceability** — Every story must close a Phase 0 Exit Criterion.
2. **PR Traceability** — Every PR names the criterion, files, evidence, validation, risk, rollback.
3. **Definition of Done** — Implemented → Tested → Reviewed → Criterion Updated → Evidence Recorded.
4. **Freeze Exceptions** — Architecture changes only for Phase 0 bug fixes or formal ARB decision.
5. **Weekly Review** — Progress = number of criteria CLOSED, not stories completed.

---

## Parallel Safety

Two roles (or their workers) may work concurrently when their owned paths do not overlap.

| Pair | Safe? | Notes |
|------|-------|-------|
| Backend Lead + Architecture Reviewer | ✅ | Backend ≠ Frontend, disjoint file sets |
| Backend Lead + Engineering Validator | ⚠️ | Check: backend code vs CI config (usually disjoint) |
| Architecture Reviewer + Engineering Validator | ⚠️ | Check: frontend code vs CI config (usually disjoint) |

Shared paths (capability registry, platform packages) require serialization via locks.

See also parallel worker patterns in [`../docs/WORKER_EXECUTION.md`](../docs/WORKER_EXECUTION.md) and [`../docs/PARALLEL_EXECUTION.md`](../docs/PARALLEL_EXECUTION.md).

---

## Escalation Path

```
Role / worker cannot resolve / conflict
        ↓
Execution Orchestrator (conflict escalator, never decides for others)
        ↓
Check ADR / EEC-001 / Phase 0 Checklist
        ↓
Escalate to Human (CTO / ARB)
```

No role may override ADR-036, EEC-001, or Baseline v1.0 without formal ARB resolution.

---

## Related

- `.ai/runtime/agent-bindings.yaml` — Engine bindings (only place engines are assigned)
- `.ai/runtime/runtime-spec.yaml` — Future runtime specification (not an engine)
- `.ai/docs/EXECUTION_LIFECYCLE.md` — Official criterion cycle
- `.ai/docs/WORKER_EXECUTION.md` — Temporary workers (namespaced)
- `.ai/docs/PARALLEL_EXECUTION.md` — Parallel spawn patterns
- `.engineering/09_OWNERSHIP_MAP.md` — Code ownership matrix
- `.engineering/26_AGENT_COORDINATION.md` — Coordination protocol
- `.engineering/31_AI_TASK_ROUTING.md` — Task dispatch rules
- `.engineering/21_RUNTIME_STATE.json` — Live operating state
- `docs/program/PHASE_0_EXIT_CHECKLIST.md` — Current objectives
- `docs/adr/0036-engineering-organization-layer-separation.md` — ADR-036
- `.ai/AI_ORGANIZATION_MIGRATION_REPORT.md` — Migration record
