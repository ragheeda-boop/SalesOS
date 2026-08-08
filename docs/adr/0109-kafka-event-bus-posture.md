# ADR-109: Kafka Event Bus — Current Posture and Graduation Path

| Property | Value |
|----------|-------|
| **Status** | Accepted |
| **Date** | 2026-08-08 |
| **Decider** | CTO (OpenCode Agent delegation) |
| **Consulted** | Enterprise Audit Board, Engineering |
| **Informed** | All stakeholders |
| **Supersedes** | ADR-101 (bootstrap — in_memory default), ADR-102 (version pin) |
| **Related** | ADR-103 (Digital Twin deferred — depends on Kafka) |

---

## Context

The SalesOS event bus supports two backends:

| Backend | Config value | Description |
|---------|:------------:|-------------|
| `InMemoryEventBus` | `event_bus_type=in_memory` | Python `asyncio.Queue` — no persistence, no cross-instance delivery, no replay |
| `KafkaEventBus` | `event_bus_type=kafka` | Confluent Kafka 7.7.2 — persistent, partitioned, replayable |

Kafka is **provisioned and healthy** in all compose files (dev, staging, production — image `confluentinc/cp-kafka:7.7.2`). A `KafkaEventBus` implementation exists with built-in graceful degradation (auto-fallback to in-memory on broker unreachable, 30s retry backoff). The `/health` endpoint reports bus status: `"connected"`, `"fallback_in_memory"`, `"in_memory"`, or `"not_configured"`.

However, the **default across ALL environments** is `event_bus_type=in_memory` (set in `app/config.py:120`, docker-compose overrides, and staging compose).

---

## Decision

### Current posture (v1.0 GA): `in_memory` default

**Kafka stays provisioned but optional.** The system ships with `EVENT_BUS_TYPE=in_memory` as the default in production, staging, and dev.

**Rationale:**

1. **Single-instance deployment** — SalesOS v1.0 does not require cross-instance event delivery. A single backend process handles all event producers and consumers within the same asyncio event loop.

2. **Event volume is unknown** — Without production traffic metrics, the operational complexity of Kafka (partitioning, consumer group rebalancing, offset management, retention policies) brings no measurable benefit.

3. **Degraded mode acceptance** — The [DEGRADED_MODE_MATRIX](../ops/DEGRADED_MODE_MATRIX.md) already classifies Kafka as optional. The `KafkaEventBus` graceful degradation means even with `event_bus_type=kafka`, the system survives Kafka outages; this safety net reduces urgency.

4. **No features require Kafka** — ADR-103 deferred the Digital Twin (which depends on persistent event replay). No shipped capability in v1.0 depends on durable cross-process messaging.
5. **K8s configmap is a known split-brain** — `infra/k8s/configmap.yaml` sets `EVENT_BUS_TYPE=kafka`, while compose files default to `in_memory`. This inconsistency is documented and intentionally deferred to the K8s migration sprint.

### Graduation criteria (when to enable Kafka in production)

The decision to switch `EVENT_BUS_TYPE=kafka` in production is deferred until **two or more** of these conditions are met:

| # | Criterion | Threshold |
|---|-----------|-----------|
| C1 | Multi-instance backend | ≥ 2 backend replicas needing cross-instance event delivery |
| C2 | Event retention required | Any shipped feature needs event replay or audit trail from the bus |
| C3 | Throughput exceeds in-memory | In-process queue depth > 10,000 events or memory > 100 MB for queued events |
| C4 | Event durability required | Any shipped capability cannot tolerate event loss on process restart |
| C5 | Enterprise customer contract requires it | Contractual obligation for message persistence/compliance |

### Operational readiness checklist (before enabling Kafka in production)

```
[ ] Kafka metrics collected (JMX exporter or via cAdvisor)
[ ] Consumer lag alerting configured (S2: lag > 10,000 messages)
[ ] Topic creation is declarative (not AUTO_CREATE_TOPICS — define in compose/Terraform)
[ ] Partition strategy reviewed (current: 3 partitions, auto-created topics)
[ ] Retention policy set per topic (production: salesos.* topics at 168h default)
[ ] Backup of Kafka data volume configured (kafka_data — currently not backed up)
[ ] Schema registry considered (events currently JSON — no schema enforcement)
[ ] End-to-end event delivery tested (produce → consume → handler executed)
[ ] Staging soak: 72h with EVENT_BUS_TYPE=kafka, zero lag, zero errors
[ ] Rollback procedure validated: switch to in_memory, purge kafka_data
```

