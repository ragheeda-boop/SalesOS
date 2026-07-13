# SalesOS Database Architecture — Deep Reverse-Engineering Audit

> **Auditor**: Database Architect (READ-ONLY)  
> **Date**: 2026-07-13  
> **Scope**: Full schema, migrations, repositories, indexes, and performance  
> **Version**: v0.2.0 (25 Alembic migrations + 5 raw SQL migrations)

---

## Table of Contents

1. [Database Architecture Overview](#1-database-architecture-overview)
2. [Complete Entity-Relationship Diagram](#2-complete-entity-relationship-diagram)
3. [Complete Table Catalog](#3-complete-table-catalog)
4. [Index Catalog](#4-index-catalog)
5. [Migration History](#5-migration-history)
6. [Repository Pattern Assessment](#6-repository-pattern-assessment)
7. [Query Patterns & Data Flow](#7-query-patterns--data-flow)
8. [Data Ownership Matrix](#8-data-ownership-matrix)
9. [Seed & Migration Data Analysis](#9-seed--migration-data-analysis)
10. [Database Performance Assessment](#10-database-performance-assessment)
11. [Data Integrity & Constraints Analysis](#11-data-integrity--constraints-analysis)
12. [Database Technical Debt Register](#12-database-technical-debt-register)

---

## 1. Database Architecture Overview

### 1.1 Multi-Database Design

SalesOS uses a **polyglot persistence** architecture with three database systems:

| Database | Version | Role | Connection |
|----------|---------|------|------------|
| **PostgreSQL** (pgvector/pgvector:pg16) | 16 | Primary OLTP store — all relational data, full-text search, vector embeddings, audit logs | `postgresql+asyncpg://salesos:***@postgres:6432/salesos` (via PgBouncer) |
| **Neo4j** (neo4j:5-community) | 5.x | Knowledge Graph — company relationships, graph traversal, community detection | `bolt://neo4j:7687` |
| **Redis** (redis:7-alpine) | 7 | Cache layer, rate limiting | `redis://redis:6379/0` |

**Connection Pooling**: PgBouncer sits between the backend and PostgreSQL at port 6432 with `transaction` pool mode.

**References**:
- `backend/app/config.py:17-25` — Database URLs
- `backend/app/database.py:6-13` — Engine creation (pool_size=20, max_overflow=10)
- `docker-compose.yml:2-38` — PostgreSQL + PgBouncer services
- `docker-compose.yml:40-55` — Neo4j service
- `docker-compose.yml:57-68` — Redis service

### 1.2 PostgreSQL Configuration

```
Engine:               create_async_engine (asyncpg)
Pool Size:            20
Max Overflow:         10
Pool Recycle:         3600s
Pool Pre-Ping:        True
Expire on Commit:     False (async_sessionmaker)

PgBouncer Pool Mode:  transaction
Max Client Conn:      100
Default Pool Size:    25
Min Pool Size:        5
Reserve Pool Size:    5
```

**References**: `backend/app/database.py:6-15`, `docker-compose.yml:20-38`

### 1.3 PostgreSQL Extensions

Enabled via `infra/docker/postgres/init/01-init.sql` and Alembic migrations:

| Extension | Purpose | Source |
|-----------|---------|--------|
| `uuid-ossp` | UUID generation (uuid_generate_v4()) | `01-init.sql:4`, `0001_baseline.py:28` |
| `vector` (pgvector) | Vector embedding storage and ANN search | `01-init.sql:2`, `0001_baseline.py:31` |
| `pg_trgm` | Trigram fuzzy matching for entity resolution | `01-init.sql:3`, `0001_baseline.py:30`, `0024_enable_pg_trgm.py:17` |
| `pgcrypto` | Cryptographic functions | `01-init.sql:5`, `0001_baseline.py:29` |

### 1.4 PostgreSQL Schemas

| Schema | Purpose | Created In |
|--------|---------|------------|
| `public` | Default — core tables | Alembic 0001 |
| `audit` | Audit logging tables | `01-init.sql:7`, `0001_baseline.py:34` |
| `identity` | Identity/tenant/user tables (reserved) | `01-init.sql:8`, `0001_baseline.py:35` |
| `company` | Company-domain tables (reserved) | `01-init.sql:9`, `0001_baseline.py:36` |
| `activity` | Activity runtime tables (reserved) | `01-init.sql:10`, `0001_baseline.py:37` |
| `crm` | CRM tables (reserved) | `01-init.sql:11`, `0001_baseline.py:38` |

**Note**: Most tables live in `public` schema. The named schemas (`audit`, `identity`, `company`, `activity`, `crm`) are reserved but underutilized — only `audit.audit_log` actually uses a non-public schema.

---

## 2. Complete Entity-Relationship Diagram

```mermaid
erDiagram
    tenants ||--o{ users : "has"
    tenants ||--o{ companies : "owns"
    tenants ||--o{ api_keys : "issues"
    tenants ||--o{ device_sessions : "hosts"
    tenants ||--o{ domain_events : "scopes"
    tenants ||--o{ golden_records : "owns"
    tenants ||--o{ entity_resolution_conflicts : "has"
    tenants ||--o{ entity_resolution_log : "logs"
    tenants ||--o{ dead_letter_queue : "queues"
    tenants ||--o{ commercial_opportunities : "owns"
    tenants ||--o{ commercial_quotes : "owns"
    tenants ||--o{ commercial_contracts : "owns"
    tenants ||--o{ commercial_proposals : "owns"
    tenants ||--o{ commercial_recommendations : "gets"
    tenants ||--o{ commercial_activity_sessions : "has"
    tenants ||--o{ commercial_activities : "performs"
    tenants ||--o{ meetings : "has"
    tenants ||--o{ emails : "sends"
    tenants ||--o{ company_features : "computes"
    tenants ||--o{ feature_definitions : "defines"
    tenants ||--o{ company_policies : "sets"
    tenants ||--o{ decisions : "makes"
    tenants ||--o{ decision_feedback_loop : "tracks"
    tenants ||--o{ workflow_definitions : "defines"
    tenants ||--o{ workflow_executions : "runs"
    tenants ||--o{ notifications : "receives"
    tenants ||--o{ signals : "detects"
    tenants ||--o{ timeline_events : "records"
    tenants ||--o{ government_records : "stores"
    tenants ||--o{ documents : "stores"
    tenants ||--o{ contacts : "has"
    tenants ||--o{ commercial_analytics_snapshots : "generates"
    tenants ||--o{ commercial_forecast_snapshots : "forecasts"
    tenants ||--o{ commercial_decision_contexts : "evaluates"
    tenants ||--o{ commercial_policies : "enforces"
    tenants ||--o{ analytics_reports : "defines"

    users ||--o{ password_reset_tokens : "requests"
    users ||--o{ refresh_token_families : "has"
    users ||--o{ device_sessions : "authenticates via"
    users ||--o{ sso_connections : "links"
    users ||--o{ api_keys : "owns"
    users ||--o{ search_history : "performs"

    companies ||--o{ branches : "has"
    companies ||--o{ licenses : "holds"
    companies ||--o{ contacts : "employs"
    companies ||--o{ golden_records : "resolved to"
    companies ||--o{ company_intelligence : "enriched by"
    companies ||--o{ decision_makers : "has"
    companies ||--o{ signals : "emits"
    companies ||--o{ timeline_events : "appears in"
    companies ||--o{ government_records : "registered in"
    companies ||--o{ documents : "files"
    companies ||--o{ opportunities : "pursues"
    companies ||--o{ tasks : "requires"
    companies ||--o{ meetings : "attends"
    companies ||--o{ company_features : "scored"
    companies ||--o{ company_funding_events : "funded by"
    companies ||--o{ company_job_postings : "posts"
    companies ||--o{ company_intent_rfps : "bids on"
    companies ||--o{ company_intent_visits : "visits"
    companies ||--o{ company_intent_content : "consumes"
    companies ||--o{ company_intent_contacts : "interacts"
    companies ||--o{ company_products : "offers"
    companies ||--o{ company_deals : "closes"
    companies ||--o{ company_payments : "makes"
    companies ||--o{ commercial_opportunities : "targeted by"
    companies ||--o{ decisions : "decided for"
    companies ||--o{ company_policies : "governs"

    commercial_opportunities ||--o{ commercial_stage_entries : "transitions"
    commercial_opportunities ||--o{ commercial_quotes : "generates"
    commercial_opportunities ||--o{ commercial_proposals : "produces"
    commercial_opportunities ||--o{ commercial_contracts : "results in"
    commercial_opportunities ||--o{ meetings : "has"
    commercial_opportunities ||--o{ emails : "exchanges"

    commercial_quotes ||--o{ commercial_quote_lines : "contains"
    commercial_quotes ||--o{ commercial_proposals : "referenced by"
    commercial_quotes ||--o{ commercial_contracts : "referenced by"

    commercial_activity_sessions ||--o{ commercial_activities : "contains"

    golden_records ||--o{ entity_resolution_conflicts : "has conflicts"
    golden_records ||--{ companies : "maps to"

    rag_documents ||--o{ rag_document_chunks : "chunked into"

    analytics_reports ||--o{ analytics_report_executions : "executed as"

    feature_definitions ||--o{ feature_values : "has values"

    pipeline_definitions ||--o{ commercial_stage_entries : "defines stages for"

    refresh_token_families ||--o{ device_sessions : "authorizes"
```

### 2.1 Simplified Core Domain ERD

```mermaid
erDiagram
    Tenant ||--o{ User : "has members"
    Tenant ||--o{ Company : "owns"
    Company ||--o{ Branch : "operates"
    Company ||--o{ License : "licensed"
    Company ||--o{ Contact : "employes"
    Company ||--o{ GoldenRecord : "resolved"
    GoldenRecord ||--o{ ResolutionConflict : "has"
    Company ||--o{ Opportunity : "targeted by"
    Opportunity ||--o{ Quote : "generates"
    Opportunity ||--o{ Proposal : "produces"
    Opportunity ||--o{ Contract : "results in"
    Quote ||--o{ QuoteLine : "contains"
    ActivitySession ||--o{ Activity : "contains"
    Company ||--o{ Feature : "scored"
    Company ||--o{ Decision : "decided for"
    Company ||--o{ TimelineEvent : "appears in"
```

---

## 3. Complete Table Catalog

### 3.1 Identity & Multi-Tenancy Domain

#### `tenants`
| Column | Type | Constraints | Description | Source |
|--------|------|-------------|-------------|--------|
| `id` | UUID | PK, DEFAULT uuid_generate_v4() | Unique tenant identifier | `models.py:11` |
| `name` | VARCHAR(255) | NOT NULL | Organization name | `models.py:14` |
| `slug` | VARCHAR(100) | UNIQUE, NOT NULL, INDEX | URL-friendly identifier | `models.py:15` |
| `domain` | VARCHAR(255) | UNIQUE, NULLABLE | Custom domain name | `models.py:16` |
| `plan` | VARCHAR(50) | NOT NULL, DEFAULT 'free' | Subscription tier | `models.py:17` |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT true | Active status | `models.py:18` |
| `settings` | JSONB | NULLABLE | Tenant-wide settings | `models.py:19` |
| `features` | JSONB | NULLABLE | Feature flags | `models.py:20` |
| `subscription_ends_at` | TIMESTAMPTZ | NULLABLE | Subscription expiry | `models.py:21` |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Creation timestamp | Inherited (BaseModel) |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Last update | Inherited (BaseModel) |

**Indexes**: `ix_tenants_slug` (btree on `slug`)  
**References**: `backend/app/modules/identity/models.py:11-26`, `backend/app/alembic/versions/0001_baseline.py:85-101`

#### `users`
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, DEFAULT uuid_generate_v4() | Unique user identifier |
| `tenant_id` | UUID | FK→tenants.id, NOT NULL, INDEX | Owning tenant |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL, INDEX | Email address |
| `password_hash` | VARCHAR(255) | NOT NULL | Hashed password |
| `full_name` | VARCHAR(255) | NOT NULL | Display name |
| `full_name_ar` | VARCHAR(255) | NULLABLE | Arabic display name |
| `role` | VARCHAR(50) | NOT NULL, DEFAULT 'user' | RBAC role |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT true | Account active |
| `is_verified` | BOOLEAN | NOT NULL, DEFAULT false | Email verified |
| `avatar_url` | VARCHAR(500) | NULLABLE | Profile picture URL |
| `phone` | VARCHAR(30) | NULLABLE | Phone number |
| `preferences` | JSONB | NULLABLE | User preferences |
| `last_login_at` | TIMESTAMPTZ | NULLABLE | Last login timestamp |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Created |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Updated |

**Indexes**: `ix_users_email` (btree), `ix_users_tenant_id` (btree on FK)  
**References**: `backend/app/modules/identity/models.py:29-53`, `backend/app/alembic/versions/0001_baseline.py:105-127`

#### `token_blacklist`
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `jti` | VARCHAR(64) | PK | JWT JTI identifier |
| `token_type` | VARCHAR(10) | NOT NULL | 'access' or 'refresh' |
| `expires_at` | TIMESTAMPTZ | NOT NULL | Token expiry |
| `revoked_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Revocation time |

**References**: `backend/app/modules/identity/models.py:98-104`, `backend/app/alembic/versions/0012_refresh_token_tables.py:20-26`

#### `password_reset_tokens`
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | VARCHAR(64) | PK | Token identifier |
| `user_id` | UUID | FK→users.id, NOT NULL, INDEX | Target user |
| `token_hash` | VARCHAR(128) | NOT NULL, INDEX | Hashed token |
| `expires_at` | TIMESTAMPTZ | NOT NULL | Expiry |
| `used_at` | TIMESTAMPTZ | NULLABLE | When used |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Created |

**References**: `backend/app/modules/identity/models.py:56-66`, `backend/app/alembic/versions/0012_refresh_token_tables.py:27-38`

#### `refresh_token_families`
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | VARCHAR(64) | PK | Token entry ID |
| `user_id` | UUID | FK→users.id, NOT NULL, INDEX | User |
| `family_id` | VARCHAR(64) | NOT NULL, INDEX | Rotation family |
| `token_hash` | VARCHAR(128) | NOT NULL | Hashed refresh token |
| `expires_at` | TIMESTAMPTZ | NOT NULL | Expiry |
| `used_at` | TIMESTAMPTZ | NULLABLE | When used |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Created |
| `is_compromised` | BOOLEAN | NOT NULL | Reuse detection |

**References**: `backend/app/modules/identity/models.py:69-79`

#### `device_sessions`
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | VARCHAR(64) | PK | Session ID |
| `user_id` | UUID | FK→users.id, NOT NULL, INDEX | User |
| `tenant_id` | UUID | FK→tenants.id, NOT NULL | Tenant |
| `refresh_family_id` | VARCHAR(64) | FK→refresh_token_families.id, NOT NULL | Token family |
| `device_name` | VARCHAR(512) | NOT NULL | Device name |
| `device_type` | VARCHAR(50) | NOT NULL | Device type |
| `ip_address` | VARCHAR(45) | NOT NULL | IP address |
| `last_used_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Last use |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Created |
| `expires_at` | TIMESTAMPTZ | NOT NULL | Expiry |
| `is_revoked` | BOOLEAN | NOT NULL | Revocation flag |

**References**: `backend/app/modules/identity/models.py:82-94`

### 3.2 Company Domain

#### `sources`
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Source identifier |
| `name` | VARCHAR(100) | UNIQUE, NOT NULL | Source name |
| `slug` | VARCHAR(100) | UNIQUE, NOT NULL | URL slug |
| `description` | TEXT | NULLABLE | Description |
| `base_url` | VARCHAR(500) | NULLABLE | Base URL |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT true | Active |
| `ingestion_config` | JSONB | NULLABLE | Ingestion settings |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Created |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Updated |

**References**: `backend/app/modules/company/models.py:13-24`, `0001_baseline.py:130-144`

#### `companies`
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Company identifier |
| `tenant_id` | UUID | FK→tenants.id, NOT NULL, INDEX | Owning tenant |
| `name_ar` | VARCHAR(500) | NOT NULL, INDEX | Arabic name |
| `name_en` | VARCHAR(500) | NULLABLE | English name |
| `cr_number` | VARCHAR(50) | NOT NULL, INDEX | Commercial Registration |
| `cr_type` | VARCHAR(50) | NULLABLE | CR type |
| `status` | VARCHAR(50) | NOT NULL, DEFAULT 'active', INDEX | Company status |
| `city` | VARCHAR(200) | NULLABLE, INDEX | City |
| `region` | VARCHAR(200) | NULLABLE | Region |
| `latitude` | FLOAT | NULLABLE | GPS latitude |
| `longitude` | FLOAT | NULLABLE | GPS longitude |
| `postal_code` | VARCHAR(20) | NULLABLE | Postal code |
| `phone` | VARCHAR(50) | NULLABLE | Phone |
| `fax` | VARCHAR(50) | NULLABLE | Fax |
| `email` | VARCHAR(255) | NULLABLE | Email |
| `website` | VARCHAR(500) | NULLABLE | Website URL |
| `address` | TEXT | NULLABLE | Full address |
| `capital` | FLOAT | NULLABLE | Registered capital |
| `currency` | VARCHAR(10) | NULLABLE, DEFAULT 'SAR' | Currency |
| `employees_count` | INTEGER | NULLABLE | Employee count |
| `activity_description` | TEXT | NULLABLE | Business activity |
| `activity_code` | VARCHAR(50) | NULLABLE | Activity code |
| `industry` | VARCHAR(200) | NULLABLE, INDEX | Industry classification |
| `isic_code` | VARCHAR(20) | NULLABLE | ISIC code |
| `isic_description` | VARCHAR(500) | NULLABLE | ISIC description |
| `legal_form` | VARCHAR(100) | NULLABLE | Legal entity type |
| `incorporation_date` | DATE | NULLABLE | Registration date |
| `expiry_date` | DATE | NULLABLE | CR expiry |
| `parent_company_id` | UUID | FK→companies.id, NULLABLE, INDEX | Parent company |
| `annual_revenue` | FLOAT | NULLABLE | Current year revenue |
| `revenue_prev_year` | FLOAT | NULLABLE | Previous year revenue |
| `revenue_2yr_ago` | FLOAT | NULLABLE | 2 years ago revenue |
| `employee_count_prev_year` | INTEGER | NULLABLE | Previous year employees |
| `linkedin_url` | VARCHAR(500) | NULLABLE | LinkedIn profile |
| `country` | VARCHAR(100) | NULLABLE | Country |
| `branch_count` | INTEGER | NULLABLE, DEFAULT 0 | Branch count |
| `do_not_contact` | BOOLEAN | NOT NULL, DEFAULT false | DNC flag |
| `is_golden_record` | BOOLEAN | NOT NULL, DEFAULT false | Golden record flag |
| `confidence_score` | FLOAT | NULLABLE, DEFAULT 0.0 | Confidence |
| `source_ids` | JSONB | NULLABLE | Source refs |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT true | Active |
| `tags` | JSONB | NULLABLE | Tags |
| `metadata` | JSONB | NULLABLE | Extra metadata |
| `tsv` | TSVECTOR | NULLABLE | Legacy full-text vector (trigger-maintained) |
| `search_vector` | TSVECTOR | GENERATED ALWAYS AS STORED | Deterministic full-text vector |
| `embedding_vector` | vector(3072) | NULLABLE | pgvector embedding (text-embedding-3-large) |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Created |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Updated |

**Indexes**: See Section 4.  
**Triggers**: `trg_companies_tsv`, `trg_companies_search_vectors` — auto-refresh TSVECTOR columns  
**References**: `app/modules/company/models.py:27-83`, `0001_baseline.py:147-195`, `0002_feature_store.py:34-71`, `0006_search_runtime.py:26-72`, `0016_drop_dual_embedding.py`, `0023_fulltext_search.py`, `0024_hybrid_search_optimization.py`

#### `branches`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | UUID | PK |
| `company_id` | UUID | FK→companies.id, NOT NULL, INDEX |
| `name_ar` | VARCHAR(500) | NOT NULL |
| `name_en` | VARCHAR(500) | NULLABLE |
| `branch_number` | VARCHAR(50) | NULLABLE |
| `city` | VARCHAR(200) | NULLABLE |
| `address` | TEXT | NULLABLE |
| `phone` | VARCHAR(50) | NULLABLE |
| `latitude` | FLOAT | NULLABLE |
| `longitude` | FLOAT | NULLABLE |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT true |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

**References**: `app/modules/company/models.py:86-106`, `0001_baseline.py:198-216`

#### `licenses`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | UUID | PK |
| `company_id` | UUID | FK→companies.id, NOT NULL, INDEX |
| `license_number` | VARCHAR(100) | NOT NULL, INDEX |
| `license_type` | VARCHAR(100) | NOT NULL |
| `license_type_ar` | VARCHAR(200) | NULLABLE |
| `status` | VARCHAR(50) | NOT NULL, DEFAULT 'active' |
| `issuing_authority` | VARCHAR(200) | NULLABLE |
| `issue_date` | DATE | NULLABLE |
| `expiry_date` | DATE | NULLABLE |
| `renewal_date` | DATE | NULLABLE |
| `source` | VARCHAR(100) | NULLABLE |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

**References**: `app/modules/company/models.py:108-127`, `0001_baseline.py:219-239`

#### `contacts` (unified, was `contacts` + `contacts_standalone`)
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | UUID | PK |
| `tenant_id` | UUID | FK→tenants.id ON DELETE CASCADE, NOT NULL, INDEX |
| `company_id` | UUID | FK→companies.id, NOT NULL, INDEX |
| `name` | VARCHAR(255) | NOT NULL |
| `name_ar` | VARCHAR(255) | NULLABLE |
| `email` | VARCHAR(255) | NULLABLE |
| `phone` | VARCHAR(50) | NULLABLE |
| `mobile` | VARCHAR(50) | NULLABLE |
| `position` | VARCHAR(255) | NULLABLE |
| `position_ar` | VARCHAR(255) | NULLABLE |
| `department` | VARCHAR(255) | NULLABLE |
| `is_primary` | BOOLEAN | NOT NULL, DEFAULT false |
| `source` | VARCHAR(100) | NULLABLE |
| `confidence_score` | FLOAT | NULLABLE, DEFAULT 0.0 |
| `tags` | JSONB | NULLABLE, DEFAULT [] |
| `metadata` | JSONB | NULLABLE, DEFAULT {} |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

**Note**: Migration `0022_consolidate_contacts.py` merged `contacts_standalone` into `contacts` on 2026-07-12.

**References**: `app/modules/company/models.py:130-151`, `0001_baseline.py:242-263`, `0022_consolidate_contacts.py`

#### `company_intelligence` (legacy)
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `company_id` | UUID | PK, FK→companies.id ON DELETE CASCADE | Company |
| `dna` | JSONB | NULLABLE | Company DNA analysis |
| `ai_recommendation` | JSONB | NULLABLE | AI recommendation |
| `buying_journey` | JSONB | NULLABLE | Buying journey |
| `golden_record` | JSONB | NULLABLE | Cached golden record |
| `generated_at` | TIMESTAMPTZ | DEFAULT now() | Generated |
| `expires_at` | TIMESTAMPTZ | DEFAULT now()+5min | Cache TTL |

**Note**: Legacy table from `001_initial.sql` — likely superseded by Feature Store.

#### `decision_makers` (legacy)
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | UUID | PK |
| `company_id` | UUID | FK→companies.id ON DELETE CASCADE, NOT NULL |
| `name` | VARCHAR(255) | NULLABLE |
| `role` | VARCHAR(255) | NULLABLE |
| `department` | VARCHAR(255) | NULLABLE |
| `influence` | VARCHAR(10) | CHECK IN ('low','medium','high') |
| `connected` | BOOLEAN | DEFAULT false |
| `email` | VARCHAR(255) | NULLABLE |
| `phone` | VARCHAR(50) | NULLABLE |
| `created_at` | TIMESTAMPTZ | DEFAULT now() |

#### `signals` (legacy)
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | UUID | PK |
| `tenant_id` | UUID | FK→tenants.id ON DELETE CASCADE (added in 0020), NULLABLE |
| `company_id` | UUID | FK→companies.id ON DELETE CASCADE |
| `type` | VARCHAR(20) | NOT NULL |
| `title` | VARCHAR(500) | NOT NULL |
| `description` | TEXT | NULLABLE |
| `source` | VARCHAR(255) | NULLABLE |
| `severity` | VARCHAR(10) | CHECK IN ('low','medium','high','critical') |
| `ai_confidence` | DECIMAL(3,2) | NULLABLE |
| `timestamp` | TIMESTAMPTZ | DEFAULT now() |
| `created_at` | TIMESTAMPTZ | DEFAULT now() |

**Indexes**: `idx_signals_company`, `idx_signals_severity`, `idx_signals_time` (DESC), `ix_signals_tenant_company` (added 0020)

#### `timeline_events` (legacy)
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | UUID | PK |
| `tenant_id` | UUID | FK→tenants.id (added 0020) |
| `company_id` | UUID | FK→companies.id ON DELETE CASCADE |
| `type` | VARCHAR(20) | NOT NULL |
| `summary` | TEXT | NOT NULL |
| `detail` | TEXT | NULLABLE |
| `source` | VARCHAR(255) | NULLABLE |
| `confidence` | DECIMAL(3,2) | NULLABLE |
| `ai_highlighted` | BOOLEAN | DEFAULT false |
| `date` | TIMESTAMPTZ | NOT NULL |
| `created_at` | TIMESTAMPTZ | DEFAULT now() |

**Note**: Legacy table — new timeline uses `timeline_entries` table (0005). Redundant.

#### `government_records` (legacy)
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | UUID | PK |
| `tenant_id` | UUID | FK→tenants.id (added 0020) |
| `company_id` | UUID | FK→companies.id ON DELETE CASCADE, NOT NULL |
| `type` | VARCHAR(20) | NOT NULL |
| `title` | VARCHAR(500) | NOT NULL |
| `status` | VARCHAR(20) | CHECK IN ('active','expired','pending','violation') |
| `issue_date` | DATE | NULLABLE |
| `expiry_date` | DATE | NULLABLE |
| `confidence` | DECIMAL(3,2) | NULLABLE |
| `source` | VARCHAR(255) | NULLABLE |
| `created_at` | TIMESTAMPTZ | DEFAULT now() |

#### `documents` (legacy)
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | UUID | PK |
| `tenant_id` | UUID | FK→tenants.id (added 0020) |
| `company_id` | UUID | FK→companies.id ON DELETE CASCADE, NOT NULL |
| `title` | VARCHAR(500) | NOT NULL |
| `type` | VARCHAR(20) | NOT NULL |
| `file_url` | TEXT | NULLABLE |
| `ai_summary` | TEXT | NULLABLE |
| `confidence` | DECIMAL(3,2) | NULLABLE |
| `date` | DATE | NOT NULL |
| `created_at` | TIMESTAMPTZ | DEFAULT now() |

### 3.3 Entity Resolution Domain

#### `golden_records`
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Record ID |
| `tenant_id` | UUID | FK→tenants.id, NOT NULL, INDEX | Tenant |
| `cr_number` | VARCHAR(50) | NOT NULL | CR number |
| `company_id` | UUID | FK→companies.id, NULLABLE | Resolved company |
| `data` | JSONB | NOT NULL | Provenance data |
| `confidence_score` | FLOAT | NOT NULL, DEFAULT 0.0 | Match confidence |
| `source_ids` | JSONB | NULLABLE | Source references |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT true | Active |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Created |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Updated |

**Index**: `ix_golden_records_tenant_cr` UNIQUE (tenant_id, cr_number)  
**References**: `app/modules/entity_resolution/models.py:13-32`, `0001_baseline.py:267-286`

#### `entity_resolution_conflicts`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | UUID | PK |
| `tenant_id` | UUID | FK→tenants.id, NOT NULL, INDEX |
| `golden_record_id` | UUID | FK→golden_records.id, NOT NULL |
| `field_name` | VARCHAR(255) | NOT NULL |
| `source_a_value` | TEXT | NULLABLE |
| `source_a_source` | VARCHAR(100) | NOT NULL |
| `source_b_value` | TEXT | NULLABLE |
| `source_b_source` | VARCHAR(100) | NOT NULL |
| `resolution_strategy` | VARCHAR(50) | NULLABLE |
| `resolved_by` | UUID | NULLABLE |
| `resolved_at` | TIMESTAMPTZ | NULLABLE |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'open' |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

#### `entity_resolution_log`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | UUID | PK |
| `tenant_id` | UUID | FK→tenants.id, NOT NULL, INDEX |
| `operation` | VARCHAR(50) | NOT NULL |
| `source_slug` | VARCHAR(100) | NULLABLE |
| `records_processed` | INTEGER | NOT NULL, DEFAULT 0 |
| `records_matched` | INTEGER | NOT NULL, DEFAULT 0 |
| `records_created` | INTEGER | NOT NULL, DEFAULT 0 |
| `records_merged` | INTEGER | NOT NULL, DEFAULT 0 |
| `confidence_threshold` | FLOAT | NULLABLE |
| `details` | JSONB | NULLABLE |
| `performed_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

### 3.4 Commercial Domain

#### `commercial_opportunities`
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | VARCHAR(36) | PK | String UUID |
| `tenant_id` | VARCHAR(36) | FK→tenants.id ON DELETE CASCADE, NOT NULL, INDEX | Tenant |
| `company_id` | VARCHAR(36) | FK→companies.id ON DELETE CASCADE, NOT NULL, INDEX | Company |
| `name` | VARCHAR(500) | NOT NULL | Opportunity name |
| `value` | FLOAT | NOT NULL, DEFAULT 0 | Deal value |
| `currency` | VARCHAR(3) | NOT NULL, DEFAULT 'SAR' | Currency |
| `stage` | VARCHAR(100) | NOT NULL, DEFAULT 'prospecting' | Pipeline stage |
| `probability` | FLOAT | NOT NULL, DEFAULT 0.10 | Win probability |
| `expected_close_date` | DATE | NULLABLE | Close date |
| `owner_id` | VARCHAR(36) | NOT NULL, DEFAULT '' | Owner user ID |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'open' | open/won/lost |
| `won_amount` | FLOAT | NULLABLE | Won amount |
| `loss_reason` | TEXT | NOT NULL, DEFAULT '' | Loss reason |
| `description` | TEXT | NOT NULL, DEFAULT '' | Description |
| `tags` | JSON | NOT NULL, DEFAULT [] | Tags |
| `metadata` | JSON | NOT NULL, DEFAULT {} | Metadata |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Created |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Updated |

**Indexes**: `ix_opportunities_tenant_stage` (tenant_id, stage), `ix_opportunities_tenant_status` (tenant_id, status)  
**FKs added**: `0019_add_commercial_fks.py`  
**References**: `domains/commercial/infrastructure/models.py:23-42`

#### `commercial_stage_entries`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | VARCHAR(36) | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL, INDEX |
| `opportunity_id` | VARCHAR(36) | FK→commercial_opportunities.id, NOT NULL, INDEX |
| `pipeline_id` | VARCHAR(36) | NOT NULL, INDEX |
| `from_stage` | VARCHAR(100) | NOT NULL |
| `to_stage` | VARCHAR(100) | NOT NULL |
| `entered_at` | TIMESTAMPTZ | NOT NULL |
| `exited_at` | TIMESTAMPTZ | NULLABLE |
| `duration_hours` | FLOAT | NULLABLE |

#### `commercial_pipeline_definitions`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | VARCHAR(36) | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL, INDEX |
| `name` | VARCHAR(200) | NOT NULL |
| `stages` | JSON | NOT NULL, DEFAULT [] |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

#### `commercial_activity_sessions`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | VARCHAR(36) | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL, INDEX |
| `title` | VARCHAR(500) | NOT NULL |
| `target_id` | VARCHAR(36) | NOT NULL, INDEX |
| `target_type` | VARCHAR(50) | NOT NULL, DEFAULT 'opportunity' |
| `start_time` | TIMESTAMPTZ | NULLABLE |
| `end_time` | TIMESTAMPTZ | NULLABLE |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'scheduled' |
| `notes` | TEXT | NOT NULL, DEFAULT '' |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

#### `commercial_activities`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | VARCHAR(36) | PK |
| `tenant_id` | VARCHAR(36) | FK→tenants.id (added 0019), NULLABLE, INDEX |
| `session_id` | VARCHAR(36) | FK→commercial_activity_sessions.id, NOT NULL, INDEX |
| `activity_type` | VARCHAR(50) | NOT NULL |
| `owner_id` | VARCHAR(36) | NOT NULL |
| `owner_name` | VARCHAR(200) | NOT NULL, DEFAULT '' |
| `outcome_id` | VARCHAR(100) | NOT NULL, DEFAULT '' |
| `outcome_label` | VARCHAR(200) | NOT NULL, DEFAULT '' |
| `notes` | TEXT | NOT NULL, DEFAULT '' |
| `scheduled_at` | TIMESTAMPTZ | NULLABLE |
| `completed_at` | TIMESTAMPTZ | NULLABLE |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'scheduled' |
| `external_id` | VARCHAR(200) | NOT NULL, DEFAULT '' |

**Index**: `ix_activities_session_type` (session_id, activity_type), `ix_commercial_activities_tenant`

#### `commercial_quotes`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | VARCHAR(36) | PK |
| `tenant_id` | VARCHAR(36) | FK→tenants.id ON DELETE CASCADE, NOT NULL, INDEX |
| `opportunity_id` | VARCHAR(36) | FK→commercial_opportunities.id ON DELETE CASCADE, NOT NULL, INDEX |
| `title` | VARCHAR(500) | NOT NULL |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'draft' |
| `total_value` | FLOAT | NOT NULL, DEFAULT 0 |
| `currency` | VARCHAR(3) | NOT NULL, DEFAULT 'SAR' |
| `notes` | TEXT | NOT NULL, DEFAULT '' |
| `sent_at` | TIMESTAMPTZ | NULLABLE |
| `approved_by` | VARCHAR(36) | NOT NULL, DEFAULT '' |
| `approved_at` | TIMESTAMPTZ | NULLABLE |
| `accepted_at` | TIMESTAMPTZ | NULLABLE |
| `version` | INTEGER | NOT NULL, DEFAULT 1 |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

**Index**: `ix_quotes_opportunity_status` (opportunity_id, status)

#### `commercial_quote_lines`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | VARCHAR(36) | PK |
| `quote_id` | VARCHAR(36) | FK→commercial_quotes.id, NOT NULL, INDEX |
| `description` | VARCHAR(500) | NOT NULL |
| `quantity` | FLOAT | NOT NULL, DEFAULT 1 |
| `unit_price` | FLOAT | NOT NULL, DEFAULT 0 |
| `total` | FLOAT | NOT NULL, DEFAULT 0 |

#### `commercial_proposals`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | VARCHAR(36) | PK |
| `tenant_id` | VARCHAR(36) | FK→tenants.id ON DELETE CASCADE, NOT NULL, INDEX |
| `opportunity_id` | VARCHAR(36) | FK→commercial_opportunities.id ON DELETE CASCADE, NOT NULL, INDEX |
| `quote_id` | VARCHAR(36) | FK→commercial_quotes.id ON DELETE SET NULL, NOT NULL, INDEX |
| `title` | VARCHAR(500) | NOT NULL |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'draft' |
| `delivery_method` | VARCHAR(100) | NOT NULL, DEFAULT '' |
| `sent_at` | TIMESTAMPTZ | NULLABLE |
| `viewed_at` | TIMESTAMPTZ | NULLABLE |
| `accepted_at` | TIMESTAMPTZ | NULLABLE |
| `rejected_at` | TIMESTAMPTZ | NULLABLE |
| `rejection_reason` | TEXT | NOT NULL, DEFAULT '' |
| `version` | INTEGER | NOT NULL, DEFAULT 1 |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

#### `commercial_contracts`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | VARCHAR(36) | PK |
| `tenant_id` | VARCHAR(36) | FK→tenants.id ON DELETE CASCADE, NOT NULL, INDEX |
| `opportunity_id` | VARCHAR(36) | FK→commercial_opportunities.id ON DELETE CASCADE, NOT NULL, INDEX |
| `quote_id` | VARCHAR(36) | FK→commercial_quotes.id ON DELETE SET NULL, NOT NULL |
| `quote_revision` | INTEGER | NOT NULL, DEFAULT 1 |
| `title` | VARCHAR(500) | NOT NULL |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'draft' |
| `parties` | JSON | NOT NULL, DEFAULT [] |
| `obligations` | JSON | NOT NULL, DEFAULT [] |
| `effective_date` | DATE | NULLABLE |
| `expiry_date` | DATE | NULLABLE |
| `renewal` | JSON | NOT NULL, DEFAULT {} |
| `legal_terms` | TEXT | NOT NULL, DEFAULT '' |
| `governing_law` | VARCHAR(100) | NOT NULL, DEFAULT '' |
| `signed_by_provider` | TIMESTAMPTZ | NULLABLE |
| `signed_by_customer` | TIMESTAMPTZ | NULLABLE |
| `notes` | TEXT | NOT NULL, DEFAULT '' |
| `version` | INTEGER | NOT NULL, DEFAULT 1 |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

**Index**: `ix_contracts_tenant_status` (tenant_id, status)

#### `meetings` (Commercial domain version)
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | VARCHAR(36) | PK |
| `tenant_id` | VARCHAR(36) | FK→tenants.id ON DELETE CASCADE, NOT NULL, INDEX |
| `opportunity_id` | VARCHAR(36) | FK→commercial_opportunities.id ON DELETE CASCADE, NOT NULL, INDEX |
| `title` | VARCHAR(500) | NOT NULL |
| `meeting_date` | TIMESTAMPTZ | NOT NULL |
| `duration_minutes` | INTEGER | NULLABLE |
| `notes` | TEXT | NOT NULL, DEFAULT '' |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'scheduled' |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

**Index**: `ix_meetings_opportunity` (opportunity_id, tenant_id)

#### `emails`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | VARCHAR(36) | PK |
| `tenant_id` | VARCHAR(36) | FK→tenants.id ON DELETE CASCADE, NOT NULL, INDEX |
| `opportunity_id` | VARCHAR(36) | FK→commercial_opportunities.id ON DELETE CASCADE, NOT NULL, INDEX |
| `subject` | VARCHAR(500) | NOT NULL |
| `from_address` | VARCHAR(254) | NOT NULL |
| `to_addresses` | JSON | NOT NULL, DEFAULT [] |
| `direction` | VARCHAR(10) | NOT NULL, DEFAULT 'outbound' |
| `email_type` | VARCHAR(50) | NOT NULL, DEFAULT 'general' |
| `body` | TEXT | NOT NULL, DEFAULT '' |
| `sent_at` | TIMESTAMPTZ | NULLABLE |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

**Index**: `ix_emails_opportunity` (opportunity_id, tenant_id)

#### `commercial_recommendations`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | VARCHAR(36) | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL, INDEX |
| `target_id` | VARCHAR(36) | NOT NULL, INDEX |
| `target_type` | VARCHAR(50) | NOT NULL |
| `title` | VARCHAR(500) | NOT NULL |
| `description` | TEXT | NOT NULL, DEFAULT '' |
| `recommendation_type` | VARCHAR(100) | NOT NULL |
| `confidence` | FLOAT | NOT NULL, DEFAULT 0 |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'pending' |
| `evidence` | JSON | NOT NULL, DEFAULT [] |
| `alternatives` | JSON | NOT NULL, DEFAULT [] |
| `applied_at` | TIMESTAMPTZ | NULLABLE |
| `dismissed_at` | TIMESTAMPTZ | NULLABLE |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

**Index**: `ix_recommendations_target` (target_id, target_type)

#### Other Commercial Tables (summary)

| Table | Primary Key | Key Columns | Source |
|-------|-------------|-------------|--------|
| `commercial_forecast_snapshots` | VARCHAR(36) | tenant_id, lines (JSON), assumptions (JSON), status, version | `0007_commercial_domain.py:210-221` |
| `commercial_analytics_snapshots` | VARCHAR(36) | tenant_id, period_start, period_end, kpis (JSON), insights (JSON) | `0007_commercial_domain.py:225-233` |
| `commercial_decision_contexts` | VARCHAR(36) | tenant_id, target_id, target_type, factors (JSON), confidence | `0007_commercial_domain.py:237-245` |
| `commercial_policies` | VARCHAR(36) | tenant_id, name, rules (JSON), outcome, priority, enabled | `0007_commercial_domain.py:249-259` |

### 3.5 Decision Engine Domain

#### `decisions`
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PK, AUTOINCREMENT | Sequential ID |
| `decision_id` | VARCHAR(64) | UNIQUE, NOT NULL | Business ID |
| `company_id` | VARCHAR(36) | NOT NULL | Company |
| `tenant_id` | VARCHAR(36) | NOT NULL | Tenant |
| `decision_type` | VARCHAR(50) | NOT NULL | Type |
| `priority` | INTEGER | NOT NULL, DEFAULT 0 | Priority |
| `confidence` | FLOAT | NOT NULL, DEFAULT 0.0 | Confidence |
| `expected_revenue` | FLOAT | NULLABLE | Revenue impact |
| `expected_probability` | FLOAT | NULLABLE | Probability |
| `reasoning` | TEXT | NULLABLE | AI reasoning |
| `evidence` | JSONB | NULLABLE | Evidence |
| `supporting_features` | JSONB | NULLABLE | Features |
| `context_snapshot` | JSONB | NULLABLE | Context |
| `required_actions` | JSONB | NULLABLE | Actions |
| `blocked_by` | JSONB | NULLABLE | Blockers |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'suggested' | suggested/accepted/executed/dismissed |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Created |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Updated |
| `expires_at` | TIMESTAMPTZ | NULLABLE | Expiry |
| `executed_at` | TIMESTAMPTZ | NULLABLE | Execution time |

**Indexes**: `ix_decisions_company` (tenant_id, company_id), `ix_decisions_status` (tenant_id, status), `ix_decisions_created` (created_at DESC)  
**References**: `0003_decision_engine.py:26-53`

#### `decision_feedback_loop`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | INTEGER | PK, AUTOINCREMENT |
| `decision_id` | VARCHAR(64) | NOT NULL |
| `company_id` | VARCHAR(36) | NOT NULL |
| `tenant_id` | VARCHAR(36) | NOT NULL |
| `user_accepted` | BOOLEAN | NOT NULL |
| `executed` | BOOLEAN | NOT NULL, DEFAULT false |
| `outcome` | VARCHAR(20) | NULLABLE |
| `outcome_value` | FLOAT | NULLABLE |
| `learning` | TEXT | NULLABLE |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

#### `company_policies`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | INTEGER | PK, AUTOINCREMENT |
| `tenant_id` | VARCHAR(36) | NOT NULL |
| `company_id` | VARCHAR(36) | NOT NULL |
| `policy_name` | VARCHAR(100) | NOT NULL |
| `policy_type` | VARCHAR(50) | NOT NULL, DEFAULT 'custom' |
| `action` | VARCHAR(20) | NOT NULL, DEFAULT 'allow' |
| `reason` | TEXT | NULLABLE |
| `severity` | INTEGER | NOT NULL, DEFAULT 0 |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT true |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

**Index**: `ix_policies_company` UNIQUE (tenant_id, company_id, policy_name)

### 3.6 Feature Store Domain

#### `feature_definitions` (generic, entity-agnostic)
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `key` | VARCHAR(255) | PK | Feature key |
| `name` | VARCHAR(255) | NOT NULL | Human name |
| `description` | TEXT | NULLABLE | Description |
| `feature_type` | VARCHAR(50) | DEFAULT 'numeric' | numeric/categorical/text/embedding |
| `domain` | VARCHAR(100) | DEFAULT 'general' | Domain |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Created |

**References**: `0025_feature_store.py:24-36`

#### `feature_values` (generic, entity-agnostic)
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | VARCHAR(36) | PK | Composite ID |
| `feature_key` | VARCHAR(255) | FK→feature_definitions.key ON DELETE CASCADE, NOT NULL | Feature |
| `entity_id` | VARCHAR(36) | NOT NULL | Entity ID |
| `entity_type` | VARCHAR(50) | NOT NULL | company/opportunity/contact/employee |
| `value` | JSON | NULLABLE | Feature value |
| `computed_at` | TIMESTAMPTZ | DEFAULT now() | Computation time |
| `ttl_seconds` | INTEGER | DEFAULT 3600 | Cache TTL |

**Index**: `idx_feature_values_lookup` (entity_type, entity_id, feature_key)  
**References**: `0025_feature_store.py:38-62`

#### `company_features` (company-specific, pre-existing)
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PK, AUTOINCREMENT | Sequential |
| `tenant_id` | VARCHAR(36) | NOT NULL | Tenant |
| `company_id` | VARCHAR(36) | NOT NULL | Company |
| `feature_name` | VARCHAR(64) | NOT NULL | Feature name |
| `score` | FLOAT | NOT NULL | Score |
| `version` | INTEGER | NOT NULL, DEFAULT 1 | Version |
| `computed_at` | TIMESTAMPTZ | NOT NULL | Computation time |
| `confidence` | FLOAT | NOT NULL, DEFAULT 0.0 | Confidence |
| `signals` | JSONB | NULLABLE | Signal data |
| `explanation` | VARCHAR(500) | NULLABLE | Explanation |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Created |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Updated |

**Index**: `ix_company_features_lookup` UNIQUE (tenant_id, company_id, feature_name)  
**FKs**: tenant_id→tenants.id, company_id→companies.id (added 0018)  
**References**: `0002_feature_store.py:73-93`

#### Company Enrichment Tables (all tenant-scoped, company-linked, CASCADE delete via 0018)

| Table | Key Columns | Description |
|-------|------------|-------------|
| `company_funding_events` | id, tenant_id, company_id, round_type, amount, date, investors (JSONB) | Funding rounds |
| `company_job_postings` | id, tenant_id, company_id, title, role, seniority, status | Job postings |
| `company_intent_rfps` | id, tenant_id, company_id, rfp_title, value, agency, status | RFP/tender signals |
| `company_intent_visits` | id, tenant_id, company_id, page_url, visited_at | Web visits |
| `company_intent_content` | id, tenant_id, company_id, content_type, consumed_at | Content consumption |
| `company_intent_contacts` | id, tenant_id, company_id, contact_name, role, last_interaction | DM interactions |
| `company_products` | id, tenant_id, company_id, name, category, price | Products/services |
| `company_deals` | id, tenant_id, company_id, deal_name, amount, status, stage | Historical deals |
| `company_payments` | id, tenant_id, company_id, invoice_number, amount, status | Payment history |

**Note**: Tables `company_news_mentions`, `company_government_contracts`, `company_patents`, `company_social_media`, `company_website_mentions`, `company_regulatory_filings`, `company_market_share`, `company_supply_chain` are listed in `0018_add_feature_store_fks.py:20-38` FKs but no Alembic migration created them explicitly. They may be ORM-only or future tables.

### 3.7 Timeline Domain

#### `timeline_entries` (replacement for `timeline_events`)
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PK, AUTOINCREMENT | Sequential |
| `entity_type` | VARCHAR(50) | NOT NULL | company/opportunity/user |
| `entity_id` | VARCHAR(64) | NOT NULL | Entity ID |
| `event_type` | VARCHAR(100) | NOT NULL | Event type |
| `data` | JSONB | NULLABLE | Event payload |
| `actor` | VARCHAR(255) | NULLABLE | Actor ID |
| `tenant_id` | VARCHAR(36) | NULLABLE | Tenant |
| `importance` | INTEGER | NOT NULL, DEFAULT 0 | Importance score (1/5/10) |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Created |

**Indexes**: `ix_timeline_entity` (entity_type, entity_id, created_at DESC), `ix_timeline_tenant` (tenant_id, entity_type, created_at DESC), `ix_timeline_event_type` (entity_type, entity_id, event_type)  
**References**: `domains/timeline/models.py:11-24`, `0005_timeline_runtime.py:23-44`

### 3.8 Search Domain

#### `search_history`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | UUID | PK |
| `user_id` | UUID | FK→users.id, NOT NULL |
| `query_text` | TEXT | NOT NULL |
| `result_count` | INTEGER | NULLABLE |
| `created_at` | TIMESTAMPTZ | DEFAULT now() |

**Indexes**: `idx_search_user` (user_id), `idx_search_time` (created_at DESC)

#### `vectors` (PgVectorStore generic table)
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | TEXT | PK | Vector ID |
| `embedding` | vector(3072) | NOT NULL | pgvector embedding |
| `metadata` | JSONB | NOT NULL, DEFAULT '{}' | Metadata |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Created |
| `updated_at` | TIMESTAMPTZ | DEFAULT now() | Updated |

**Indexes**: `ix_vectors_created_at` (btree), `idx_vectors_embedding_hnsw` (HNSW on embedding vector_cosine_ops)  
**Migration Note**: Originally created with ARRAY(Float) in 0010, migrated to vector(3072) in `0021_fix_vectors_embedding_type.py`

### 3.9 Knowledge Graph Domain (PostgreSQL fallback)

#### `graph_nodes`
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | VARCHAR(64) | PK | Node ID |
| `tenant_id` | VARCHAR(36) | NOT NULL, INDEX | Tenant |
| `labels` | VARCHAR(50)[] | NOT NULL | Node labels |
| `properties` | JSONB | NULLABLE | Properties |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Created |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Updated |

**Index**: `ix_graph_nodes_search` (GIN on to_tsvector of name_ar, name_en, cr_number from properties)  
**References**: `0004_knowledge_graph.py:39-57`

#### `graph_edges`
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PK, AUTOINCREMENT | Sequential |
| `source_id` | VARCHAR(64) | NOT NULL | Source node |
| `target_id` | VARCHAR(64) | NOT NULL | Target node |
| `edge_type` | VARCHAR(50) | NOT NULL | Relationship type |
| `properties` | JSONB | NULLABLE | Properties |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Created |

**Indexes**: `ix_graph_edges_source` (source_id, edge_type), `ix_graph_edges_target` (target_id, edge_type), `ix_graph_edges_unique` UNIQUE (source_id, target_id, edge_type)

### 3.10 RAG Domain

#### `rag_documents`
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Document ID |
| `tenant_id` | VARCHAR(36) | NOT NULL | Tenant |
| `source_type` | VARCHAR(50) | NOT NULL | email/meeting/note/company_profile |
| `source_id` | VARCHAR(255) | NOT NULL | Source ID |
| `title` | TEXT | NOT NULL, DEFAULT '' | Title |
| `content` | TEXT | NOT NULL, DEFAULT '' | Full content |
| `metadata` | JSONB | NOT NULL, DEFAULT '{}' | Metadata |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Created |

**Index**: `idx_rag_chunks_tenant` (tenant_id)  
**References**: `0015_rag_tables.py:25-37`

#### `rag_document_chunks`
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Chunk ID |
| `document_id` | UUID | FK→rag_documents.id ON DELETE CASCADE, NOT NULL | Document |
| `content` | TEXT | NOT NULL | Chunk content |
| `chunk_index` | INTEGER | NOT NULL, DEFAULT 0 | Chunk position |
| `embedding` | vector(3072) | NULLABLE | pgvector embedding |
| `metadata` | JSONB | NOT NULL, DEFAULT '{}' | Metadata |

**Indexes**: `idx_rag_chunks_document` (document_id), `idx_rag_chunks_vector` (IVFFlat on embedding vector_cosine_ops WITH lists=100)

### 3.11 Workflow Domain

#### `workflow_definitions`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | VARCHAR(64) | PK |
| `tenant_id` | VARCHAR(64) | NOT NULL, INDEX |
| `name` | VARCHAR(255) | NOT NULL |
| `description` | TEXT | NOT NULL, DEFAULT '' |
| `trigger_type` | VARCHAR(50) | NOT NULL, DEFAULT 'manual' |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'draft' |
| `steps` | JSONB | NOT NULL, DEFAULT '[]' |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

**Index**: `idx_workflow_definitions_status` (status)  
**References**: `004_workflow.sql:4-16`

#### `workflow_executions`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | VARCHAR(64) | PK |
| `workflow_id` | VARCHAR(64) | NOT NULL, INDEX |
| `tenant_id` | VARCHAR(64) | NOT NULL, INDEX |
| `trigger_event` | VARCHAR(100) | NOT NULL, DEFAULT 'manual' |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'running' |
| `started_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| `completed_at` | TIMESTAMPTZ | NULLABLE |
| `error` | TEXT | NULLABLE |
| `step_results` | JSONB | NOT NULL, DEFAULT '[]' |

**References**: `004_workflow.sql:19-32`

### 3.12 Notifications Domain

#### `notifications`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | SERIAL | PK |
| `notification_id` | VARCHAR(64) | UNIQUE, NOT NULL |
| `tenant_id` | VARCHAR(64) | NOT NULL, INDEX |
| `user_id` | VARCHAR(64) | NOT NULL, INDEX |
| `type` | VARCHAR(50) | NOT NULL |
| `title` | VARCHAR(500) | NOT NULL |
| `body` | TEXT | NOT NULL, DEFAULT '' |
| `data` | JSONB | NULLABLE |
| `read` | BOOLEAN | NOT NULL, DEFAULT false, INDEX |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now(), INDEX |

**References**: `005_notifications.sql:2-18`

### 3.13 Analytics Domain

#### `analytics_reports`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | VARCHAR(36) | PK |
| `tenant_id` | VARCHAR(36) | NOT NULL, INDEX |
| `name` | VARCHAR(500) | NOT NULL |
| `type` | VARCHAR(50) | NOT NULL, DEFAULT 'custom' |
| `config` | JSON | NOT NULL, DEFAULT {} |
| `schedule` | VARCHAR(100) | NOT NULL, DEFAULT 'one-time' |
| `recipients` | JSON | NOT NULL, DEFAULT [] |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

**References**: `domains/analytics/infrastructure/models.py:15-30`, `0014_analytics.py:24-35`

#### `analytics_report_executions`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | VARCHAR(36) | PK |
| `report_id` | VARCHAR(36) | NOT NULL, INDEX |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'pending' |
| `output_format` | VARCHAR(10) | NOT NULL, DEFAULT 'json' |
| `output_path` | VARCHAR(1000) | NULLABLE |
| `error` | TEXT | NULLABLE |
| `started_at` | TIMESTAMPTZ | NULLABLE |
| `completed_at` | TIMESTAMPTZ | NULLABLE |

**References**: `0014_analytics.py:36-47`

#### `revenue_analytics_snapshots` (legacy, raw SQL)
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | VARCHAR(64) | PK |
| `tenant_id` | VARCHAR(64) | NOT NULL, INDEX |
| `period_start` | TIMESTAMPTZ | NULLABLE |
| `period_end` | TIMESTAMPTZ | NULLABLE |
| `values` | JSONB | NOT NULL, DEFAULT '[]' |
| `generated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| `version` | INTEGER | NOT NULL, DEFAULT 1 |

### 3.14 Infrastructure Tables

| Table | Schema | PK Type | Key Columns | Source |
|-------|--------|---------|-------------|--------|
| `domain_events` | public | UUID | event_id (UNIQUE), event_type, aggregate_type, aggregate_id, tenant_id, data (JSONB) | `0001_baseline.py:68-82` |
| `activity_records` | public | VARCHAR(64) | actor, action, entity_type, entity_id, tenant_id, metadata (JSONB) | `0009_activity_runtime.py:23-44` |
| `audit_log` | audit | UUID | tenant_id, entity_type, entity_id, action, changes (JSONB) | `0001_baseline.py:45-65` |
| `audit_logs` | public | BIGSERIAL | tenant_id, user_id, action, resource_type, resource_id, details (JSONB) | `database.py:48-70` |
| `dead_letter_queue` | public | INTEGER AUTOINCREMENT | tenant_id, source_slug, cr_number, stage, record_data (JSONB), error_message, retry_count | `0011_dead_letter_queue.py:17-34` |
| `sso_connections` | public | VARCHAR(64) | user_id (FK), provider, provider_user_id, access_token, refresh_token | `database.py:108-123` |
| `api_keys` | public | VARCHAR(64) | tenant_id (FK), user_id (FK), key_prefix, key_hash, permissions (JSONB) | `database.py:144-163` |
| `telemetry_events` | public | INTEGER AUTOINCREMENT | tenant_id, user_id, event_type, properties (JSONB) | `telemetry/models.py:10-19` |
| `graph_nodes` | public | VARCHAR(64) | tenant_id, labels (ARRAY), properties (JSONB) | `0004_knowledge_graph.py:39-49` |
| `graph_edges` | public | INTEGER AUTOINCREMENT | source_id, target_id, edge_type | `0004_knowledge_graph.py:24-37` |

### 3.15 Legacy Tables (from 001_initial.sql — partially superseded)

| Table | Status | Superseded By |
|-------|--------|---------------|
| `opportunities` | REDUNDANT | `commercial_opportunities` (0007) |
| `opportunity_notes` | REDUNDANT | `commercial_activities` |
| `tasks` | REDUNDANT | Not replaced, but has separate ORM model |
| `meetings` (legacy, company_id) | REDUNDANT | `meetings` (0013, opportunity_id) |
| `search_history` | ACTIVE | None |
| `company_intelligence` | LEGACY | Feature Store tables |
| `decision_makers` | LEGACY | `contacts` |
| `signals` | LEGACY | `company_intent_*` tables |
| `timeline_events` | LEGACY | `timeline_entries` (0005) |
| `government_records` | LEGACY | `licenses` |
| `documents` | LEGACY | `rag_documents` |

---

## 4. Index Catalog

### 4.1 B-Tree Indexes

| Index Name | Table | Columns | Purpose |
|-----------|-------|---------|---------|
| `ix_tenants_slug` | tenants | (slug) | Fast slug lookup |
| `ix_users_email` | users | (email) | Fast email lookup |
| `ix_users_tenant_id` | users | (tenant_id) | Tenant-scoped user queries |
| `ix_password_reset_tokens_user_id` | password_reset_tokens | (user_id) | User's reset tokens |
| `ix_password_reset_tokens_token_hash` | password_reset_tokens | (token_hash) | Token validation |
| `ix_refresh_token_families_user_id` | refresh_token_families | (user_id) | User's tokens |
| `ix_refresh_token_families_family_id` | refresh_token_families | (family_id) | Token rotation |
| `ix_device_sessions_user_id` | device_sessions | (user_id) | User's sessions |
| `ix_companies_tenant_cr` | companies | (tenant_id, cr_number) UNIQUE | **Critical**: Enforce one CR per tenant |
| `ix_companies_cr_number` | companies | (cr_number) | CR lookup |
| `ix_companies_name_ar` | companies | (name_ar) | Arabic name lookup |
| `ix_companies_status` | companies | (status) | Status filter |
| `ix_companies_city` | companies | (city) | City filter |
| `ix_companies_industry` | companies | (industry) | Industry filter |
| `ix_companies_tenant_id` | companies | (tenant_id) | Tenant scoping |
| `ix_golden_records_tenant_cr` | golden_records | (tenant_id, cr_number) UNIQUE | One golden record per CR per tenant |
| `ix_licenses_license_number` | licenses | (license_number) | License lookup |
| `ix_contacts_tenant_email` | contacts | (tenant_id, email) | Contact dedup |
| `ix_contacts_tenant_company` | contacts | (tenant_id, company_id) | Company contacts |
| `ix_notifications_tenant_id` | notifications | (tenant_id) | Tenant notifications |
| `ix_notifications_user_id` | notifications | (user_id) | User notifications |
| `ix_notifications_read` | notifications | (read) | Unread filter |
| `ix_notifications_created_at` | notifications | (created_at) | Time ordering |
| `ix_opportunities_tenant_stage` | commercial_opportunities | (tenant_id, stage) | Pipeline by stage |
| `ix_opportunities_tenant_status` | commercial_opportunities | (tenant_id, status) | Open/won/lost filter |
| `ix_quotes_opportunity_status` | commercial_quotes | (opportunity_id, status) | Opportunity quotes |
| `ix_contracts_tenant_status` | commercial_contracts | (tenant_id, status) | Contract status |
| `ix_activities_session_type` | commercial_activities | (session_id, activity_type) | Session activities |
| `ix_commercial_activities_tenant` | commercial_activities | (tenant_id) | Tenant scoping |
| `ix_recommendations_target` | commercial_recommendations | (target_id, target_type) | Recommendation lookup |
| `ix_decision_contexts_target` | commercial_decision_contexts | (target_id, target_type) | Decision context |
| `ix_meetings_opportunity` | meetings | (opportunity_id, tenant_id) | Opportunity meetings |
| `ix_emails_opportunity` | emails | (opportunity_id, tenant_id) | Opportunity emails |
| `ix_timeline_entity` | timeline_entries | (entity_type, entity_id, created_at DESC) | **Critical**: Entity timeline |
| `ix_timeline_tenant` | timeline_entries | (tenant_id, entity_type, created_at DESC) | Tenant timeline |
| `ix_timeline_event_type` | timeline_entries | (entity_type, entity_id, event_type) | Filter by event |
| `ix_decisions_company` | decisions | (tenant_id, company_id) | Company decisions |
| `ix_decisions_status` | decisions | (tenant_id, status) | Status filter |
| `ix_decisions_created` | decisions | (created_at DESC) | Time ordering |
| `ix_feedback_decision` | decision_feedback_loop | (decision_id) | Feedback lookup |
| `ix_feedback_company` | decision_feedback_loop | (tenant_id, company_id) | Company feedback |
| `ix_policies_company` | company_policies | (tenant_id, company_id, policy_name) UNIQUE | Policy dedup |
| `ix_company_features_lookup` | company_features | (tenant_id, company_id, feature_name) UNIQUE | Feature dedup |
| `ix_feature_values_lookup` | feature_values | (entity_type, entity_id, feature_key) | Feature lookup |
| `ix_dlq_tenant_status` | dead_letter_queue | (tenant_id, status) | DLQ management |
| `ix_dlq_created_at` | dead_letter_queue | (created_at) | Time ordering |
| `ix_domain_events_type` | domain_events | (event_type) | Event type filter |
| `ix_domain_events_aggregate` | domain_events | (aggregate_type, aggregate_id) | Aggregate lookup |
| `ix_activity_entity` | activity_records | (entity_type, entity_id, timestamp DESC) | Entity activity |
| `ix_activity_tenant_action` | activity_records | (tenant_id, action, timestamp DESC) | Tenant activity |
| `ix_activity_actor` | activity_records | (actor, timestamp DESC) | Actor activity |
| `ix_activity_action` | activity_records | (action, timestamp DESC) | Action filter |
| `ix_audit_log_entity` | audit.audit_log | (entity_type, entity_id) | Entity audit |
| `ix_audit_log_tenant_performed` | audit.audit_log | (tenant_id, performed_at DESC) | Tenant audit |
| `ix_audit_logs_tenant_action` | audit_logs | (tenant_id, action, created_at DESC) | Audit query |
| `ix_audit_logs_tenant_resource` | audit_logs | (tenant_id, resource_type, created_at DESC) | Resource audit |
| `ix_audit_logs_created_at` | audit_logs | (created_at DESC) | Time ordering |
| `ix_api_keys_prefix` | api_keys | (key_prefix) | Key lookup |
| `ix_api_keys_user` | api_keys | (user_id) | User's keys |
| `ix_sso_user_provider` | sso_connections | (user_id, provider) | SSO lookup |
| `ix_graph_edges_source` | graph_edges | (source_id, edge_type) | Graph traversal |
| `ix_graph_edges_target` | graph_edges | (target_id, edge_type) | Reverse traversal |
| `ix_graph_edges_unique` | graph_edges | (source_id, target_id, edge_type) UNIQUE | Edge dedup |
| `ix_vectors_created_at` | vectors | (created_at) | Time ordering |
| `idx_rag_chunks_tenant` | rag_documents | (tenant_id) | Tenant docs |
| `idx_rag_chunks_document` | rag_document_chunks | (document_id) | Document chunks |
| `idx_companies_tenant_search_vector` | companies | (tenant_id, search_vector) GIN | **Critical**: Tenant-scoped FTS |
| `ix_companies_embedding_hnsw` | companies | (embedding_vector vector_cosine_ops) HNSW | **Critical**: ANN semantic search |
| `idx_vectors_embedding_hnsw` | vectors | (embedding vector_cosine_ops) HNSW | Generic vector ANN |
| `idx_rag_chunks_vector` | rag_document_chunks | (embedding vector_cosine_ops) IVFFlat lists=100 | RAG vector search |
| `ix_graph_nodes_search` | graph_nodes | GIN(to_tsvector(...)) | Graph node FTS |
| `ix_companies_tsv` | companies | (tsv) GIN | Legacy FTS |

### 4.2 Full-Text Search Indexes

| Index | Type | Columns | Language | Generation |
|-------|------|---------|----------|------------|
| `ix_companies_tsv` | GIN | (tsv) | arabic | Trigger `trg_companies_tsv` → `refresh_companies_tsv()` |
| `ix_companies_search_vector` | GIN | (search_vector) | simple | GENERATED ALWAYS AS STORED |
| `ix_companies_tenant_search_vector` | GIN | (tenant_id, search_vector) | simple | Composite for filtered FTS |
| `ix_graph_nodes_search` | GIN | (to_tsvector(...)) | simple | Properties FTS |

**Note**: `search_vector` (0023) is the deterministic replacement for `tsv` (0006). The old `tsv` column uses Arabic text search configuration; the new `search_vector` uses `simple` (which handles both Arabic and English better with the tokenizer). The `refresh_companies_search_vectors` trigger (0024) keeps both in sync.

### 4.3 Vector/ANN Indexes

| Index | Type | Column | Operator | Dimensions | Notes |
|-------|------|--------|----------|------------|-------|
| `idx_companies_embedding_hnsw` | HNSW | embedding_vector vector_cosine_ops | <=> | 3072 | Created 0017, confirmed 0024 |
| `idx_vectors_embedding_hnsw` | HNSW | embedding vector_cosine_ops | <=> | 3072 | Created 0021 |
| `idx_rag_chunks_vector` | IVFFlat | embedding vector_cosine_ops | <=> | 3072 | lists=100, Created 0015 |

### 4.4 Trigram/Fuzzy Indexes

| Index | Type | Column | Purpose |
|-------|------|--------|---------|
| `idx_companies_name_trgm` | GIN | (name_ar gin_trgm_ops) | **Critical**: Entity resolution fuzzy matching on Arabic company names |

### 4.5 Partial Indexes

| Index | Table | Condition | Purpose |
|-------|-------|-----------|---------|
| `idx_tasks_priority` | tasks | WHERE NOT completed | Active task priority filter |

### 4.6 Index Assessment Summary

| Category | Count | Coverage |
|----------|-------|----------|
| B-tree indexes | 60+ | Excellent — all FK columns indexed |
| GIN (full-text) indexes | 4 | Excellent — both legacy and deterministic FTS |
| GIN (trigram) indexes | 1 | Good — Arabic name fuzzy matching |
| HNSW (vector ANN) indexes | 2 | Excellent — both companies and generic vectors |
| IVFFlat (vector ANN) indexes | 1 | Good for small-medium RAG datasets |
| Partial indexes | 1 | Minimal — only tasks |
| Composite indexes | 20+ | Good — tenant-scoped queries optimized |
| UNIQUE constraints via indexes | 5 | Good — deduplication enforced |

### 4.7 Missing Recommended Indexes

| Table | Suggested Index | Reason |
|-------|----------------|--------|
| `commercial_opportunities` | (tenant_id, expected_close_date) | Pipeline forecasting queries |
| `commercial_opportunities` | (owner_id) | Sales rep filtering |
| `contacts` | (email) | Contact deduplication and lookup |
| `company_features` | (tenant_id, feature_name) | Feature aggregation queries |
| `rag_documents` | (tenant_id, source_type) | RAG source filtering |
| `emails` | (sent_at DESC) | Email timeline |
| `meetings` | (meeting_date DESC) | Meeting timeline |
| `notifications` | (tenant_id, user_id, read) | Unread notification count |
| `feature_values` | (feature_key, entity_type) | Feature value aggregation |
| `analytics_reports` | (tenant_id, type) | Report type filtering |

---

## 5. Migration History

### 5.1 Raw SQL Migrations (`backend/migrations/`)

| File | Date | Tables Created | Status |
|------|------|----------------|--------|
| `001_initial.sql` | ~2026-06 (v1.0) | tenants, users, companies, company_intelligence, decision_makers, signals, timeline_events, government_records, documents, opportunities, opportunity_notes, tasks, meetings, search_history | **Partially superseded** by Alembic 0001+ |
| `002_create_opportunities_tasks.sql` | ~2026-07 (v0.2) | opportunities, opportunity_notes, tasks (idempotent CREATE IF NOT EXISTS) | **Redundant** with 001_initial.sql and 0007 |
| `003_revenue_analytics.sql` | ~2026-07 | revenue_analytics_snapshots | **Active** — raw SQL table |
| `004_workflow.sql` | ~2026-07 | workflow_definitions, workflow_executions | **Active** — raw SQL tables |
| `005_notifications.sql` | ~2026-07 | notifications | **Active** — raw SQL table (no ORM model registered) |

### 5.2 Alembic Migration History

| Revision | Date | Title | Tables/Changes | Impact |
|----------|------|-------|----------------|--------|
| `0001` | 2026-06-30 | baseline | audit_log, domain_events, tenants, users, sources, companies, branches, licenses, contacts, golden_records, entity_resolution_conflicts, entity_resolution_log | **FOUNDATION** — 12 core tables + 5 extensions + 5 schemas |
| `0002` | 2026-06-30 | feature store | company_features, company_funding_events, company_job_postings, company_intent_rfps, company_intent_visits, company_intent_content, company_intent_contacts, company_products, company_deals, company_payments + 10 columns added to companies | **LARGE** — 10 feature tables + company enrichment fields |
| `0003` | 2026-06-30 | decision engine | decisions, decision_feedback_loop, company_policies + do_not_contact column | **MEDIUM** — Decision intelligence tables |
| `0004` | 2026-06-30 | knowledge graph | graph_edges, graph_nodes + GIN index | **MEDIUM** — Graph fallback tables |
| `0005` | 2026-06-30 | timeline runtime | timeline_entries | **MEDIUM** — Universal timeline |
| `0006` | 2026-06-30 | search runtime | companies.embedding, companies.embedding_vector, companies.tsv + GIN index + trigger | **HIGH** — Search infrastructure |
| `0007` | 2026-07-02 | commercial domain | commercial_opportunities, commercial_stage_entries, commercial_pipeline_definitions, commercial_activity_sessions, commercial_activities, commercial_quotes, commercial_quote_lines, commercial_proposals, commercial_contracts, commercial_forecast_snapshots, commercial_analytics_snapshots, commercial_decision_contexts, commercial_policies, commercial_recommendations | **LARGEST** — 14 tables |
| `0008` | 2026-07-02 | contact module | contacts_standalone | **SMALL** — later merged into contacts |
| `0009` | 2026-07-03 | activity runtime | activity_records | **MEDIUM** — Activity spine |
| `0010` | 2026-07-03 | vector store | vectors | **MEDIUM** — Generic vector storage |
| `0011` | 2026-07-03 | dead letter queue | dead_letter_queue | **SMALL** — DLQ for pipeline failures |
| `020cfcbab7b4` | 2026-07-08 | refresh tokens | token_blacklist, password_reset_tokens, refresh_token_families, device_sessions | **HIGH** — Security: token management |
| `0013` | 2026-07-11 | meetings & emails | meetings, emails | **MEDIUM** — Communications domain |
| `0014` | 2026-07-11 | analytics | analytics_reports, analytics_report_executions | **MEDIUM** — Reporting |
| `0015` | 2026-07-12 | RAG tables | rag_documents, rag_document_chunks + IVFFlat index | **MEDIUM** — Document retrieval |
| `0016` | 2026-07-12 | drop dual embedding | Drops companies.embedding ARRAY column | **FIX** — Cleanup after 0006 |
| `0017` | 2026-07-12 | HNSW index | idx_companies_embedding_hnsw | **PERF** — ANN search index |
| `0018` | 2026-07-12 | feature store FKs | FKs on 18 company_* tables → tenants + companies | **INTEGRITY** — Referential constraints |
| `0019` | 2026-07-12 | commercial FKs | FKs on commercial_* tables → tenants + companies + each other | **INTEGRITY** — Referential constraints |
| `0020` | 2026-07-12 | tenant_id | tenant_id + FK on signals, timeline_events, government_records, documents, meetings (legacy) | **INTEGRITY** — Multi-tenant isolation |
| `0021` | 2026-07-12 | fix vectors embedding | vectors.embedding ARRAY→vector(3072) + HNSW index | **FIX** — Native pgvector type |
| `0022` | 2026-07-12 | consolidate contacts | Merge contacts_standalone → contacts + drop contacts_standalone | **REFACTOR** — Deduplicate tables |
| `0023` | 2026-07-12 | fulltext search | companies.search_vector GENERATED ALWAYS + GIN index | **PERF** — Deterministic FTS (BUG-001 fix) |
| `0024` (enable_pg_trgm) | 2026-07-12 | trigram index | idx_companies_name_trgm GIN | **PERF** — Fuzzy name matching |
| `0024` (hybrid) | 2026-07-12 | hybrid search | idx_companies_tenant_search_vector GIN + trigger | **PERF** — Tenant-scoped FTS |
| `0025` | 2026-07-12 | feature store v2 | feature_definitions, feature_values | **MEDIUM** — Entity-agnostic feature store |

**Total**: 25 Alembic migrations + 5 raw SQL migrations = 30 schema changes.

### 5.3 Migration Integrity Concerns

1. **Duplicate Revision ID `0024`**: Two migration files share revision `0024`:
   - `0024_enable_pg_trgm.py` (line 10: `revision = "0024"`)
   - `0024_hybrid_search_optimization.py` (line 17: `revision = "0024"`)
   - **Risk**: Alembic may skip one of them. Both have `down_revision = "0023"` — branch conflict.

2. **Raw SQL vs Alembic**: The raw SQL files under `migrations/` are NOT managed by Alembic's revision tracking. They use `CREATE TABLE IF NOT EXISTS` for idempotency, which is safer but may mask schema drift if not carefully maintained.

3. **Revision 0012 has a different format**: Uses `revision: str = '020cfcbab7b4'` (hash-style) instead of numbered format. This is auto-generated by `alembic revision --autogenerate`.

4. **Missing downgrade for some migrations**: Raw SQL files have no downgrade path. Alembic migrations have downgrades.

---

## 6. Repository Pattern Assessment

### 6.1 Repository Architecture

SalesOS uses a **Clean Architecture** pattern with domain-layer repository interfaces (ABCs/Protocols) and infrastructure-layer implementations.

```
Layer                      Pattern
─────────────────────────────────────────
Domain/Contracts           Repository ABC (interface)
Domain/Engine              InMemoryRepository (test/dev)
Infrastructure             PostgresRepository (production)
```

Base classes from `sdk/database.py`:
- `Repository[T, TId]` — Generic ABC (get, save, delete, exists)
- `SqlAlchemyRepository[T, TId]` — SQLAlchemy implementation (find_all added)
- `UnitOfWork` — Transaction management
- `Specification` — Query filter composition

### 6.2 Repository Inventory

| Domain | Interface (ABC) | PostgreSQL Implementation | InMemory Implementation | Status |
|--------|-----------------|--------------------------|------------------------|--------|
| **Identity** | `SqlAlchemyRepository` | `TenantRepository`, `UserRepository` (`app/modules/identity/repositories.py`) | — | ✅ PostgreSQL |
| **Company** | Implicit | `company/repositories.py` | — | ✅ PostgreSQL |
| **Company (Search)** | — | `company/search_repository.py` | — | ✅ PostgreSQL |
| **Company (Vector)** | — | `company/pgvector_repository.py` | — | ✅ PostgreSQL |
| **Contact** | Implicit | `contact/repositories.py`, `contact/search_repository.py` | — | ✅ PostgreSQL |
| **Entity Resolution** | Implicit | `entity_resolution/repositories.py` | — | ✅ PostgreSQL |
| **Commercial — Opportunity** | `OpportunityRepository` | `PostgresOpportunityRepository` (`domains/commercial/infrastructure/postgres_repositories.py:50`) | `InMemoryOpportunityRepository` (`opportunity/engine/in_memory_repo.py`) | ✅ PostgreSQL |
| **Commercial — Pipeline** | `PipelineRepository` | `PostgresPipelineRepository` (postgres_repositories.py:166) | `InMemoryPipelineRepository` (`pipeline/engine/in_memory_repo.py`) | ✅ PostgreSQL |
| **Commercial — Activity** | `ActivityRepository` | `PostgresActivityRepository` (postgres_repositories.py:254) | `InMemoryActivityRepository` (`activity/engine/in_memory_repo.py`) | ✅ PostgreSQL |
| **Commercial — Quote** | `QuoteRepository` | `PostgresQuoteRepository` (postgres_repositories.py:336) | `InMemoryQuoteRepository` (`quote/engine/in_memory_repo.py`) | ✅ PostgreSQL |
| **Commercial — Proposal** | `ProposalRepository` | `PostgresProposalRepository` (postgres_repositories.py:423) | `InMemoryProposalRepository` (`proposal/engine/in_memory_repo.py`) | ✅ PostgreSQL |
| **Commercial — Contract** | `ContractRepository` | `PostgresContractRepository` (postgres_repositories.py:507) | `InMemoryContractRepository` (`contract/in_memory_repo.py`) | ✅ PostgreSQL |
| **Commercial — Meeting** | `MeetingRepository` | `PostgresMeetingRepository` (postgres_repositories.py:857) | `InMemoryMeetingRepository` (`meeting/in_memory_repo.py`) | ✅ PostgreSQL |
| **Commercial — Email** | `EmailRepository` | `PostgresEmailRepository` (postgres_repositories.py:928) | `InMemoryEmailRepository` (`email/in_memory_repo.py`) | ✅ PostgreSQL |
| **Forecast** | `ForecastRepository` | `PostgresForecastRepository` (postgres_repositories.py:617) | `InMemoryForecastRepository` (`revenue/forecast/in_memory_repo.py`) | ✅ PostgreSQL |
| **Analytics (Revenue)** | `AnalyticsRepository` | `PostgresAnalyticsRepository` (postgres_repositories.py:690) | `InMemoryAnalyticsRepository` (`revenue/analytics/in_memory_repo.py`) | ✅ PostgreSQL |
| **Decision — Context** | `DecisionRepository` | `PostgresDecisionRepository` (postgres_repositories.py:740) | `InMemoryDecisionRepository` (`decision/context/in_memory_repo.py`) | ✅ PostgreSQL |
| **Decision — Recommendation** | `RecommendationRepository` | `PostgresRecommendationRepository` (postgres_repositories.py:799) | `InMemoryRecommendationRepository` (`decision/recommendation/in_memory_repo.py`) | ✅ PostgreSQL |
| **Timeline** | `TimelineRepository` | `PostgresTimelineRepository` (`domains/timeline/engine/postgres_repo.py`) | `InMemoryTimelineRepository` (`timeline/engine/in_memory_repo.py`) | ✅ PostgreSQL |
| **Search** | `SearchRepository` | `PostgresSearchRepository` (`domains/search/engine/postgres_repo.py`) | — | ✅ PostgreSQL |
| **Feature Store** | `FeatureStoreRepository` | `PostgresFeatureStoreRepository` (`domains/feature_store/postgres_repo.py`) | `InMemoryFeatureStoreRepository` (`feature_store/repository.py`) | ✅ PostgreSQL |
| **Analytics (Reports)** | — | `PostgresReportRepository` (`domains/analytics/infrastructure/postgres_repository.py`) | — | ✅ PostgreSQL |
| **Scoring** | — | `PostgresScoringRepository` (`domains/scoring/infrastructure/postgres_repository.py`) | — | ✅ PostgreSQL |
| **Workflow** | Implicit | `PostgresWorkflowRepository` (`domains/workflow/postgres_repo.py`) | — | ✅ PostgreSQL |
| **Notifications** | `NotificationRepository` | `PostgresNotificationRepository` (`domains/notifications/postgres_repo.py`) | `InMemoryNotificationRepository` (`notifications/models.py`) | ✅ PostgreSQL |
| **Telemetry** | — | `TelemetryRepository` (`app/modules/telemetry/repository.py`) | — | ✅ PostgreSQL |
| **Admin** | — | `AdminRepositories` (`app/modules/admin/pg_repositories.py`) | InMemory (`admin/repositories.py`) | ✅ PostgreSQL |

### 6.3 InMemory vs PostgreSQL Summary

| Status | Count | Notes |
|--------|-------|-------|
| PostgreSQL (production) | All 25+ repositories | Complete migration as of Sprint 5 |
| InMemory (test/dev only) | 15+ (parallel) | Used in unit tests, never in production |
| No implementation | 0 | All domains covered |

**Assessment**: The entire repository layer has been migrated to PostgreSQL as documented in the Engineering Dashboard (Sprint 5 — "7 InMemory repos → PostgreSQL (TD-001)"). InMemory implementations remain for unit testing purposes, which is correct architecture per the Engineering Constitution (Article 2.2).

### 6.4 Repository Implementation Patterns

All PostgreSQL repositories follow one of three patterns:

**Pattern A: Save-or-Update** (most common)
```python
stmt = select(Model).where(Model.id == entity.id)
model = result.scalar_one_or_none()
if model:  # Update
    model.field = entity.field
else:      # Insert
    model = Model(...)
    self.session.add(model)
await self.session.flush()
```
Used by: Opportunity, Quote, Proposal, Contract, FeatureStore

**Pattern B: Direct Add** (simple)
```python
model = Model(...)
self.session.add(model)
await self.session.flush()
```
Used by: Forecast, Analytics, Recommendation

**Pattern C: SqlAlchemyRepository Base** (inherited)
```python
class TenantRepository(SqlAlchemyRepository[Tenant, uuid.UUID]):
    model_class = Tenant
```
Used by: Identity (Tenant, User)

---

## 7. Query Patterns & Data Flow

### 7.1 Core Data Flow Architecture

```
FastAPI Router → Service → Repository (ABC) → PostgreSQL/Neo4j
                                    ↑
                              Dependency Injection
                                    ↑
                         AsyncSession (per-request)
```

**References**: `backend/app/database.py:31-40` (get_db), `backend/sdk/database.py:131-156` (UnitOfWork)

### 7.2 Search Data Flow (Hybrid Search)

```
Client → POST /search
    → SearchRuntime (planner/parser/ranking)
        → PostgresSearchRepository.search()
            → Full-text: search_vector @@ to_tsquery → GIN index
            → Semantic: embedding_vector <-> $query_vector → HNSW index
            → RRF fusion (Reciprocal Rank Fusion)
        → StrategyMatrix (selects best strategy per query)
        → SearchResult with ranking metadata
```

**References**: `domains/search/engine/postgres_repo.py:78`, `domains/search/engine/hybrid_search.py`

### 7.3 Company Pipeline Query Pattern

```
Client → GET /companies/{id}
    → CompanyService
        → CompanyRepository (SQLAlchemy) → companies + branches + licenses + contacts
        → DecisionProvider → DecisionRepository → decisions, company_policies
        → FeatureProvider → FeatureStoreRepository → company_features
        → TimelineService → PostgresTimelineRepository → timeline_entries
        → GraphService → Neo4j → knowledge graph relationships
```

### 7.4 Entity Resolution Pipeline

```
Ingestion → pg_trgm fuzzy match (idx_companies_name_trgm)
    → GoldenRecord merge
        → EntityResolutionConflict detection
        → DeadLetterQueue for failures
    → Company create/update
```

### 7.5 Common Query Patterns

**Tenant-scoped queries** (used everywhere):
```sql
WHERE tenant_id = $1 AND ...
```
All major tables have `tenant_id` indexed.

**Full-text search on companies** (via search_vector):
```sql
WHERE search_vector @@ plainto_tsquery('simple', $query)
AND tenant_id = $1
ORDER BY ts_rank(search_vector, query) DESC
```

**Vector similarity search** (via embedding_vector):
```sql
ORDER BY embedding_vector <=> $query_vector
LIMIT $k
```

**Timeline queries** (entity-scoped):
```sql
WHERE entity_type = $1 AND entity_id = $2
ORDER BY created_at DESC
```

### 7.6 N+1 Query Risks

| Risk | Location | Mitigation |
|------|----------|------------|
| Company → Branches | `company/models.py:78` | `lazy="selectin"` — eager load |
| Company → Licenses | `company/models.py:79` | `lazy="selectin"` |
| Company → Contacts | `company/models.py:80` | `lazy="selectin"` |
| Tenant → Users | `identity/models.py:23` | `lazy="selectin"` |
| Opportunity → Stage Entries | Query pattern | **Risk**: Not eagerly loaded in PostgresOpportunityRepository |
| Opportunity → Quotes | Query pattern | **Risk**: Separate query per opportunity |
| Opportunity → Meetings/Emails | Query pattern | **Risk**: Separate queries |

**Recommendation**: Add `selectinload` or `joinedload` for opportunity sub-entities in `PostgresOpportunityRepository.query()`.

### 7.7 Neo4j Data Flow

```
GraphService (sdk/graph.py)
    ├── create_node(labels, properties)
    ├── find_node(node_type, property_key, property_value)
    ├── create_relationship(from_id, to_id, rel_type, properties)
    ├── find_related(node_id, rel_type, direction)
    ├── shortest_path(from, to, max_hops=6)
    └── run_community_detection(label="Company")  → Louvain algorithm
```

Neo4j is used for:
- Company ownership hierarchies (parent/subsidiary)
- Knowledge graph relationship traversal
- Community detection for market segmentation
- Shortest path between companies

The `graph_nodes` and `graph_edges` PostgreSQL tables serve as a **SQL fallback** but are not the primary graph store.

---

## 8. Data Ownership Matrix

| Domain | Tables | Owned By Layer |
|--------|--------|----------------|
| **Identity** | tenants, users, password_reset_tokens, refresh_token_families, device_sessions, token_blacklist, sso_connections, api_keys | `app/modules/identity/` |
| **Company** | companies, branches, licenses, contacts, sources | `app/modules/company/` |
| **Company (Legacy)** | company_intelligence, decision_makers, signals, timeline_events, government_records, documents, search_history | `migrations/001_initial.sql` (no dedicated module) |
| **Entity Resolution** | golden_records, entity_resolution_conflicts, entity_resolution_log, dead_letter_queue | `app/modules/entity_resolution/` |
| **Commercial** | commercial_opportunities, commercial_stage_entries, commercial_pipeline_definitions, commercial_activity_sessions, commercial_activities, commercial_quotes, commercial_quote_lines, commercial_proposals, commercial_contracts, meetings, emails | `domains/commercial/` |
| **Commercial (Analytics)** | commercial_forecast_snapshots, commercial_analytics_snapshots, commercial_decision_contexts, commercial_policies, commercial_recommendations | `domains/commercial/` + `domains/revenue/` + `domains/decision/` |
| **Decision Engine** | decisions, decision_feedback_loop, company_policies | `domains/decision/` |
| **Feature Store** | company_features, company_funding_events, company_job_postings, company_intent_rfps, company_intent_visits, company_intent_content, company_intent_contacts, company_products, company_deals, company_payments, feature_definitions, feature_values | `domains/feature_store/` + reference columns in `0018_add_feature_store_fks.py` for company_news_mentions, company_government_contracts, company_patents, company_social_media, company_website_mentions, company_regulatory_filings, company_market_share, company_supply_chain |
| **Timeline** | timeline_entries, activity_records | `domains/timeline/` |
| **Search** | vectors, search_history | `domains/search/` (indirectly, via engine layer) |
| **Knowledge Graph** | graph_nodes, graph_edges | `domains/graph.py` → Neo4j via `sdk/graph.py` |
| **RAG** | rag_documents, rag_document_chunks | `domains/rag/` |
| **Workflow** | workflow_definitions, workflow_executions | `domains/workflow/` |
| **Notifications** | notifications | `domains/notifications/` |
| **Analytics** | analytics_reports, analytics_report_executions, revenue_analytics_snapshots | `domains/analytics/` + `migrations/003_revenue_analytics.sql` |
| **Audit** | audit.audit_log, audit_logs (public) | `app/modules/audit/` |
| **Telemetry** | telemetry_events | `app/modules/telemetry/` |
| **Domain Events** | domain_events | `sdk/events/` (not a module per se) |
| **Legacy CRM** | opportunities, opportunity_notes, tasks | `migrations/001_initial.sql` (superseded by `domains/commercial/`) |

---

## 9. Seed & Migration Data Analysis

### 9.1 PostgreSQL Initialization (`infra/docker/postgres/init/01-init.sql`)

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS audit;
CREATE SCHEMA IF NOT EXISTS identity;
CREATE SCHEMA IF NOT EXISTS company;
CREATE SCHEMA IF NOT EXISTS activity;
CREATE SCHEMA IF NOT EXISTS crm;
-- handled by alembic migration
```

**Assessment**: Clean initialization. Extensions are idempotent. Schemas are reserved but underutilized.

### 9.2 Run-Time Table Creation (`backend/app/database.py:init_db()`)

The `init_db()` function creates tables outside the ORM's metadata:
- `audit.audit_log`
- `domain_events`
- `activity_records`
- `sso_connections`
- `audit_logs` (public)
- `api_keys`

**Risk**: These tables are NOT in `Base.metadata` and will NOT be discovered by Alembic's auto-generation. They exist as both Alembic migrations (0001, 0009, etc.) and raw SQL creation. This dual creation could cause conflicts if the schema diverges.

### 9.3 Seed Data

- `0003_decision_engine.py:100-105` — Seeds `company_policies` for companies with `do_not_contact = true`
- No explicit seed data scripts found for tenants, users, companies. Likely via the application layer (demo mode).

### 9.4 Backup Strategy

**`backup-db.sh`** (`infra/scripts/backup-db.sh`):
- Uses `pg_dump --format=custom --compress=9`
- Retention: 7 days (configurable)
- Optional S3 upload via `aws s3 cp` or `rclone`
- Healthcheck ping and webhook notification

**`restore-db.sh`** (`infra/scripts/restore-db.sh`):
- Uses `pg_restore --clean --if-exists --no-owner --no-acl`
- Simple 2-argument invocation

**Production schedule**: Daily at 03:00 UTC via cron in the `backup` Docker service.

**Assessment**: Backups are compressed custom-format dumps. Good for medium datasets. No WAL archiving, no point-in-time recovery (PITR), no Neo4j backup strategy documented.

---

## 10. Database Performance Assessment

### 10.1 Index Strategy Assessment

| Aspect | Rating | Notes |
|--------|--------|-------|
| B-tree coverage | 🟢 Excellent | All FK columns indexed, composite indexes for common filters |
| Full-text search | 🟢 Excellent | Dual-path (trigger + GENERATED ALWAYS), GIN indexes |
| Vector/ANN search | 🟢 Excellent | HNSW on companies + vectors, IVFFlat on RAG chunks |
| Fuzzy search | 🟢 Good | pg_trgm GIN on name_ar, no trigram on name_en or cr_number |
| Tenant isolation | 🟢 Excellent | Every table has tenant_id + index |
| Composite indexes | 🟢 Good | Common query patterns covered |
| Covering indexes | 🔴 None | No covering indexes — every query hits the heap |

### 10.2 Query Performance Characteristics

| Query Pattern | Index Used | Complexity | Concern |
|--------------|------------|------------|---------|
| `SELECT * FROM companies WHERE tenant_id = $1` | `companies_tenant_id_idx` | O(log n) | None |
| `WHERE search_vector @@ query` | `idx_companies_search_vector` (GIN) | O(n) | GIN scan is efficient |
| `ORDER BY embedding_vector <=> $vec` | `idx_companies_embedding_hnsw` (HNSW) | O(log n) | Very fast ANN |
| `WHERE tenant_id = $1 AND search_vector @@ query` | `idx_companies_tenant_search_vector` (GIN) | O(n) | Good composite |
| `WHERE name_ar % $name` (trigram) | `idx_companies_name_trgm` (GIN) | O(n*m) | Fuzzy, OK for moderate data |
| `SELECT * FROM timeline_entries WHERE entity_type = $1 AND entity_id = $2 ORDER BY created_at DESC` | `ix_timeline_entity` | O(log n) | Efficient |
| `SELECT c.*, b.*, l.*, ct.* FROM companies c LEFT JOIN branches b LEFT JOIN licenses l LEFT JOIN contacts ct WHERE c.id = $1` | Multiple indexes, 3 JOINs | O(1) with PK | N+1 eliminated via `selectin` |

### 10.3 Potential Performance Bottlenecks

| Bottleneck | Location | Severity | Action |
|-----------|----------|----------|--------|
| Dual TSVECTOR columns | companies table | Low | `tsv` is legacy — consider removing after search_vector is validated |
| Missing owner_id index | commercial_opportunities | Medium | Filter by sales rep requires full scan |
| No pagination cursor pattern | Timeline, Search | Medium | Offset-based pagination degrades on deep pages |
| JSONB-heavy queries | company_features, decisions | Medium | No computed indexes on JSONB fields (e.g., `(features->>'value')::float`) |
| Neo4j + PostgreSQL dual-write | GraphService | Low | No distributed transaction — eventual consistency |
| 3072-d vector dimensionality | companies, vectors, RAG | Medium | High memory usage for HNSW/IVFFlat indexes |
| IVFFlat on RAG chunks | rag_document_chunks | Medium | IVFFlat needs periodic REINDEX; less accurate than HNSW |

### 10.4 Connection Pool Assessment

```
App Layer:          20 connections (pool_size=20) + 10 overflow
PgBouncer:          25 default pool, 100 max client connections
PostgreSQL:         Handles up to 25 active connections from PgBouncer
```

**Assessment**: Conservative settings for development. Production with 4 workers would need:
- Backend pool_size: 5 per worker × 4 workers = 20 (OK)
- PgBouncer pool_size: 25 (OK for 20 backend connections)
- Consider `pool_size=5` for 4-worker production to avoid exceeding PgBouncer

---

## 11. Data Integrity & Constraints Analysis

### 11.1 Constraint Coverage

| Constraint Type | Count | Coverage |
|----------------|-------|----------|
| PRIMARY KEY | 60+ | All tables have PKs |
| FOREIGN KEY | 50+ | Comprehensive — added progressively |
| NOT NULL | 200+ | Good on critical fields |
| UNIQUE constraint (via PK) | 60+ | All PKs |
| UNIQUE constraint (non-PK) | ~10 | slugs, CRs, emails |
| CHECK constraint | ~8 | stage, status, risk_level |
| DEFAULT values | 100+ | Comprehensive |
| CASCADE delete | ~25 | Feature store + commercial tables |
| SET NULL delete | 2 | Proposals.quote_id, Contracts.quote_id |
| Application-level | Many | Stage transitions, status workflows |

### 11.2 FK Integrity Timeline

FKs were added retroactively across two migrations:
- `0018_add_feature_store_fks.py` (2026-07-12): 18 tables → tenants + companies
- `0019_add_commercial_fks.py` (2026-07-12): Commercial tables → tenants + companies + chains
- `0020_add_tenant_id.py` (2026-07-12): Legacy tables → tenants

**Assessment**: FKs were added late (after data existed), which is architecturally sound for zero-downtime but means orphan records may exist if data was loaded before FKs existed.

### 11.3 Schema Design Issues

| Issue | Tables Affected | Severity | Recommendation |
|-------|----------------|----------|----------------|
| **Duplicate audit tables** | `audit.audit_log` vs `public.audit_logs` | 🟡 Medium | Consolidate — same purpose, different schemas |
| **Duplicate meetings tables** | Legacy `migrations/001_initial.sql` meetings vs Alembic `0013` meetings | 🔴 High | Legacy meetings has `company_id`, new has `opportunity_id`. Different schemas for same concept |
| **Duplicate opportunities** | Legacy `migrations/001_initial.sql` opportunities vs `commercial_opportunities` | 🔴 High | Two tables for same concept — different column names and types |
| **contacts_standalone → contacts merge** | Contacts | 🟢 Fixed | Merged in 0022 — clean now |
| **VARCHAR(36) vs UUID types** | Commercial tables | 🟡 Medium | Commercial domain uses `String(36)` for IDs while Identity/Company use native `UUID`. Type mismatch prevents direct FK from commercial_* → companies/tenants |
| **Dual embedding columns** | companies | 🟢 Fixed | `embedding` ARRAY removed in 0016 — single `embedding_vector vector(3072)` remains |
| **Dual TSVECTOR columns** | companies | 🟡 Low | `tsv` (trigger, arabic) vs `search_vector` (GENERATED ALWAYS, simple) — keep both for now |
| **Missing FK for `company_id` in commercial_recommendations** | commercial_recommendations | 🟡 Low | Uses `target_id` + `target_type` pattern but no FK to companies |
| **SERIAL vs UUID PKs** | Mixed | 🟡 Medium | `notifications` uses SERIAL, `graph_edges` uses SERIAL, most others use UUID. Inconsistent |
| **varchar tenant_id vs UUID tenant_id** | Across all tables | 🔴 High | Identity tables use native UUID for tenant_id. Commercial, Feature Store, Search, etc. use VARCHAR(36). Prevents FK constraints between Identity and other domains |
| **Revisions 0024 duplication** | Migration history | 🔴 High | Two migration files with same revision ID |

### 11.4 Critical Integrity Issue: VARCHAR(36) vs UUID

This is the **most significant data integrity issue** in the database:

- **Identity domain**: `tenants.id` = `UUID`, `users.tenant_id` = `UUID` (native PostgreSQL)
- **Everything else**: `tenant_id` = `VARCHAR(36)` or `VARCHAR(64)`

This type mismatch means:
- Direct FK constraints from `commercial_opportunities` → `tenants` are **not enforceable at the database level** unless explicit type casting is used
- The FKs added in 0018, 0019 use the raw column types, so PostgreSQL may accept them but comparisons may be unreliable
- ORM-level validation is the only protection

---

## 12. Database Technical Debt Register

| ID | Area | Severity | Effort | Description | Recommendation |
|----|------|----------|--------|-------------|----------------|
| DB-TD-001 | Duplicate tables | 🔴 Critical | 1 sprint | `opportunities` vs `commercial_opportunities`, legacy `meetings` vs new `meetings` | Consolidate legacy tables, add data migration, drop old tables |
| DB-TD-002 | Type mismatch | 🔴 Critical | 2 sprints | `VARCHAR(36)` tenant_id in commercial/feature/search vs native `UUID` in identity | Standardize all tenant_id to UUID. Requires data migration |
| DB-TD-003 | Duplicate migration revision | 🔴 Critical | 1 day | Two files with revision "0024" | Rename one of them, update down_revision chain |
| DB-TD-004 | Raw SQL vs Alembic | 🟡 High | 1 sprint | 5 SQL files not managed by Alembic version tracking | Convert to Alembic migrations, remove raw SQL files |
| DB-TD-005 | No covering indexes | 🟡 Medium | 3 days | No covering indexes for frequently queried column subsets | Add covering indexes for hot query paths (e.g., company name + cr_number queries) |
| DB-TD-006 | No DB-level enum types | 🟡 Medium | 5 days | stage, status, priority stored as VARCHAR with CHECK constraints | Consider native ENUM types or enum tables for referential integrity |
| DB-TD-007 | Dual audit tables | 🟡 Medium | 3 days | `audit.audit_log` + `audit_logs` serve same purpose | Consolidate, keep one schema |
| DB-TD-008 | Missing Neo4j backup | 🟡 Medium | 3 days | No documented Neo4j backup strategy | Add neo4j-admin backup to backup service |
| DB-TD-009 | No PITR/archiving | 🟡 Medium | 1 sprint | No WAL archiving for point-in-time recovery | Enable WAL archiving, add archive_command |
| DB-TD-010 | Missing composite FK indexes | 🟡 Medium | 2 days | `commercial_recommendations`, `commercial_forecast_snapshots` lack composite indexes | Add (tenant_id, status), (tenant_id, target_type) composite indexes |
| DB-TD-011 | JSONB query inefficiency | 🟡 Medium | 1 sprint | Features, decisions, policies stored as JSONB without computed indexes | Add expression indexes on commonly filtered JSONB fields |
| DB-TD-012 | Offset pagination | 🟢 Low | 3 days | Timeline and Search use offset/limit instead of keyset/cursor | Convert to cursor-based pagination for deep page performance |
| DB-TD-013 | IVFFlat staleness | 🟢 Low | 1 day | RAG chunks use IVFFlat — needs periodic REINDEX | Switch to HNSW for RAG chunks (consistent with companies) |
| DB-TD-014 | No tenant isolation at DB level | 🟢 Low | 1 sprint | All tenants share one database | Evaluate row-level security (RLS) policies for defense-in-depth |
| DB-TD-015 | Legacy TSVECTOR column | 🟢 Low | 1 day | `companies.tsv` maintained by trigger alongside `search_vector` (GENERATED ALWAYS) | Drop `tsv` once `search_vector` is validated in production |
| DB-TD-016 | SERIAL vs UUID inconsistency | 🟢 Low | 3 days | `notifications.id` and `graph_edges.id` are SERIAL instead of UUID | Standardize on UUID for all primary keys |
| DB-TD-017 | No enum reference tables | 🟢 Low | 3 days | Stage, status, type values hardcoded in CHECK constraints | Extract to reference/lookup tables for better extensibility |

---

## Executive Summary

### Key Statistics
| Metric | Value |
|--------|-------|
| Total database tables | ~60 |
| Alembic migrations | 25 |
| Raw SQL migrations | 5 |
| B-tree indexes | 60+ |
| GIN (full-text) indexes | 4 |
| HNSW (vector) indexes | 2 |
| IVFFlat (vector) indexes | 1 |
| Trigram (fuzzy) indexes | 1 |
| Foreign key constraints | 50+ |
| PostgreSQL extensions | 4 |
| Database schemas | 6 (public + 5 named) |
| ORM model files | 10+ |
| Repository implementations | 25+ (all PostgreSQL) |

### Overall Assessment

| Dimension | Score | Notes |
|-----------|-------|-------|
| Schema Design | 7/10 | Type inconsistency (UUID vs VARCHAR), duplicate tables |
| Index Strategy | 9/10 | Comprehensive — full-text, vector, fuzzy, tenant-scoped |
| Data Integrity | 6/10 | FKs added late, type mismatch prevents cross-domain FKs |
| Migration Hygiene | 6/10 | Duplicate revision, raw SQL outside Alembic |
| Repository Pattern | 10/10 | Perfect Clean Architecture — ABC → PostgreSQL + InMemory |
| Multi-Tenancy | 8/10 | Every table has tenant_id, but no RLS, type mismatch |
| Backup/Recovery | 6/10 | Daily dumps only, no PITR, no Neo4j backup |
| Performance Readiness | 8/10 | Good indexes, potential JSONB and pagination bottlenecks |
| Search Architecture | 10/10 | Excellent hybrid search with RRF fusion |

### Critical Actions (P0)
1. **Resolve duplicate revision 0024** (`DB-TD-003`)
2. **Consolidate duplicate opportunities/meetings tables** (`DB-TD-001`)
3. **Standardize tenant_id to UUID** (`DB-TD-002`)
4. **Convert raw SQL migrations to Alembic** (`DB-TD-004`)
