# Docker Deployment Guide

> **دليل نشر Docker — تشغيل SalesOS محليًا أو في الإنتاج**

---

## Prerequisites

- Docker 24.0+ with Compose v2
- 8 GB RAM minimum (16 GB recommended)
- Git

---

## Quick Start

```bash
# Clone
git clone https://github.com/salesos/salesos.git
cd salesos

# Configure
cp .env.example .env
# Edit .env with your settings (see configuration guide)

# Start all services
docker compose up -d

# Run migrations
docker compose exec api make migrate

# Create admin user
docker compose exec api python scripts/create_admin.py

# Verify
curl http://localhost:8000/api/v1/health
```

---

## Services

| Service | Port | Description |
|---------|------|-------------|
| `api` | 8000 | FastAPI backend |
| `frontend` | 3000 | Next.js frontend |
| `postgres` | 5432 | Primary database |
| `neo4j` | 7687 | Knowledge graph |
| `redis` | 6379 | Cache layer |

---

## Wave 3 Add-On

For RAG, workflows, and Kafka:

```bash
docker compose -f docker-compose.yml -f docker-compose.wave3.yml up -d
```

Additional services: `kafka`, `schema-registry`, `rag-service`, `workflow-engine`, `warehouse`.

---

## Health Checks

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

---

## Volumes

| Volume | Service | Path |
|--------|---------|------|
| `pgdata` | postgres | `/var/lib/postgresql/data` |
| `neo4jdata` | neo4j | `/data` |
| `redisdata` | redis | `/data` |
| `kafkadata` | kafka | `/var/lib/kafka/data` |

---

## Logs

```bash
# Follow all services
docker compose logs -f

# Specific service
docker compose logs -f api

# Last 100 lines
docker compose logs --tail=100 api
```

---

## Common Commands

```bash
# Rebuild
docker compose build api

# Restart single service
docker compose restart api

# Scale
docker compose up -d --scale api=3

# Reset database
docker compose down -v && docker compose up -d
```

---

## Production TL;DR

1. Use strong passwords in `.env`
2. Enable TLS via reverse proxy (nginx/Caddy)
3. Use PostgreSQL connection pooler (pgBouncer)
4. Set up regular backups
5. Configure monitoring (Prometheus + Grafana)

See [Production Checklist](production.md) for details.
