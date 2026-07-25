# 07 — Database Audit

> **Generated:** 2026-07-15
> **Scope:** All data stores — PostgreSQL, Neo4j, Redis, vector/search, migrations
> **Source files:** `salesos/backend/` (database.py, config.py, sdk/, domains/, runtime/, app/)

---

## 1. PostgreSQL

### 1.1 Infrastructure

| Property | Value |
|----------|-------|
| **Image** | `pgvector/pgvector:pg16` |
| **Version** | PostgreSQL 16 + pgvector extension |
| **Host** | `postgres` (Docker service) |
| **Port** | 5432 (direct), 6432 (PgBouncer) |
| **Database** | `salesos` |
| **User** | `salesos` |
| **ORM** | SQLAlchemy async (`postgresql+asyncpg://`) |
| **Connection pool** | pool_size=20, max_overflow=10, pool_pre_ping=True, pool_recycle=1800s, pool_timeout=30s |
| **PgBouncer** | `edoburu/pgbouncer:latest` — transaction pooling, max_client=100, default_pool=25, min=5, reserve=5 |

### 1.2 Extensions

| Extension | Purpose | Migration |
|-----------|---------|-----------|
| `uuid-ossp` | UUID generation (`uuid_generate_v4()`) | 0001 |
| `pgcrypto` | Cryptographic functions | 0001 |
| `pg_trgm` | Trigram similarity for fuzzy search | 0001, re-enabled 0024 |
| `vector` | pgvector — vector embeddings for semantic search | 0001 |

### 1.3 Schemas

| Schema | Purpose | Created |
|--------|---------|---------|
| `audit` | Audit trail (legacy `audit_log` table) | 0001 |
| `identity` | (Reserved, not actively used) | 0001 |
| `company` | (Reserved, not actively used) | 0001 |
| `activity` | (Reserved, not actively used) | 0001 |
| `crm` | (Reserved, not actively used) | 0001 |
| `public` | All main tables | default |

### 1.4 Text Search Configuration

| Configuration | Purpose | Migration |
|---------------|---------|-----------|
| `arabic` (COPY OF simple) | Full-text search for Arabic text (stemming disabled — uses simple config) | 0001 |

### 1.5 Connection Settings (from `app/config.py`)

```python
database_url = "postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"
# host: postgres (default) → port 6432 (PgBouncer)
# host: localhost (local dev) → port 5432 (direct)

neo4j_uri = "bolt://neo4j:7687"
redis_url = "redis://redis:6379/0"
meili_url = "http://meilisearch:7700"
```

---

## 2. Table Inventory — PostgreSQL

### 2.1 Core Domain Tables (public schema)

| Table | Model | Columns (key) | Indexes | Migration |
|-------|-------|---------------|---------|-----------|
| `tenants` | `identity.models.Tenant` | id (UUID PK), name, slug (unique), domain, plan, is_active, settings (JSONB), features (JSONB), subscription_ends_at | ix_tenants_slug | 0001 |
| `users` | `identity.models.User` | id (UUID PK), tenant_id (FK→tenants), email (unique), password_hash, full_name, full_name_ar, role, is_active, is_verified, avatar_url, phone, preferences (JSONB), last_login_at, failed_login_attempts, locked_until | ix_users_email, ix_users_tenant_id | 0001, 0033 |
| `sources` | `company.models.Source` | id (UUID PK), name (unique), slug (unique), description, base_url, is_active, ingestion_config (JSONB) | — | 0001 |
| `companies` | `company.models.Company` | id (UUID PK), tenant_id (FK→tenants), name_ar, name_en, cr_number, cr_type, status, city, region, latitude, longitude, postal_code, phone, fax, email, website, address, capital, currency, employees_count, activity_description, activity_code, isic_code, isic_description, legal_form, incorporation_date, expiry_date, is_golden_record, confidence_score, source_ids (JSONB), is_active, tags (JSONB), metadata (JSONB), industry, search_vector (tsvector) | ix_companies_cr_number, ix_companies_name_ar, ix_companies_status, ix_companies_city, ix_companies_tenant_cr (unique), ix_companies_search (GIN tsvector), ix_companies_industry, ix_companies_name_ar_trgm, ix_companies_name_en_trgm | 0001, 0023, 0024, 0025, 0029, 0034 |
| `branches` | `company.models.Branch` | id (UUID PK), company_id (FK→companies), name_ar, name_en, branch_number, city, address, phone, latitude, longitude, is_active | — | 0001 |
| `licenses` | `company.models.License` | id (UUID PK), company_id (FK→companies), license_number, license_type, license_type_ar, status, issuing_authority, issue_date, expiry_date, renewal_date, source | ix_licenses_license_number | 0001 |
| `contacts` | `contact.models.Contact` | id (UUID PK), company_id (FK→companies), name, name_ar, email, phone, mobile, position, position_ar, department, is_primary, source, confidence_score | — | 0001, 0022 |
| `sso_connections` | `sso.models.SSOConnection` | id (VARCHAR PK), user_id (FK→users), provider, provider_user_id, provider_email, access_token, refresh_token, expires_at, is_active | ix_sso_user_provider | 0001 (init_db) |
| `audit_logs` | `audit.models.AuditLog` | id (BIGSERIAL PK), tenant_id, user_id, action, resource_type, resource_id, details (JSONB), ip_address, user_agent, request_id, created_at | ix_audit_logs_tenant_action, ix_audit_logs_tenant_resource, ix_audit_logs_created_at | 0001 (init_db) |
| `api_keys` | `api_keys.models.ApiKey` | id (VARCHAR PK), tenant_id (FK→tenants), user_id (FK→users), name, key_prefix, key_hash, permissions (JSONB), scopes, expires_at, is_revoked, revoked_at, last_used_at | ix_api_keys_prefix, ix_api_keys_user | 0001 (init_db) |

