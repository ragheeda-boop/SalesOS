# Execution Lifecycle

> **Official cycle** for Phase 0 criterion execution (Architecture Baseline v1.0).  
> **ARB:** `ARB-2026-08-01-003` · [`.ai/VERSION`](../VERSION)  
> **Governed by:** ADR-036, EEC-001, [`.ai/roles/registry.md`](../roles/registry.md), [`.ai/runtime/runtime-spec.yaml`](../runtime/runtime-spec.yaml)  
> **Bindings:** [`.ai/runtime/agent-bindings.yaml`](../runtime/agent-bindings.yaml)

---

## Gate question (every request)

> **Which Phase 0 Exit Criterion will this close?**

If there is no clear answer → **defer the work**.

---

## Official execution cycle (sole approved path)

```text
OPEN
    ↓
Execution Orchestrator
    ↓
ASSIGNED
    ↓
Backend Lead
    ↓
READY_FOR_REVIEW
    ↓
Architecture Reviewer
    ↓
ARCHITECTURE PASS
    ↓
Engineering Validator
    ↓
VALIDATION PASS
    ↓
Execution Orchestrator
    ↓
VERIFIED
    ↓
CLOSED
    ↓
Next Criterion
```

ARCHITECTURE FAIL or VALIDATION FAIL returns findings to the assigned implementer → remediates → READY_FOR_REVIEW again. No role self-marks **VERIFIED** / **CLOSED** except the Execution Orchestrator recording the verified outcome.

---

## State ownership (summary)

| Stage | Authority |
|-------|-----------|
| OPEN / QUEUED / ASSIGNED | Execution Orchestrator |
| IN_PROGRESS / READY_FOR_REVIEW | Backend Lead (when assigned implementer) |
| Architecture Review / ARCHITECTURE PASS | Architecture Reviewer |
| Engineering Validation / VALIDATION PASS | Engineering Validator |
| VERIFIED / CLOSED / BLOCKED | Execution Orchestrator |

---

## What success means

Not commits or PRs. Track only:

| Metric | Target |
|--------|--------|
| Phase 0 Exit | 17/54 → **54/54** |
| OPEN criteria | ↓ continuously |
| VERIFIED criteria | ↑ continuously |
| BLOCKED criteria | ↓ continuously |
| CI status | Green |
| Security P0 | Zero critical remaining |
| Independent EOS audit | PASS |

---

## When organizational redesign may reopen

Only if:

1. **54/54** reached, or  
2. An architectural defect **blocks** closing a Phase 0 criterion, or  
3. A formal **ARB** decision mandates an architectural change  

Otherwise `docs/program/`, `.engineering/`, and `.ai/` stay stable; focus is `salesos/` + Phase 0 criteria.

---

## Workers

Temporary workers may run inside a stage when locks allow. Namespaced only (`backend/api-worker`, …). See [`WORKER_EXECUTION.md`](WORKER_EXECUTION.md).

---

## Related

- [`PARALLEL_EXECUTION.md`](PARALLEL_EXECUTION.md)
- [`../roles/execution-orchestrator.md`](../roles/execution-orchestrator.md)
- `docs/program/PHASE_0_EXIT_CHECKLIST.md`
