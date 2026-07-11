# Wave 3 Architecture Decision Records

> **الغرض:** توثيق القرارات المعمارية الرئيسية لـ Wave 3 — الأساس المنطقي لكل خيار، والمفاضلات التي تم النظر فيها
>
> **تاريخ:** 2026-07-11
> **المرحلة:** Wave 3 — Architecture Decisions

---

## ADR-001: Vector Store — pgvector

| Field | Value |
|-------|-------|
| **ID** | ADR-001 |
| **Date** | 2026-07-11 |
| **Title** | Vector Store Selection for RAG Pipeline |
| **Status** | Accepted |
| **Owner** | AI Engineer |

### Context

نحتاج مخزن vectors لدعم RAG pipeline. الخيارات المتاحة:
- pgvector (PostgreSQL extension)
- Pinecone (managed vector DB)
- Weaviate (open-source vector DB)
- Qdrant (open-source vector DB)

### Decision

**Choose pgvector.**

### Rationale

1. **Zero additional infrastructure** — نستخدم PostgreSQL الموجود (يضاف extension فقط)
2. **Transactional consistency** — نفس transaction اللي نكتب فيها الـ chunk نكتب فيها الـ vector
3. **Operational simplicity** — فريق DevOps يدير PostgreSQL بالفعل
4. **Multi-tenancy** — نفس آلية tenant isolation الموجودة
5. **Hybrid search** — pgvector يدعم semantic search + PostgreSQL FTS للـ keyword search
6. **Performance** — HNSW index يعطينا أداء مقبول لملايين الـ vectors

### Tradeoffs Considered

| Option | Pros | Cons |
|--------|------|------|
| **Pinecone** | Fully managed, high performance | $70+/mo, data sovereignty concerns (Saudi data) |
| **Weaviate** | Built-in hybrid search, schemas | Additional operational overhead, not as mature in K8s |
| **Qdrant** | Fast, Rust-based, filtering | Smaller ecosystem, additional infra |

### Consequences

- سنحتاج ترقية PostgreSQL إلى v14+ لاستخدام pgvector
- أداء البحث يقل بعد 10M+ vectors لكل tenant — نراقب ونخطط للتقسيم
- HNSW index يستهلك ذاكرة إضافية (~2GB لكل 1M vectors مع 1024 dimensions)

---

## ADR-002: Embedding Model — Self-Hosted Multilingual E5

| Field | Value |
|-------|-------|
| **ID** | ADR-002 |
| **Date** | 2026-07-11 |
| **Title** | Embedding Model Selection |
| **Status** | Accepted |
| **Owner** | AI Engineer |

### Context

نحتاج embedding model يدعم العربية والإنجليزية بجودة عالية. الخيارات:
- intfloat/multilingual-e5-large (self-hosted, open-source)
- Cohere embed-multilingual-v3.0 (API)
- OpenAI text-embedding-3-large (API)
- LaBSE (self-hosted, open-source)

### Decision

**Choose intfloat/multilingual-e5-large, self-hosted.**

### Rationale

1. **Arabic quality** — E5 Large مدرب على مزيج متوازن من AR + EN
2. **Cost** — self-hosted = $0 تشغيل بعد الـ setup
3. **Data sovereignty** — البيانات لا تغادر بيئتنا
4. **1024 dimensions** — توازن جيد بين الدقة والأداء (مقارنة 768 لـ LaBSE)
5. **Performance** — ONNX Runtime يمكن أن يشغل النموذج على CPU بكفاءة

### Tradeoffs

| Factor | Self-Hosted E5 | Cohere API | OpenAI API |
|--------|---------------|------------|------------|
| Cost | ~$30/mo (compute) | $0.10/1K tokens | $0.13/1K tokens |
| Arabic Quality | ★★★★★ | ★★★★★ | ★★★☆☆ |
| Latency | ~50ms | ~200ms | ~150ms |
| Data Privacy | ✅ Full | ⚠️ Data sent | ⚠️ Data sent |

### Consequences

