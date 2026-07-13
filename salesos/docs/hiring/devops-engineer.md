# DevOps Engineer — SalesOS

> SalesOS Engineering Team · Saudi Arabia (Remote OK)

---

## About SalesOS

SalesOS is an AI-native enterprise intelligence platform running on Docker Compose (staging) with Kubernetes (production). Our infrastructure spans PostgreSQL 16, Neo4j 5.x, Redis 7, Prometheus/Grafana monitoring, and GitHub Actions CI/CD. We deploy via tag-triggered pipelines with SSH-based VPS deployment.

## Role

You will own and improve SalesOS infrastructure — CI/CD pipelines, container orchestration, monitoring, backup/restore, security scanning, and production deployment. You will harden our deployment pipeline for GA and scale infrastructure as tenant count grows.

## Requirements

### Must-Have

- **Docker** — multi-stage builds, docker-compose, health checks, resource limits, image optimization
- **Kubernetes** — deployments, services, ingress, ConfigMaps, Secrets, rolling updates
- **Terraform** — infrastructure as code, state management, module composition
- **AWS** — EC2, RDS, S3, VPC, IAM, CloudWatch (or equivalent cloud provider)
- **Prometheus/Grafana** — metrics collection, dashboard creation, alerting rules
- **CI/CD** — GitHub Actions (or equivalent), pipeline design, artifact management
- **Linux** — system administration, networking, troubleshooting

### Nice-to-Have

- **Security scanning** — Trivy, Bandit, Semgrep, dependency auditing
- **Database administration** — PostgreSQL backup/restore, replication, monitoring
- **SSL/TLS** — certificate management, Caddy/nginx configuration
- **Log aggregation** — Loki, ELK, or Docker json-file logging
- **Cost optimization** — right-sizing, reserved instances, spot instances

## Architecture Context

| Component | Current State | Target |
|-----------|--------------|--------|
| Staging | Docker Compose | Docker Compose |
| Production | Docker Compose (VPS) | Kubernetes (AWS EKS) |
| CI/CD | GitHub Actions (tag-triggered) | GitHub Actions + security gates |
| Monitoring | Prometheus + Grafana (configured) | + alerting, uptime monitoring |
| Backup | Daily cron (7-day retention) | + S3 offsite, restore testing |
| Images | Pinned (version-based) | + Trivy scanning in CI |

## Infrastructure Stack

| Layer | Technology |
|-------|-----------|
| Containers | Docker, Docker Compose |
| Orchestration | Kubernetes (production target) |
| IaC | Terraform (AWS) |
| CI/CD | GitHub Actions |
| Monitoring | Prometheus, Grafana |
| Security | Trivy, Bandit, Semgrep |
| Database | PostgreSQL 16 (pgvector, pg_trgm), Neo4j 5.x |
| Cache | Redis 7 |
| Reverse Proxy | Caddy 2 (auto-TLS) |

## Responsibilities

1. Maintain and harden CI/CD pipeline (security gates, arch compliance, rollback)
2. Manage Docker images — build, pin versions, scan for vulnerabilities
3. Design and maintain Kubernetes manifests for production
4. Implement and test backup/restore procedures
5. Set up monitoring dashboards and alerting rules
6. Manage SSL/TLS certificates and DNS configuration
7. Implement security scanning workflows (Trivy, Bandit, Semgrep)
8. Optimize infrastructure costs and performance
9. Maintain infrastructure documentation and runbooks
10. Support production incidents and on-call rotation

## Key Projects

| Project | Description | Priority |
|---------|-------------|----------|
| K8s Migration | Move from Docker Compose to Kubernetes production | P1 |
| Backup Restore Test | Verify backup/restore to staging | P0 |
| External Uptime Monitoring | UptimeRobot or BetterStack integration | P0 |
| Security Scan Pipeline | Trivy + Bandit + Semgrep in CI | P0 |
| Log Aggregation | Loki or equivalent for centralized logging | P1 |
| S3 Offsite Backup | Disaster recovery with cross-region replication | P1 |

## What We Offer

- Own the entire infrastructure stack from CI/CD to production monitoring
- Modern tooling: Docker, K8s, Terraform, Prometheus/Grafana
- Security-first culture with automated scanning in CI
- Clear path: DevOps → Platform Architect → Infrastructure Lead
- Competitive compensation aligned with Saudi market

## Interview Process

1. **Technical Screening** — Infrastructure design and troubleshooting (1 hour)
2. **Hands-On Challenge** — Docker/K8s setup + CI/CD pipeline design (take-home, 2 hours max)
3. **Architecture Discussion** — Production deployment, monitoring, incident response (45 min)
4. **Team Fit** — Meet the engineering team (30 min)
5. **Offer** — Within 48 hours of final interview

---

*SalesOS is an equal opportunity employer. We value diversity and inclusion.*