### 2.2 Entity Resolution Tables

| Table | Model | Columns (key) | Indexes | Migration |
|-------|-------|---------------|---------|-----------|
| `golden_records` | `entity_resolution.models.GoldenRecord` | id (UUID PK), tenant_id, cr_number, company_id (FK→companies), data (JSONB — provenance), confidence_score, source_ids (JSONB), is_active | ix_golden_records_tenant_cr (unique), ix_golden_records_tenant_company, ix_golden_records_tenant_active | 0001, 0030 |
| `entity_resolution_conflicts` | `entity_resolution.models.EntityResolutionConflict` | id (UUID PK), tenant_id, golden_record_id (FK→golden_records), field_name, source_a_value, source_a_source, source_b_value, source_b_source, resolution_strategy, resolved_by, resolved_at, status | ix_conflicts_tenant_status | 0001 |
| `entity_resolution_log` | `entity_resolution.models.EntityResolutionLog` | id (UUID PK), tenant_id, operation, source_slug, records_processed, records_matched, records_created, records_merged, confidence_threshold, details (JSONB) | — | 0001 |
| `dead_letter_queue` | `entity_resolution.models.DeadLetterRecord` | id (UUID PK), tenant_id, source_slug, cr_number, stage, record_data (JSONB), error_message, error_type, retry_count, max_retries, status, last_retry_at | — | 0011 |

### 2.3 Knowledge Graph Tables (SQL Fallback)

| Table | Model | Columns (key) | Indexes | Migration |
|-------|-------|---------------|---------|-----------|
| `graph_edges` | (raw SQL) | id (SERIAL PK), source_id (VARCHAR(64)), target_id (VARCHAR(64)), edge_type (VARCHAR(50)), properties (JSONB), created_at | ix_graph_edges_source, ix_graph_edges_target, ix_graph_edges_unique (unique: source+target+type) | 0004 |
| `graph_nodes` | (raw SQL) | id (VARCHAR(64) PK), tenant_id (VARCHAR(36)), labels (ARRAY(VARCHAR(50))), properties (JSONB), created_at, updated_at | ix_graph_nodes_tenant, ix_graph_nodes_search (GIN fulltext) | 0004 |

### 2.4 Vector / Embedding Tables

| Table | Model | Columns (key) | Indexes | Migration |
|-------|-------|---------------|---------|-----------|
| `vectors` | (PgVectorStore) | id (TEXT PK), embedding (ARRAY(FLOAT) / vector), metadata (JSONB), created_at, updated_at | ix_vectors_created_at | 0010, 0021 |
| `rag_documents` | (RAG runtime) | id (UUID PK), tenant_id, source_type, source_id, title, content, metadata (JSONB), created_at | idx_rag_chunks_tenant | 0015 |
| `rag_document_chunks` | (RAG runtime) | id (UUID PK), document_id (FK→rag_documents), content, embedding (vector(3072)), chunk_index, metadata (JSONB) | idx_rag_chunks_document | 0015 |

> **Note:** `rag_document_chunks.embedding` is `vector(3072)` (text-embedding-3-large). HNSW index was NOT created because 3072 exceeds the 2000-dim limit for HNSW in pgvector.

### 2.5 Feature Store Tables

