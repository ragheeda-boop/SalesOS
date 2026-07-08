# SalesOS — RUNTIME ARCHITECTURE

> **كيف يعيش النظام أثناء التشغيل — Execution Model, Resilience, Observability**
> Version 1.0 | Last Updated: 2026-06-30
> Owner: CTO / Chief Architect

---

## 1. REQUEST LIFECYCLE

Every request follows this deterministic path:

```
[User / Agent / API Consumer]
    │
    ▼
1. API GATEWAY — Rate limit, AuthN, TLS, routing (CloudFront → Nginx)
    │
    ▼
2. IDENTITY — Tenant resolution, AuthZ, RBAC, API key validation
    │
    ▼
3. CAPABILITY ROUTER — Route to capability (Company 360, Pipeline, AI, Search)
    │
    ▼
4. WORKFLOW ENGINE — Evaluate triggers, conditions, actions (if configured)
    │
    ▼
5. AI RUNTIME — Semantic Cache → RAG → LLM → Eval (if AI needed)
    │
    ▼
6. DATA FABRIC — Feature Store, Revenue Graph, Entity Resolution
    │
    ▼
7. REVENUE BRAIN — Next Best Action computation (async)
    │
    ▼
8. RECOMMENDATION — Evidence chain, confidence, alternatives
    │
    ▼
9. EVENTS — Every mutation → CloudEvent → Timeline → Projections
    │
    ▼
10. ANALYTICS — KPIs, Metrics, Business impact (async, eventual)
    │
    ▼
11. STORAGE — PostgreSQL, Neo4j, Redis, Data Lake
```

### Request Context

Every request carries a **RuntimeContext** propagated through the entire chain:

```python
@dataclass
class RuntimeContext:
    trace_id: UUID
    tenant_id: UUID
    user_id: UUID
    capability_id: str
    request_id: UUID
    start_time: datetime
    auth_context: AuthContext
    feature_flags: dict[str, bool]
```

The context is automatically created by the API Gateway and propagated via the SDK's `@with_runtime_context` decorator.

---

## 2. EXECUTION MODELS

### 2.1 Synchronous (CRUD)

```
Request → Gateway → Identity → Capability Router → Service → Repository → DB
                                                                              │
                                                                              ▼
                                                                         Response
```

Used for: Simple CRUD operations, search queries, data retrieval.
Timeout: 30 seconds.
Retry: Not applicable (idempotent reads only).

### 2.2 AI Query

```
Request → Gateway → Identity → AI Runtime
                                    │
                         Semantic Cache ──HIT──→ Return cached
                                    │
                                MISS
                                    ▼
                         SearchPlanner
                                    │
              ┌─────┬─────┬────┬────┴────┬────┬─────┐
              ▼     ▼     ▼    ▼         ▼    ▼     ▼
            PgVector Neo4j Timeline Feature Signals Data
            HNSW    Graph          Store         Lake
              └─────┴─────┴────┬────┴─────────┘
                               ▼
                         RRF Fusion
                               ▼
                         Rerank (cross-encoder)
                               ▼
                         LLM (GPT-4o-mini/4o)
                               ▼
                         Eval (confidence, hallucination)
                               ▼
                         Semantic Cache (store)
                               ▼
                         Response
```

### 2.3 Event-Driven (Async)

```
[Mutation] → [Domain Service] → [Domain Event] → [EventBus]
                                                      │
                                    ┌─────────────────┼──────────────────┐
                                    ▼                 ▼                  ▼
                              [Timeline]      [Feature Store]      [Knowledge Graph]
                              Append event    Recompute features   Update relations
                                    │                 │                  │
                                    ▼                 ▼                  ▼
                              [Analytics]      [Digital Twin]       [Search Index]
                              Update KPIs      Refresh state       Rebuild index
                                                      │
                                                      ▼
                                               [Revenue Brain]
                                               Recompute NBA
```

### 2.4 Scheduled (Cron)

```
[Scheduler] → [Workflow Engine] → [Condition Check]
                                        │
                                   True / False
                                        │
                                      True
                                        ▼
                                   [Execute Action]
                                        │
                                        ▼
                                   [Event / Notification]
```

### 2.5 Workflow (Multi-Step)

```
[Trigger: CompanyCreated / SignalDetected / Schedule]
       │
       ▼
[Workflow Engine: resolve conditions]
       │
       ▼
[Simulation Engine: "What happens?"]
       ├── Predict: replies, meetings, revenue
       ├── Risk: compliance, rate limits, negative response
       └── Recommendation: proceed / modify / abort
       │
       ▼
[Execute: Email / Webhook / Update / AI Agent]
       │
       ▼
[Event: WorkflowExecuted → Timeline → Metrics → Digital Twin]
```

---

## 3. RESILIENCE PATTERNS

### 3.1 Circuit Breaker

```
┌─────────┐    failure > threshold     ┌────────┐    timeout     ┌───────┐
│  CLOSED  │ ────────────────────────→ │  OPEN   │ ───────────→ │ HALF  │
│ (normal) │                           │ (block) │              │ OPEN  │
└─────────┘                            └────────┘              └───┬───┘
      ↑                                                             │
      └─────────────────── success ────────────────────────────────┘
```

Every external call (DB, LLM, API, Scraper) is wrapped with `@circuit_breaker(max_failures=5, reset_timeout=30)`.

### 3.2 Retry with Backoff

```
Attempt 1: 0s
Attempt 2: 1s
Attempt 3: 2s
Attempt 4: 4s
Attempt 5: 8s
Max: 5 attempts, 15s total, jitter ±20%
```

