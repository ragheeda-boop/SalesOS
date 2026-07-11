# Installation Guide — Docker Deployment

> **دليل التثبيت — نشر SalesOS باستخدام Docker**

---

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│              Load Balancer                    │
├─────────────────────────────────────────────┤
│         FastAPI Application (Gunicorn)        │
│  ┌─────────────────────────────────────────┐ │
│  │  Wave 1 │ Wave 2 │ Wave 3 | Decision    │ │
│  │  APIs   │ APIs   │ APIs   | Platform    │ │
│  └─────────┴────────┴────────┴────────────┘ │
├─────────────────────────────────────────────┤
│  PostgreSQL │ Neo4j │ Redis │ Kafka (Wave 3)│
└─────────────────────────────────────────────┘
```

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Docker | 24.0+ | With Compose v2 |
| Docker Compose | 2.20+ | `docker compose` (not `docker-compose`) |
| At least | 8 GB RAM | 16 GB recommended |
| PostgreSQL | 16+ | With pgvector extension (Wave 3) |

---

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/salesos/salesos.git
cd salesos
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your settings. At minimum:

```env
# Required
DATABASE_URL=postgresql://salesos:salesos@postgres:5432/salesos
SECRET_KEY=generate-a-random-secret-key-here
ALLOWED_HOSTS=localhost,api.salesos.sa

# API Keys (Wave 2 features)
OPENAI_API_KEY=sk-...           # For NBA AI reasoning (optional)
GOOGLE_CLIENT_ID=...             # For Gmail integration (optional)
OUTLOOK_CLIENT_ID=...            # For Outlook integration (optional)
```

### 3. Start Services

```bash
docker compose up -d
```

This starts:
- `api` — FastAPI backend (port 8000)
- `frontend` — Next.js frontend (port 3000)
- `postgres` — PostgreSQL database (port 5432)
- `neo4j` — Knowledge graph (port 7687)
- `redis` — Cache layer (port 6379)

### 4. Run Database Migrations

```bash
docker compose exec api make migrate
```

### 5. Verify Installation

```bash
curl http://localhost:8000/api/v1/health

# Response:
# {"status": "healthy", "version": "0.9.0", "services": {"postgres": "ok", "neo4j": "ok", "redis": "ok"}}
```

---

## Docker Compose Configuration

```yaml
# docker-compose.yml (simplified)
version: "3.8"

services:
  api:
    build: ./backend
    ports: ["8000:8000"]
    env_file: .env
    depends_on: [postgres, neo4j, redis]

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    depends_on: [api]

  postgres:
    image: pgvector/pgvector:pg16
    volumes: [pgdata:/var/lib/postgresql/data]
    environment:
      POSTGRES_DB: salesos
      POSTGRES_USER: salesos
      POSTGRES_PASSWORD: salesos

  neo4j:
    image: neo4j:5-community
    volumes: [neo4jdata:/data]
    environment:
      NEO4J_AUTH: neo4j/password

  redis:
    image: redis:7-alpine

volumes:
  pgdata:
  neo4jdata:
```

---

## Wave 3 Services (Optional)

For RAG, workflows, and Kafka:

```bash
# Start Wave 3 infrastructure
docker compose -f docker-compose.yml -f docker-compose.wave3.yml up -d
```

Additional services:
- `kafka` — Event bus (port 9092)
- `schema-registry` — Avro schema management (port 8081)
- `rag-service` — RAG pipeline (port 8100)
- `workflow-engine` — Workflow automation (port 8200)
- `warehouse` — Analytics PostgreSQL (port 5433)

---

## Production Checklist

See the [Production Deployment Guide](../deployment/production.md) for:

- SSL/TLS configuration
- PostgreSQL connection pooling (pgBouncer)
- Redis sentinel for HA
- Neo4j backup strategy
- Monitoring with Prometheus + Grafana
- Horizontal scaling with Kubernetes

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `api` container crashes | Missing `SECRET_KEY` | Generate one: `openssl rand -hex 32` |
| Database connection refused | PostgreSQL not ready | Wait 30s, use `healthcheck` |
| Neo4j connection errors | Auth mismatch | Check `NEO4J_AUTH` matches `.env` |
| CORS errors | `ALLOWED_HOSTS` misconfigured | Add your domain to `ALLOWED_HOSTS` |
