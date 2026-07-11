# Wave 3 Infrastructure Architecture

> **الهدف:** توثيق متطلبات البنية التحتية لـ Wave 3 — الخدمات الجديدة، التوسع، التكاليف، والمراقبة
>
> **تاريخ:** 2026-07-11
> **المرحلة:** Wave 3 — Infrastructure

---

## 1. New Services Overview

```
Wave 3 Services
      │
      ├── AI / RAG
      │     ├── Document Ingestion Service
      │     ├── Embedding Service
      │     ├── RAG Retrieval Service
      │     ├── RAG Generation Service
      │     └── Citation Verification Service
      │
      ├── Event Bus
      │     ├── Kafka Cluster (3 brokers)
      │     ├── Schema Registry
      │     └── DLQ Consumer
      │
      ├── Workflow
      │     ├── Workflow Engine Service
      │     ├── Action Executor Service
      │     ├── Trigger Resolver Service
      │     └── Workflow Builder (Frontend)
      │
      ├── Analytics
      │     ├── Data Warehouse (PostgreSQL)
      │     ├── ETL Pipeline Service
      │     ├── Cube Builder Service
      │     ├── Report API Service
      │     ├── Export Engine Service
      │     └── Report Scheduler Service
      │
      └── Shared
            ├── Redis Cache Cluster
            └── Monitoring Stack
```

---

## 2. Service Specifications

### 2.1 Document Ingestion Service

| Property | Value |
|----------|-------|
| **Runtime** | Python 3.12 |
| **Framework** | FastAPI |
| **CPU** | 2 vCPU |
| **Memory** | 4 GB RAM |
| **Storage** | 50 GB (document storage) |
| **Scaling** | Horizontal (event-driven, max 4 replicas) |
| **Dependencies** | PostgreSQL, Redis, Kafka (producer) |
| **Key Libraries** | PyMuPDF, python-docx, BeautifulSoup, OCR |
| **Sprint** | 10 |

### 2.2 Embedding Service

| Property | Value |
|----------|-------|
| **Runtime** | Python 3.12 |
| **Framework** | FastAPI + ONNX Runtime |
| **CPU** | 4 vCPU (or GPU optional) |
| **Memory** | 8 GB RAM |
| **Storage** | 10 GB (model cache) |
| **Scaling** | Horizontal (CPU-bound, max 3 replicas) |
| **Dependencies** | Redis (L1 cache), pgvector (L2 cache) |
| **Model** | intfloat/multilingual-e5-large (self-hosted) |
| **Sprint** | 10 |

### 2.3 RAG Retrieval Service

| Property | Value |
|----------|-------|
| **Runtime** | Python 3.12 |
| **Framework** | FastAPI |
| **CPU** | 2 vCPU |
| **Memory** | 4 GB RAM |
| **Scaling** | Horizontal, max 5 replicas |
| **Dependencies** | pgvector, Embedding Service, Redis |
| **Sprint** | 10 |

### 2.4 RAG Generation Service

| Property | Value |
|----------|-------|
| **Runtime** | Python 3.12 |
| **Framework** | FastAPI + LangChain / LlamaIndex |
| **CPU** | 2 vCPU |
| **Memory** | 4 GB RAM |
| **Scaling** | Horizontal (I/O bound), max 5 replicas |
| **Dependencies** | LLM API (OpenAI/Claude), Context Manager |
| **Sprint** | 10 |

### 2.5 Kafka Cluster

| Property | Value |
|----------|-------|
| **Software** | Apache Kafka 3.x (KRaft mode) |
| **Brokers** | 3 |
| **CPU per Broker** | 4 vCPU |
| **Memory per Broker** | 8 GB RAM |
| **Storage per Broker** | 100 GB SSD (GP3) |
| **Network** | 1 Gbps |
| **Sprint** | 11 |

### 2.6 Schema Registry

| Property | Value |
|----------|-------|
| **Software** | Confluent Schema Registry |
| **Instances** | 2 (HA) |
| **CPU** | 2 vCPU |
| **Memory** | 4 GB RAM |
| **Storage** | 20 GB |
| **Sprint** | 11 |

### 2.7 Workflow Engine Service

| Property | Value |
|----------|-------|
| **Runtime** | Python 3.12 |
| **Framework** | FastAPI |
| **CPU** | 2 vCPU |
| **Memory** | 4 GB RAM |
| **Scaling** | Horizontal (event-driven), max 6 replicas |
| **Dependencies** | Kafka (consumer + producer), PostgreSQL, Redis |
| **Sprint** | 12 |

### 2.8 Data Warehouse (PostgreSQL)

