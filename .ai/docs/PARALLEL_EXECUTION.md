# Parallel Execution

> **Layer:** `.ai/` (AI Runtime organization)  
> **Governed by:** ADR-036, DEC-107 (swarm always-on READY), [`WORKER_EXECUTION.md`](WORKER_EXECUTION.md)

---

## Principle

The **Execution Orchestrator** may spawn **multiple temporary workers** under permanent roles whenever the execution DAG and file locks allow. Workers execute **in parallel** when owned paths and dependencies do not conflict.

Permanent roles remain four. Parallelism scales via **workers**, not new permanent roles.

---

## Example: Backend Lead workers

Parent role: `backend-lead` (engine from `agent-bindings.yaml`)

| Worker name | Typical scope |
|-------------|---------------|
| `backend/api-worker` | Routers / modules API surface |
| `backend/migration-worker` | Alembic revisions (gated) |
| `backend/test-worker` | Narrow pytest / contract tests |
| `backend/performance-worker` | Benchmarks / hot-path profiling notes |

All inherit [`../roles/backend-lead.md`](../roles/backend-lead.md). None become permanent.

---

## Example: Architecture Reviewer workers

Parent role: `architecture-reviewer`

| Worker name | Typical scope |
|-------------|---------------|
| `architecture/adr-worker` | ADR compliance / freeze checks (read-only unless assigned) |
| `architecture/dependency-worker` | Import / layer rule review |

All inherit [`../roles/architecture-reviewer.md`](../roles/architecture-reviewer.md).

---

## Example: Engineering Validator workers

Parent role: `engineering-validator`

| Worker name | Typical scope |
|-------------|---------------|
| `validation/security-worker` | Scan / SARIF / gate honesty |
| `validation/ci-worker` | Workflow / Stage evidence |
| `validation/performance-worker` | CI timing / resource checks |

All inherit [`../roles/engineering-validator.md`](../roles/engineering-validator.md).

---

## Caps (max agents)

Pinned in [`.ai/runtime/runtime-spec.yaml`](../runtime/runtime-spec.yaml) (DEC-145 / criterion **8.2**):

| Cap | Value | Meaning |
|-----|-------|---------|
| `permanent_roles_max` | **4** | Hard organizational freeze (ARB) |
| `max_parallel_workers` | **8** | Concurrent temporary workers ceiling |
| `min_parallel_ready` | **2** | DEC-107 floor while ops wait |
| `prefer_parallel_ready` | **3** | Prefer when Multitask capacity allows |
| `max_agents_total` | **12** | ≤4 permanent + ≤8 workers |

Exceeding the worker ceiling requires Orchestrator pause / serialize — do **not** invent a fifth permanent role.

## Dependency rules (conflict)

1. Do not parallelize writers on overlapping paths without `22_FILE_LOCKS.json`.
2. Prefer Orchestrator-owned parallel groups in `21_RUNTIME_STATE.json`.
3. When CI-08/CI-09 (or other ops) block publish, keep **independent READY** workers busy (DEC-107) — do not idle the swarm.
4. Workers terminate when their task completes; the Orchestrator continues the criterion state machine.
5. One agent owns a path at a time (see [`.engineering/26_AGENT_COORDINATION.md`](../../.engineering/26_AGENT_COORDINATION.md)).
6. Leave `TenantList` / security P0 endpoints alone unless assigned (AGENTS.md §7).

---

## Related

- [`WORKER_EXECUTION.md`](WORKER_EXECUTION.md)
- [`../roles/registry.md`](../roles/registry.md)
- [`../runtime/agent-bindings.yaml`](../runtime/agent-bindings.yaml)
- [`../runtime/runtime-spec.yaml`](../runtime/runtime-spec.yaml)
- `.engineering/26_AGENT_COORDINATION.md`
- `docs/program/decisions/DEC-107-SWARM-ALWAYS-ON-PARALLEL-READY.md`
- `docs/program/decisions/DEC-145-CRITERION-8-2-AGENT-COORDINATION.md`