| Table | Model | Columns (key) | Indexes | Migration |
|-------|-------|---------------|---------|-----------|
| `feature_definitions` | (Feature Store) | key (VARCHAR PK), name, description, feature_type, domain, created_at | — | 0026 |
| `feature_values` | (Feature Store) | id (VARCHAR PK), feature_key (FK→feature_definitions), entity_id, entity_type, value (JSON), computed_at, ttl_seconds | idx_feature_values_lookup (entity_type+entity_id+feature_key) | 0026 |

### 2.6 Commercial Domain Tables

| Table | Model | Columns (key) | Indexes | Migration |
|-------|-------|---------------|---------|-----------|
| `commercial_opportunities` | `OpportunityModel` | id, tenant_id, company_id, name, value, currency, stage, probability, expected_close_date, owner_id, status, won_amount, loss_reason, description, tags (JSON), metadata (JSON) | ix_commercial_opps_tenant_stage, ix_commercial_opps_tenant_status, ix_commercial_opps_owner | 0007, 0019 |
| `commercial_stage_entries` | `StageEntryModel` | id, tenant_id, opportunity_id (FK), pipeline_id, from_stage, to_stage, entered_at, exited_at, duration_hours | ix_stage_entries_opportunity, ix_stage_entries_tenant_entered | 0007, 0019 |
| `commercial_pipeline_definitions` | `PipelineDefinitionModel` | id, tenant_id, name, stages (JSON) | — | 0007, 0019 |
| `commercial_activity_sessions` | `ActivitySessionModel` | id, tenant_id, title, target_id, target_type, start_time, end_time, status, notes | ix_activity_sessions_tenant_status, ix_activity_sessions_target | 0007, 0019 |
| `commercial_activities` | `ActivityModel` | id, session_id (FK), activity_type, owner_id, owner_name, outcome_id, outcome_label, notes, scheduled_at, completed_at, status, external_id | ix_activities_type_status, ix_activities_owner | 0007, 0019 |
| `commercial_quotes` | `QuoteModel` | id, tenant_id, opportunity_id, title, status, total_value, currency, notes, sent_at, approved_by, approved_at, accepted_at, version | ix_commercial_quotes_tenant_status | 0007, 0019 |
| `commercial_quote_lines` | `QuoteLineModel` | id, quote_id (FK), description, quantity, unit_price, total | — | 0007, 0019 |
| `commercial_proposals` | `ProposalModel` | id, tenant_id, opportunity_id, quote_id, title, status, delivery_method, sent_at, viewed_at, accepted_at, rejected_at, rejection_reason, version | ix_commercial_proposals_tenant_status | 0007, 0019 |
| `commercial_contracts` | `ContractModel` | id, tenant_id, opportunity_id, quote_id, quote_revision, title, status, parties (JSON), obligations (JSON), effective_date, expiry_date, renewal (JSON), legal_terms, governing_law, signed_by_provider, signed_by_customer, notes, version | ix_commercial_contracts_tenant_status, ix_commercial_contracts_expiry | 0007, 0019 |
| `commercial_forecast_snapshots` | `ForecastSnapshotModel` | id, tenant_id, title, horizon_months, status, lines (JSON), assumptions (JSON), finalized_at, version | — | 0007, 0019 |
| `commercial_analytics_snapshots` | `AnalyticsSnapshotModel` | id, tenant_id, period_start, period_end, kpis (JSON), insights (JSON) | — | 0007, 0019 |
| `commercial_decision_contexts` | `DecisionContextModel` | id, tenant_id, target_id, target_type, factors (JSON), confidence | — | 0007, 0019 |
| `commercial_policies` | `PolicyModel` | id, tenant_id, name, rules (JSON), outcome, priority, enabled | — | 0007, 0019 |
| `commercial_recommendations` | `RecommendationModel` | id, tenant_id, target_id, target_type, title, description, recommendation_type, confidence, status, evidence (JSON), alternatives (JSON), applied_at, dismissed_at | ix_commercial_recs_tenant_status, ix_commercial_recs_target | 0007, 0019 |

### 2.7 Activity / Timeline / Analytics Tables

| Table | Model | Columns (key) | Indexes | Migration |
|-------|-------|---------------|---------|-----------|
| `activity_records` | (ActivityRuntime) | id (VARCHAR PK), actor, action, entity_type, entity_id, target_type, target_id, metadata (JSONB), tenant_id, timestamp | ix_activity_entity, ix_activity_tenant_action, ix_activity_actor, ix_activity_action | 0009, init_db |
| `domain_events` | (PostgresEventStore) | id (UUID PK), event_id (unique), event_type, event_version, aggregate_id, aggregate_type, tenant_id, occurred_at, data (JSONB), metadata (JSONB) | ix_domain_events_type, ix_domain_events_aggregate | 0001, init_db |
| `reports` | `analytics.models.ReportModel` | id, tenant_id, name, report_type, config (JSON), status, created_by, executed_at | — | 0014 |
| `report_executions` | `analytics.models.ReportExecutionModel` | id, report_id (FK), tenant_id, status, result (JSON), started_at, completed_at, error | — | 0014 |
| `timeline_events` | `timeline.models.TimelineEventModel` | id, tenant_id, entity_type, entity_id, event_type, payload (JSONB), created_at | — | 0005 |

