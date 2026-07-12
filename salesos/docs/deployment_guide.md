# SalesOS GA Deployment Guide

> **Audience**: DevOps / SRE engineers deploying SalesOS to production.
> **Last updated**: 2026-07-12
> **Version**: 1.0

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Prerequisites](#2-prerequisites)
3. [Docker Deployment](#3-docker-deployment)
4. [Kubernetes Deployment](#4-kubernetes-deployment)
5. [Database Setup](#5-database-setup)
6. [Environment Configuration](#6-environment-configuration)
7. [Deployment Procedure](#7-deployment-procedure)
8. [CI/CD Pipeline](#8-cicd-pipeline)
9. [Monitoring & Observability](#9-monitoring--observability)
10. [Security](#10-security)
11. [Disaster Recovery](#11-disaster-recovery)

---

## 1. Architecture Overview

### 1.1 Production Infrastructure Diagram

```
                          ┌──────────────────────┐
                          │   Cloudflare (WAF)    │
                          │   DDoS + Bot Fight    │
                          └──────────┬───────────┘
                                     │
                          ┌──────────▼───────────┐
                          │    Caddy (TLS/LB)     │
                          │    Port 80 / 443      │
                          └──┬───────────────┬───┘
                             │               │
              ┌──────────────▼──┐    ┌───────▼──────────────┐
              │  Frontend:3000  │    │   API (Backend):8000  │
              │  Next.js SSR    │    │   FastAPI + Uvicorn   │
              │  (2 replicas)   │    │   (4 workers)         │
              └─────────────────┘    └───┬───────┬───────┬──┘
                                         │       │       │
                          ┌──────────────▼──┐ ┌─▼─────┐ ┌▼────────┐
                          │  PgBouncer:6432 │ │ Redis │ │ Neo4j   │
                          │  (conn pooling) │ │ :6379 │ │ :7687   │
                          └────────┬────────┘ └───────┘ └─────────┘
                                   │
                          ┌────────▼────────┐
                          │  PostgreSQL:5432 │
                          │  pgvector/pg16   │
                          │  (primary)       │
                          └────────┬────────┘
                                   │
                          ┌────────▼────────┐
                          │   RDS (managed)  │
                          │   Multi-AZ       │
                          └─────────────────┘
```

### 1.2 Component Relationships

| Component | Version | Role | Communicates With |
|-----------|---------|------|-------------------|
| **Caddy** | 2-alpine | Reverse proxy, TLS termination, auto-renewal | Frontend, Backend |
| **Frontend** | Next.js 14 (Node 22) | SSR web application | Backend (API) |
| **Backend** | Python 3.12, FastAPI | REST API server | PostgreSQL, Neo4j, Redis, OpenAI |
| **PgBouncer** | latest | Connection pooling (transaction mode) | PostgreSQL |
| **PostgreSQL** | 16 + pgvector | Primary relational database | — |
| **Neo4j** | 5-community | Knowledge graph | — |
| **Redis** | 7-alpine | Cache, rate limiting, sessions | — |
| **Migrations** | Alembic (same image as backend) | Schema management | PostgreSQL |
| **Backup** | postgres:16-alpine + pg_dump | Automated daily backups | PostgreSQL |

### 1.3 Network Topology

```
Internet
    │
    ▼
[Cloudflare] ── WAF rules, DDoS mitigation, Bot Fight Mode
    │
    ▼
[Caddy :80/:443] ── TLS 1.3, auto-renew Let's Encrypt
    │
    ├──► Frontend (ClusterIP :3000) ── SSR, static assets
    │
    └──► Backend (ClusterIP :8000) ── REST API
              │
              ├──► PgBouncer (:6432) ── transaction-mode pooling ──► PostgreSQL (:5432)
              ├──► Redis (:6379) ── cache, rate limiter, sessions
              └──► Neo4j (:7687) ── Bolt protocol, knowledge graph
```

All internal services communicate on a private Docker network (or K8s cluster network). Only Caddy exposes ports 80 and 443 to the public internet.

### 1.4 Authentication Flow

```
User ──► Frontend (/login)
  │
  ├─ SSO (Google/Microsoft/GitHub OAuth) ──► OAuth callback ──► Backend (/api/v1/identity/auth/callback)
  │     → SSO_GOOGLE_CLIENT_ID / SSO_MICROSOFT_CLIENT_ID
  │     → JWT issued with tenant context
  │
  └─ Email/Password ──► Backend (/api/v1/identity/auth/login)
        → bcrypt verification
        → JWT access token (30 min) + refresh token (7 days)
        → Token stored in httpOnly cookie
```

JWT tokens contain `sub` (user ID), `tenant_id`, `role`, and `exp`. All API requests carry the JWT in the `Authorization: Bearer` header. The backend validates the token on every request using `JWT_SECRET_KEY`.

---

## 2. Prerequisites

### 2.1 Infrastructure Requirements

| Component | CPU | RAM | Storage | Notes |
|-----------|-----|-----|---------|-------|
| **Backend** | 2 cores | 1 GB | — | 4 Uvicorn workers |
| **Frontend** | 1 core | 512 MB | — | Next.js standalone |
| **Caddy** | 0.25 cores | 128 MB | 1 GB (cert cache) | TLS auto-renewal |
| **PostgreSQL** | 2 cores | 2 GB | 50 GB SSD min | gp3 recommended |
| **PgBouncer** | 0.5 cores | 256 MB | — | Transaction-mode pooling |
| **Neo4j** | 2 cores | 4 GB | 10 GB | Community edition |
| **Redis** | 0.5 cores | 256 MB | — | AOF persistence |
| **Backup** | 0.5 cores | 256 MB | 30 GB | 7-day retention |
| **Total minimum** | ~8.75 cores | ~8.5 GB | ~60 GB | Single VPS |

**Recommended production VPS**: 12 vCPU, 16 GB RAM, 200 GB NVMe SSD (e.g., AWS `c6i.3xlarge` or Hetzner AX102).

### 2.2 Required Services

| Service | Version | Purpose | Provisioning |
|---------|---------|---------|-------------|
| PostgreSQL | 16+ | Primary database | `pgvector/pgvector:pg16` Docker image or AWS RDS |
| pgvector | 0.7+ | Vector similarity search | Included in `pgvector/pgvector:pg16` |
| pg_trgm | — | Fuzzy text search | Pre-installed in PostgreSQL 16 |
| Neo4j | 5.x | Knowledge graph, entity relationships | `neo4j:5-community` Docker image |
| Redis | 7.x | Cache, rate limiting, session store | `redis:7-alpine` Docker image |
| Docker | 24.0+ | Container runtime | Install on host |
| Docker Compose | v2+ | Multi-container orchestration | Included with Docker |

**Optional services** (for enhanced functionality):

| Service | Version | Purpose |
|---------|---------|---------|
| Kafka | 7.x | Durable event bus (post-GA) |
| Meilisearch | latest | Full-text search engine (alternative to PostgreSQL FTS) |
| Prometheus | latest | Metrics collection |
| Grafana | latest | Monitoring dashboards |

### 2.3 Domain and SSL

| Requirement | Details |
|-------------|---------|
| Domain | A registered domain (e.g., `salesos.com`) |
| DNS A record | `@` → VPS public IP |
| DNS A record | `api` → VPS public IP (or same as `@`) |
| SSL certificates | **Auto-managed by Caddy** via Let's Encrypt (no manual cert needed) |
| Wildcard (optional) | If using `*.salesos.com`, configure Cloudflare proxy |

Caddy automatically provisions and renews TLS certificates when it starts. No certbot or manual renewal is required.

### 2.4 External Service Accounts

| Service | Purpose | How to obtain |
|---------|---------|---------------|
| **OpenAI API** | Embeddings (`text-embedding-3-large`), copilot | [platform.openai.com](https://platform.openai.com) |
| **Google OAuth** | SSO login | Google Cloud Console → OAuth 2.0 credentials |
| **Microsoft OAuth** | SSO login | Azure AD → App registrations |
| **GitHub OAuth** | SSO login | GitHub Settings → Developer settings → OAuth Apps |
| **SMTP** | Transactional emails (invitations, notifications) | Any SMTP provider (Gmail, SendGrid, etc.) |
| **Sentry** (optional) | Error tracking | [sentry.io](https://sentry.io) |
| **S3-compatible storage** (optional) | Offsite backup storage | AWS S3, MinIO, or DigitalOcean Spaces |

---

## 3. Docker Deployment

### 3.1 Building Docker Images

**Backend image** (`backend/Dockerfile`):

```bash
# Multi-stage build: builder (pip install) → production (slim runtime)
docker build \
  -t ghcr.io/ragheeda-boop/salesos/backend:v1.0.0 \
  -t ghcr.io/ragheeda-boop/salesos/backend:latest \
  -f backend/Dockerfile backend/
```

The backend Dockerfile uses a multi-stage build:
- **Builder stage**: Python 3.12-slim, installs build tools, copies source, runs `pip install .`
- **Production stage**: Python 3.12-slim with only `curl`, runs as non-root user `salesos`, exposes port 8000

**Frontend image** (`frontend/Dockerfile`):

```bash
docker build \
  -t ghcr.io/ragheeda-boop/salesos/frontend:v1.0.0 \
  -t ghcr.io/ragheeda-boop/salesos/frontend:latest \
  -f frontend/Dockerfile frontend/
```

The frontend Dockerfile uses a multi-stage build:
- **Build stage**: Node 22-alpine, installs dependencies, runs `next build`
- **Production stage**: Node 22-alpine, copies `.next/standalone` and static assets, runs as non-root user `salesos`

**Push to registry**:

```bash
docker push ghcr.io/ragheeda-boop/salesos/backend:v1.0.0
docker push ghcr.io/ragheeda-boop/salesos/backend:latest
docker push ghcr.io/ragheeda-boop/salesos/frontend:v1.0.0
docker push ghcr.io/ragheeda-boop/salesos/frontend:latest
```

### 3.2 Docker Compose for Production

The production compose file is `docker-compose.prod.yml`. It defines 9 services with strict dependency ordering:

```
postgres (healthy)
  └─► pgbouncer (healthy)
  └─► migrations (completed)
        └─► backend (healthy)
              └─► frontend (healthy)
                    └─► caddy (healthy)
postgres (healthy)
  └─► backup (cron)
```

Start the full stack:

```bash
cd /opt/salesos
docker compose -f docker-compose.prod.yml up -d
```

Start in dependency order (for debugging):

```bash
docker compose -f docker-compose.prod.yml up -d postgres redis neo4j
# Wait for health checks to pass (30-60 seconds)
docker compose -f docker-compose.prod.yml up -d pgbouncer migrations
# Wait for migrations to complete
docker compose -f docker-compose.prod.yml up -d backend frontend caddy backup
```

### 3.3 Resource Limits

Every production service has CPU and memory limits defined in `docker-compose.prod.yml`:

| Service | CPU Limit | CPU Reservation | Memory Limit | Memory Reservation |
|---------|-----------|----------------|--------------|-------------------|
| postgres | 2 | 0.5 | 2 GB | 1 GB |
| pgbouncer | 0.5 | — | 256 MB | 128 MB |
| neo4j | 2 | 1 | 4 GB | 2 GB |
| redis | 0.5 | — | 256 MB | 128 MB |
| migrations | 0.5 | — | 256 MB | — |
| backend | 2 | 0.5 | 1 GB | 512 MB |
| frontend | 1 | 0.5 | 512 MB | 256 MB |
| caddy | 0.25 | — | 128 MB | 64 MB |
| backup | 0.5 | — | 256 MB | — |

**Total guaranteed**: ~2.75 cores, ~2.4 GB RAM
**Total burst**: ~10.75 cores, ~8.5 GB RAM

To scale backend workers horizontally, increase replicas via `docker compose up -d --scale backend=2`.

### 3.4 Health Check Configuration

All services include health checks. The dependency chain ensures services start only after their dependencies are healthy:

| Service | Health Check | Interval | Timeout | Start Period | Retries |
|---------|-------------|----------|---------|--------------|---------|
| postgres | `pg_isready -U salesos` | 10s | 5s | 10s | 5 |
| pgbouncer | `pg_isready -h postgres` | 10s | 5s | — | 5 |
| neo4j | `cypher-shell RETURN 1` | 15s | 10s | 30s | 10 |
| redis | `redis-cli ping` | 5s | 3s | — | 5 |
| backend | `curl -f http://localhost:8000/health` | 30s | 5s | 30s | 3 |
| frontend | `wget -qO- http://localhost:3000` | 30s | 5s | 15s | 3 |
| caddy | `wget -qO- http://localhost:80/health` | 15s | 5s | 5s | 3 |
| backup | `test -d /backups` | 60s | 5s | — | 3 |

**Backend health endpoint** (`GET /health`):

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "neo4j": "connected",
  "redis": "connected",
  "uptime_seconds": 12345
}
```

### 3.5 Docker Environment Files

Create `.env.production` from the template:

```bash
cp .env.production.template .env.production
```

**Required secrets** (generate with `openssl`):

```bash
# Database password
openssl rand -base64 24

# Neo4j password
openssl rand -hex 32

# JWT secret
openssl rand -hex 64

# Meilisearch master key
openssl rand -hex 32
```

Replace every `CHANGE_ME` value in `.env.production`. The compose file references these variables via `env_file: .env.production` and inline `${VAR:?Set VAR}` syntax that will fail fast if a required secret is missing.

**Logging configuration** (applied to all services):

```yaml
x-logging: &default-logging
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
    tag: "{{.Name}}/{{.ID}}"
```

Each service retains 3 log files of 10 MB max, preventing disk exhaustion.

---

## 4. Kubernetes Deployment

Kubernetes manifests are in `infra/k8s/`. This section covers deploying to an EKS cluster provisioned via Terraform (`infra/terraform/`).

### 4.1 Namespace Setup

```bash
# Create namespace
kubectl create namespace salesos-production

# Set context
kubectl config set-context --current --namespace=salesos-production
```

### 4.2 ConfigMaps and Secrets

**Secrets** — copy from template and generate real values:

```bash
cp infra/k8s/secrets.yaml.template infra/k8s/secrets.yaml
```

Edit `infra/k8s/secrets.yaml` and replace all `CHANGE_ME` values:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: salesos-secrets
type: Opaque
stringData:
  database_url: "postgresql+asyncpg://salesos:<REAL_PASSWORD>@postgres:5432/salesos"
  jwt_secret_key: "<REAL_HEX_64>"
  openai_api_key: "sk-<REAL_KEY>"
```

Apply:

```bash
kubectl apply -f infra/k8s/secrets.yaml
```

> **NEVER** commit `secrets.yaml` to version control. It is in `.gitignore`.

### 4.3 Deployments and Services

**Backend** (2 replicas by default):

```bash
kubectl apply -f infra/k8s/backend-deployment.yaml
```

This creates:
- `Deployment/salesos-backend` (2 replicas, image `salesos/backend:latest`)
- `Service/salesos-backend` (ClusterIP, port 8000)

**Frontend** (2 replicas):

```bash
kubectl apply -f infra/k8s/frontend-deployment.yaml
```

This creates:
- `Deployment/salesos-frontend` (2 replicas, image `salesos/frontend:latest`)
- `Service/salesos-frontend` (ClusterIP, port 3000)

### 4.4 Ingress Configuration

Create `infra/k8s/ingress.yaml`:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: salesos-ingress
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - salesos.com
        - api.salesos.com
      secretName: salesos-tls
  rules:
    - host: salesos.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: salesos-frontend
                port:
                  number: 3000
    - host: api.salesos.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: salesos-backend
                port:
                  number: 8000
```

Apply:

```bash
kubectl apply -f infra/k8s/ingress.yaml
```

### 4.5 Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: salesos-backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: salesos-backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Pods
          value: 2
          periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Pods
          value: 1
          periodSeconds: 120
```

Apply:

```bash
kubectl apply -f infra/k8s/hpa.yaml
```

### 4.6 Persistent Volume Claims

For databases running on EKS (not using managed RDS):

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-data
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: gp3
  resources:
    requests:
      storage: 100Gi
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: neo4j-data
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: gp3
  resources:
    requests:
      storage: 20Gi
```

Apply:

```bash
kubectl apply -f infra/k8s/pvc.yaml
```

---

## 5. Database Setup

### 5.1 PostgreSQL Initialization

The initialization script (`infra/docker/postgres/init/01-init.sql`) runs automatically on first container start:

```sql
CREATE EXTENSION IF NOT EXISTS vector;       -- pgvector for embeddings
CREATE EXTENSION IF NOT EXISTS pg_trgm;      -- trigram matching for fuzzy search
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";  -- UUID generation
CREATE EXTENSION IF NOT EXISTS pgcrypto;     -- encryption functions

CREATE SCHEMA IF NOT EXISTS audit;
CREATE SCHEMA IF NOT EXISTS identity;
CREATE SCHEMA IF NOT EXISTS company;
CREATE SCHEMA IF NOT EXISTS activity;
CREATE SCHEMA IF NOT EXISTS crm;
```

**Verify extensions** after startup:

```bash
docker compose exec postgres psql -U salesos -d salesos -c "\dx"
```

Expected output should show: `vector`, `pg_trgm`, `uuid-ossp`, `pgcrypto`.

### 5.2 Neo4j Initialization

Neo4j starts with no data. The backend populates the knowledge graph at runtime. The initial password is set via `NEO4J_AUTH` environment variable.

**Verify Neo4j**:

```bash
docker compose exec neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD" "RETURN 1 AS ok"
```

### 5.3 Migrations (Alembic)

Alembic migrations run automatically before the backend starts via the `migrations` service:

```yaml
migrations:
  image: ${REGISTRY}/${IMAGE_NAMESPACE}/backend:${IMAGE_TAG}
  restart: on-failure
  entrypoint: ["sh", "-c", "alembic upgrade head"]
  depends_on:
    postgres:
      condition: service_healthy
```

**Manual migration commands**:

```bash
# Run all pending migrations
docker compose exec backend alembic upgrade head

# Check current revision
docker compose exec backend alembic current

# View migration history
docker compose exec backend alembic history

# Rollback one step
docker compose exec backend alembic downgrade -1

# Generate new migration
docker compose exec backend alembic revision --autogenerate -m "description"
```

### 5.4 Database Backup Configuration

**Automated backups** run daily at 03:00 UTC via the `backup` service:

```yaml
backup:
  command: |
    echo "0 3 * * * /usr/local/bin/backup-db" | crontab -
    crond -f -l 2
```

**Manual backup**:

```bash
# Via script
./infra/scripts/backup-db.sh

# Via docker compose
docker compose -f docker-compose.prod.yml --profile backup run --rm backup backup-db
```

**Scheduled backup via host cron** (recommended):

```bash
# Install cron entry on the host
crontab -e
# Add: 0 3 * * * /opt/salesos/infra/scripts/cron-backup.sh >> /var/log/salesos-backup.log 2>&1
```

**Backup configuration**:

| Setting | Value | Env Var |
|---------|-------|---------|
| Backup directory | `/backups/postgres` | `BACKUP_DIR` |
| Retention | 7 days | `RETENTION_DAYS` |
| Format | pg_dump custom (compressed) | — |
| S3 upload | Optional | `S3_BUCKET` |
| Webhook notification | Optional | `NOTIFY_WEBHOOK` |

**Restore from backup**:

```bash
./infra/scripts/restore-db.sh /backups/postgres/salesos_20260712_030000.dump
```

### 5.5 Connection Pooling

PgBouncer runs in **transaction mode** with these settings:

| Setting | Value | Description |
|---------|-------|-------------|
| Pool mode | transaction | Connections returned after each transaction |
| Max client connections | 100 | Total concurrent clients |
| Default pool size | 25 | Connections per user/database pair |
| Min pool size | 5 | Always-maintained connections |
| Reserve pool size | 5 | Extra connections for bursts |

**PgBouncer connects to PostgreSQL on port 5432**. Application code should connect to PgBouncer on port 6432 in production, or directly to PostgreSQL for migrations.

**Verify pool status**:

```bash
docker compose exec pgbouncer psql -h pgbouncer -p 6432 pgbouncer -c "SHOW POOLS;"
```

---

## 6. Environment Configuration

### 6.1 Environment Variables Reference

All variables are defined in `.env.production.template`. Copy and customize.

#### Required (must change)

| Variable | Example | Description |
|----------|---------|-------------|
| `POSTGRES_PASSWORD` | `<openssl rand -base64 24>` | PostgreSQL password |
| `NEO4J_PASSWORD` | `<openssl rand -hex 32>` | Neo4j authentication password |
| `JWT_SECRET_KEY` | `<openssl rand -hex 64>` | JWT signing secret (64 bytes minimum) |
| `DOMAIN` | `salesos.com` | Production domain for TLS and CORS |
| `OPENAI_API_KEY` | `sk-...` | OpenAI API key for embeddings |

#### Database

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_USER` | `salesos` | PostgreSQL username |
| `POSTGRES_DB` | `salesos` | PostgreSQL database name |
| `DATABASE_URL` | — | SQLAlchemy async connection string (auto-built from above) |

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
| `OPENAI_API_KEY` | — | Required for embeddings and copilot |
| `OPENAI_MODEL` | `gpt-4o-mini` | Chat model for copilot |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-large` | Embedding model |

#### JWT

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token lifetime |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime |

#### Frontend

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `https://api.${DOMAIN}` | Backend API URL (browser-side) |

#### SSO / OAuth

| Variable | Description |
|----------|-------------|
| `SSO_GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `SSO_GOOGLE_CLIENT_SECRET` | Google OAuth client secret |
| `SSO_MICROSOFT_CLIENT_ID` | Microsoft OAuth client ID |
| `SSO_MICROSOFT_CLIENT_SECRET` | Microsoft OAuth client secret |
| `SSO_GITHUB_CLIENT_ID` | GitHub OAuth client ID |
| `SSO_GITHUB_CLIENT_SECRET` | GitHub OAuth client secret |

#### SMTP

| Variable | Default | Description |
|----------|---------|-------------|
| `SMTP_HOST` | — | SMTP server hostname |
| `SMTP_PORT` | `465` | SMTP port (TLS) |
| `SMTP_USER` | — | SMTP username |
| `SMTP_PASSWORD` | — | SMTP password |
| `SMTP_FROM` | `noreply@salesos.io` | Sender email address |

#### Rate Limiting

| Variable | Default | Description |
|----------|---------|-------------|
| `RATE_LIMIT_AUTHENTICATED` | `100` | Requests per minute (authenticated) |
| `RATE_LIMIT_ANONYMOUS` | `20` | Requests per minute (anonymous) |
| `RATE_LIMIT_SEARCH` | `30` | Requests per minute (search endpoint) |

#### Feature Flags

| Variable | Default | Description |
|----------|---------|-------------|
| `FEATURE_SEARCH_FUZZY_V2` | `false` | Enable v2 fuzzy search |
| `FEATURE_AI_COPILOT` | `false` | Enable AI copilot features |
| `FEATURE_CRM_KANBAN` | `false` | Enable CRM kanban view |

#### Observability

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Python logging level |
| `SENTRY_DSN` | — | Sentry DSN for error tracking |

#### Scraper API Keys (optional)

| Variable | Description |
|----------|-------------|
| `BALADY_API_KEY` | Saudi government scraper API |
| `TAQEEM_API_KEY` | Taqyem scraper API |
| `NAJIZ_API_KEY` | Najiz scraper API |
| `REGA_API_KEY` | Rega scraper API |
| `NCNP_API_KEY` | NCNP scraper API |
| `NOTION_TOKEN` | Notion integration token |

### 6.2 Secrets Management

**Docker Compose**: Secrets are loaded from `.env.production` via `env_file` directive. The file must have `chmod 600` permissions on the host:

```bash
chmod 600 /opt/salesos/.env.production
chown root:root /opt/salesos/.env.production
```

**Kubernetes**: Secrets are stored in `infra/k8s/secrets.yaml` (never committed to git) and applied via `kubectl apply`. The backend reads them via `secretKeyRef` in the deployment spec.

**AWS (Terraform)**: Secrets are stored in AWS Secrets Manager (`salesos-production-secrets`). The Terraform module creates and manages them. Retrieve values with:

```bash
aws secretsmanager get-secret-value --secret-id salesos-production-secrets --query SecretString --output text
```

**Production recommendation**: Use HashiCorp Vault or AWS Secrets Manager with an ESO (External Secrets Operator) to sync K8s secrets from the vault.

### 6.3 Feature Flags

Feature flags are boolean environment variables prefixed with `FEATURE_`. They are read at application startup and control feature availability.

| Flag | Controls | Default |
|------|----------|---------|
| `FEATURE_SEARCH_FUZZY_V2` | New fuzzy search algorithm | `false` |
| `FEATURE_AI_COPILOT` | AI copilot sidebar and suggestions | `false` |
| `FEATURE_CRM_KANBAN` | CRM opportunity kanban view | `false` |

To enable a feature, set the variable to `true` in `.env.production` and restart the backend container:

```bash
# Enable AI copilot
sed -i 's/FEATURE_AI_COPILOT=false/FEATURE_AI_COPILOT=true/' .env.production
docker compose -f docker-compose.prod.yml restart backend
```

### 6.4 Rate Limiting Configuration

Rate limiting is enforced at the application level using Redis as the backing store. The middleware checks the client IP (or JWT user ID for authenticated requests) against the configured limits.

| Endpoint Category | Default Limit | Window | Key |
|-------------------|--------------|--------|-----|
| Authentication (`/api/v1/identity/auth/*`) | 100 req/min | 60s | IP |
| Authenticated API | 100 req/min | 60s | User ID |
| Anonymous API | 20 req/min | 60s | IP |
| Search (`/api/v1/search`) | 30 req/min | 60s | User ID |

Rate limit headers are returned on every response:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1689168000
```

When the limit is exceeded, the server returns `429 Too Many Requests` with a `Retry-After` header.

---

## 7. Deployment Procedure

### 7.1 First-Time Deployment

#### Step 1: Provision infrastructure

```bash
# Via Terraform (AWS)
cd infra/terraform
terraform init
terraform workspace select production
terraform plan -var-file="environments/production.tfvars"
terraform apply -var-file="environments/production.tfvars"
```

This creates: VPC, EKS cluster, RDS PostgreSQL, and AWS Secrets Manager.

#### Step 2: Configure DNS

Point your domain to the VPS/Load Balancer IP:

```
salesos.com       A    <VPS_IP>
api.salesos.com   A    <VPS_IP>
```

#### Step 3: Install Docker (on VPS)

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

#### Step 4: Clone and configure

```bash
cd /opt/salesos
git clone https://github.com/ragheeda-boop/salesos.git .

# Create production environment file
cp .env.production.template .env.production
# Edit .env.production with real secrets
nano .env.production
chmod 600 .env.production
```

#### Step 5: Deploy

```bash
./infra/scripts/deploy.sh
```

Or manually:

```bash
# Pull images
docker compose -f docker-compose.prod.yml pull

# Start all services
docker compose -f docker-compose.prod.yml up -d

# Verify
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs --tail=50 backend
curl -s https://api.salesos.com/health | jq .
curl -s https://salesos.com | head -20
```

#### Step 6: Create initial admin user

```bash
docker compose -f docker-compose.prod.yml exec backend python scripts/create_admin.py \
  --email admin@yourcompany.com \
  --password "$(openssl rand -base64 16)" \
  --tenant yourcompany
```

#### Step 7: Install scheduled backups

```bash
# On the host
crontab -e
# Add:
0 3 * * * /opt/salesos/infra/scripts/cron-backup.sh >> /var/log/salesos-backup.log 2>&1
```

#### Step 8: Verify everything

```bash
# Health checks
curl -s https://api.salesos.com/health | jq .
curl -s -o /dev/null -w "%{http_code}" https://salesos.com

# Database
docker compose exec postgres psql -U salesos -d salesos -c "\dt" | head -20

# Extensions
docker compose exec postgres psql -U salesos -d salesos -c "\dx"

# Backup test
./infra/scripts/backup-db.sh

# Logs
docker compose -f docker-compose.prod.yml logs --tail=20
```

### 7.2 Upgrades (Rolling Update)

#### Docker Compose upgrade

```bash
# 1. Pull new images
IMAGE_TAG=v1.1.0 docker compose -f docker-compose.prod.yml pull

# 2. Run migrations first
IMAGE_TAG=v1.1.0 docker compose -f docker-compose.prod.yml run --rm migrations

# 3. Deploy with zero downtime (services restart sequentially)
IMAGE_TAG=v1.1.0 docker compose -f docker-compose.prod.yml up -d --remove-orphans

# 4. Verify
curl -s https://api.salesos.com/health | jq .version
docker compose -f docker-compose.prod.yml ps
```

#### Kubernetes rolling update

```bash
# Update image tag
kubectl set image deployment/salesos-backend backend=ghcr.io/ragheeda-boop/salesos/backend:v1.1.0
kubectl set image deployment/salesos-frontend frontend=ghcr.io/ragheeda-boop/salesos/frontend:v1.1.0

# Monitor rollout
kubectl rollout status deployment/salesos-backend
kubectl rollout status deployment/salesos-frontend
```

### 7.3 Rollback Procedure

If a deployment fails health checks or causes errors:

**Docker Compose rollback**:

```bash
# 1. Stop all services
docker compose -f docker-compose.prod.yml down

# 2. Restore database if migrations were applied
LATEST_BACKUP=$(ls -t /opt/salesos/backups/postgres/salesos_*.dump | head -1)
./infra/scripts/restore-db.sh "$LATEST_BACKUP"

# 3. Set previous version
export IMAGE_TAG=v1.0.0  # previous working version

# 4. Restart
docker compose -f docker-compose.prod.yml up -d

# 5. Verify
curl -s https://api.salesos.com/health | jq .
```

**Kubernetes rollback**:

```bash
# Rollback backend
kubectl rollout undo deployment/salesos-backend

# Rollback frontend
kubectl rollout undo deployment/salesos-frontend

# Check status
kubectl rollout status deployment/salesos-backend
```

### 7.4 Blue-Green Deployment Strategy

For zero-downtime deployments with full traffic switching:

```
Blue (current v1.0.0)  ──────►  Load Balancer  ◄──────  Green (new v1.1.0)
                                    │
                          ┌─────────┴──────────┐
                          │  Health check new   │
                          │  Switch traffic     │
                          │  Verify             │
                          └────────────────────┘
```

**Procedure**:

1. Deploy green environment with new version (separate Docker Compose project or K8s namespace)
2. Run smoke tests against green's internal endpoint
3. Update Caddy/Ingress to point to green
4. Monitor for 15 minutes
5. If issues: switch back to blue
6. If healthy: decommission blue

**Docker Compose implementation**:

```bash
# Deploy green alongside blue
COMPOSE_PROJECT_NAME=salesos-green IMAGE_TAG=v1.1.0 \
  docker compose -f docker-compose.prod.yml -p salesos-green up -d

# Verify green
curl -s http://localhost:8001/health  # green backend on different port

# Switch Caddy to green (update Caddyfile and reload)
docker compose -f docker-compose.prod.yml restart caddy

# Decommission blue
COMPOSE_PROJECT_NAME=salesos-blue docker compose -f docker-compose.prod.yml down
```

---

## 8. CI/CD Pipeline

### 8.1 Pipeline Overview

```
Push tag (v*) → [Lint] → [Test] → [Build] → [Deploy] → [Verify]
```

### 8.2 Build Stage

Triggered on push of tags matching `v*`:

```yaml
# .github/workflows/deploy.yml (conceptual)
name: Deploy
on:
  push:
    tags: ['v*']

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run backend tests
        working-directory: backend
        run: |
          pip install -e .
          pytest --cov=app --cov-report=xml -v
      - name: Architecture compliance check
        run: pwsh scripts/arch-compliance.ps1 -JsonOnly

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build and push backend
        uses: docker/build-push-action@v5
        with:
          context: backend
          file: backend/Dockerfile
          push: true
          tags: |
            ghcr.io/ragheeda-boop/salesos/backend:${{ github.ref_name }}
            ghcr.io/ragheeda-boop/salesos/backend:latest
      - name: Build and push frontend
        uses: docker/build-push-action@v5
        with:
          context: frontend
          file: frontend/Dockerfile
          push: true
          tags: |
            ghcr.io/ragheeda-boop/salesos/frontend:${{ github.ref_name }}
            ghcr.io/ragheeda-boop/salesos/frontend:latest

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to VPS via SSH
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.VPS_SSH_KEY }}
          script: |
            cd /opt/salesos
            IMAGE_TAG=${{ github.ref_name }} ./infra/scripts/deploy.sh
```

### 8.3 Test Stage

| Test Type | Tool | Command | Gate |
|-----------|------|---------|------|
| Unit tests | pytest | `pytest --cov=app --cov-report=xml -v` | Fail if coverage < 85% |
| Lint | ruff | `ruff check .` | Fail on any error |
| Type check | mypy | `mypy app/ --ignore-missing-imports` | Fail on any error |
| Architecture compliance | Custom | `pwsh scripts/arch-compliance.ps1 -JsonOnly` | Fail if compliance < 95% |
| Security scan | gitleaks | `gitleaks detect --source .` | Fail on any secret |
| Dependency audit | pip-audit, npm audit | `pip-audit && npm audit` | Fail on critical |

### 8.4 Deploy Stage

The deploy script (`infra/scripts/deploy.sh`) performs:

1. Validates `.env.production` exists on the VPS
2. Copies compose file and infra configs to `/opt/salesos`
3. Pulls new images
4. Starts services with `docker compose up -d --remove-orphans`
5. Prunes old images

### 8.5 Smoke Tests

Post-deploy verification:

```bash
# Health check
curl -sf https://api.salesos.com/health || exit 1

# Frontend loads
curl -sf -o /dev/null https://salesos.com || exit 1

# API responds with correct version
VERSION=$(curl -s https://api.salesos.com/health | jq -r .version)
[ "$VERSION" = "$EXPECTED_VERSION" ] || exit 1

# Database accessible
docker compose exec postgres pg_isready -U salesos
```

---

## 9. Monitoring & Observability

### 9.1 Health Endpoints

| Endpoint | Method | Response | Purpose |
|----------|--------|----------|---------|
| `/health` | GET | `{"status":"healthy",...}` | Full health check (DB, Neo4j, Redis) |
| `/health/ready` | GET | 200 OK | Readiness probe (is service ready for traffic?) |
| `/ping` | GET | `{"ping":"pong"}` | Simple liveness check |
| `/metrics` | GET | Prometheus text format | Application metrics |
| `/decision/metrics` | GET | JSON | Decision engine stats |
| `/event-runtime/stats` | GET | JSON | Event bus throughput and dead letter count |

### 9.2 Metrics Collection

Prometheus is configured in `infra/monitoring/prometheus.yml` with these scrape targets:

| Job | Target | Interval |
|-----|--------|----------|
| `salesos-backend` | `backend:8000/metrics` | 15s |
| `prometheus` | `localhost:9090` | 15s |
| `postgres-exporter` | `postgres-exporter:9187` | 15s |
| `redis-exporter` | `redis-exporter:9121` | 15s |

**Key application metrics** (exposed at `/metrics`):

| Metric | Type | Description |
|--------|------|-------------|
| `salesos_http_requests_total` | Counter | Total HTTP requests by path and status |
| `salesos_http_request_duration_seconds` | Histogram | Request latency distribution |
| `salesos_db_query_duration_seconds` | Histogram | Database query latency |
| `salesos_ai_inference_duration_seconds` | Histogram | AI model inference latency |
| `salesos_decision_evaluations_total` | Counter | Decision engine evaluations |
| `salesos_event_bus_messages_total` | Counter | Events processed |

### 9.3 Log Aggregation

All services use JSON file logging with rotation:

```yaml
x-logging: &default-logging
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
    tag: "{{.Name}}/{{.ID}}"
```

**View logs**:

```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# Specific service with timestamps
docker compose -f docker-compose.prod.yml logs -f --tail=100 --timestamps backend

# Search logs
docker compose -f docker-compose.prod.yml logs backend 2>&1 | grep -i error

# JSON parsing
docker compose -f docker-compose.prod.yml logs backend 2>&1 | jq -r 'select(.level == "error")'
```

**Production recommendation**: Deploy Loki + Promtail for centralized log aggregation and long-term storage, or ship logs to an external service (Datadog, CloudWatch Logs).

### 9.4 Alert Rules

Defined in `infra/monitoring/alerts.yml`:

| Alert | Condition | Severity | Duration |
|-------|-----------|----------|----------|
| `HighErrorRate` | 5xx rate > 5% | critical | 5m |
| `HighLatency` | p99 > 1s | critical | 5m |
| `HighLatencyP95` | p95 > 500ms | warning | 5m |
| `BackendServiceDown` | `up == 0` | critical | 1m |
| `BackendUnhealthy` | `up == 0` | critical | 5m |
| `BackendDegraded` | Any 5xx errors | warning | 10m |
| `PostgresDown` | `pg_up == 0` | critical | 1m |
| `PostgresHighConnections` | connections > 50 | warning | 5m |
| `RedisDown` | `redis_up == 0` | critical | 1m |
| `Neo4jDown` | `neo4j_up == 0` | critical | 1m |
| `SlowDatabaseQueries` | p95 query > 1s | warning | 5m |
| `SlowAIInference` | p95 inference > 10s | warning | 5m |
| `NoTraffic` | Zero requests | warning | 10m |
| `DiskSpaceLow` | Available < 10% | critical | 10m |
| `MemoryUsageHigh` | Used > 90% | warning | 5m |

### 9.5 Alertmanager Configuration

Alerts are routed via `infra/monitoring/alertmanager.yml`:

| Receiver | Severity | Repeat Interval | Channel |
|----------|----------|-----------------|---------|
| `default` | warning | 4h | Slack webhook |
| `critical` | critical | 1h | Slack webhook (with `[CRITICAL]` prefix) |

Configure the Slack webhook URL in `alertmanager.yml`:

```yaml
receivers:
  - name: "default"
    slack_configs:
      - api_url: "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
  - name: "critical"
    slack_configs:
      - api_url: "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
```

### 9.6 Dashboard Configuration

Pre-built Grafana dashboards are in `infra/monitoring/grafana/dashboards/`:

| Dashboard | File | Refresh |
|-----------|------|---------|
| SalesOS Overview | `salesos-overview.json` | 5 min |
| Pipeline Metrics | `salesos-pipeline.json` | 1 min |

**Grafana provisioning** is configured in `infra/monitoring/grafana/provisioning/dashboards.yml` and auto-loads dashboards on startup.

Access Grafana at `http://<VPS_IP>:3001` (or via port-forward in K8s).

---

## 10. Security

### 10.1 TLS Configuration

TLS is handled by **Caddy** with automatic Let's Encrypt certificate provisioning:

```caddy
{$DOMAIN} {
    reverse_proxy frontend:3000
}

api.{$DOMAIN} {
    reverse_proxy backend:8000
}
```

Caddy automatically:
- Provisions TLS certificates on first request
- Redirects HTTP to HTTPS
- Renews certificates before expiry
- Supports OCSP stapling

**TLS settings** (Caddy defaults):
- TLS 1.2 and 1.3 enabled
- Automatic cipher suite selection
- OCSP stapling enabled

**Additional security headers** should be added via Caddyfile or application middleware:

```
api.{$DOMAIN} {
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        X-XSS-Protection "1; mode=block"
        Referrer-Policy "strict-origin-when-cross-origin"
        Content-Security-Policy "default-src 'self'"
    }
    reverse_proxy backend:8000
}
```

### 10.2 Network Policies

**Docker Compose**: Services communicate on a default bridge network. Only Caddy exposes ports to the host:

```yaml
caddy:
  ports:
    - "80:80"
    - "443:443"
# All other services: no published ports (internal only)
```

**Kubernetes**: Apply network policies to restrict pod-to-pod communication:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: salesos-backend-policy
spec:
  podSelector:
    matchLabels:
      app: salesos-backend
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: salesos-frontend
        - podSelector:
            matchLabels:
              app: salesos-caddy
      ports:
        - port: 8000
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: salesos-postgres
      ports:
        - port: 5432
    - to:
        - podSelector:
            matchLabels:
              app: salesos-redis
      ports:
        - port: 6379
    - to:
        - podSelector:
            matchLabels:
              app: salesos-neo4j
      ports:
        - port: 7687
```

### 10.3 WAF / Reverse Proxy Configuration

**Cloudflare** (recommended for production):

1. Add domain to Cloudflare
2. Enable proxy (orange cloud) on DNS records
3. Enable **Bot Fight Mode** under Security → Bots
4. Configure WAF rules:
   - Block requests from countries outside Saudi Arabia (if applicable)
   - Rate limit by IP at the edge
   - Block known attack patterns (SQLi, XSS)
5. Enable **HSTS** in SSL/TLS settings
6. Set minimum TLS version to 1.2

### 10.4 Audit Logging

The application logs all mutating operations to the `audit` schema in PostgreSQL:

| Event | Details Logged | Retention |
|-------|---------------|-----------|
| Login success | User ID, IP, timestamp, tenant | 1 year |
| Login failure | Email, IP, timestamp, reason | 1 year |
| Data access | User ID, resource, action, timestamp | 6 months |
| Permission change | Admin ID, target user, old/new role | 1 year |
| Tenant creation | Admin ID, tenant details | 7 years |
| API key usage | Key ID, endpoint, timestamp | 6 months |
| NBA action | User ID, company, action, outcome | 1 year |

**Query audit logs**:

```bash
docker compose exec postgres psql -U salesos -d salesos \
  -c "SELECT * FROM audit.events ORDER BY created_at DESC LIMIT 100;"
```

---

## 11. Disaster Recovery

### 11.1 Backup Strategy

| Component | Method | Frequency | Retention | Storage |
|-----------|--------|-----------|-----------|---------|
| PostgreSQL | `pg_dump` custom format | Daily at 03:00 UTC | 7 days | Local + S3 |
| PostgreSQL WAL | Continuous archiving | Real-time | 7 days | S3 |
| Neo4j | `neo4j-admin dump` | Daily at 04:00 UTC | 14 days | Local + S3 |
| Redis | RDB snapshot | Every 6 hours | 7 days | Local |
| Docker volumes | Volume snapshot | Daily | 7 days | Local |
| Terraform state | S3 backend | On every apply | Indefinite | S3 (versioned) |

**Offsite backup** (configure in `.env.production`):

```bash
S3_BUCKET=s3://salesos-backups-production
```

The backup script uploads to S3 using `aws s3 cp` or `rclone copy`.

### 11.2 Restore Procedure

**PostgreSQL restore**:

```bash
# 1. Stop the backend (prevent writes)
docker compose -f docker-compose.prod.yml stop backend

# 2. Restore from latest backup
LATEST=$(ls -t /opt/salesos/backups/postgres/salesos_*.dump | head -1)
./infra/scripts/restore-db.sh "$LATEST"

# 3. Verify data
docker compose exec postgres psql -U salesos -d salesos -c "SELECT COUNT(*) FROM identity.users;"

# 4. Restart backend
docker compose -f docker-compose.prod.yml start backend

# 5. Verify health
curl -s https://api.salesos.com/health | jq .
```

**Full stack restore**:

```bash
# 1. Stop all services
docker compose -f docker-compose.prod.yml down

# 2. Restore PostgreSQL volume
docker volume create pgdata  # if needed
docker run --rm -v pgdata:/data -v /opt/salesos/backups:/backups \
  postgres:16 pg_restore -d /data /backups/postgres/salesos_<timestamp>.dump

# 3. Start all services
docker compose -f docker-compose.prod.yml up -d

# 4. Verify
curl -s https://api.salesos.com/health | jq .
```

### 11.3 Failover Plan

**Single VPS deployment** (current):

| Scenario | Recovery Time | Procedure |
|----------|--------------|-----------|
| Application crash | < 1 min | Docker auto-restarts container |
| VPS reboot | < 5 min | Docker `restart: always` + systemd |
| VPS failure | < 30 min | Provision new VPS, restore from S3 backup |
| Database corruption | < 1 hour | Restore from latest `pg_dump` backup |
| Complete data loss | < 2 hours | Provision new VPS, restore from S3 backup |

**Multi-AZ deployment** (EKS/RDS):

| Scenario | Recovery Time | Procedure |
|----------|--------------|-----------|
| Pod failure | < 30s | K8s auto-restarts, HPA scales |
| AZ failure | < 5 min | RDS Multi-AZ failover, EKS reschedules pods |
| Region failure | < 30 min | Restore from cross-region RDS replica |

### 11.4 RPO and RTO Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| **RPO** (Recovery Point Objective) | < 1 hour | Time between last backup and failure |
| **RTO** (Recovery Time Objective) | < 4 hours | Time to restore service after failure |
| **Backup window** | 03:00-04:00 UTC | Daily full backups |
| **Backup testing** | Monthly | Restore test to staging environment |

**Backup verification command** (run monthly):

```bash
# Restore latest backup to staging
STAGING_DB="salesos_staging_$(date +%Y%m%d)"
createdb "$STAGING_DB"
pg_restore -d "$STAGING_DB" /opt/salesos/backups/postgres/salesos_latest.dump

# Verify row counts
psql -d "$STAGING_DB" -c "
  SELECT schemaname, tablename, n_live_tup
  FROM pg_stat_user_tables
  ORDER BY n_live_tup DESC;
"

# Cleanup
dropdb "$STAGING_DB"
```

---

## Quick Reference

### Essential Commands

```bash
# Deploy
IMAGE_TAG=v1.0.0 ./infra/scripts/deploy.sh

# Status
docker compose -f docker-compose.prod.yml ps

# Logs
docker compose -f docker-compose.prod.yml logs -f --tail=100 backend

# Health
curl -s https://api.salesos.com/health | jq .

# Restart single service
docker compose -f docker-compose.prod.yml restart backend

# Backup
./infra/scripts/backup-db.sh

# Restore
./infra/scripts/restore-db.sh <backup-file.dump>

# Scale backend
docker compose -f docker-compose.prod.yml up -d --scale backend=3

# View resource usage
docker stats --no-stream
```

### File Locations

| File | Location | Purpose |
|------|----------|---------|
| Docker Compose (production) | `docker-compose.prod.yml` | Production service definitions |
| Environment config | `.env.production` | Secrets and configuration |
| Caddy config | `infra/caddy/Caddyfile` | Reverse proxy and TLS |
| K8s manifests | `infra/k8s/` | Kubernetes deployment specs |
| Terraform | `infra/terraform/` | AWS infrastructure as code |
| Prometheus config | `infra/monitoring/prometheus.yml` | Metrics scraping |
| Alert rules | `infra/monitoring/alerts.yml` | Alerting thresholds |
| Alertmanager config | `infra/monitoring/alertmanager.yml` | Alert routing |
| Grafana dashboards | `infra/monitoring/grafana/dashboards/` | Pre-built dashboards |
| Backup script | `infra/scripts/backup-db.sh` | PostgreSQL backup |
| Restore script | `infra/scripts/restore-db.sh` | PostgreSQL restore |
| Deploy script | `infra/scripts/deploy.sh` | Deployment automation |
| DB init SQL | `infra/docker/postgres/init/01-init.sql` | Extensions and schemas |

### Support

| Channel | Contact |
|---------|---------|
| Email | support@salesos.sa |
| On-call (critical) | WhatsApp group |
| Engineering lead | escalation after 1 hour |

---

*Created: 2026-07-12*
*Version: 1.0*
*Owner: DevOps / Release Manager*
