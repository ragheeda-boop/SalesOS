# Kafka Event Bus Architecture

> **الهدف:** تصميم Kafka Event Bus — العمود الفقري للاتصالات بين خدمات Wave 3
>
> **تاريخ:** 2026-07-11
> **المرحلة:** Wave 3 — Sprint 11

---

## 1. Purpose

### لماذا Kafka بدلاً من Event Runtime الحالي؟

| الميزة | Event Runtime (حاليًا) | Kafka (Wave 3) |
|--------|----------------------|----------------|
| Persistence | In-memory فقط | Disk-based, قابل للاسترجاع |
| Exactly-Once | غير مضمون | مضمون مع proper configuration |
| Schema Management | TypeScript types فقط | Schema Registry + Avro |
| Replayability | غير ممكن | يمكن إعادة تشغيل events من أي نقطة |
| Consumer Groups | Subscriber list بسيط | Consumer groups مع offset management |
| Dead Letter Queue | Manual | DLQ تلقائي مع retry policies |
| Scalability | Single process | Horizontal scaling مع partitions |
| Retention | غير مدعوم | Configurable retention period |

### Migration Target

حل TD-002: استبدال Event Runtime بـ Kafka مع الاحتفاظ بجميع subscribers الحاليين.

---

## 2. Event Schema Registry

### Schema Format (Avro)

```avro
{
  "namespace": "com.salesos.event",
  "type": "record",
  "name": "OpportunityStageChanged",
  "fields": [
    {"name": "event_id",         "type": "string"},
    {"name": "aggregate_id",     "type": "string"},
    {"name": "tenant_id",        "type": "string"},
    {"name": "timestamp",        "type": "string", "logicalType": "timestamp-millis"},
    {"name": "version",          "type": "int",    "default": 1},
    {"name": "data",             "type": {
      "type": "record",
      "name": "OpportunityStageChangedData",
      "fields": [
        {"name": "opportunity_id", "type": "string"},
        {"name": "company_id",     "type": "string"},
        {"name": "previous_stage", "type": "string"},
        {"name": "new_stage",      "type": "string"},
        {"name": "changed_by",     "type": "string"},
        {"name": "reason",         "type": ["null", "string"], "default": null}
      ]
    }}
  ]
}
```

### Schema Registry Architecture

```
Schema Registry (Confluent or Apicurio)
      │
      ├── Stores Avro schemas with versioning
      ├── Enforces compatibility (BACKWARD by default)
      ├── Provides REST API for schema CRUD
      └── Integrates with Kafka producers/consumers
```

### Event Types Catalog

| Event Type | Schema Version | Producer | Key Consumers | Retention |
|-----------|---------------|---------|---------------|-----------|
| `opportunity.created` | v1 | Opportunity Service | NBA, Workflow, Search, Pipeline | 30 days |
| `opportunity.stage_changed` | v1 | Opportunity Service | NBA, Workflow, Pipeline, Analytics | 90 days |
| `opportunity.deleted` | v1 | Opportunity Service | Search, Pipeline, Analytics | 7 days |
| `activity.logged` | v1 | Activity Service | NBA, Timeline, Analytics | 30 days |
| `deal_health.changed` | v1 | Deal Health Service | NBA, Workflow, Alerting | 90 days |
| `company.signal.detected` | v1 | Signal Runtime | NBA, Company Intelligence | 30 days |
| `nba.generated` | v1 | NBA Engine | Analytics, Audit | 90 days |
| `nba.feedback.recorded` | v1 | NBA Engine | Learning Engine, Analytics | 90 days |
| `workflow.started` | v1 | Workflow Engine | Analytics, Monitoring | 30 days |
| `workflow.completed` | v1 | Workflow Engine | Analytics, Monitoring | 30 days |
| `workflow.failed` | v1 | Workflow Engine | Alerting, Analytics | 90 days |
| `workflow.step_executed` | v1 | Workflow Engine | Monitoring, Execution Trace | 7 days |

---

## 3. Topic Design

### Topic Naming Convention

```
salesos.{domain}.{event_type}.{version}
```

Examples:
- `salesos.opportunity.stage_changed.v1`
- `salesos.activity.logged.v1`
- `salesos.workflow.completed.v1`

### Topic Configuration

```python
TOPIC_CONFIG = {
    "salesos.opportunity.stage_changed.v1": {
        "partitions": 8,
        "replication_factor": 3,
        "retention_ms": 7_776_000_000,     # 90 days
        "cleanup_policy": "delete",
        "compression_type": "snappy",
    },
    "salesos.activity.logged.v1": {
        "partitions": 16,                   # High volume topic
        "replication_factor": 3,
        "retention_ms": 2_592_000_000,     # 30 days
        "cleanup_policy": "delete",
        "compression_type": "snappy",
    },
    "salesos.workflow.completed.v1": {
        "partitions": 4,
        "replication_factor": 3,
        "retention_ms": 2_592_000_000,
        "cleanup_policy": "delete",
    },
    "salesos.nba.feedback.recorded.v1": {
        "partitions": 4,
        "replication_factor": 3,
        "retention_ms": 7_776_000_000,     # 90 days for learning
        "cleanup_policy": "compact",        # Keep latest per key
    },
}
```