### 2.8 Meetings / Emails

| Table | Model | Columns (key) | Indexes | Migration |
|-------|-------|---------------|---------|-----------|
| `meetings` | `MeetingModel` | id, tenant_id, opportunity_id, title, meeting_date, duration_minutes, notes, status | ix_meetings_tenant_date, ix_meetings_status | 0013 |
| `emails` | `EmailModel` | id, tenant_id, opportunity_id, subject, from_address, to_addresses (JSON), direction, email_type, body, sent_at | ix_emails_tenant_sent, ix_emails_direction | 0013 |

### 2.9 Authentication / Refresh Tokens

| Table | Model | Columns (key) | Indexes | Migration |
|-------|-------|---------------|---------|-----------|
| `refresh_tokens` | `identity.models.RefreshToken` | id (UUID PK), user_id (FK→users), token (unique), family_id, tenant_id, is_revoked, expires_at, created_at, revoked_at, device_info | — | 0012 |
| `refresh_token_families` | `identity.models.RefreshTokenFamily` | id (UUID PK), user_id (FK→users), family_id (unique), is_compromised, created_at | — | 0012 |

### 2.10 Notification / Workflow Tables

| Table | Model | Columns (key) | Indexes | Migration |
|-------|-------|---------------|---------|-----------|
| `notifications` | (InMemory in code — migration 0032 created table) | id, tenant_id, user_id, type, title, body, data (JSONB), read, created_at | — | 0032 |
| `workflows` | (Workflow domain — migration 0031) | id, tenant_id, name, description, trigger_type, status, steps (JSON) | — | 0031 |
| `workflow_executions` | (Workflow domain — migration 0031) | id, workflow_id (FK), tenant_id, trigger_event, status, started_at, completed_at, error, step_results (JSON) | — | 0031 |

### 2.11 Audit Tables (Public Schema — Non-ORM)

| Table | Created via | Columns (key) | Indexes |
|-------|-------------|---------------|---------|
| `audit.audit_log` | `init_db()` raw SQL | id (BIGSERIAL PK), tenant_id, entity_type, entity_id, action, changes (JSONB), performed_by, performed_at, ip_address, request_id, metadata (JSONB) | ix_audit_log_entity, ix_audit_log_tenant_performed |

### 2.12 Other Tables

| Table | Created via | Columns (key) | Migration |
|-------|-------------|---------------|-----------|
| `sso_connections` | `init_db()` raw SQL | id, user_id (FK→users), provider, provider_user_id, provider_email, access_token, refresh_token, expires_at, is_active | init_db |
| `api_keys` | `init_db()` raw SQL | id, tenant_id (FK→tenants), user_id (FK→users), name, key_prefix, key_hash, permissions (JSONB), scopes, expires_at, is_revoked, revoked_at, last_used_at | init_db |

---

## 3. Indexes Summary

### 3.1 Performance Indexes (from migrations 0027–0030)

| Migration | Index | Table | Columns | Type |
|-----------|-------|-------|---------|------|
| 0027 | ix_companies_search | companies | search_vector | GIN (tsvector) |
| 0027 | ix_companies_industry | companies | industry | btree |
| 0027 | ix_golden_records_confidence | golden_records | confidence_score | btree |
| 0028 | ix_companies_updated_at | companies | updated_at | btree |
| 0029 | ix_companies_name_ar_trgm | companies | name_ar | GIN (pg_trgm) |
| 0029 | ix_companies_name_en_trgm | companies | name_en | GIN (pg_trgm) |
| 0030 | ix_golden_records_tenant_active | golden_records | tenant_id, is_active | btree |

### 3.2 Full-Text Search

| Feature | Table | Column/Index | Config | Migration |
|---------|-------|--------------|--------|-----------|
| Company full-text | companies | search_vector (tsvector) | arabic | 0023, 0027 |
| Company trigram (ILIKE) | companies | name_ar, name_en | pg_trgm | 0024, 0029 |
| Graph nodes full-text | graph_nodes | properties (GIN) | simple | 0004 |

### 3.3 Vector Indexes