| Property | Value |
|----------|-------|
| **Version** | PostgreSQL 16 |
| **CPU** | 8 vCPU |
| **Memory** | 32 GB RAM |
| **Storage** | 500 GB SSD (provisioned IOPS) |
| **Extensions** | None (separate from operational DB) |
| **Backup** | Daily snapshot + WAL streaming |
| **Sprint** | 13 |

### 2.9 ETL Pipeline Service

| Property | Value |
|----------|-------|
| **Runtime** | Python 3.12 |
| **Framework** | Apache Airflow / Prefect |
| **CPU** | 4 vCPU |
| **Memory** | 8 GB RAM |
| **Storage** | 50 GB (DAGs, logs) |
| **Scaling** | Worker auto-scaling |
| **Dependencies** | Operational DB, Warehouse, Kafka |
| **Sprint** | 13 |

### 2.10 Report Scheduler Service

| Property | Value |
|----------|-------|
| **Runtime** | Python 3.12 |
| **Framework** | FastAPI + Celery |
| **CPU** | 2 vCPU |
| **Memory** | 4 GB RAM |
| **Storage** | 100 GB (temporary report generation) |
| **Scaling** | Horizontal (Celery workers), max 4 |
| **Dependencies** | Warehouse, Email Service, S3 |
| **Sprint** | 13 |

---

## 3. Scaling Considerations

### 3.1 RAG Pipeline Scaling

```
Component             │  Bottleneck         │  Scaling Strategy
──────────────────────┼─────────────────────┼─────────────────────────
Document Ingestion    │  I/O (PDF parsing)  │  Parallel workers
Embedding             │  CPU (model infer)  │  GPU instance + batch
Vector Search         │  CPU/Memory         │  HNSW index + partitioning
LLM Generation        │  API rate limit     │  Queue + tiered models
Cache                 │  Memory             │  Redis Cluster
```

### 3.2 Kafka Scaling

```
Metric                │  Current (Wave 3)   │  Future (Wave 4)
──────────────────────┼─────────────────────┼─────────────────────────
Topics                │  20                 │  50+
Messages/sec          │  500                │  5,000+
Partitions total      │  80                 │  200+
Consumer Groups       │  15                 │  30+
Data throughput       │  5 MB/s             │  50 MB/s
Retention             │  7-90 days          │  30-365 days
```

### 3.3 Data Warehouse Scaling

| Stage | Data Volume | Query Complexity | Scaling Action |
|-------|------------|-----------------|----------------|
| Launch (Sprint 13) | < 100 GB | Standard cubes | Single node (8 vCPU, 32GB) |
| 6 months | 100-500 GB | Custom reports | Add replicas for read-only queries |
| 12 months | 500 GB - 2 TB | Complex analytics | Partition by month + parallel queries |
| 24 months | > 2 TB | Machine learning | TimescaleDB or ClickHouse migration |

---

## 4. Cost Estimates (Monthly)

### Infrastructure Costs

| Service | Type | Unit Cost | Qty | Monthly |
|---------|------|-----------|-----|---------|
| **RAG Pipeline** | | | | |
| Document Ingestion | Container (2 vCPU, 4GB) | $30 | 2 | $60 |
| Embedding Service | Container (4 vCPU, 8GB) | $60 | 2 | $120 |
| RAG Retrieval | Container (2 vCPU, 4GB) | $30 | 2 | $60 |
| RAG Generation | Container (2 vCPU, 4GB) | $30 | 2 | $60 |
| *Subtotal* | | | | **$300** |

| | | | | |
| **Kafka Event Bus** | | | | |
| Kafka Brokers | EC2 (4 vCPU, 8GB) | $80 | 3 | $240 |
| Storage (SSD) | 100 GB × 3 | $0.10/GB | 300 GB | $30 |
| Schema Registry | Container (2 vCPU, 4GB) | $30 | 2 | $60 |
| *Subtotal* | | | | **$330** |

| | | | | |
| **Workflow Engine** | | | | |
| Engine Service | Container (2 vCPU, 4GB) | $30 | 2 | $60 |
| Action Executor | Container (2 vCPU, 4GB) | $30 | 2 | $60 |
| Builder Frontend | Static hosting | $10 | 1 | $10 |
| *Subtotal* | | | | **$130** |

| | | | | |
| **Analytics** | | | | |
| Data Warehouse | PostgreSQL (8 vCPU, 32GB) | $400 | 1 | $400 |
| ETL Pipeline | Airflow (4 vCPU, 8GB) | $60 | 1 | $60 |
| Report Scheduler | Container (2 vCPU, 4GB) | $30 | 2 | $60 |
| Cube Builder | Container (2 vCPU, 4GB) | $30 | 1 | $30 |
| *Subtotal* | | | | **$550** |

