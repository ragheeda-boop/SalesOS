# Performance Baseline

## Infrastructure

| Metric | Value |
|--------|-------|
| Container startup (Postgres) | ~5s |
| Container startup (Neo4j) | ~8s |
| Container startup (API) | ~10s (includes Alembic migrations) |
| Memory idle (Postgres) | 51MB |
| Memory idle (Neo4j) | 446MB |
| Memory idle (API) | 136MB |
| CPU idle (Postgres) | 0% |
| CPU idle (Neo4j) | 1% |
| CPU idle (API) | < 2% |
| Docker image size (Backend) | ~600MB (Python 3.12-slim) |

## Backend API Latency

Measured inside Docker network (no Docker Desktop overhead).

| Endpoint | p50 | p95 | p99 |
|----------|-----|-----|-----|
| `/ping` (no deps) | < 0.1ms | < 0.2ms | < 1ms |
| `/health` (DB + optional services) | < 1ms | < 10ms | < 15ms |
| `/register` (full auth flow + DB writes) | < 200ms | < 500ms | — |
| `/login` (auth + token + session) | < 100ms | < 300ms | — |

### API Latency via Docker Desktop Port Forwarding (Windows only — NOT production)

| Metric | Value |
|--------|-------|
| Overhead per request | 4000–7000ms |
| Cause | Docker Desktop WSL2 networking |
| Note | Not representative of production performance |

## Database

| Parameter | Value |
|-----------|-------|
| Connection pool | 20 connections, 10 overflow |
| Pool recycle | 3600s |
| Query time (SELECT 1) | < 5ms |
| PostgreSQL version | 16 with pgvector extension |
| Slow query log | Not configured |

## Known Issues

1. **Docker Desktop port forwarding overhead** — Docker Desktop adds 4–7s overhead per request via port forwarding. Use `docker exec` for accurate measurements, or deploy on Linux for production.
2. **Redis health check timeout** — Redis health check was causing 4s timeout when Redis is unavailable. Fixed with `socket_connect_timeout=1`.
3. **No memory limits in dev compose** — Dev docker-compose uses host defaults; no memory limits configured.
