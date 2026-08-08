# 08 — DATABASE: ERD, Tables, Migrations, RLS

> Source: Source code analysis (Phase 8)
> Classification: IMPLEMENTATION ONLY

---

## 1. Database Architecture

### 1.1 Dual-Engine Pattern

```
┌─────────────────────────────────────────────┐
│              Application Layer               │
│                                              │
│  ┌──────────────┐    ┌──────────────────┐   │
│  │  app role     │    │  owner role       │   │
│  │  salesos_app  │    │  salesos          │   │
│  │  (RLS enforced)│   │  (BYPASSRLS)     │   │
│  └──────┬───────┘    └────────┬─────────┘   │
│         │                      │              │
│         ▼                      ▼              │
│  ┌──────────────┐    ┌──────────────────┐   │
│  │  engine       │    │  owner_engine     │   │
│  │  pool: 20     │    │  pool: 5          │   │
│  │  overflow: 10 │    │  overflow: 2      │   │
│  └──────┬───────┘    └────────┬─────────┘   │
│         │                      │              │
│         ▼                      ▼              │
│  ┌─────────────────────────────────────┐    │
│  │           PostgreSQL                 │    │
│  │  - pg_trgm (trigram search)         │    │
│  │  - uuid-ossp (UUID generation)      │    │
│  │  - vector (pgvector embeddings)     │    │
│  │  - RLS policies on tenant tables    │    │
│  └─────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
```

### 1.2 Extensions

| Extension | Purpose |
|-----------|---------|
| `pg_trgm` | Trigram similarity search (Arabic/English fuzzy matching) |
| `uuid-ossp` | UUID generation |
| `vector` | pgvector embedding similarity search |

---

## 2. Tables (Discovered from Models + Migrations)

### 2.1 Identity & Access

| Table | Purpose | tenant_id |
|-------|---------|-----------|
| `tenants` | Multi-tenant organizations | N/A (root) |
| `users` | Auth users | ✅ |
| `refresh_token_families` | Token rotation tracking | ✅ |
| `device_sessions` | Device tracking | ✅ |
| `password_reset_tokens` | Password reset | ✅ |
| `token_blacklists` | JWT revocation | ✅ |
| `sso_connections` | SSO provider links | ✅ |
| `api_keys` | API key management | ✅ |

### 2.2 Core Business

| Table | Purpose | tenant_id |
|-------|---------|-----------|
| `companies` | Company profiles | ✅ |
| `branches` | Company branches | ✅ |
| `licenses` | Company licenses | ✅ |
| `contacts` | People linked to companies | ✅ |
| `employees` | Employee profiles | ✅ |
| `opportunities` | Sales opportunities | ✅ |
| `pipelines` | Sales pipelines | ✅ |
| `pipeline_stages` | Pipeline stages | ✅ |

### 2.3 Commercial

| Table | Purpose | tenant_id |
|-------|---------|-----------|
| `contracts` | Legal agreements | ✅ |
| `proposals` | Communication documents | ✅ |
| `quotes` | Commercial drafts | ✅ |

### 2.4 Intelligence

| Table | Purpose | tenant_id |
|-------|---------|-----------|
| `feature_values` | Computed feature scores | ✅ |
| `golden_records` | Merged authoritative entities | ✅ |
| `entity_resolution_conflicts` | Field-level conflicts | ✅ |
| `entity_resolution_logs` | Resolution audit trail | ✅ |
| `analytics_events` | Business analytics events | ✅ |
| `analytics_aggregates` | Pre-computed analytics | ✅ |

### 2.5 AI & Search

| Table | Purpose | tenant_id |
|-------|---------|-----------|
| `vector_embeddings` | pgvector embeddings | ✅ |
| `copilot_sessions` | Copilot chat sessions | ✅ |
| `copilot_feedback` | Copilot feedback | ✅ |
| `prompt_library` | Versioned prompts | ✅ |
| `ai_policies` | AI governance policies | ✅ |
| `ai_memory` | Conversation memory | ✅ |

### 2.6 Workflow & Automation

| Table | Purpose | tenant_id |
|-------|---------|-----------|
| `workflows` | Workflow definitions | ✅ |
| `workflow_steps` | Workflow step definitions | ✅ |
| `workflow_executions` | Workflow run history | ✅ |
| `rules` | Business rules | ✅ |
| `rule_definitions` | Rule logic | ✅ |

### 2.7 Billing & Subscriptions

| Table | Purpose | tenant_id |
|-------|---------|-----------|
| `plans` | Subscription plans | N/A (platform) |
| `subscriptions` | Tenant subscriptions | ✅ |
| `usage_meters` | Usage tracking | ✅ |
| `invoices` | Billing invoices | ✅ |
| `dunning_events` | Payment retry events | ✅ |
| `proration_entries` | Plan change proration | ✅ |

