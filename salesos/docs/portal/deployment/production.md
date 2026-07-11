# Production Deployment Checklist

> **قائمة النشر الإنتاجي — التحقق من الجاهزية قبل الإطلاق**

---

## Pre-Deployment

| Item | Check |
|------|-------|
| [ ] Security audit passed (zero Critical findings) | [Production Audit Report](../../docs/PRODUCTION_AUDIT_REPORT.md) |
| [ ] Architecture Review Board approval | ADR documents |
| [ ] Performance benchmarks met | All budgets within limits |
| [ ] Rollback plan documented | [Migration Guide](migration.md) |
| [ ] Database migrations reversible | All migrations have `down` |
| [ ] Feature flags configured | Gradual rollout plan |
| [ ] Monitoring stack deployed | Prometheus + Grafana |

---

## Infrastructure

| Component | Production Spec |
|-----------|----------------|
| **API** | 4+ replicas behind load balancer |
| **PostgreSQL** | 8 vCPU, 32 GB, 500 GB SSD, HA with streaming replica |
| **Neo4j** | 4 vCPU, 8 GB, HA cluster (3 nodes) |
| **Redis** | 2+ nodes, Sentinel for HA |
| **Kafka** | 3 brokers (4 vCPU, 8 GB each), replication factor 3 |
| **Frontend** | CDN (Vercel / Cloudflare) |

---

## Security Checklist

| Item | Status |
|------|--------|
| TLS 1.3 enabled on all endpoints | ✅ Required |
| HSTS header (`max-age=31536000; includeSubDomains`) | ✅ Required |
| CSP header configured | ✅ Required |
| CORS restricted to known origins | ✅ Required |
| Rate limiting configured per tenant | ✅ Required |
| JWT secret rotated (not default) | ✅ Required |
| Database passwords strong (20+ chars) | ✅ Required |
| Secrets in Vault / K8s Secrets (not .env) | ✅ Required |
| Audit logging enabled | ✅ Required |
| Backups configured (daily + WAL) | ✅ Required |

---

## Database

```bash
# Verify connection pooling
docker compose exec postgres psql -c "SHOW pool_size;"

# Run migrations
docker compose exec api make migrate

# Verify data
docker compose exec api python scripts/verify_data.py
```

---

## Monitoring

| Tool | Purpose |
|------|---------|
| Prometheus | Metrics collection |
| Grafana | Dashboards and alerting |
| Sentry | Error tracking |
| PagerDuty | Incident alerting |

See [Monitoring Guide](monitoring.md) for setup.

---

## Gradual Rollout

```yaml
stages:
  - name: internal
    users: development team
    duration: 1 week
    
  - name: beta
    users: early access customers
    duration: 2 weeks
    verification: check NBA acceptance rate > 60%
    
  - name: enterprise
    users: all customers
    duration: permanent
    verification: all metrics green
```

---

## Rollback Plan

| Scenario | Action | RTO |
|----------|--------|-----|
| API regression | Deploy previous Docker image | 5 min |
| Database migration failure | `make migrate-down` | 10 min |
| Data corruption | Restore from backup | 1 hour |
| Full outage | Failover to DR region | 30 min |