### Partition Strategy

| Event Type | Partition Key | Rationale |
|-----------|--------------|-----------|
| opportunity.* | `opportunity_id` | All events for same opportunity in order |
| activity.* | `tenant_id` | Distribute load across partitions |
| workflow.* | `workflow_id` | All steps of same workflow in order |
| nba.* | `opportunity_id` | Per-opportunity NBA ordering |

---

## 4. Event Sourcing

### Domains Using Event Sourcing

| Domain | Events Stored | Replay Purpose |
|--------|--------------|----------------|
| **Opportunity** | created, stage_changed, value_updated, owner_changed, deleted | Rebuild opportunity state at any point |
| **Pipeline** | snapshot_taken | Historical pipeline analysis |
| **Deal Health** | health_changed | Health trend analysis |
| **NBA** | generated, feedback_recorded | NBA effectiveness over time |
| **Workflow** | started, step_executed, completed, failed | Workflow audit trail |

### Event Store

```sql
CREATE TABLE event_store (
    id BIGSERIAL PRIMARY KEY,
    event_id UUID NOT NULL UNIQUE,
    aggregate_type VARCHAR(50) NOT NULL,     -- opportunity / deal / nba / workflow
    aggregate_id VARCHAR(100) NOT NULL,
    tenant_id UUID NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    version INTEGER NOT NULL,
    data JSONB NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (aggregate_type, aggregate_id, version)
);

CREATE INDEX idx_event_store_aggregate
    ON event_store (aggregate_type, aggregate_id, version);
```

### Event Replay

```python
class EventStore:
    async def replay_aggregate(
        self,
        aggregate_type: str,
        aggregate_id: str,
        target_state: type
    ) -> AggregateState:
        """Replay all events for an aggregate to rebuild state."""
        events = await self.db.query(
            "SELECT * FROM event_store "
            "WHERE aggregate_type = $1 AND aggregate_id = $2 "
            "ORDER BY version ASC",
            aggregate_type, aggregate_id
        )

        state = target_state()
        for event in events:
            handler = self._get_handler(event.event_type)
            state = handler(state, event.data)

        return state
```

---

## 5. Exactly-Once Semantics

### Where Exactly-Once Is Required

| Operation | Semantics | Implementation |
|-----------|-----------|----------------|
| Opportunity stage change | Exactly-Once | Idempotent producer + transactions |
| Activity logging | At-Least-Once | Deduplication on consumer side |
| NBA generation | At-Least-Once | Idempotent (same NBA on retry) |
| Workflow execution | Exactly-Once | Kafka transactions + idempotent actions |
| Analytics ETL | At-Least-Once | Upsert logic in warehouse |
| Notification sending | At-Most-Once | Deduplication window on send |

### Configuration for Exactly-Once

```python
from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers=['kafka1:9092', 'kafka2:9092', 'kafka3:9092'],
    acks='all',                          # Wait for all replicas
    enable_idempotence=True,              # Exactly-once producer
    max_in_flight_requests_per_connection=5,
    retries=Integer.MAX_VALUE,
    compression_type='snappy',
)

# For transactional workflows:
producer.init_transactions()
producer.begin_transaction()
# ... produce events ...
producer.commit_transaction()
```

---

## 6. Dead Letter Queue Strategy

### DLQ Architecture

```
Kafka Topic (source)
      │
      ▼
Consumer
      │
      ├── Success ──► Process event
      │
      └── Failure ──► Check retry count
            │
            ├── < max_retries ──► Retry with backoff (DLQ with delay)
            │
            └── >= max_retries ──► salesos.dlq.{domain}
                                      │
                                      ▼
                              DLQ Consumer
                                    │
                                    ├── Log + Alert
                                    ├── Store for manual replay
                                    └── Optional: route to engineering Slack
```

### DLQ Configuration

```python
DLQ_CONFIG = {
    "retry_count": 3,
    "backoff_strategy": "exponential",    # exponential / fixed
    "initial_backoff_ms": 1_000,          # 1 second
    "max_backoff_ms": 60_000,             # 1 minute
    "dlq_topic_prefix": "salesos.dlq.",
    "alert_threshold": 10,                # Alert after 10 DLQ messages
    "manual_replay": True,                # Allow manual replay from DLQ
}
```

### DLQ Consumer