| Table | Index | Status | Notes |
|-------|-------|--------|-------|
| vectors | — | NO HNSW index | ARRAY(FLOAT) column — not native vector type |
| rag_document_chunks | — | NO HNSW index | vector(3072) exceeds 2000-dim HNSW limit |

---

## 4. Repository Pattern

### 4.1 SDK Layer (`sdk/database.py`)

| Class | Purpose |
|-------|---------|
| `Base` | SQLAlchemy `DeclarativeBase` — all models inherit from this |
| `BaseModel` | Adds `id` (UUID PK), `created_at`, `updated_at` with `TimestampMixin` |
| `Repository[T, TId]` | Abstract generic repository — `get`, `save`, `delete`, `exists` |
| `SqlAlchemyRepository[T, TId]` | Concrete SQLAlchemy implementation — adds `find_all` (offset pagination), `find_all_cursored` (cursor-based keyset pagination) |
| `UnitOfWork` | Transaction manager — wraps `async_sessionmaker`, auto-commit/rollback |
| `Specification` | Query filter builder (AndSpecification, OrSpecification) |

### 4.2 Domain Repository Implementations

| Domain | Repository | Location | Notes |
|--------|-----------|----------|-------|
| Search | `PostgresSearchRepository` | `domains/search/engine/postgres_repo.py` | Full-text (tsvector/tsquery), faceted aggregation, prefix suggestions, filter queries |
| Search (Vector) | `PgVectorStore` | `domains/search/engine/vector_store.py` | Cosine similarity search, upsert, delete via raw SQL |
| Search (Vector) | `InMemoryVectorStore` | `domains/search/engine/vector_store.py` | Brute-force cosine — dev/demo only |
| Entity Resolution | ORM models | `app/modules/entity_resolution/models.py` | Via BaseModel/SqlAlchemyRepository |
| Company | ORM models | `app/modules/company/models.py` | Via BaseModel/SqlAlchemyRepository |
| Identity | ORM models | `app/modules/identity/models.py` | Via BaseModel/SqlAlchemyRepository |
| Commercial | ORM models | `domains/commercial/infrastructure/models.py` | 14 models, all via Base |
| Analytics | ORM models | `domains/analytics/infrastructure/models.py` | ReportModel, ReportExecutionModel |
| Timeline | ORM models | `domains/timeline/models.py` | TimelineEventModel |
| Knowledge Graph | `KnowledgeGraphEngine` | `runtime/knowledge_graph_runtime/__init__.py` | Neo4j primary + SQL fallback (raw SQL via `graph_edges`/`graph_nodes`) |

---

## 5. Neo4j

### 5.1 Infrastructure

| Property | Value |
|----------|-------|
| **Image** | `neo4j:5-community` |
| **Host** | `neo4j` (Docker service) |
| **Ports** | 7475 (HTTP), 7688 (Bolt) |
| **Auth** | `neo4j` / `${NEO4J_PASSWORD}` |
| **Database** | `neo4j` |
| **Driver config** | max_connection_pool_size=50, connection_acquisition_timeout=30s, max_transaction_retry_time=10s, max_connection_lifetime=1800s |

### 5.2 Node Labels (from `NodeLabel` enum)

| Label | Purpose | Properties |
|-------|---------|------------|
| `Company` | Company entity | id, tenant_id, name_ar, name_en, cr_number, industry, city, region, status |
| `Person` | Contact/employee | id, tenant_id, name, email, phone, position |
| `Source` | Data source | — |
| `License` | Company license | id, tenant_id, license_number, license_type, status |
| `Branch` | Company branch | id, tenant_id, name_ar, city |
| `Product` | Company product | — |
| `FundingEvent` | Funding round | — |
| `JobPosting` | Job listing | — |
| `IntentSignal` | Buying intent signal | — |

### 5.3 Edge Types (from `EdgeType` enum)

| Edge | From → To | Properties |
|------|-----------|------------|
| `HAS_LICENSE` | Company → License | — |
| `HAS_BRANCH` | Company → Branch | — |
| `HAS_PRODUCT` | Company → Product | — |
| `EMPLOYS` | Company → Person | — |
| `RECEIVED_FUNDING` | Company → FundingEvent | — |
| `POSTED_JOB` | Company → JobPosting | — |
| `HAS_INTENT` | Company → IntentSignal | — |
| `SUBSIDIARY_OF` | Company → Company | — |
| `COMPETITOR_OF` | Company → Company | reason |
| `PARTNER_WITH` | Company → Company | reason |
| `INGESTED_FROM` | Entity → Source | — |
| `CONTACT_OF` | Person → Company | — |
| `REWIRED` | (temp) During merge | Created during node merge |

