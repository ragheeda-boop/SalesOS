# ADR-0110: Agent Runtime — Re-scope to Build Now

**Status:** ACCEPTED (supersedes ADR-0104)
**Date:** 2026-08-09
**Review:** STAR Audit remediation + Comp AI comparative analysis

---

## Context

ADR-0104 (2026-08-07) deferred the Agent Runtime to v2.0 based on the STAR Audit finding
that only a placeholder existed (`runtime/agent_runtime/__init__.py` containing a single
comment `# PLANNED FOR RT3`).

Four factors motivate re-scoping:

1. **Comp AI CRM analysis** (2026-08-09) demonstrated that a minimal, durable Agent Runtime
   can be built on PostgreSQL + existing infrastructure, without new frameworks.

2. **Repository Reality Check** (2026-08-09) verified that SalesOS's EventRuntime,
   ResearchAgent, TenantContext, Celery, UBOM, and RLS are all capable of hosting
   an Agent Runtime without architectural changes.

3. **12 library-only agents** (11 domain agents + 1 coordinator) exist under
   `intelligence/agents/` but have no execution infrastructure — no persistence,
   no retry, no scheduling, no sandboxing.

4. **GA readiness** requires autonomous revenue intelligence capabilities; a read-only
   Agent Runtime is the minimal viable step.

## Decision

**Agent Runtime is no longer deferred.** A minimal, durable execution layer shall be built
in Phase 1, reusing existing infrastructure (Event Runtime, Capability Registry, PDP, UBOM,
Data Fabric) and adapting proven patterns from the Comp AI CRM reference implementation.

## Core Principle

> **Agent Runtime is an execution subsystem, not a second application platform.**
> It orchestrates existing SalesOS capabilities through governed boundaries.
> It owns execution state (tasks, runs, leases, budgets); SalesOS owns business state
> (companies, contacts, opportunities). The two never blur.

## Architecture Invariants

| # | Invariant |
|---|-----------|
| INV-01 | Agent Runtime owns execution state. SalesOS owns business state. Boundary: governed repositories. |
| INV-02 | No agent may access domain ORM/repositories directly. |
| INV-03 | Every agent-originated side effect MUST perform fencing + idempotency + mutation atomically. |
| INV-04 | Approval resume preserves `agent_run.id`; retry creates a new `agent_run`. |
| INV-05 | Budget spend is fenced against current lease generation. |

## Scope Boundaries

**Phase 1 (Build now):**
- 3 PostgreSQL tables: `agent_tasks`, `agent_runs`, `agent_actions`
- AgentDispatcher + AgentRuntime (state machine, fencing, budget, preamble)
- ResearchAgent wired through runtime (read-only, existing code unchanged)
- Celery Beat dispatch (60s cycle)
- 8 lifecycle events (post-commit, best-effort)

**Explicitly excluded from Phase 1:**
- ToolRegistry, ToolDispatcher, EvidenceEngine, FactRecorder
- ApprovalManager, AgentSandbox, SignalDetector
- Any agent other than ResearchAgent

## Consequences

- Re-opens the v1.0 scope with a ~7-week addition (1 freeze + 3 implementation phases)
- Requires 5 Architecture Freeze acceptance artifacts before Phase 1
- ResearchAgent becomes the first production agent (read-only enrichment)
- Agent Runtime becomes a platform capability for all future agents

## Related

- ADR-0104 (superseded): Agent Runtime deferred to v2.0
- ADR-0111: Task Queue strategy
- ADR-0112: Agent State Machine
- ADR-0113: Evidence Architecture
- ADR-0114: Canonical Write Boundary
- ADR-0115: Agent Security Boundary
- ADR-0116: Tool/Capability Architecture
- ADR-0117: Signal → Agent Integration
