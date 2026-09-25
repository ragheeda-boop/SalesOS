# KAFKA PRODUCTION DECISION — 2026-08-24

**Question:** Does production currently require Kafka?

---

## Current State

- `EVENT_BUS_TYPE=in_memory` (default)
- Production compose (`docker-compose.prod.yml`) has NO Kafka/Zookeeper services
- EventRuntime (`runtime/event_runtime/__init__.py`) works in-memory with Postgres-backed DLQ
- KafkaEventBus (`sdk/events/kafka_bus.py`) exists but is unused in production

## Evaluation

| Criterion | In-Memory | Kafka | Delta |
|-----------|:---------:|:-----:|:-----:|
| Throughput | Adequate for single-node | High (distributed) | Kafka wins |
| Durability | Postgres DLQ (restart-safe) | Topic-based (persistent) | Comparable |
| Retry semantics | Exponential backoff per subscriber | Consumer group retry | Comparable |
| Ordering | Priority-based (in-process) | Partition-based (distributed) | Kafka wins |
| Replay | Not supported (events lost on restart) | Topic offset replay | Kafka wins |
| Operational complexity | Zero | Moderate (Zookeeper, topics, consumer groups) | In-memory wins |
| Current load | Adequate (Phase 1-4 features) | Overkill for current scale | In-memory wins |

## Analysis

1. **Current architecture works in-memory.** The EventRuntime with Postgres-backed DLQ provides durability for the current feature set (timeline events, signal detection, workflow triggers, agent tasks).

2. **No cross-service event streaming required.** All event subscribers run in the same process. Kafka's primary value (decoupled services) is not needed for a monolithic deployment.

3. **No event replay requirement.** The DLQ provides dead-letter persistence, but there is no business requirement to replay historical events.

4. **Operational overhead not justified.** Kafka + Zookeeper adds significant infrastructure complexity for a single-node deployment.

5. **Future need likely.** If the platform moves to microservices or multi-region deployment, Kafka would be required.

## Decision: DEFER

**Kafka is DEFERRED, not rejected.**

| Aspect | Decision |
|--------|----------|
| Current deployment | In-memory only |
| Kafka infrastructure | Not deployed |
| KafkaEventBus code | Retained (drop-in replacement when needed) |
| Trigger for activation | Multi-service architecture OR event replay requirement |
| Migration path | Change `EVENT_BUS_TYPE=kafka` + deploy Kafka cluster |

## Conditions for Activation

Kafka should be activated when:
1. Platform moves to microservices architecture
2. Event replay is required for business logic
3. Multi-region deployment is implemented
4. Throughput exceeds single-node capacity (>10K events/sec)

## Risk

| Risk | Mitigation |
|------|------------|
| Events lost on crash | Postgres DLQ persists dead letters |
| No event ordering across services | Not needed for current monolith |
| No replay capability | Not a current requirement |

---

**Status: DEFERRED — Evidence-based decision. No activation required for current production scope.**