### 2.8 Admin & Platform

| Table | Purpose | tenant_id |
|-------|---------|-----------|
| `feature_flags` | Feature toggles | N/A (platform) |
| `entitlements` | Plan entitlements | N/A (platform) |
| `audit_logs` | Audit trail | ✅ |
| `webhook_subscriptions` | Webhook endpoints | ✅ |
| `webhook_deliveries` | Delivery history | ✅ |
| `monitoring_events` | System monitoring | ✅ |
| `telemetry_events` | Usage telemetry | ✅ |

### 2.9 GTM & Intelligence

| Table | Purpose | tenant_id |
|-------|---------|-----------|
| `icp_profiles` | Ideal customer profiles | ✅ |
| `market_sizing_results` | TAM/SAM/SOM calculations | ✅ |
| `leads` | Discovered leads | ✅ |
| `scoring_rules` | Scoring configuration | ✅ |
| `territory_rules` | Territory definitions | ✅ |
| `notification_rules` | Notification configuration | ✅ |
| `custom_field_definitions` | Dynamic field definitions | ✅ |

### 2.10 Knowledge & Graph

| Table | Purpose | tenant_id |
|-------|---------|-----------|
| `knowledge_graph_edges` | Entity relationships | ✅ |
| `graph_nodes` | Graph nodes | ✅ |
| `graph_edges` | Graph edges | ✅ |

### 2.11 Communication & Integration

| Table | Purpose | tenant_id |
|-------|---------|-----------|
| `email_accounts` | Connected email accounts | ✅ |
| `calendar_events` | Calendar synchronization | ✅ |
| `integration_connections` | External system connections | ✅ |
| `sync_runs` | Sync execution history | ✅ |

---

## 3. Alembic Migrations

| Migration | Purpose |
|-----------|---------|
| 001_initial.sql | Initial schema |
| 003_revenue_analytics.sql | Revenue analytics tables |
| 004_workflow.sql | Workflow tables |
| 005_notifications.sql | Notification tables |
| 005_workflow_v2.sql | Workflow v2 |
| 006_database_indexes.sql | Performance indexes |
| 007_ai_foundation.sql | AI foundation tables |
| 83 Alembic versions | Progressive schema evolution through migration 0051 |

---

## 4. RLS (Row-Level Security)

### 4.1 Implementation Pattern

```sql
-- Tenant GUC set per request
SET app.tenant_id = '<tenant-uuid>';

-- RLS policy (example)
CREATE POLICY tenant_isolation ON companies
  USING (tenant_id = current_setting('app.tenant_id')::uuid);
```

### 4.2 Coverage

- **72/77 tables** have `tenant_id` column
- **5 tables** intentionally Owner-Platform-scoped (SSO connections, marketplace plugins, feature definitions/values)
- RLS policies enforced via `salesos_app` role
- Owner role (`salesos`) uses `BYPASSRLS` for migrations/bootstrap

### 4.3 Critical Finding

⚠️ **RLS policies exist in code but are UNVERIFIED in production.** The production database has a single shared tenant, meaning cross-tenant isolation has never been tested with real data.

---

## 5. Indexes

### 5.1 Performance Indexes (from migration 006)

- `pg_trgm` indexes on text fields (name, email, etc.)
- UUID indexes on foreign keys
- Composite indexes on (tenant_id, created_at) patterns
- Partial indexes on soft-delete columns

### 5.2 Vector Indexes

- `ivfflat` or `hnsw` indexes on embedding columns
- Used for pgvector similarity search

---

## 6. Key Database Patterns

| Pattern | Implementation |
|---------|---------------|
| Soft Delete | `deleted_at` timestamp on tenants, users |
| Audit Trail | Request-level logging in audit_logs |
| UUID Primary Keys | All tables use UUID PKs |
| JSONB Settings | Tenant settings, features stored as JSONB |
| Embedding Storage | pgvector for company/contact embeddings |
| Event Store | Domain events for event-driven architecture |

---

## 7. Database Health

| Metric | Value |
|--------|-------|
| Total tables | 72+ |
| Total migrations | 83 Alembic versions (through 0051) |
| Extensions | 3 (pg_trgm, uuid-ossp, vector) |
| RLS coverage | 72/77 tenant tables |
| Connection pool (app) | 20 + 10 overflow |
| Connection pool (owner) | 5 + 2 overflow |
| Bounded timeouts | Checkout: 8s, set_config: 5s, commit: 10s |

---

*This document describes the database reality. Security comparison is in 07_SECURITY_COMPARISON.md.*
