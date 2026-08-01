# AI Organization & Coordination (`.ai/`)

> **Baseline:** [`VERSION`](VERSION) → `ai_organization: 1.0.0`  
> **ARB:** `ARB-2026-08-01-003` — AI Organization Baseline v1.0 **APPROVED** · Architecture **FROZEN** · Execution **ACTIVE** · Further organizational changes **REJECTED**
>
> AI Engineering Organization layer (ADR-036). Full scheduler/dispatcher **runtime** remains deferred; **role contracts + bindings + specs** are active.
>
> **Architecture Frozen:** Do not modify `.ai/` unless the change closes a criterion in `PHASE_0_EXIT_CHECKLIST.md` or fixes an organizational defect.
>
> **Criterion 9.3 (DEC-146):** Org baseline ≠ live Agent OS. Full runtime stays **DEFERRED** until ADR-036 trigger conditions (Phase 0 54/54 · CI GREEN · EOS ARB 4.1/4.8 PASS · drift still closed · formal ARB Phase 3 authorize). See [`docs/adr/0036-engineering-organization-layer-separation.md`](../docs/adr/0036-engineering-organization-layer-separation.md) §`.ai/` Runtime deferral.

## Golden boot order (every agent)

```text
1. docs/program/PHASE_0_EXIT_CHECKLIST.md
        ↓
2. .engineering/21_RUNTIME_STATE.json
        ↓
3. .ai/roles/<role>.md
        ↓
4. .ai/runtime/agent-bindings.yaml
        ↓
5. Current task only
```

Do not read the rest of the repository unless required to execute that task.

## Four stable layers

```text
docs/program/     → Business Truth
.engineering/     → Engineering Specification
.ai/              → AI Organization & Coordination
salesos/          → Implementation
```

## Layout

| Path | Purpose |
|------|---------|
| [`VERSION`](VERSION) | Compatibility pin (Baseline v1.0) |
| [`roles/`](roles/) | **Permanent role contracts** (exactly four) + [`registry.md`](roles/registry.md) |
| [`runtime/agent-bindings.yaml`](runtime/agent-bindings.yaml) | **Only** place engines are assigned to roles |
| [`runtime/runtime-spec.yaml`](runtime/runtime-spec.yaml) | Future runtime **specification** (not an engine) |
| [`docs/EXECUTION_LIFECYCLE.md`](docs/EXECUTION_LIFECYCLE.md) | Official criterion cycle |
| [`docs/WORKER_EXECUTION.md`](docs/WORKER_EXECUTION.md) | Temporary workers (namespaced names) |
| [`docs/PARALLEL_EXECUTION.md`](docs/PARALLEL_EXECUTION.md) | Parallel spawn patterns |
| [`AI_ORGANIZATION_MIGRATION_REPORT.md`](AI_ORGANIZATION_MIGRATION_REPORT.md) | Migration record (v2) |
| [`agents/`](agents/) | **Retired** engine-named stubs → redirect to `roles/` |

## Permanent roles

1. Backend Lead  
2. Architecture Reviewer  
3. Engineering Validator  
4. Execution Orchestrator  

Engines (Cursor, Claude, OpenCode, DeepSeek, …) are **bindings**, not organizational identities.

## Phase 0 focus (organizational design complete)

| Goal | Status |
|------|--------|
| Close Phase 0 criteria | 🎯 |
| CI Green | 🎯 |
| Security P0 | 🎯 |
| Railway R-14 | 🎯 |
| Independent EOS Re-audit | 🎯 |
| Reach 54/54 | 🎯 |