| | | | | |
| **Shared** | | | | |
| Redis Cache | ElastiCache (2 vCPU, 4GB) | $40 | 2 | $80 |
| Monitoring Stack | Prometheus + Grafana | $50 | 1 | $50 |
| *Subtotal* | | | | **$130** |

### API Costs

| Service | Usage Estimate | Unit Cost | Monthly |
|---------|---------------|-----------|---------|
| Embedding API (self-host) | 500K chunks/mo | $0.00 | $0 |
| LLM (GPT-4o-mini) | 100K queries/mo | $0.002/query | $200 |
| LLM (GPT-4o) | 10K complex queries/mo | $0.01/query | $100 |
| Total API | | | **$300** |

### Total Monthly Cost

| Category | Amount |
|----------|--------|
| Infrastructure | $1,440 |
| API / LLM | $300 |
| **Total Wave 3** | **$1,740/mo** |
| Wave 1 + 2 (existing) | ~$2,000/mo |
| **Total SalesOS** | **~$3,740/mo** |

---

## 5. Monitoring Additions

### Prometheus Metrics (per service)

| Metric | Type | Service |
|--------|------|---------|
| `rag_ingestion_duration_ms` | Histogram | Document Ingestion |
| `rag_embedding_duration_ms` | Histogram | Embedding Service |
| `rag_retrieval_duration_ms` | Histogram | RAG Retrieval |
| `rag_generation_duration_ms` | Histogram | RAG Generation |
| `rag_cache_hit_ratio` | Gauge | Embedding Service |
| `rag_citation_accuracy` | Gauge | Citation Verification |
| `kafka_consumer_lag` | Gauge | All consumers |
| `kafka_dlq_count` | Counter | DLQ Consumer |
| `workflow_execution_duration_ms` | Histogram | Workflow Engine |
| `workflow_success_rate` | Gauge | Workflow Engine |
| `warehouse_query_duration_ms` | Histogram | Report API |
| `warehouse_cube_freshness` | Gauge | Cube Builder |
| `report_export_duration_ms` | Histogram | Export Engine |

### Grafana Dashboards

| Dashboard | Panels |
|-----------|--------|
| **RAG Pipeline** | Ingestion rate, Embedding latency, Retrieval p95, Generation latency, Cache hit ratio, Citation accuracy |
| **Kafka Cluster** | Broker health, Partition count, Consumer lag per group, Produce/Consume rate, DLQ count, Under-replicated partitions |
| **Workflow Engine** | Active executions, Success rate, Avg duration, Failure breakdown, Trigger rate, SLA compliance |
| **Analytics** | Warehouse query performance, Cube refresh status, ETL pipeline health, Report generation time |
| **Wave 3 Overview** | All services health, Cost tracking, Error rate, Request rate, Resource utilization |

### Alerting Rules

| Alert | Condition | Severity | Channel |
|-------|-----------|----------|---------|
| RAG retrieval latency high | p95 > 2s for 5 min | Warning | Slack |
| Embedding cache hit low | < 60% for 15 min | Warning | Slack |
| Citation accuracy low | < 85% for 30 min | Critical | Slack + Email |
| Kafka consumer lag critical | > 100,000 for 5 min | Critical | PagerDuty |
| Kafka broker down | Broker offline for 1 min | Critical | PagerDuty |
| Workflow failure rate high | > 10% failure for 15 min | Warning | Slack |
| Warehouse query timeout | > 5s for 10 min | Warning | Slack |
| ETL pipeline stalled | No new data for 2 hours | Critical | Slack + Email |
| Cost anomaly | Daily cost > 2x average | Warning | Email |

---

## 6. Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Kubernetes Cluster                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  RAG Pods     │  │  Workflow    │  │  Analytics    │       │
│  │  (5 services) │  │  Pods (3)    │  │  Pods (4)     │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐     │
│  │              Istio Service Mesh                        │     │
│  │  Mutual TLS, Traffic Management, Observability        │     │
│  └──────────────────────────────────────────────────────┘     │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  PostgreSQL   │  │  Redis       │  │  Kafka (3)   │       │
│  │  (Stateful)   │  │  (Stateful)  │  │  (Stateful)  │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. Security Considerations

| Concern | Mitigation |
|---------|------------|
| LLM API keys | Stored in Kubernetes Secrets / Vault; not in code |
| Embedding model data | Self-hosted model; no data sent to third parties |
| PII in documents | Document ingestion strips PII before embedding |
| Kafka encryption | TLS for inter-broker + client-broker communication |
| Kafka authentication | SASL/SCRAM for all client connections |
| Warehouse access | Read-only user for analytics; separate from operational credentials |
| Report exports | Generated reports stored in private S3 with presigned URLs |
| API rate limiting | Per-tenant rate limits on all Wave 3 services |

---

*Wave 3 Infrastructure complete. Ready for cost review and deployment planning.*
