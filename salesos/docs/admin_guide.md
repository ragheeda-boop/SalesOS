# SalesOS — General Availability Admin Guide

> System administration reference for deploying, configuring, and maintaining SalesOS in production.
>
> Version: 1.0 | Last Updated: 2026-07-12 | Status: GA

---

## Table of Contents

- [1. System Overview](#1-system-overview)
- [2. Installation](#2-installation)
- [3. Configuration](#3-configuration)
- [4. Administration](#4-administration)
- [5. Security](#5-security)
- [6. Backup & Recovery](#6-backup--recovery)
- [7. Troubleshooting](#7-troubleshooting)
- [8. Maintenance](#8-maintenance)

---

## 1. System Overview

### 1.1 Architecture Summary

SalesOS is a multi-tenant SaaS platform for company intelligence and revenue execution. The architecture follows a layered design with strict domain boundaries.

```
                        ┌──────────────────────┐
                        │      Caddy (TLS)     │
                        │   :80 → :443 (auto)  │
                        └──────┬───────┬───────┘
                               │       │
                    ┌──────────┘       └──────────┐
                    ▼                              ▼
          ┌──────────────────┐          ┌──────────────────┐
          │   Next.js (SSR)  │          │   FastAPI (REST)  │
          │     :3000        │          │     :8000         │
          └──────────────────┘          └────────┬─────────┘
                                                 │
                    ┌──────────────┬──────────────┼──────────────┐
                    ▼              ▼              ▼              ▼
          ┌──────────────┐ ┌─────────────┐ ┌──────────┐ ┌────────────┐
          │  PostgreSQL   │ │    Neo4j    │ │  Redis   │ │ PgBouncer  │
          │  :5432        │ │  :7687      │ │  :6379   │ │  :6432     │
          │  (pgvector,   │ │  (Graph DB) │ │  (Cache) │ │  (Pool)    │
          │   pg_trgm)    │ │             │ │          │ │            │
          └──────────────┘ └─────────────┘ └──────────┘ └────────────┘
```

### 1.2 Key Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Frontend** | Next.js 15 (App Router), React 19, TypeScript | SSR dashboard, 37 domain widgets |
| **Backend API** | Python 3.11+, FastAPI, SQLAlchemy 2.0, Pydantic 2 | REST API, business logic, AI pipeline |
| **Primary Database** | PostgreSQL 16 (pgvector, pg_trgm extensions) | Structured data, vector embeddings, full-text search |
| **Graph Database** | Neo4j 5 (Community) | Knowledge graph, entity relationships |
| **Cache** | Redis 7 | Session cache, rate limiting, ephemeral data |
| **Connection Pooler** | PgBouncer (transaction mode) | Database connection management |
| **Reverse Proxy** | Caddy 2 | TLS termination, automatic HTTPS, routing |
| **Task Queue** | Celery + Redis | Background tasks, scheduled jobs |
| **Monitoring** | Prometheus + Grafana | Metrics, dashboards, alerting |
| **Database Backups** | pg_dump (custom format, gzip-9) | Automated daily backups with 7-day retention |

### 1.3 Authentication Flow

```
User Login (email + password)
    │
    ▼
POST /api/v1/identity/auth/login
    │  → Password verified (bcrypt)
    │  → JWT access token issued (HS256, 30 min expiry)
    │  → JWT refresh token issued (7 day expiry)
    │  → tenant_id embedded in token claims
    ▼
Client stores tokens (localStorage)
    │
    ▼
Every API request:
    Authorization: Bearer <access_token>
    │
    ▼
Backend middleware:
    1. Verify JWT signature (HS256)
    2. Check token expiry
    3. Extract tenant_id and user_id
    4. Resolve RBAC permissions
    5. Apply rate limit tier
    │
    ▼
Request reaches route handler with validated context
```

### 1.4 RBAC Roles

| Role | Permissions | Typical User |
|------|------------|--------------|
| `ADMIN` | Full access to all tenant data, user management, settings, billing | Tenant administrator |
| `MANAGER` | Manage data and users (except billing and tenant settings) | Sales manager, team lead |
| `USER` | View and create data within assigned scope | Sales representative |
| `API` | Programmatic API-only access with limited scope | Integration scripts, bots |
| `AUDITOR` | Read-only access across all tenant data for compliance | Compliance officer |

### 1.5 Rate Limiting Tiers

| Tier | Window | Limit | Applies To |
|------|--------|-------|------------|
| Authenticated | 1 minute | 100 requests | All authenticated API calls |
| Anonymous | 1 minute | 20 requests | Unauthenticated endpoints |
| Search | 1 minute | 30 requests | `/api/v1/search` endpoints |

Rate limits are enforced globally per IP (anonymous) or per JWT token (authenticated). Exceeding the limit returns HTTP 429 with a `Retry-After` header.

---

## 2. Installation

### 2.1 Prerequisites

| Dependency | Minimum Version | Purpose |
|-----------|----------------|---------|
| **Operating System** | Ubuntu 22.04 LTS (recommended) | Production host |
| **Docker** | 24.0+ | Container runtime |
| **Docker Compose** | v2.20+ | Multi-container orchestration |
| **Python** | 3.11+ | Backend runtime (inside container) |
| **Node.js** | 18+ | Frontend build (inside container) |
| **PostgreSQL** | 15+ (16 recommended) | Primary database (pgvector/pg16 image) |
| **Neo4j** | 5+ (Community) | Knowledge graph |
| **Redis** | 7+ | Caching and rate limiting |
| **Domain Name** | Valid DNS A record pointing to server | TLS certificate provisioning |

**Minimum VPS specs for production:**

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| vCPU | 4 | 8 |
| RAM | 8 GB | 16 GB |
| Storage | 80 GB SSD | 200 GB SSD |
| Network | 1 Gbps | 1 Gbps |

### 2.2 Clone and Setup

```bash
# 1. Clone the repository
git clone https://github.com/ragheeda-boop/salesos.git /opt/salesos
cd /opt/salesos

# 2. Create the production environment file
cp .env.production.template .env.production

# 3. Generate secure secrets
POSTGRES_PW=$(openssl rand -hex 32)
NEO4J_PW=$(openssl rand -hex 32)
JWT_SEC=$(openssl rand -hex 64)
MEILI_PW=$(openssl rand -hex 32)

# 4. Edit .env.production with generated values
# Replace all CHANGE_ME placeholders
sed -i "s/CHANGE_ME/$POSTGRES_PW/" .env.production  # POSTGRES_PASSWORD
sed -i "s/CHANGE_ME/$NEO4J_PW/" .env.production      # NEO4J_PASSWORD
sed -i "s/CHANGE_ME/$JWT_SEC/" .env.production        # JWT_SECRET_KEY
sed -i "s/CHANGE_ME/$MEILI_PW/" .env.production       # MEILI_MASTER_KEY

# 5. Set your production domain
sed -i "s/salesos.com/yourdomain.com/" .env.production

# 6. Secure the env file
chmod 600 .env.production

# 7. Start all services
docker compose -f docker-compose.prod.yml up -d

# 8. Verify all services are healthy
docker compose -f docker-compose.prod.yml ps
```

### 2.3 Docker Deployment

The production stack is defined in `docker-compose.prod.yml` and includes 9 services:

```bash
# Start the full production stack
docker compose -f docker-compose.prod.yml up -d

# Check service health
docker compose -f docker-compose.prod.yml ps

# View logs for a specific service
docker compose -f docker-compose.prod.yml logs -f backend

# Stop all services
docker compose -f docker-compose.prod.yml down

# Restart a single service
docker compose -f docker-compose.prod.yml restart backend
```

**Service startup order** (managed by `depends_on`):

```
postgres (healthy) → pgbouncer (healthy)
                 → neo4j (healthy)
                 → redis (healthy)
                     → migrations (completed)
                         → backend (healthy)
                             → frontend (healthy)
                                 → caddy (healthy)
```

**Production resource allocation (total):**

| Service | CPU Limit | Memory Limit | CPU Reserve | Memory Reserve |
|---------|----------|-------------|------------|---------------|
| PostgreSQL | 2 | 2 GB | 0.5 | 1 GB |
| PgBouncer | 0.5 | 256 MB | — | 128 MB |
| Neo4j | 2 | 4 GB | 1 | 2 GB |
| Redis | 0.5 | 256 MB | — | 128 MB |
| Migrations | 0.5 | 256 MB | — | — |
| Backend (4 workers) | 2 | 1 GB | 0.5 | 512 MB |
| Frontend | 1 | 512 MB | 0.5 | 256 MB |
| Caddy | 0.25 | 128 MB | — | 64 MB |
| Backup | 0.5 | 256 MB | — | — |
| **Total** | **~9.25** | **~8.5 GB** | **~2.5** | **~4.4 GB** |

### 2.4 CI/CD Deployment

The automated deployment pipeline is triggered by Git tags matching `v*`:

```bash
# Tag a release to trigger deployment
git tag v1.0.0
git push origin v1.0.0
```

**Pipeline stages:**

1. **Test** — Run pytest with coverage, Alembic migration validation
2. **Build** — Build and push Docker images (backend + frontend) to GHCR
3. **Deploy** — SSH to VPS, pull images, run migrations, restart services

---

## 3. Configuration

### 3.1 Environment Variables Reference

All configuration is managed through the `.env.production` file. The template is at `.env.production.template`.

#### Required Secrets (MUST change from defaults)

| Variable | Description | How to Generate |
|----------|-------------|----------------|
| `POSTGRES_PASSWORD` | PostgreSQL database password | `openssl rand -hex 32` |
| `NEO4J_PASSWORD` | Neo4j database password | `openssl rand -hex 32` |
| `JWT_SECRET_KEY` | JWT signing key (HS256) | `openssl rand -hex 64` |
| `DOMAIN` | Production domain (e.g., `salesos.com`) | Your registered domain |

#### Database

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_USER` | `salesos` | PostgreSQL username |
| `POSTGRES_DB` | `salesos` | PostgreSQL database name |
| `DATABASE_URL` | `postgresql+asyncpg://salesos:${POSTGRES_PASSWORD}@postgres:5432/salesos` | Async connection string for Alembic migrations |

#### Neo4j

| Variable | Default | Description |
|----------|---------|-------------|
| `NEO4J_USER` | `neo4j` | Neo4j username |

#### Redis

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection string |

#### AI / OpenAI

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | (required) | OpenAI API key for embeddings and copilot |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model for chat completions |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-large` | Model for vector embeddings |

#### JWT Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token lifetime |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime |

#### Frontend

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `https://api.${DOMAIN}` | Backend API URL exposed to browser |

#### Scraper API Keys (optional — leave empty to use mock scrapers)

| Variable | Description |
|----------|-------------|
| `BALADY_API_KEY` | Balady government data scraper key |
| `TAQEEM_API_KEY` | Taqeem company data scraper key |
| `NAJIZ_API_KEY` | Najiz legal data scraper key |
| `REGA_API_KEY` | Rega business registry scraper key |
| `NCNP_API_KEY` | NCNP nonprofit data scraper key |

#### Observability

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Python logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `SENTRY_DSN` | (empty) | Sentry error tracking DSN |

#### SMTP (Email Notifications)

| Variable | Default | Description |
|----------|---------|-------------|
| `SMTP_HOST` | (empty) | SMTP server hostname |
| `SMTP_PORT` | `465` | SMTP server port |
| `SMTP_USER` | (empty) | SMTP authentication username |
| `SMTP_PASSWORD` | (empty) | SMTP authentication password |
| `SMTP_FROM` | `noreply@salesos.io` | Sender email address |

#### SSO / OAuth

| Variable | Description |
|----------|-------------|
| `SSO_GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `SSO_GOOGLE_CLIENT_SECRET` | Google OAuth client secret |
| `SSO_MICROSOFT_CLIENT_ID` | Microsoft OAuth client ID |
| `SSO_MICROSOFT_CLIENT_SECRET` | Microsoft OAuth client secret |
| `SSO_GITHUB_CLIENT_ID` | GitHub OAuth client ID |
| `SSO_GITHUB_CLIENT_SECRET` | GitHub OAuth client secret |

#### Meilisearch

| Variable | Default | Description |
|----------|---------|-------------|
| `MEILI_MASTER_KEY` | (required) | Meilisearch master key |
| `MEILI_URL` | `http://meilisearch:7700` | Meilisearch connection URL |

#### Rate Limiting

| Variable | Default | Description |
|----------|---------|-------------|
| `RATE_LIMIT_AUTHENTICATED` | `100` | Requests per minute for authenticated users |
| `RATE_LIMIT_ANONYMOUS` | `20` | Requests per minute for anonymous users |
| `RATE_LIMIT_SEARCH` | `30` | Requests per minute for search endpoints |

#### Kafka (Event Bus)

| Variable | Default | Description |
|----------|---------|-------------|
| `KAFKA_BOOTSTRAP_SERVERS` | `kafka:9092` | Kafka broker connection string |

#### Feature Flags

| Variable | Default | Description |
|----------|---------|-------------|
| `FEATURE_SEARCH_FUZZY_V2` | `false` | Enable v2 fuzzy search algorithm |
| `FEATURE_AI_COPILOT` | `false` | Enable AI copilot feature |
| `FEATURE_CRM_KANBAN` | `false` | Enable CRM Kanban view |

#### Celery (Background Tasks)

| Variable | Default | Description |
|----------|---------|-------------|
| `CELERY_TASK_TIME_LIMIT` | `600` | Hard time limit per task (seconds) |
| `CELERY_TASK_SOFT_TIME_LIMIT` | `300` | Soft time limit — raises SoftTimeLimitExceeded |
| `CELERY_RESULT_EXPIRES` | `86400` | Task result retention (seconds) |

#### LLM Defaults

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_TEMPERATURE` | `0.7` | LLM generation temperature |
| `LLM_MAX_TOKENS` | `1024` | Maximum tokens per LLM response |

### 3.2 Feature Flags

Feature flags control phased rollout of new capabilities. They can be toggled per-tenant or globally.

| Flag | Scope | Description |
|------|-------|-------------|
| `FEATURE_SEARCH_FUZZY_V2` | Global | Enables the v2 fuzzy search algorithm with improved Arabic support |
| `FEATURE_AI_COPILOT` | Global | Enables the AI copilot sidebar for contextual assistance |
| `FEATURE_CRM_KANBAN` | Global | Enables Kanban drag-and-drop view for pipeline management |
| `nba-enabled` | Tenant | Controls NBA (Next Best Action) engine availability |
| `pipeline-intelligence` | Tier-based | Pipeline analytics — rolled out internal → beta → enterprise |
| `meeting-intelligence` | Tier-based | Meeting intelligence features — phased rollout |

To enable a feature flag, set the corresponding environment variable to `true` in `.env.production` and restart the backend service:

```bash
# Enable a feature flag
# Edit .env.production:
#   FEATURE_AI_COPILOT=true

docker compose -f docker-compose.prod.yml restart backend
```

### 3.3 Caddy (TLS and Routing)

Caddy handles automatic TLS certificate provisioning and reverse routing. The Caddyfile at `infra/caddy/Caddyfile`:

```
{$DOMAIN} {
    reverse_proxy frontend:3000
}

api.{$DOMAIN} {
    reverse_proxy backend:8000
}
```

- `{$DOMAIN}` — Frontend is served at the root domain (e.g., `salesos.com`)
- `api.{$DOMAIN}` — Backend API is served at the `api` subdomain (e.g., `api.salesos.com`)

Caddy automatically provisions and renews Let's Encrypt TLS certificates. Ensure DNS A records exist for both the root domain and `api` subdomain pointing to your server.

### 3.4 PostgreSQL Extensions

The database initializes with the following extensions (from `infra/docker/postgres/init/01-init.sql`):

```sql
CREATE EXTENSION IF NOT EXISTS vector;      -- pgvector: vector similarity search
CREATE EXTENSION IF NOT EXISTS pg_trgm;    -- Trigram: fuzzy text matching
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";-- UUID generation
CREATE EXTENSION IF NOT EXISTS pgcrypto;   -- Cryptographic functions
```

And the following schemas:

```sql
CREATE SCHEMA IF NOT EXISTS audit;
CREATE SCHEMA IF NOT EXISTS identity;
CREATE SCHEMA IF NOT EXISTS company;
CREATE SCHEMA IF NOT EXISTS activity;
CREATE SCHEMA IF NOT EXISTS crm;
```

---

## 4. Administration

### 4.1 User Management

Users are managed through the Identity domain API. All user operations require `ADMIN` or `MANAGER` role.

**Create a user:**

```bash
POST /api/v1/identity/users
Content-Type: application/json
Authorization: Bearer <admin_token>

{
  "email": "user@example.com",
  "full_name": "John Smith",
  "role": "USER",
  "password": "secure_password_here"
}
```

**Available roles:** `ADMIN`, `MANAGER`, `USER`, `API`, `AUDITOR`

**Disable a user:**

```bash
PATCH /api/v1/identity/users/{user_id}
Authorization: Bearer <admin_token>

{
  "is_active": false
}
```

**Password reset:** Users can request a password reset via `/api/v1/identity/auth/forgot-password`. A reset token is sent to their email (requires SMTP configuration).

**SSO users:** When SSO is configured (Google, Microsoft, or GitHub), users authenticating via SSO are automatically provisioned on first login.

### 4.2 Tenant Management

SalesOS is multi-tenant. Each tenant has isolated data, users, and configuration.

**Tenant provisioning flow:**

1. Create tenant record in PostgreSQL
2. Create admin user account for the tenant
3. Assign `ADMIN` role to the admin user
4. Initialize empty tenant namespace
5. Optionally seed data (companies, contacts)

**Tenant isolation:** Every database query is scoped by `tenant_id` extracted from the JWT token. Cross-tenant data access is architecturally impossible.

### 4.3 Monitoring Dashboard

Grafana is available at port 3001 (mapped from container port 3000):

```bash
# Access Grafana
http://your-server:3001
# Default credentials:
#   Username: admin
#   Password: value of GRAFANA_PASSWORD (set in .env.production)
```

**Pre-configured dashboards:**

| Dashboard | Data Source | Refresh Rate |
|-----------|-----------|-------------|
| SalesOS Overview | Prometheus | 1 minute |
| Pipeline Intelligence | Prometheus | 1 minute |
| API Performance | Prometheus + custom metrics | 1 minute |
| Database Health | PostgreSQL exporter | 1 minute |
| Security Events | Application logs + Sentry | Real-time |
| Infrastructure | Docker stats + Prometheus | 1 minute |

**Prometheus** is available at port 9090 for direct metric queries.

### 4.4 Logging

All services use JSON structured logging via Docker's `json-file` driver:

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"    # Max 10 MB per log file
    max-file: "3"      # Keep 3 rotated files (30 MB total per service)
    tag: "{{.Name}}/{{.ID}}"
```

**Log levels:** Controlled by the `LOG_LEVEL` environment variable.

**View logs:**

```bash
# All services
docker compose -f docker-compose.prod.yml logs

# Specific service (follow mode)
docker compose -f docker-compose.prod.yml logs -f backend

# Last 100 lines
docker compose -f docker-compose.prod.yml logs --tail 100 backend

# Logs for a specific time range
docker compose -f docker-compose.prod.yml logs --since="2026-07-12T10:00:00" --until="2026-07-12T11:00:00" backend
```

**Structured log format (backend):**

```json
{
  "timestamp": "2026-07-12T10:30:00Z",
  "level": "INFO",
  "logger": "app.routers.companies",
  "message": "Company retrieved",
  "tenant_id": "t_abc123",
  "user_id": "u_xyz789",
  "method": "GET",
  "path": "/api/v1/companies/42",
  "status_code": 200,
  "duration_ms": 45
}
```

**Audit log events** (stored in the `audit` schema):

| Event | Details | Retention |
|-------|---------|-----------|
| Login success | User ID, IP, timestamp, tenant | 1 year |
| Login failure | Email, IP, timestamp, reason | 1 year |
| Data access | User ID, resource, action, timestamp | 6 months |
| Permission change | Admin ID, target user, old/new role | 1 year |
| Tenant creation | Admin ID, tenant details | 7 years |
| NBA action | User ID, company, action, outcome | 1 year |

---

## 5. Security

### 5.1 Authentication Configuration

**JWT settings:**

| Parameter | Value | Notes |
|-----------|-------|-------|
| Algorithm | HS256 | Symmetric signing |
| Access token lifetime | 30 minutes | Configurable via `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` |
| Refresh token lifetime | 7 days | Configurable via `JWT_REFRESH_TOKEN_EXPIRE_DAYS` |
| Token storage | localStorage | Standard browser pattern |
| Password hashing | bcrypt | Cost factor tuned for server hardware |

**Token rotation:** When an access token expires, the client uses the refresh token to obtain a new access token without requiring re-authentication. Refresh tokens are single-use and family-tracked to prevent replay attacks.

### 5.2 CSRF Protection

CSRF protection is implemented on all state-changing (mutating) endpoints. The middleware:

1. Validates the `Origin` header against the configured `DOMAIN`
2. Requires a valid CSRF token on `POST`, `PUT`, `PATCH`, `DELETE` requests
3. Returns HTTP 403 if the token is missing or invalid

**To verify CSRF is working:**

```bash
# Should return 403 without CSRF token
curl -X POST https://api.yourdomain.com/api/v1/companies \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test"}'
```

### 5.3 Rate Limiting

Rate limiting is enforced globally per IP (anonymous) or per JWT token (authenticated). The in-memory rate limiter runs a stale-entry sweep every 300 seconds.

**Tier configuration:**

| Tier | Default | Env Variable | Applies To |
|------|---------|-------------|------------|
| Authenticated | 100 req/min | `RATE_LIMIT_AUTHENTICATED` | All endpoints with valid JWT |
| Anonymous | 20 req/min | `RATE_LIMIT_ANONYMOUS` | Public/unauthenticated endpoints |
| Search | 30 req/min | `RATE_LIMIT_SEARCH` | Search-specific endpoints |

**Response headers on rate-limited requests:**

```
HTTP/1.1 429 Too Many Requests
Retry-After: 30
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1689168000
```

**Tuning:** Adjust the rate limit values in `.env.production` based on your expected traffic patterns. For high-traffic deployments, increase `RATE_LIMIT_AUTHENTICATED` to 200-500.

### 5.4 Secrets Management

**Rules:**

1. All secrets are in environment variables — zero secrets in code
2. `.env.production` must be `chmod 600` and owned by the deployment user
3. `.env.production` is excluded from git (verify with `git ls-files .env.production`)
4. Never paste secrets into Slack, email, or chat
5. Rotate secrets every 90 days

**Secret rotation procedure:**

```bash
# 1. Generate new secrets
NEW_POSTGRES_PW=$(openssl rand -hex 32)
NEW_NEO4J_PW=$(openssl rand -hex 32)
NEW_JWT_SEC=$(openssl rand -hex 64)

# 2. Update .env.production with new values

# 3. Restart all services (this invalidates all active sessions)
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d

# 4. All users must re-login (old JWT tokens are invalidated)
```

**SSO secret rotation:** For Google/Microsoft/GitHub OAuth, update the client secrets in `.env.production` and also update the corresponding OAuth provider console (Google Cloud Console, Azure Portal, GitHub Settings).

### 5.5 Security Audit Procedures

Run the security audit script monthly:

```bash
# Full security audit
pwsh scripts/security-audit.ps1
```

The audit checks:

- No secrets in tracked git files
- All API routers have authentication dependencies
- `.env.production` is not tracked by git
- CSRF protection is active on mutating endpoints
- Rate limiting is configured
- Dependency vulnerabilities (npm audit, pip-audit)
- Docker image vulnerabilities (Trivy scan)

**External penetration testing** should be conducted before GA and annually thereafter.

---

## 6. Backup & Recovery

### 6.1 Automated PostgreSQL Backups

The `backup` service runs a cron job daily at 03:00 UTC:

```
0 3 * * * /usr/local/bin/backup-db
```

**Backup configuration:**

| Parameter | Default | Env Variable |
|-----------|---------|-------------|
| Backup directory | `/backups/postgres` | `BACKUP_DIR` |
| Retention period | 7 days | `RETENTION_DAYS` |
| Format | PostgreSQL custom (`--compress=9`) | Built into script |
| S3 upload | Disabled | `S3_BUCKET` |
| Webhook notification | Disabled | `NOTIFY_WEBHOOK` |

**Backup file naming:** `salesos_YYYYMMDD_HHMMSS.dump`

**View existing backups:**

```bash
docker compose -f docker-compose.prod.yml exec backup ls -la /backups/postgres/
```

**Trigger a manual backup:**

```bash
docker compose -f docker-compose.prod.yml run --rm backup /usr/local/bin/backup-db
```

### 6.2 Neo4j Backups

Neo4j data is stored in the `neo4j_data` Docker volume. To create a Neo4j backup:

```bash
# Dump the Neo4j database
docker compose -f docker-compose.prod.yml exec neo4j \
  cypher-shell -u neo4j -p "$NEO4J_PASSWORD" \
  "CALL dbms.dump.database('/tmp/neo4j-backup')" \
  2>/dev/null

# Copy backup out of container
docker compose -f docker-compose.prod.yml cp neo4j:/tmp/neo4j-backup ./backups/neo4j/
```

For production, schedule Neo4j backups alongside PostgreSQL backups using the same cron mechanism.

### 6.3 Recovery Procedures

**PostgreSQL restore:**

```bash
# 1. Stop the backend to prevent writes
docker compose -f docker-compose.prod.yml stop backend frontend

# 2. Restore from backup
docker compose -f docker-compose.prod.yml exec postgres \
  pg_restore -U salesos -d salesos --clean --if-exists --no-owner --no-acl \
  /backups/postgres/salesos_YYYYMMDD_HHMMSS.dump

# 3. Alternatively, use the restore script
docker compose -f docker-compose.prod.yml run --rm -e PGPASSWORD="$POSTGRES_PW" \
  backup /bin/sh -c "pg_restore -h postgres -U salesos -d salesos --clean --if-exists --no-owner --no-acl /backups/postgres/salesos_YYYYMMDD_HHMMSS.dump"

# 4. Restart all services
docker compose -f docker-compose.prod.yml up -d

# 5. Verify
docker compose -f docker-compose.prod.yml logs -f backend | grep "Application startup"
```

### 6.4 Disaster Recovery Plan

| Metric | Target |
|--------|--------|
| **Recovery Time Objective (RTO)** | < 4 hours |
| **Recovery Point Objective (RPO)** | < 1 hour (based on daily backups + WAL) |
| **Backup frequency** | Daily at 03:00 UTC |
| **Backup retention** | 7 days local, 30 days S3 (when configured) |
| **Backup verification** | Quarterly restore test to staging |

**Disaster recovery steps:**

1. Provision new VPS (same or larger spec)
2. Install Docker and Docker Compose
3. Clone repository and copy `.env.production`
4. Pull latest Docker images
5. Restore PostgreSQL from latest backup
6. Restore Neo4j from latest backup
7. Start all services
8. Verify health checks
9. Update DNS to point to new server
10. Notify affected tenants

**S3 offsite backup (recommended):**

```bash
# Install AWS CLI on the backup container
# Add to .env.production:
#   S3_BUCKET=s3://salesos-backups/production

# Backups will be uploaded automatically after each daily backup
```

---

## 7. Troubleshooting

### 7.1 Common Issues and Solutions

#### Backend fails to start

```bash
# Check logs
docker compose -f docker-compose.prod.yml logs backend

# Common causes:
# 1. PostgreSQL not ready — wait for health check
# 2. Missing environment variables — verify .env.production
# 3. Migration failure — check migrations service logs
# 4. Invalid JWT_SECRET_KEY — ensure it's set

# Fix: Restart the full stack
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```

#### Database connection exhausted

```bash
# Check PgBouncer status
docker compose -f docker-compose.prod.yml exec pgbouncer \
  psql -h localhost -p 6432 -U salesos -d pgbouncer -c "SHOW POOLS;"

# Check active PostgreSQL connections
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U salesos -d salesos -c "SELECT count(*) FROM pg_stat_activity;"

# Fix: Restart PgBouncer to release stale connections
docker compose -f docker-compose.prod.yml restart pgbouncer
```

#### Neo4j connection errors

```bash
# Check Neo4j health
docker compose -f docker-compose.prod.yml exec neo4j \
  cypher-shell -u neo4j -p "$NEO4J_PASSWORD" "RETURN 1"

# Check Neo4j logs
docker compose -f docker-compose.prod.yml logs neo4j | tail -50

# Common causes:
# 1. Out of memory — increase NEO4J memory limits
# 2. Connection pool exhausted — check NEO4J_MAX_CONNECTIONS
# 3. Slow queries — check Neo4j query log

# Fix: Restart Neo4j (data is persisted in volume)
docker compose -f docker-compose.prod.yml restart neo4j
```

#### High memory usage

```bash
# Check container resource usage
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Fix: Identify the container exceeding limits and either:
# 1. Increase memory limit in docker-compose.prod.yml
# 2. Investigate memory leak in application logs
# 3. Restart the specific container
```

#### SSL/TLS certificate issues

```bash
# Caddy auto-renews certificates. If renewal fails:

# Check Caddy logs
docker compose -f docker-compose.prod.yml logs caddy

# Verify DNS resolution
dig +short yourdomain.com
dig +short api.yourdomain.com

# Common fixes:
# 1. Ensure DNS A records point to server IP
# 2. Ensure ports 80 and 443 are open on firewall
# 3. Restart Caddy to trigger re-provisioning
docker compose -f docker-compose.prod.yml restart caddy
```

#### Rate limiting too aggressive

```bash
# Check if users are hitting 429 errors
docker compose -f docker-compose.prod.yml logs backend | grep "429"

# Adjust limits in .env.production:
#   RATE_LIMIT_AUTHENTICATED=200   (increase from 100)
#   RATE_LIMIT_SEARCH=50           (increase from 30)

# Restart backend to apply
docker compose -f docker-compose.prod.yml restart backend
```

### 7.2 Log Locations

| Service | Log Location | Command |
|---------|-------------|---------|
| Backend | Docker json-file | `docker compose logs backend` |
| Frontend | Docker json-file | `docker compose logs frontend` |
| PostgreSQL | Docker json-file + volume | `docker compose logs postgres` |
| Neo4j | Docker json-file + `/logs` volume | `docker compose logs neo4j` |
| Caddy | Docker json-file | `docker compose logs caddy` |
| Prometheus | Docker json-file | `docker compose logs prometheus` |
| Grafana | Docker json-file | `docker compose logs grafana` |
| Backup | `/backups/postgres/backup.log` | `docker compose exec backup cat /backups/postgres/backup.log` |

### 7.3 Support Escalation Process

| Severity | Response Time | Escalation Path |
|----------|--------------|-----------------|
| **P0 — Critical** (service down, data loss) | 15 minutes | On-call engineer → Engineering Lead → CTO |
| **P1 — High** (feature broken, degraded performance) | 1 hour | On-call engineer → Engineering Lead |
| **P2 — Medium** (non-critical bug, workaround exists) | 4 hours | Assigned engineer |
| **P3 — Low** (cosmetic, enhancement) | 24 hours | Backlog |

**Incident communication:** Use the WhatsApp group for real-time coordination during P0 incidents.

---

## 8. Maintenance

### 8.1 Dependency Updates

**Frontend (npm):**

```bash
# Check for outdated packages
cd frontend && npm outdated

# Update packages
npm update

# Run tests to verify no regressions
npm test

# Check for security vulnerabilities
npm audit
npm audit fix
```

**Backend (Python):**

```bash
# Check for outdated packages
cd backend && poetry show --outdated

# Update packages
poetry update

# Run tests
poetry run pytest

# Security audit
pip-audit
```

**Docker images:**

```bash
# Pull latest base images
docker compose -f docker-compose.prod.yml pull

# Rebuild application images if needed
docker compose -f docker-compose.prod.yml build --no-cache backend frontend

# Restart with new images
docker compose -f docker-compose.prod.yml up -d
```

**Schedule:** Run dependency updates monthly. Security-critical updates should be applied within 48 hours of disclosure.

### 8.2 Database Maintenance

**PostgreSQL VACUUM and ANALYZE:**

```bash
# Manual VACUUM (reclaim space from deleted rows)
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U salesos -d salesos -c "VACUUM VERBOSE;"

# ANALYZE (update query planner statistics)
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U salesos -d salesos -c "ANALYZE VERBOSE;"

# Check table sizes
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U salesos -d salesos -c "
  SELECT schemaname, relname, pg_size_pretty(pg_total_relation_size(relid))
  FROM pg_stat_user_tables
  ORDER BY pg_total_relation_size(relid) DESC
  LIMIT 20;"

# Check index usage
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U salesos -d salesos -c "
  SELECT schemaname, relname, indexrelname, idx_scan
  FROM pg_stat_user_indexes
  ORDER BY idx_scan ASC
  LIMIT 20;"
```

**PostgreSQL index maintenance:**

```bash
# Reindex bloated indexes
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U salesos -d salesos -c "REINDEX DATABASE salesos;"
```

**Connection monitoring:**

```bash
# Check active connections and queries
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U salesos -d salesos -c "
  SELECT pid, state, query, query_start, now() - query_start AS duration
  FROM pg_stat_activity
  WHERE state != 'idle'
  ORDER BY duration DESC;"
```

### 8.3 SSL Certificate Rotation

Caddy handles TLS certificate provisioning and renewal automatically via Let's Encrypt. No manual rotation is needed.

**Verify certificate status:**

```bash
# Check Caddy certificate storage
docker compose -f docker-compose.prod.yml exec caddy ls -la /data/caddy/certificates/

# Check certificate expiry from outside
echo | openssl s_client -servername yourdomain.com -connect yourdomain.com:443 2>/dev/null | openssl x509 -noout -dates
```

**Force certificate renewal:**

```bash
# Remove cached certificates and restart Caddy
docker compose -f docker-compose.prod.yml exec caddy rm -rf /data/caddy/certificates/
docker compose -f docker-compose.prod.yml restart caddy
```

**Note:** Ensure your server's firewall allows inbound traffic on ports 80 (for ACME HTTP-01 challenges) and 443 (for HTTPS traffic). Caddy needs port 80 to provision and renew certificates.

---

## Quick Reference Commands

```bash
# ── Stack Management ────────────────────────────────────
docker compose -f docker-compose.prod.yml up -d              # Start all services
docker compose -f docker-compose.prod.yml down                # Stop all services
docker compose -f docker-compose.prod.yml restart backend     # Restart a service
docker compose -f docker-compose.prod.yml ps                  # Check service health
docker compose -f docker-compose.prod.yml logs -f backend     # Follow backend logs

# ── Backup & Recovery ───────────────────────────────────
docker compose -f docker-compose.prod.yml run --rm backup /usr/local/bin/backup-db   # Manual backup
docker compose -f docker-compose.prod.yml exec backup ls -la /backups/postgres/      # List backups

# ── Database ────────────────────────────────────────────
docker compose -f docker-compose.prod.yml exec postgres psql -U salesos -d salesos   # Connect to PostgreSQL
docker compose -f docker-compose.prod.yml exec neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD"  # Connect to Neo4j

# ── Monitoring ──────────────────────────────────────────
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"   # Resource usage
docker compose -f docker-compose.prod.yml logs --tail 100 backend       # Recent backend logs

# ── CI/CD ───────────────────────────────────────────────
git tag v1.0.0 && git push origin v1.0.0    # Trigger deployment
pwsh scripts/security-audit.ps1              # Run security audit
pwsh scripts/coverage-runner.ps1             # Run test coverage
```

---

*Created: 2026-07-12*
*Version: 1.0 — General Availability*
*Owner: Release Manager*
*Review: Quarterly*