- نحتاج instance مع 4 vCPU + 8GB RAM للتشغيل
- ONNX Runtime inference يستغرق ~50ms لكل batch
- سنحتاج تحديث النموذج دوريًا (كل 6 أشهر)

---

## ADR-003: Event Bus — Apache Kafka

| Field | Value |
|-------|-------|
| **ID** | ADR-003 |
| **Date** | 2026-07-11 |
| **Title** | Event Bus Replacement for TD-002 |
| **Status** | Accepted |
| **Owner** | Backend Engineer |

### Context

حل Technical Debt TD-002: استبدال in-memory Event Runtime الحالي. الخيارات:
- Apache Kafka
- RabbitMQ
- AWS SQS + SNS
- Redis Streams

### Decision

**Choose Apache Kafka.**

### Rationale

1. **Event sourcing** — Kafka يخزن events على القرص ويدعم replay
2. **Exactly-once semantics** — Required for event sourcing domains
3. **Consumer groups** — Flexible consumption patterns (fan-out, competing consumers)
4. **Scalability** — Horizontal scaling مع partitions
5. **Ecosystem** — Schema Registry, Kafka Connect, Kafka Streams
6. **Retention** — Configurable retention للـ events (7-90 يومًا)

### Tradeoffs

| Factor | Kafka | RabbitMQ | SQS+SNS | Redis Streams |
|--------|-------|----------|---------|---------------|
| Exactly-Once | ✅ | ❌ | ❌ (at-least-once) | ⚠️ |
| Event Replay | ✅ (retention) | ❌ | ❌ | ⚠️ |
| Operational Overhead | Medium | Low | None | Low |
| Throughput | Very High | High | High | Very High |
| Message Ordering | ✅ (per partition) | ❌ | ❌ | ✅ |

### Consequences

- نحتاج تشغيل Kafka cluster (3 brokers) و Schema Registry
- فريق DevOps يحتاج تدريب على Kafka operations
- فترة dual-run مع Event Runtime لمدة أسبوعين
- رفع تكلفة الـ infrastructure ~$330/شهر

---

## ADR-004: Workflow Engine — Custom State Machine (DAG)

| Field | Value |
|-------|-------|
| **ID** | ADR-004 |
| **Date** | 2026-07-11 |
| **Title** | Workflow Engine Design |
| **Status** | Accepted |
| **Owner** | Backend Engineer |

### Context

نحتاج محرك Workflow لأتمتة دورات المبيعات. الخيارات:
- Temporal.io (managed workflow engine)
- Apache Airflow
- Camunda BPMN
- Custom lightweight DAG engine
- AWS Step Functions

### Decision

**Choose custom lightweight DAG engine (Python + PostgreSQL).**

### Rationale

1. **Complexity fit** — Sales workflows are simple DAGs (5-15 steps). BPMN or Temporal overkill.
2. **No additional infra** — PostgreSQL لتخزين الحالة، Redis للـ locks
3. **Sales-specific** — Temporal/Airflow مصممة لـ engineering workflows، ليست sales
4. **Visual builder** — Custom engine يسمح ببناء UI مخصص (drag-and-drop)
5. **Integration** — يتكامل مباشرة مع NBA, Email, CRM بدون middle layer

### Tradeoffs

| Factor | Custom DAG | Temporal | Airflow | Step Functions |
|--------|-----------|----------|---------|---------------|
| Development Time | 3 weeks | 1 week | 1 week | 1 week |
| Operational Cost | ~$130/mo | ~$200/mo | ~$150/mo | ~$50/mo |
| Sales-Specific UX | ✅ Build what we need | ❌ Generic | ❌ Generic | ❌ Limited UI |
| Retry/DLQ | ✅ Built | ✅ Built | ✅ Built | ✅ Built |
| State Persistence | PostgreSQL | Temporal Server | Metadata DB | AWS-managed |

### Consequences