Implemented by SDK `@retry(max_retries=5, backoff=exponential, jitter=true)`.

### 3.3 Timeout

| Capability | Timeout | Source |
|-----------|---------|--------|
| CRUD (read) | 10s | DB query timeout |
| CRUD (write) | 30s | DB write timeout |
| AI (GPT-4o-mini) | 15s | LLM API timeout |
| AI (GPT-4o) | 30s | LLM API timeout |
| Search | 5s | Aggregated search timeout |
| Scraper | 120s | External API timeout |
| Workflow | 300s | Multi-step workflow timeout |

### 3.4 Fallback

When a capability fails, the system degrades gracefully:

| Primary | Fallback | Acceptable? |
|---------|----------|-------------|
| PostgreSQL | Redis cache (stale) | ✅ Read-only |
| Neo4j | PostgreSQL (stale) | ✅ Read-only |
| LLM API | Cache (stale) | ✅ Low confidence |
| Scraper | Last known good data | ✅ Stale acceptable |
| Feature Store | Default values | ✅ Acceptable |

### 3.5 Bulkhead

Each capability gets an isolated resource pool:

```
Capability        │ Max Concurrency │ Queue Size
──────────────────┼─────────────────┼───────────
Search            │ 50              │ 100
AI                │ 20              │ 50
Workflow          │ 10              │ 20
Scraper           │ 5               │ 10
Webhook           │ 30              │ 50
```

If a capability's pool is full, new requests return HTTP 503 with `Retry-After` header.

---

## 4. OBSERVABILITY

### 4.1 Three Pillars

```
[Every Request] → [Tracing: OpenTelemetry spans]
                → [Logging: structlog JSON to stdout]
                → [Metrics: Prometheus counters + histograms]
```

### 4.2 Tracing

Every request gets a `trace_id` (UUID v7 with timestamp prefix), propagated through all services via HTTP headers.

Spans:
- `http.request` — Gateway → Response
- `identity.auth` — AuthN + AuthZ
- `capability.route` — Router → Capability
- `db.query` — Database operation
- `ai.invoke` — LLM call (with token count)
- `event.publish` — EventBus emission
- `cache.hit/miss` — Cache operations

### 4.3 Structured Logging

Every log line is JSON with:
```json
{
  "timestamp": "2026-06-30T10:00:00Z",
  "level": "info",
  "trace_id": "0192abcd-...",
  "tenant_id": "uuid",
  "capability": "search",
  "event": "search.executed",
  "duration_ms": 142,
  "query": "Riyadh construction companies",
  "results_count": 25,
  "error": null
}
```

### 4.4 Business Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `http_requests_total` | Counter | tenant, capability, status, method | Total requests |
| `http_request_duration_ms` | Histogram | tenant, capability | Request latency |
| `ai_tokens_total` | Counter | model, tenant | Token usage |
| `ai_cost_total` | Counter | model, tenant | Cost in USD |
| `ai_cache_hit_ratio` | Gauge | tenant | Semantic Cache hit rate |
| `events_emitted_total` | Counter | event_type, tenant | Events published |
| `searches_total` | Counter | tenant | Search count |
| `capability_errors_total` | Counter | capability, error_type | Error count |
| `digital_twin_state_version` | Gauge | tenant | Current DT version |

### 4.5 SLAs

| Metric | Target | Measurement |
|--------|--------|-------------|
| API Availability | 99.9% | Uptime over 30d |
| API Latency (p95) | <500ms | Over 5min window |
| AI Latency (p95) | <5s | Over 5min window |
| Search Latency (p95) | <200ms | Over 5min window |
| Error Rate | <1% | Over 5min window |
| Event Delivery | 99.99% | Events delivered within 5s |

---

## 5. DIGITAL TWIN RUNTIME

### 5.1 State Computation

```
[Event Stream] → [State Manager: apply event to current state]
                    │
                    ▼
              [Version Bump: snapshot_id += 1]
                    │
                    ▼
              [Predictor: ML model inference]
                    │
                    ▼
              [Risk Detector: rule + AI evaluation]
                    │
                    ▼
              [Scenario Simulator: what-if analysis]
                    │
                    ▼
              [Revenue Brain: recompute NBA]
                    │
                    ▼
              [Cache: store in Redis with version key]
```

### 5.2 Feedback Loop

```
[Action Taken] → [Outcome Observed]
                    │
                    ▼
              [Compare: Actual vs Predicted]
                    │
                    ▼
              [Record: PredictionAccuracy event]
                    │
                    ▼
              [Model Retrain: if accuracy < threshold]
                    │
                    ▼
              [Update: Digital Twin model version]
```

---

## 6. CAPABILITY EXECUTION CHECKLIST

Before a capability is promoted to production:

- [ ] All 3 execution paths documented (sync, async, event-driven)
- [ ] Timeout configured in capability registry
- [ ] Circuit breaker parameters set
- [ ] Retry policy defined
- [ ] Fallback strategy documented
- [ ] Bulkhead pool size configured
- [ ] Traces instrumented with meaningful spans
- [ ] Logs structured with all required fields
- [ ] Business metrics registered in Prometheus
- [ ] SLA targets documented and monitored
- [ ] Digital Twin state integration designed
- [ ] Error responses follow RFC 7807

---

*This document describes the runtime behavior of the SalesOS platform. All capabilities must conform to these execution models. Exceptions require documented justification and CTO approval.*