### 5.4 Full-Text Indexes (auto-created)

```cypher
CREATE FULLTEXT INDEX company_fulltext IF NOT EXISTS
FOR (n:COMPANY) ON EACH [n.name_ar, n.name_en, n.cr_number]

CREATE FULLTEXT INDEX person_fulltext IF NOT EXISTS
FOR (n:PERSON) ON EACH [n.name_ar, n.name_en, n.position, n.email]
```

### 5.5 Fallback Strategy

The `KnowledgeGraphEngine` implements a dual-store pattern:
1. **Primary:** Neo4j (via `neo4j` async driver)
2. **Fallback:** PostgreSQL (`graph_edges` + `graph_nodes` tables)

Routing logic (`_run` method):
- If Neo4j is available: try Neo4j → retry up to 3 times (exponential backoff) → fallback to SQL
- If Neo4j is unavailable: go straight to SQL
- SQL fallback provides: edge CRUD, competitor search, path finding, ego network, decision makers, search, entity subgraph, node merge

### 5.6 SQL Fallback Tables

| Table | Purpose |
|-------|---------|
| `graph_edges` | Stores all graph relationships (source_id, target_id, edge_type, properties) |
| `graph_nodes` | Stores graph node cache (id, tenant_id, labels, properties) |

---

## 6. Redis

### 6.1 Infrastructure

| Property | Value |
|----------|-------|
| **Image** | `redis:7-alpine` |
| **Host** | `redis` (Docker service) |
| **Port** | 6379 |
| **Persistence** | RDB (AOF disabled by default) |
| **Volume** | `redis-data:/data` |

### 6.2 Connection Settings

```python
redis_url = "redis://redis:6379/0"
redis_socket_connect_timeout = 2
redis_socket_timeout = 2
redis_health_socket_connect_timeout = 1
redis_health_socket_timeout = 1
```

### 6.3 Usage in Codebase

| Module | Class/File | Purpose | Graceful Degradation |
|--------|-----------|---------|---------------------|
| **Cache (SDK)** | `sdk/cache/__init__.py` → `CacheService` | High-level cache with typed get/set, TTL, `remember()` pattern | Fails if Redis unavailable |
| **Cache (Low-level)** | `sdk/cache/redis_cache.py` → `RedisCache` | Low-level wrapper with JSON serialization, scan_delete | ✅ Degrades to empty cache |
| **Cache (App)** | `app/cache.py` → `CacheService` | Backward-compatible wrapper accepting `redis_url` | ✅ Degrades (health() returns False) |
| **Redis Client** | `app/common/redis_client.py` → `AsyncRedisClient` | Singleton pattern, raw string get/set/delete | ✅ Degrades (returns None) |
| **Celery Broker** | `app/celery_app.py` | Celery task queue broker + result backend | N/A (hard dependency) |
| **Rate Limiter** | Middleware | IP-based rate limiting (auth:100/min, search:30/min, anon:20/min) | ✅ Degrades (allows all) |
| **Sessions** | Auth middleware | JWT token blacklist, session management | ✅ Degrades (allows all) |

### 6.4 Cache Key Patterns

| Pattern | TTL | Usage |
|---------|-----|-------|
| `search:{tenant}:{query_hash}` | 300s (5 min) | Search results cache |
| `company:{id}` | 300s | Company detail cache |
| `feature:{entity_type}:{entity_id}:{key}` | configurable (default 300s) | Feature store cache |
| `rate:{ip}:{window}` | 60s | Rate limiting counter |
| `celery:*` | varies | Celery result backend |

---

## 7. Search / Vector Infrastructure

### 7.1 PostgreSQL Full-Text Search

| Component | Implementation | Notes |
|-----------|---------------|-------|
| **tsvector column** | `companies.search_vector` | Auto-populated tsvector for Arabic/English |
| **tsquery** | `plainto_tsquery(:lang, :q)` | Config: `arabic` (COPY OF simple) |
| **GIN index** | `ix_companies_search` | Migration 0023, 0027 |
| **Ranking** | `ts_rank(search_vector, plainto_tsquery(...))` | PostgreSQL built-in ranking |
| **Trigram (ILIKE)** | `ix_companies_name_ar_trgm`, `ix_companies_name_en_trgm` | Migration 0024, 0029 — for partial/fuzzy match |
| **Timeout** | `SET LOCAL statement_timeout = 10000` (10s) | Per-query timeout |
| **Max page size** | 50 | Hard limit in `PostgresSearchRepository` |

### 7.2 Hybrid Search (`domains/search/engine/hybrid_search.py`)

