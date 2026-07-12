# SalesOS Infrastructure

Infrastructure as Code and deployment configuration for all environments.

## Directory Structure

```
infra/
├── caddy/                  # Caddy reverse proxy config
├── docker/                 # Docker utility configs
│   ├── backup/             # Database backup scripts
│   └── postgres/           # PostgreSQL Docker config
├── k8s/                    # Kubernetes manifests
│   ├── backend-deployment.yaml
│   ├── frontend-deployment.yaml
│   └── secrets.yaml
├── monitoring/             # Observability stack
│   ├── grafana/            # Grafana dashboards
│   ├── prometheus.yml      # Prometheus config
│   ├── alertmanager.yml    # Alertmanager config
│   └── alerts.yml          # Alert rules
├── scripts/                # Operational scripts
│   ├── deploy.sh           # Deployment script
│   ├── backup-db.sh        # Database backup
│   ├── restore-db.sh       # Database restore
│   └── cron-backup.sh      # Scheduled backup runner
├── staging/                # Staging environment
│   └── docker-compose.staging.yml
└── terraform/              # Terraform IaC
    ├── main.tf             # Main infrastructure
    ├── variables.tf        # Input variables
    └── outputs.tf          # Output values
```

## Environment Topology

| Environment | Type | Deploy Trigger | Database | Notes |
|-------------|------|----------------|----------|-------|
| **dev** | Local | Manual | Local PostgreSQL | `docker compose up` |
| **staging** | Shared | PR merge to `develop` | Separate PG instance | `docker compose -f docker-compose.staging.yml up` |
| **production** | Production | Release tag | Production PG + Redis + Neo4j | Gradual rollout |

## Kubernetes Namespace Conventions

```
┌─────────────────────────────────────────────┐
│  salesos-production                          │
│  ├── salesos-backend (deployment)            │
│  ├── salesos-frontend (deployment)           │
│  ├── postgres (statefulset)                  │
│  ├── redis (deployment)                      │
│  └── neo4j (statefulset)                     │
├─────────────────────────────────────────────┤
│  salesos-staging                             │
│  └── (same structure, suffixed -staging)     │
└─────────────────────────────────────────────┘
```

Naming convention: `{app-name}-{environment}` (e.g., `salesos-backend-production`).

## Terraform Workspace Management

```bash
# List workspaces
terraform workspace list

# Select environment
terraform workspace select staging
terraform workspace select production

# Plan and apply
terraform plan -var-file="environments/$(terraform workspace show).tfvars"
terraform apply -var-file="environments/$(terraform workspace show).tfvars"
```

One workspace per environment (`dev`, `staging`, `production`). Variables are managed via `tfvars` files.

## Monitoring Stack

| Component | Purpose | Config Location |
|-----------|---------|-----------------|
| **Prometheus** | Metrics collection and alerting | `monitoring/prometheus.yml` |
| **Alertmanager** | Alert routing and notification | `monitoring/alertmanager.yml` |
| **Grafana** | Dashboards and visualization | `monitoring/grafana/` |
| **Sentry** | Error tracking | Backend env config |
| **OpenTelemetry** | Distributed tracing | Backend SDK config |

### Alert Rules

Defined in `monitoring/alerts.yml`:
- High API error rate (>5% over 5m)
- Database connection pool exhaustion
- Neo4j connectivity loss
- High p99 latency (>1s for core endpoints)
- Low disk space on persistent volumes

## Backup Strategy

| Component | Frequency | Retention | Method |
|-----------|-----------|-----------|--------|
| PostgreSQL | Daily (full) + Continuous WAL | 30 days | `pg_dump` via `backup-db.sh` |
| Redis | Snapshot every 6h | 7 days | RDB persistence |
| Neo4j | Daily | 14 days | Neo4j dump |
| Terraform state | On every apply | Indefinite | Backend storage (S3/Azure Blob) |

### Backup Commands

```bash
# Manual backup
./scripts/backup-db.sh

# Restore from backup
./scripts/restore-db.sh <backup-file>

# Set up scheduled backup (cron)
./scripts/cron-backup.sh install
```

Backups are stored in `infra/docker/backup/` and should be uploaded to external storage (configured in `cron-backup.sh`).