- نحتاج تطوير عمل إضافي (3 أسابيع) للـ engine + UI
- محدودية الميزات مقارنة بـ Temporal (مثل multi-instance, saga patterns)
- سنحتاج كتابة retry policy و DLQ بأنفسنا (لكنها بسيطة)

---

## ADR-005: Data Warehouse — Separate PostgreSQL Instance

| Field | Value |
|-------|-------|
| **ID** | ADR-005 |
| **Date** | 2026-07-11 |
| **Title** | Data Warehouse Storage |
| **Status** | Accepted |
| **Owner** | Backend Engineer |

### Context

نحتاج Data Warehouse للتحليلات منفصل عن operational DB. الخيارات:
- Separate PostgreSQL instance (OLTP for operations, OLAP for analytics)
- ClickHouse (columnar DB for analytics)
- TimescaleDB (time-series optimized)
- BigQuery / Snowflake (cloud warehouse)

### Decision

**Choose separate PostgreSQL instance with star-schema.**

### Rationale

1. **Team familiar** — نفس التقنية، لا تدريب جديد
2. **Sufficient for Wave 3** — 100-500 GB data, standard cubes، PostgreSQL يكفي
3. **Star schema** — Dimensions + Facts مناسبة لـ sales analytics
4. **Materialized views** — Pre-aggregation مع materialized views يعطي أداء جيدًا
5. **Future option** — الترحيل إلى ClickHouse أو BigQuery مستقبلًا سهل لأن الـ ETL مفصول

### Tradeoffs

| Factor | PostgreSQL (separate) | ClickHouse | BigQuery |
|--------|----------------------|------------|----------|
| Query Speed (cube) | ~500ms | ~100ms | ~200ms |
| Query Speed (custom) | ~3s | ~500ms | ~1s |
| Operational Overhead | Low | Medium | None |
| Cost | ~$400/mo | ~$300/mo | ~$200/mo + per-query |
| Learning Curve | None | Medium | Low |
| Saudi Data Residency | ✅ Self-hosted | ✅ Self-hosted | ❌ (depends on region) |

### Consequences

- نحتاج instance منفصل (8 vCPU, 32GB, 500GB SSD)
- ETL pipeline ينقل البيانات hourly (incremental) و daily (full)
- PostgreSQL ليس مثاليًا للـ OLAP الثقيل — نراقب الأداء
- نخطط للترقية إلى ClickHouse في Wave 4 إذا لزم الأمر

---

## ADR-006: RAG Generation — GPT-4o-mini as Primary

| Field | Value |
|-------|-------|
| **ID** | ADR-006 |
| **Date** | 2026-07-11 |
| **Title** | LLM Selection for RAG Generation |
| **Status** | Accepted |
| **Owner** | AI Engineer |

### Context

نحتاج LLM لـ RAG generation. الخيارات:
- GPT-4o (high quality, high cost)
- GPT-4o-mini (good quality, low cost)
- Claude 3.5 Sonnet (good Arabic, medium cost)
- Claude 3 Haiku (fast, low cost)
- Self-hosted LLM (Llama 70B, etc.)

### Decision

**Choose GPT-4o-mini as primary, GPT-4o for complex cases.**

### Rationale

1. **Cost efficiency** — GPT-4o-mini أرخص 20x من GPT-4o، وجودته ممتازة
2. **Arabic support** — GPT-4o-mini يدعم العربية بشكل جيد مع التوجيه الصحيح
3. **Citation accuracy** — GPT-4o-mini يحترم التعليمات بشكل جيد (يستخدم context فقط)
4. **Tiered approach** — 90% من requests تذهب إلى GPT-4o-mini، 10% (complex analysis) إلى GPT-4o
5. **Self-hosted option** — نراقب Llama 3.1 70B كخيار مستقبلي

### Tiered Routing

```python
class LLMRouter:
    def select_model(self, query: str, context: Context) -> str:
        """Route to appropriate model based on complexity."""
        if context.total_tokens > 4000:
            return "gpt-4o"              # Long context needs stronger model
        if self._is_complex_analysis(query):
            return "gpt-4o"              # Complex reasoning
        if query_language(query) == "ar":
            return "gpt-4o-mini"         # Arabic support is good
        return "gpt-4o-mini"             # Default
```

