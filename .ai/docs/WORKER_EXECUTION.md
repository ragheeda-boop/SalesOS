# Worker Execution Architecture

> **Layer:** `.ai/` (AI Runtime organization)  
> **Governed by:** ADR-036, EEC-001, [`.ai/roles/registry.md`](../roles/registry.md)  
> **Bindings:** [`.ai/runtime/agent-bindings.yaml`](../runtime/agent-bindings.yaml)

---

## Permanent Roles (exactly four)

| Role ID | Contract |
|---------|----------|
| `backend-lead` | [`../roles/backend-lead.md`](../roles/backend-lead.md) |
| `architecture-reviewer` | [`../roles/architecture-reviewer.md`](../roles/architecture-reviewer.md) |
| `engineering-validator` | [`../roles/engineering-validator.md`](../roles/engineering-validator.md) |
| `execution-orchestrator` | [`../roles/execution-orchestrator.md`](../roles/execution-orchestrator.md) |

**Never create additional permanent roles** without ARB resolution. The organization freezes at four permanent roles.

---

## Temporary Workers

Workers are **not** roles.

| Property | Rule |
|----------|------|
| Lifetime | Task-scoped; created dynamically for one assignment |
| Contract | **Inherit** the parent permanent role contract in full |
| Engine | Inherit parent binding from `agent-bindings.yaml` |
| Authority | Same path ownership and May-NOT rules as parent |
| Permanence | **Never** become permanent; no registry row; no new contract file |
| Termination | **Automatic** after task completion, failure, or Orchestrator cancel |
| Override | Workers **never** override parent role authority or Orchestrator coordination |

### Spawn authority

- **Execution Orchestrator** may spawn workers under any permanent role when parallelizing a criterion or DAG node.
- A permanent role may recommend worker splits; only the Orchestrator (or explicit human assignment) dispatches them.
- Workers do not self-select criteria (same as parent roles under EEC-001 / Orchestrator policy).

### Naming (namespaced — mandatory)

Worker labels are operational, not organizational. **Never** use opaque IDs (`Worker-001`, `Worker-002`).

Always use a **parent-domain / task** namespace:

```text
backend/api-worker
backend/test-worker
backend/migration-worker
backend/performance-worker

architecture/adr-worker
architecture/dependency-worker

validation/security-worker
validation/ci-worker
validation/performance-worker
```

| Prefix | Parent role |
|--------|-------------|
| `backend/` | `backend-lead` |
| `architecture/` | `architecture-reviewer` |
| `validation/` | `engineering-validator` |
| `orchestration/` | `execution-orchestrator` (rare; coordination helpers only) |

Labels must not be promoted into `.ai/roles/`.

### Caps (with parallel execution)

See [`PARALLEL_EXECUTION.md`](PARALLEL_EXECUTION.md) and [`.ai/runtime/runtime-spec.yaml`](../runtime/runtime-spec.yaml) (DEC-145 / criterion **8.2**):

- Permanent roles ≤ **4**
- Concurrent temporary workers ≤ **8**
- Total agents ≤ **12**
- While ops wait: keep ≥ **2** (prefer **3**) independent READY workers (DEC-107)

---

## Inheritance model

```
Permanent Role (contract + bindings)
        │
        │ spawn (Orchestrator)
        ▼
Temporary Worker
  - reads same contract as parent
  - same owned paths / May-NOT
  - reports through parent cycle (Implement / Review / Validate / Coordinate)
  - terminates → no leftover permanent artifact
```

---

## Related

- [`PARALLEL_EXECUTION.md`](PARALLEL_EXECUTION.md) — parallel spawn patterns
- [`../roles/registry.md`](../roles/registry.md) — permanent role index
- [`../AI_ORGANIZATION_MIGRATION_REPORT.md`](../AI_ORGANIZATION_MIGRATION_REPORT.md)
