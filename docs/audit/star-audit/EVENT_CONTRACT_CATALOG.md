# Event Contract Catalog — Agent Runtime

**Status:** ACCEPTED
**Accepted:** 2026-08-09
**Review:** Cross-artifact consistency verified

---

## Publication Model

```
Phase 1: post-commit, best-effort, duplicate-tolerant
Events are non-authoritative projections of committed state.
Events MUST NOT be required for correctness of task execution.
Transactional outbox is deferred to a future ADR.
```

---

## Event Envelope

All events follow the CloudEvents 1.0 compatible `DomainEvent` base class
(`sdk/events/base.py`):

```python
@dataclass
class DomainEvent:
    event_id: str           # UUID4
    event_type: str         # "agent.task.created"
    event_version: int      # 1
    aggregate_id: str       # task_id / run_id
    aggregate_type: str     # "agent_task" / "agent_run"
    tenant_id: str          # UUID
    occurred_at: datetime   # UTC now
    data: dict              # Payload (see per-event below)
    metadata: dict          # correlation_id, causation_id, trace info
```

---

## Phase 1 Lifecycle Events (8 events)

### Existing (already defined in `sdk/events/domain_events.py`)

| # | Event Type | Producer | Payload |
|---|-----------|----------|---------|
| E01 | `agent.task.created` | AgentTaskService | `task_id`, `kind`, `entity_type`, `entity_id`, `priority`, `budget`, `tenant_id` |
| E02 | `agent.task.completed` | AgentRuntime | `task_id`, `run_id`, `outcome`, `completion_reason`, `tenant_id` |
| E03 | `agent.task.failed` | AgentRuntime | `task_id`, `run_id`, `error`, `attempts`, `max_attempts`, `tenant_id` |

### New (to be added to `sdk/events/domain_events.py`)

| # | Event Type | Producer | Payload |
|---|-----------|----------|---------|
| E04 | `agent.task.claimed` | AgentDispatcher | `task_id`, `worker_id`, `lease_generation`, `leased_until`, `attempt`, `tenant_id` |
| E05 | `agent.run.started` | AgentRuntime | `run_id`, `task_id`, `agent_type`, `budget`, `tenant_id` |
| E06 | `agent.run.completed` | AgentRuntime | `run_id`, `task_id`, `duration_ms`, `input_tokens`, `output_tokens`, `cost_usd`, `budget_spent`, `tenant_id` |
| E07 | `agent.run.failed` | AgentRuntime | `run_id`, `task_id`, `error`, `duration_ms`, `tenant_id` |
| E08 | `agent.task.exhausted` | AgentDispatcher | `task_id`, `attempts`, `max_attempts`, `tenant_id` |

---

## Phase 2 Events (5 events)

| # | Event Type | Producer | Payload |
|---|-----------|----------|---------|
| E09 | `agent.action.requested` | ToolDispatcher | `action_id`, `run_id`, `action_type`, `target_entity`, `target_id`, `idempotency_key`, `tenant_id` |
| E10 | `agent.action.completed` | ToolDispatcher | `action_id`, `run_id`, `status`, `pdp_result`, `tenant_id` |
| E11 | `agent.evidence.recorded` | EvidenceEngine | `evidence_id`, `run_id`, `evidence_kind`, `score`, `tenant_id` |

---

## Phase 3 Events (2 events)

| # | Event Type | Producer | Payload |
|---|-----------|----------|---------|
| E12 | `agent.approval.required` | ApprovalManager | `approval_id`, `run_id`, `entity_type`, `entity_id`, `field`, `value`, `band`, `score`, `tenant_id` |
| E13 | `agent.memory.updated` | MemoryRuntime | `run_id`, `memory_type`, `memory_key`, `tenant_id` |

---

## Correlation Model

```
AgentTaskCreated.correlation_id=X
  └── AgentTaskClaimed.correlation_id=X,  causation_id=AgentTaskCreated.event_id
        └── AgentRunStarted.correlation_id=X,  causation_id=AgentTaskClaimed.event_id
              └── AgentActionRequested.correlation_id=X,  causation_id=AgentRunStarted.event_id
                    └── AgentActionCompleted.correlation_id=X,  causation_id=AgentActionRequested.event_id
              └── AgentRunCompleted.correlation_id=X,  causation_id=AgentRunStarted.event_id
```

---

## Implementation in Phase 1

Each new event type requires:

```python
# In sdk/events/domain_events.py:
@dataclass
class AgentTaskClaimed(DomainEvent):
    event_type: str = "agent.task.claimed"

# Add to EVENT_REGISTRY class list:
EVENT_REGISTRY = [
    ...
    AgentTaskCreated,
    AgentTaskCompleted,
    AgentTaskFailed,
    AgentMemoryUpdated,
    AgentTaskClaimed,       # NEW
    AgentRunStarted,        # NEW
    AgentRunCompleted,      # NEW
    AgentRunFailed,         # NEW
    AgentTaskExhausted,     # NEW
]

# Publishing (post-commit, best-effort):
try:
    await event_runtime.publish(AgentTaskClaimed(
        tenant_id=tenant_id,
        aggregate_id=task_id,
        aggregate_type="agent_task",
        data={...},
        metadata={"correlation_id": corr_id, "causation_id": cause_id},
    ))
except Exception:
    logger.warning("Failed to publish AgentTaskClaimed event", exc_info=True)
    # NOT re-raised — events are best-effort
```

---

## Subscription

Subscribers register on the existing EventRuntime:

```python
event_runtime.register("agent.task.claimed", handler, priority=SubscriberPriority.NORMAL)
event_runtime.register_wildcard(audit_handler, priority=SubscriberPriority.LATE)
```

---

## Backward Compatibility

No existing events are modified. The existing 4 agent events (E01-E03 + `agent.memory.updated`) remain
unchanged but will now be published by the new Agent Runtime instead of being declared-only.
