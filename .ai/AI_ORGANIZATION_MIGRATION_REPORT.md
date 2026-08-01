# AI Organization Migration Report

> **Date:** 2026-08-01  
> **Agent:** AI Organization Migration Agent  
> **Scope:** Organizational refactor of `.ai/` only  
> **Out of scope:** Production code, APIs, infrastructure, application behavior  
> **Architecture:** ADR-036 frozen (compliant)

---

## Mission result

| Goal | Status |
|------|--------|
| Rename engine contracts → role contracts | **DONE** |
| Create `.ai/runtime/agent-bindings.yaml` | **DONE** |
| Update internal references | **DONE** |
| Worker Architecture documentation | **DONE** |
| Parallel Execution documentation | **DONE** |
| Migration report (this file) | **DONE** |
| Exactly four permanent roles | **DONE** |
| No broken links (stubs + registry) | **DONE** |

---

## Before → After

| Before (engine-named) | After (role-named) |
|-----------------------|--------------------|
| `.ai/agents/cursor.md` | `.ai/roles/backend-lead.md` |
| `.ai/agents/claude-code.md` / `CLAUDE.md` | `.ai/roles/architecture-reviewer.md` |
| `.ai/agents/opencode.md` | `.ai/roles/engineering-validator.md` |
| `.ai/agents/execution-orchestrator.md` | `.ai/roles/execution-orchestrator.md` |
| `.ai/agents/registry.md` | `.ai/roles/registry.md` |

Former paths under `.ai/agents/` are **redirect stubs** only (no duplicated contract bodies).

---

## Engine bindings (sole assignment surface)

File: [`.ai/runtime/agent-bindings.yaml`](runtime/agent-bindings.yaml)

| Role ID | Engine |
|---------|--------|
| `backend-lead` | `cursor` |
| `architecture-reviewer` | `claude` |
| `engineering-validator` | `opencode` |
| `execution-orchestrator` | `deepseek` |

Contracts no longer encode engine identity as the organizational name. Swapping an engine is a bindings edit only.

---

## Permanent roles vs temporary workers

- **Permanent (4):** Backend Lead, Architecture Reviewer, Engineering Validator, Execution Orchestrator  
- **Temporary:** Unlimited task-scoped workers; inherit parent contract + binding; never permanent; auto-terminate  

Docs:

- [`.ai/docs/WORKER_EXECUTION.md`](docs/WORKER_EXECUTION.md)  
- [`.ai/docs/PARALLEL_EXECUTION.md`](docs/PARALLEL_EXECUTION.md)  

---

## References updated

| Location | Change |
|----------|--------|
| `.engineering/21_RUNTIME_STATE.json` | `agent_registry` → `.ai/roles/registry.md`; added `agent_bindings`; parallel group labels use role names |
| `.ai/README.md` | New index |
| `.ai/agents/*` | Redirect stubs |

No `salesos/` application or workflow files were modified for this migration.

---

## ADR-036 compliance

- `.ai/` remains the AI Runtime organization layer (not merged into `.engineering/` or `docs/program/`).  
- Full scheduler/dispatcher runtime remains **deferred**; this migration only installs **role contracts + bindings + worker docs**.  
- Four-layer separation unchanged.  
- Engine-swappable consequence of ADR-036 §Consequences is now explicit via `agent-bindings.yaml`.

---

## Success criteria checklist

- [x] Engineering Organization contains 4 permanent roles  
- [x] Unlimited temporary workers (documented)  
- [x] Engine-independent contracts  
- [x] Parallel execution documented  
- [x] No broken references (stubs + registry links)  
- [x] Architecture remains compliant with ADR-036  

---

## v2 follow-ups (post-review)

| Addition | Path |
|----------|------|
| Runtime specification (not an engine) | `.ai/runtime/runtime-spec.yaml` |
| Official execution lifecycle | `.ai/docs/EXECUTION_LIFECYCLE.md` |
| Namespaced workers (`backend/api-worker`, …) | `.ai/docs/WORKER_EXECUTION.md` + `PARALLEL_EXECUTION.md` |
| `.ai/` Architecture Frozen | `.ai/README.md` + `runtime-spec.yaml` |

From this point, treat `.ai/` like `.engineering/`: **frozen** except Phase 0 criterion closure or organizational defect fixes.

---

## Validation

**docs only / not validated** against live multi-engine runtime (runtime still deferred).  
**Production GO / CI GREEN:** not claimed (out of scope).