- Combines full-text (tsvector/tsquery) + semantic (pgvector cosine similarity)
- Reciprocal Rank Fusion (RRF) to merge result sets
- Strategy selection via `strategy_matrix.py`

### 7.3 Vector Store (pgvector)

| Property | Value |
|----------|-------|
| **Table** | `vectors` (generic), `rag_document_chunks` (RAG-specific) |
| **Embedding model** | `text-embedding-3-large` (OpenAI) |
| **Dimension** | 3072 |
| **Distance** | Cosine (`<=>` operator) |
| **HNSW index** | ❌ Not created — 3072 dims exceeds 2000-dim limit |
| **Search method** | Sequential scan + ORDER BY cosine distance LIMIT N |

### 7.4 Meilisearch

| Property | Value |
|----------|-------|
| **URL** | `http://meilisearch:7700` |
| **Master key** | Configured via `MEILI_MASTER_KEY` |
| **Status** | Config-only — no active integration code found |
| **Usage** | Referenced in `config.py` and `demo audit` only |

---

## 8. Migration History

### 8.1 Overview

| Property | Value |
|----------|-------|
| **Tool** | Alembic |
| **Total migrations** | 34 (0001–0034) |
| **Baseline** | 0001 (2026-06-30) |
| **Latest** | 0034 (2026-07-15) |

### 8.2 Migration Timeline

| # | ID | Description | Date |
|---|-----|-------------|------|
| 1 | 0001 | Baseline: tenants, users, companies, branches, licenses, contacts, golden_records, conflicts, audit_log, domain_events | 2026-06-30 |
| 2 | 0002 | Feature store (feature_definitions, feature_values) | 2026-06-30 |
| 3 | 0003 | Decision engine tables | 2026-06-30 |
| 4 | 0004 | Knowledge graph SQL fallback (graph_edges, graph_nodes) | 2026-06-30 |
| 5 | 0005 | Timeline runtime (timeline_events) | 2026-06-30 |
| 6 | 0006 | Search runtime | 2026-06-30 |
| 7 | 0007 | Commercial domain (14 tables) | 2026-06-30 |
| 8 | 0008 | Contact module | 2026-06-30 |
| 9 | 0009 | Activity runtime (activity_records) | 2026-06-30 |
| 10 | 0010 | Vector store (vectors table) | 2026-07-12 |
| 11 | 0011 | Dead letter queue | 2026-07-12 |
| 12 | 0012 | Refresh token tables (refresh_tokens, refresh_token_families) | 2026-07-12 |
| 13 | 0013 | Meetings and emails | 2026-07-12 |
| 14 | 0014 | Analytics (reports, report_executions) | 2026-07-12 |
| 15 | 0015 | RAG tables (rag_documents, rag_document_chunks with vector(3072)) | 2026-07-12 |
| 16 | 0016 | Drop dual embedding column | 2026-07-12 |
| 17 | 0017 | HNSW index attempt (reverted — 3072 > 2000 dim limit) | 2026-07-12 |
| 18 | 0018 | Add feature store foreign keys | 2026-07-12 |
| 19 | 0019 | Add commercial domain foreign keys | 2026-07-12 |
| 20 | 0020 | Add tenant_id to various tables | 2026-07-12 |
| 21 | 0021 | Fix vectors embedding type (ARRAY(FLOAT) → vector) | 2026-07-12 |
| 22 | 0022 | Consolidate contacts (contacts_standalone → contacts) | 2026-07-12 |
| 23 | 0023 | Full-text search (companies.search_vector tsvector column + GIN index) | 2026-07-12 |
| 24 | 0024 | Enable pg_trgm extension | 2026-07-12 |
| 25 | 0025 | Hybrid search optimization | 2026-07-12 |
| 26 | 0026 | Feature store tables (feature_definitions, feature_values) | 2026-07-12 |
| 27 | 0027 | Performance indexes (search_vector GIN, industry btree) | 2026-07-12 |
| 28 | 0028 | Enrichment performance (updated_at index) | 2026-07-12 |
| 29 | 0029 | GIN trigram indexes (name_ar, name_en) | 2026-07-14 |
| 30 | 0030 | Confidence score index on golden_records | 2026-07-14 |
| 31 | 0031 | Workflow tables (workflows, workflow_executions) | 2026-07-14 |
| 32 | 0032 | Notifications table | 2026-07-14 |
| 33 | 0033 | Users lockout columns (failed_login_attempts, locked_until) | 2026-07-14 |
| 34 | 0034 | Add missing company columns (fax, website, industry, etc.) | 2026-07-15 |

---

## 9. Connection Flow

