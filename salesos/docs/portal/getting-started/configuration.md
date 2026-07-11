# Configuration Reference

> **مرجع الإعدادات — شرح جميع متغيرات البيئة**

All configuration is via environment variables. Below is the complete reference organized by domain.

---

## Core

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | ✅ | — | PostgreSQL connection string |
| `SECRET_KEY` | ✅ | — | JWT signing key (min 32 chars) |
| `ALLOWED_HOSTS` | ✅ | `localhost` | Comma-separated allowed CORS origins |
| `DEBUG` | ❌ | `false` | Enable debug mode (never in production) |
| `LOG_LEVEL` | ❌ | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

---

## Authentication & SSO

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JWT_ALGORITHM` | ❌ | `HS256` | JWT signing algorithm |
| `JWT_EXPIRY_MINUTES` | ❌ | `30` | Access token lifetime |
| `REFRESH_TOKEN_EXPIRY_DAYS` | ❌ | `7` | Refresh token lifetime |
| `SSO_PROVIDER` | ❌ | — | `azure`, `google`, `okta`, or `custom` |
| `SSO_CLIENT_ID` | SSO | — | OAuth client ID |
| `SSO_CLIENT_SECRET` | SSO | — | OAuth client secret |
| `SSO_TENANT` | Azure | — | Azure AD tenant ID |

See [SSO Setup Guide](../guides/sso-setup.md) for detailed configuration.

---

## Search

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SEARCH_ENGINE` | ❌ | `postgres` | `postgres`, `elasticsearch`, or `typesense` |
| `SEARCH_INDEX_PREFIX` | ❌ | `salesos_` | Prefix for search indices |
| `SEARCH_MAX_RESULTS` | ❌ | `100` | Max results per search query |
| `ELASTICSEARCH_URL` | Search | — | Elasticsearch connection string |

---

## NBA Engine (Wave 2)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | ❌ | — | Enables AI reasoning in NBA |
| `NBA_DEFAULT_SOURCE` | ❌ | `rule` | `rule`, `ai`, or `hybrid` |
| `NBA_RULE_ONLY_TIMEOUT_MS` | ❌ | `200` | Rule-only evaluation timeout |
| `NBA_AI_TIMEOUT_MS` | ❌ | `3000` | AI reasoning timeout |

---

## Email Integration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_CLIENT_ID` | ❌ | — | Gmail API client ID |
| `GOOGLE_CLIENT_SECRET` | ❌ | — | Gmail API client secret |
| `OUTLOOK_CLIENT_ID` | ❌ | — | Outlook API client ID |
| `OUTLOOK_CLIENT_SECRET` | ❌ | — | Outlook API client secret |
| `EMAIL_SYNC_INTERVAL_MINUTES` | ❌ | `30` | Email sync frequency |

---

## AI & RAG (Wave 3)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `EMBEDDING_MODEL` | ❌ | `intfloat/multilingual-e5-large` | Embedding model |
| `EMBEDDING_DIMENSIONS` | ❌ | `1024` | Vector dimensions |
| `EMBEDDING_CACHE_TTL_HOURS` | ❌ | `24` | Embedding cache lifetime |
| `LLM_PROVIDER` | ❌ | `openai` | `openai`, `anthropic`, or `azure` |
| `LLM_MODEL` | ❌ | `gpt-4o-mini` | Primary LLM model |
| `LLM_COMPLEX_MODEL` | ❌ | `gpt-4o` | Model for complex analysis |
| `OPENAI_API_KEY` | ❌ | — | Required for RAG generation |
| `RAG_MAX_CHUNKS` | ❌ | `10` | Max chunks per RAG query |
| `RAG_CONTEXT_MAX_TOKENS` | ❌ | `6000` | Max context window tokens |

---

## Kafka Event Bus (Wave 3)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `KAFKA_BOOTSTRAP_SERVERS` | ❌ | — | `host1:9092,host2:9092` |
| `KAFKA_CONSUMER_GROUP_PREFIX` | ❌ | `salesos_` | Consumer group prefix |
| `KAFKA_AUTO_OFFSET_RESET` | ❌ | `latest` | `latest` or `earliest` |
| `KAFKA_SECURITY_PROTOCOL` | ❌ | `PLAINTEXT` | `PLAINTEXT`, `SSL`, `SASL_SSL` |
| `KAFKA_SASL_MECHANISM` | SASL | — | `PLAIN`, `SCRAM-SHA-256` |
| `KAFKA_SASL_USERNAME` | SASL | — | Kafka username |
| `KAFKA_SASL_PASSWORD` | SASL | — | Kafka password |

---

## Redis Cache

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REDIS_URL` | ❌ | `redis://localhost:6379` | Redis connection string |
| `REDIS_PASSWORD` | ❌ | — | Redis auth password |
| `CACHE_DEFAULT_TTL` | ❌ | `300` | Default cache TTL in seconds |
| `CACHE_PREFIX` | ❌ | `salesos:` | Cache key prefix |

---

## Database

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_POOL_SIZE` | ❌ | `10` | PostgreSQL connection pool size |
| `DATABASE_MAX_OVERFLOW` | ❌ | `20` | Max overflow connections |
| `DATABASE_POOL_RECYCLE` | ❌ | `1800` | Connection recycle in seconds |
| `NEO4J_URI` | ❌ | `bolt://localhost:7687` | Neo4j connection URI |
| `NEO4J_USER` | ❌ | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | ❌ | — | Neo4j password |

---

## Monitoring

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SENTRY_DSN` | ❌ | — | Sentry error tracking DSN |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | ❌ | — | OpenTelemetry collector endpoint |
| `PROMETHEUS_METRICS_PORT` | ❌ | `9090` | Prometheus metrics endpoint |
| `HEALTH_CHECK_TOKEN` | ❌ | — | Health check auth token |

---

## Feature Flags

| Variable | Default | Description |
|----------|---------|-------------|
| `FF_NBA_ENABLED` | `true` | Enable NBA engine |
| `FF_MEETING_INTELLIGENCE` | `true` | Enable meeting intelligence |
| `FF_EMAIL_INTELLIGENCE` | `true` | Enable email intelligence |
| `FF_WORKFLOW_AUTOMATION` | `false` | Enable workflow engine |
| `FF_RAG_PIPELINE` | `false` | Enable RAG pipeline |
| `FF_KAFKA_EVENT_BUS` | `false` | Enable Kafka event bus |