---

## Consequences

### Positive

- **Reduced operational complexity** — No Kafka topic management, partition rebalancing, or consumer group coordination in v1.0.
- **Faster restarts** — No Kafka consumer group join at startup.
- **No split-brain risk** — Single event bus eliminates dual-write/data-divergence concerns.
- **Graceful upgrade path** — When criteria are met, switch requires only an env var change (`EVENT_BUS_TYPE=kafka`) + restart. The `KafkaEventBus` is production-coded and tested.

### Negative

- **No event persistence** — Process restart loses in-flight events (acceptable per current feature set).
- **No cross-instance delivery** — Blocks horizontal scaling of the backend process.
- **No event replay** — Event Sourcing / CQRS patterns cannot be implemented without Kafka.
- **K8s deployment blocked** — The K8s configmap expects `kafka`, so K8s migration requires either flipping the flag or reconciling the configmap.
- **Backward data loss on migration** — When switching to Kafka, the `in_memory` queue contents are discarded (no migration of in-flight events to Kafka).

### Neutral

- Kafka container continues running (consumes resources: 0.5-1 CPU, 512 MB-1 GB RAM reservation) but receives no traffic.
- Health endpoint correctly reports `"in_memory"` — monitoring dashboards must not alert on this status.
- Manual testing of Kafka path remains possible: set `EVENT_BUS_TYPE=kafka`, restart backend, run integration tests.

---

## Rejected Alternatives

### 1. Enable Kafka immediately for v1.0 GA

**Rejected** because it adds operational risk (partition management, consumer lag, disk usage) without any feature benefit. The system has zero production traffic on the event bus; enabling Kafka would be "solve for scale before measuring load."

### 2. Remove Kafka completely from compose files

**Rejected** because:
- The `KafkaEventBus` codebase is stable and tested.
- Kafka is the only viable path to horizontal scaling.
- Removing and re-adding Kafka later would re-introduce integration risk.
- The container overhead is minimal in single-instance deployments.

### 3. Dual-write (publish to both in_memory and Kafka)

**Rejected** because dual-write introduces ordering and consistency problems. If the bus must be Kafka, switch entirely to Kafka. If in_memory is sufficient, stay in_memory. Dual-write creates complexity without benefit.

### 4. Use Kafka as the ONLY event bus (remove in_memory)

**Rejected** because the `InMemoryEventBus` is the ideal test harness (fast, deterministic, no external dependency). It also serves as the graceful degradation fallback within `KafkaEventBus` itself. Maintaining both implementations is low-cost.

---

## Phased Plan

| Phase | What | When | Duration |
|-------|------|------|:--------:|
| 0 (Current) | `in_memory` default, Kafka provisioned idle | v1.0 GA | indefinite |
| 1 | Operational readiness items completed (monitoring, backups, retention) | Before C1–C5 trigger | ~2 weeks |
| 2 | Staging soak: 72h `EVENT_BUS_TYPE=kafka`, validate consumer lag, no data loss | When C1–C5 trigger | 1 sprint |
| 3 | Production flip: `EVENT_BUS_TYPE=kafka` in `.env.production`, rolling restart, monitor 48h | After Phase 2 pass | 1 sprint |
| 4 | Remove in_memory default, make Kafka the canonical path | When 90d stable on Kafka | ~2 weeks |

---

## References

- [DEGRADED_MODE_MATRIX.md](../ops/DEGRADED_MODE_MATRIX.md) — Kafka classified as optional
- [ADR-101: Platform Bootstrap Stabilization](../adr/0101-platform-bootstrap-stabilization.md) — in_memory default documented
- [ADR-102: Engineering Hardening](../adr/0102-engineering-hardening.md) — Kafka version pin to 7.7.2
- [ADR-103: Digital Twin Deferred](../adr/0103-digital-twin-deferred.md) — depends on persistent event bus
- `app/boot/startup.py:79-103` — Event bus initialization with graceful degradation
- `sdk/events/kafka_bus.py` — KafkaEventBus implementation with 30s retry backoff
- `app/config.py:120-123` — `event_bus_type`, `kafka_bootstrap_servers`, `kafka_group_id`, `kafka_auto_offset_reset`