```
┌──────────────────────────────────────────────────────┐
│                     Application                       │
│  app/database.py                                     │
│  ┌─────────────────────────────────────────────────┐ │
│  │ engine = create_async_engine(                   │ │
│  │   "postgresql+asyncpg://salesos:***@postgres:6432/salesos" │ │
│  │   pool_size=20, max_overflow=10,                │ │
│  │   pool_pre_ping=True, pool_recycle=1800         │ │
│  │ )                                               │ │
│  │ async_session = async_sessionmaker(engine)      │ │
│  └──────────────────────┬──────────────────────────┘ │
│                         │                             │
│  ┌──────────────────────▼──────────────────────────┐ │
│  │  PgBouncer (port 6432)                          │ │
│  │  Transaction pooling, max_client=100            │ │
│  │  default_pool=25, min=5, reserve=5              │ │
│  └──────────────────────┬──────────────────────────┘ │
│                         │                             │
│  ┌──────────────────────▼──────────────────────────┐ │
│  │  PostgreSQL 16 + pgvector (port 5432)           │ │
│  │  Extensions: uuid-ossp, pgcrypto, pg_trgm, vector│ │
│  └─────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│  Neo4j 5 Community (bolt://neo4j:7687)              │
│  Driver pool: max=50, acquisition_timeout=30s       │
│  Fallback: SQL (graph_edges + graph_nodes tables)    │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│  Redis 7 Alpine (redis://redis:6379/0)              │
│  Used for: cache, Celery broker/backend,            │
│            rate limiting, sessions                   │
│  Graceful degradation: ✅ all cache ops fail safe    │
└──────────────────────────────────────────────────────┘
```

---

## 10. Key Observations

### 10.1 Architecture Strengths
- **Dual-store pattern (Neo4j + SQL fallback):** All graph operations degrade gracefully to PostgreSQL when Neo4j is unavailable
- **Redis graceful degradation:** All cache operations catch `RedisError` and return `None`/empty — no hard dependency
- **Repository pattern:** Clean separation between domain and infrastructure (`Repository → SqlAlchemyRepository → UnitOfWork`)
- **Connection pool monitoring:** `get_pool_metrics()` exposes live pool stats for Prometheus
- **PgBouncer:** Transaction-level connection pooling reduces PostgreSQL connection overhead
- **Full-text + trigram:** Dual search strategy — exact FTS (tsvector) + fuzzy (pg_trgm ILIKE)
- **Cursor-based pagination:** `find_all_cursored()` in `SqlAlchemyRepository` for efficient deep pagination

### 10.2 Known Issues
- **HNSW index missing on vector(3072):** `rag_document_chunks.embedding` cannot use HNSW (limit 2000 dims) — falls back to sequential scan
- **`vectors` table uses ARRAY(FLOAT), not native vector:** Migration 0021 attempted to fix but `vectors.embedding` remains `ARRAY(Float)` — not compatible with pgvector `<=>` operator
- **Duplicate vector models:** `sdk/vector.py::VectorRecord` and `domains/search/engine/vector_store.py::VectorRecord` are duplicated
- **Notifications in-memory only:** `InMemoryNotificationRepository` — no PostgreSQL persistence despite migration 0032 creating the table
- **Workflow/Notification models not registered:** `app/database.py` imports are missing `domains/workflow`, `domains/notifications`, `domains/scoring`
- **No Redis persistence config:** RDB snapshots only — no AOF, data loss risk on crash
- **`audit.audit_log` uses BIGSERIAL, not UUID:** Inconsistent with other tables (all use UUID PKs)
- **Meilisearch unused:** Configured but no active integration code

### 10.3 Table Count by Domain

| Domain | Table Count | Notes |
|--------|-------------|-------|
| Core (tenants, users, companies, etc.) | 10 | Public schema |
| Entity Resolution | 4 | golden_records, conflicts, log, DLQ |
| Knowledge Graph (SQL fallback) | 2 | graph_edges, graph_nodes |
| Vector / Embedding | 3 | vectors, rag_documents, rag_document_chunks |
| Feature Store | 2 | feature_definitions, feature_values |
| Commercial | 14 | Full CRM pipeline |
| Activity / Timeline / Analytics | 4 | activity_records, domain_events, reports, timeline_events |
| Meetings / Emails | 2 | meetings, emails |
| Auth (Refresh tokens) | 2 | refresh_tokens, refresh_token_families |
| Notifications / Workflow | 3 | notifications, workflows, workflow_executions |
| Audit | 2 | audit.audit_log (raw SQL), audit_logs (ORM) |
| Other (SSO, API keys) | 2 | sso_connections, api_keys |
| **Total** | **~50** | |

---

*End of Database Audit*