```python
class DLQConsumer:
    async def process_dlq(self, dlq_topic: str):
        async for message in self.consumer:
            dlq_entry = message.value

            # Log
            logger.error(
                f"DLQ entry: topic={dlq_entry.original_topic}, "
                f"event_id={dlq_entry.event_id}, "
                f"error={dlq_entry.error}, "
                f"retry_count={dlq_entry.retry_count}"
            )

            # Store for manual inspection
            await self.dlq_store.save(dlq_entry)

            # Alert if threshold exceeded
            alert_count = await self.dlq_store.count_hourly(dlq_entry.original_topic)
            if alert_count >= DLQ_CONFIG["alert_threshold"]:
                await self.alerter.send(
                    f"DLQ threshold exceeded: {dlq_entry.original_topic} — {alert_count} in last hour"
                )
```

---

## 7. Event Versioning

### Versioning Strategy

| Change Type | Schema Compatibility | Version Bump |
|-------------|---------------------|-------------|
| Add optional field | BACKWARD | MINOR |
| Add required field with default | BACKWARD | MINOR |
| Remove field | FORWARD | MAJOR |
| Rename field | NONE (new field + deprecate old) | MAJOR |
| Change field type | NONE (new schema version) | MAJOR |

### Handling Version Evolution

```python
class EventVersionResolver:
    """Resolve event handlers based on schema version."""

    HANDLERS = {
        "opportunity.stage_changed": {
            1: handle_stage_changed_v1,
            # Future versions:
            # 2: handle_stage_changed_v2,
        }
    }

    async def handle(self, event: KafkaEvent):
        handler = self.HANDLERS[event.type].get(event.version)
        if not handler:
            # Fallback to latest handler for forward compatibility
            handler = self.HANDLERS[event.type][max(self.HANDLERS[event.type].keys())]
            logger.warning(f"No handler for v{event.version}, using latest")
        await handler(event)
```

### Migration from v1 to v2 (Example)

```python
# When upgrading an event schema:
# 1. Create new Avro schema as v2 (BACKWARD compatible)
# 2. Update producer to emit v2 events (old consumers still work)
# 3. Update consumers one by one to handle v2
# 4. After all consumers updated, remove v1 handler
# 5. Set compatibility to FORWARD to allow old events

SCHEMA_REGISTRY_COMPATIBILITY = "BACKWARD"  # Default

async def migrate_event_v1_to_v2(event_type: str):
    """Migration steps for event version upgrade."""
    # Step 1: Register v2 schema (BACKWARD compatible)
    await schema_registry.register(f"{event_type}.v2", schema_v2)

    # Step 2: Update producer
    # (done in code)

    # Step 3: Wait for all consumers to update
    await wait_for_consumer_update(event_type)

    # Step 4: Set to FORWARD for old events
    await schema_registry.set_compatibility(f"{event_type}.*", "FORWARD")

    # Step 5: Deprecate v1 schema
    await schema_registry.deprecate(f"{event_type}.v1")
```

---

## 8. Consumer Group Management

### Consumer Group Architecture

```
Topic: salesos.opportunity.stage_changed.v1 (8 partitions)
      │
      ├── Consumer Group: nba-engine (4 consumers)
      │     ├── consumer-1 (partitions 0, 1)
      │     ├── consumer-2 (partitions 2, 3)
      │     ├── consumer-3 (partitions 4, 5)
      │     └── consumer-4 (partitions 6, 7)
      │
      ├── Consumer Group: workflow-engine (2 consumers)
      │     ├── consumer-1 (partitions 0-3)
      │     └── consumer-2 (partitions 4-7)
      │
      ├── Consumer Group: analytics-etl (1 consumer)
      │     └── consumer-1 (all 8 partitions)
      │
      └── Consumer Group: audit-log (1 consumer)
            └── consumer-1 (all 8 partitions)
```

### Consumer Group Configuration

```python
CONSUMER_GROUPS = {
    "nba-engine": {
        "consumers": 4,              # Match partition count
        "auto_offset_reset": "latest",
        "max_poll_records": 100,
        "max_poll_interval_ms": 300000,  # 5 min
        "session_timeout_ms": 30000,
        "heartbeat_interval_ms": 3000,
    },
    "workflow-engine": {
        "consumers": 2,
        "auto_offset_reset": "latest",
        "max_poll_records": 50,
        "max_poll_interval_ms": 600000,
        "session_timeout_ms": 45000,
    },
    "analytics-etl": {
        "consumers": 1,
        "auto_offset_reset": "earliest",  # Need full history
        "max_poll_records": 500,
        "max_poll_interval_ms": 300000,
    },
    "audit-log": {
        "consumers": 1,
        "auto_offset_reset": "earliest",
        "max_poll_records": 100,
    },
}
```

---