### Consequences

- نعتمد على API خارجي (OpenAI) — نحتاج fallback إذا كان API غير متاح
- التكلفة ~$200-300/شهر للـ 100K query
- نخطط لاختبار self-hosted Llama في Wave 4 لتقليل الاعتماد على API
- نحتاج rate limiting و queue management

---

## ADR-007: Real-Time Analytics — Kafka → Redis → WebSocket

| Field | Value |
|-------|-------|
| **ID** | ADR-007 |
| **Date** | 2026-07-11 |
| **Title** | Real-Time Analytics Pipeline |
| **Status** | Accepted |
| **Owner** | Backend Engineer |

### Context

نحتاج real-time updates لبعض المقاييس الحرجة (pipeline total value, win rate). الخيارات:
- Kafka → Stream processor → WebSocket
- Kafka → Redis → WebSocket
- Direct DB polling
- Server-Sent Events from batch system

### Decision

**Choose Kafka → Stream Processor → Redis → WebSocket.**

### Rationale

1. **Low latency** — Redis يخزن aggregations الحالية (< 100ms read)
2. **Kafka integration** — نفس الـ event bus يُغذي real-time pipeline
3. **Scalability** — WebSocket connections تتعامل مع load عبر horizontal scaling
4. **Simplicity** — Stream processor بسيط (Python + Redis) بدون framework ثقيل
5. **Separation** — Real-time pipeline منفصل عن الـ batch ETL

### Architecture

```
Kafka (pipeline.snapshot.changed)
      │
      ▼
Stream Processor (Python)
      │  Aggregates: total_value, deal_count, stage_value:{stage}, health:{level}
      ▼
Redis (real-time aggregates)
      │  Keys: pipeline:{tenant_id}:total_value
      │        pipeline:{tenant_id}:deal_count
      │        pipeline:{tenant_id}:stage:{stage}:value
      ▼
WebSocket Server
      │  Clients subscribe to Redis keys via channels
      ▼
Dashboard Components
```

### Consequences

- نحتاج Stream processor إضافي (بسيط)
- Redis يستخدم للـ caching + real-time
- Real-time metrics محدودة (5-10 metrics رئيسية)
- الـ batch pipeline يبقى المصدر الرئيسي للتقارير التاريخية

---

## Summary of Decisions

| ADR | Decision | Rationale | Cost Impact |
|-----|----------|-----------|-------------|
| ADR-001 | pgvector | Zero new infra, transactional consistency | $0 (existing) |
| ADR-002 | Self-hosted multilingual-e5 | Arabic quality, data privacy, $0/query | ~$30/mo compute |
| ADR-003 | Apache Kafka | Event sourcing, exactly-once, scalability | ~$330/mo |
| ADR-004 | Custom DAG engine | Sales-specific UX, integrated with NBA/CRM | ~$130/mo |
| ADR-005 | Separate PostgreSQL | Team familiar, sufficient for Wave 3 | ~$400/mo |
| ADR-006 | GPT-4o-mini primary | Cost-effective, good Arabic, tiered approach | ~$200-300/mo |
| ADR-007 | Kafka → Redis → WS | Low latency, real-time, simple architecture | ~$80/mo (Redis) |
| **Total** | | | **~$1,170/mo** |

---

## Decisions Deferred

| Decision | Expected Sprint | Reason |
|----------|----------------|--------|
| Self-hosted LLM (Llama 70B) | Wave 4 | ننتظر نضوج Arabic fine-tuning |
| ClickHouse migration | Wave 4 | PostgreSQL كافٍ الآن |
| Cross-opportunity optimization | Wave 4 | NBA الحالي لكل فرصة على حدة |
| Automated workflow execution | Wave 4 | Human-in-the-loop باقٍ في Wave 3 |

---

*Architecture Decision Records complete. Ready for Architecture Review Board approval.*