## 9. Migration Path from In-Memory Event Runtime (TD-002)

### Dual-Run Strategy

```
Phase 1: Dual Publishing (Sprint 11, Week 1)
────────────────────────────────────────
Event Runtime (current)
      │
      ├── Emit to existing subscribers (Wave 1+2)
      └── Also emit to Kafka topics (new Wave 3 consumers)
              │
              └── Wave 3 services consume from Kafka

Phase 2: Kafka Primary (Sprint 11, Week 2)
────────────────────────────────────────
Event Runtime (degraded)
      │
      ├── Kafka becomes primary event bus
      └── Event Runtime mirrors from Kafka
              │
              └── Legacy subscribers still work via Event Runtime

Phase 3: Full Migration (Sprint 11, Week 3)
────────────────────────────────────────
Kafka only
      │
      ├── All subscribers migrated to Kafka consumer groups
      ├── Event Runtime decommissioned
      └── Legacy subscribers move to Kafka
```

### Migration Service

```python
class EventBusMigrationBridge:
    """Bridges between old Event Runtime and new Kafka bus."""

    def __init__(self, event_runtime: EventRuntime, kafka_producer: KafkaProducer):
        self.event_runtime = event_runtime
        self.kafka = kafka_producer

    async def start_dual_run(self):
        """Phase 1: Emit to both buses."""
        @self.event_runtime.on("*", priority="LATE")
        async def bridge_to_kafka(event: DomainEvent):
            topic = self._map_to_topic(event.type)
            await self.kafka.produce(topic, event.to_dict())

    async def switch_to_kafka_primary(self):
        """Phase 2: Kafka is primary; Event Runtime mirrors."""
        # Start Kafka consumer that re-emits to Event Runtime
        # for legacy subscribers that haven't migrated

    async def verify_migration(self):
        """Verify no events lost during migration."""
        # Compare event counts between old and new bus
        # for a sample period
```

### Rollback Plan

| Scenario | Action |
|----------|--------|
| Kafka cluster failure | Fall back to Event Runtime (events preserved in Kafka for replay) |
| Schema mismatch | Block producer until schema registered; alert on mismatch |
| Consumer lag exceeds threshold | Scale consumer group; alert if > 10 min lag |
| Data loss detected | Replay from Event Store or Kafka retention |

---

## 10. Monitoring & Observability

### Kafka Metrics

| Metric | Source | Alert Threshold |
|--------|--------|----------------|
| Consumer lag | Kafka Consumer Group API | > 10,000 messages |
| Produce rate | Kafka broker metrics | N/A (baseline) |
| Consume rate | Kafka broker metrics | N/A (baseline) |
| Under-replicated partitions | Kafka broker metrics | > 0 |
| Offline partitions | Kafka broker metrics | > 0 |
| Request latency (p99) | Kafka broker metrics | > 100ms |
| Schema registry errors | Schema Registry API | > 0 |
| DLQ message count | DLQ store | > 10/hr |

### Consumer Health

```
Consumer Group: nba-engine
═══════════════════════════════════════
Consumer     │  Partitions  │  Lag    │  Status
─────────────┼──────────────┼────────┼───────
consumer-1   │  0, 1        │  12    │  ✅
consumer-2   │  2, 3        │  8     │  ✅
consumer-3   │  4, 5        │  45    │  ⚠️  High lag
consumer-4   │  6, 7        │  3     │  ✅

Total: 68 lag (avg: 17)
```

---

## 11. Infrastructure Requirements

| Component | Specification | Count |
|-----------|--------------|-------|
| Kafka Broker | 4 vCPU, 8GB RAM, 100GB SSD | 3 |
| Schema Registry | 2 vCPU, 4GB RAM | 2 |
| Kafka Connect (optional) | 2 vCPU, 4GB RAM | 1 |
| Zookeeper (if not KRaft) | 2 vCPU, 4GB RAM | 3 |
| Monitoring (Kafka Exporter) | 1 vCPU, 2GB RAM | 1 |

### Kafka Configuration

```properties
# broker.properties
broker.id=1
num.network.threads=8
num.io.threads=16
socket.send.buffer.bytes=102400
socket.receive.buffer.bytes=102400
socket.request.max.bytes=104857600
log.dirs=/data/kafka
num.partitions=8
num.recovery.threads.per.data.dir=1
offsets.topic.replication.factor=3
transaction.state.log.replication.factor=3
transaction.state.log.min.isr=2
log.retention.hours=168
log.segment.bytes=1073741824
log.retention.check.interval.ms=300000
zookeeper.connect=zk1:2181,zk2:2181,zk3:2181
zookeeper.connection.timeout.ms=18000
group.initial.rebalance.delay.ms=3000
```

---

*Kafka Event Bus Architecture complete. Ready for Sprint 11 implementation.*
