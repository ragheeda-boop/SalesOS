# Changelog

All notable changes to SalesOS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.3.0] - 2026-07-13

### Added

- Engineering Dashboard confidence column and audit markers ([A]) for metrics verification
- Architecture Decision Framework (`engineering-os/ARCHITECTURE_DECISION_FRAMEWORK.md`) — ADR process, template, review workflow
- Incident Response Plan (`docs/INCIDENT_RESPONSE_PLAN.md`) — S1-S5 severity levels, escalation paths, communication templates, post-mortem template
- Team hiring documents — backend, frontend, DevOps, QA job descriptions in `docs/hiring/`
- Makefile targets: `verify-backup`, `security-audit`, `perf-test`, `e2e`, `health`, `deploy-staging`, `deploy-prod`

### Changed

- Technical Debt register updated: TD-001 through TD-009 all resolved; TD-002 (Kafka), TD-004 (hardcoded configs), TD-005 (auth review) remain open
- Engineering Dashboard: all production readiness scores now include Confidence column explaining verification method
- CHANGELOG format alignment with keepachangelog.com specification

### Fixed

- Dashboard metrics accuracy: added [A] markers to audited values, flagged self-reported estimates
- Technical debt count corrected from 2 active to 3 active (TD-002, TD-004, TD-005)

---

## [1.2.0] - 2026-07-12

### Added

- Auth on all 9 runtime routers (router-level `Depends(verify_token)`)
- Tiered rate limiting (auth 100/min, search 30/min, anon 20/min)
- `Retry-After` header on 429 responses
- Global-per-IP rate limit keying (not per-path)
- In-memory rate limiter stale sweep (every 300s)
- `.env.production.template` expanded (SMTP, SSO, Meili, Rate Limit, Kafka, Celery)
- Admin guide (`admin_guide.md`)
- Deployment guide (`deployment_guide.md`)
- Production runbook (`production_runbook.md`)
- User guide (`user_guide.md`)
- API documentation portal (`docs/portal/api/` — 26 files)
- Engineering dashboard updated with Sprint 6 completion

### Security

- Frontend dependencies updated (58 packages, 0 vulnerabilities)
- `.gitignore` hardened (`secrets.*`, `*.key`, `*.pem`, `.env.*` patterns)
- `secrets.yaml` and `.env.staging` removed from git tracking
- Hardcoded dev credential removed from `seed_graph.py`

---

## [1.1.0] - 2026-07-12

### Added

- Entity Resolution pipeline (pg_trgm matching + merge flow)
- Hybrid Search (full-text + semantic, RRF fusion)
- Feature Store (20 tests, REST API, ScoringEngine wiring)
- Knowledge Graph integration (entity resolution → KG merge)
- Search PostgreSQL repository (VIO-103 closed)
- DecisionProvider → Dashboard + Company (VIO-105 closed)
- 119 new tests (AI 92%, Search 93%, Workflow 95% coverage)
- Pilot launch (3 tenants, monitoring, feedback)
- GA Launch Plan (`docs/GA_LAUNCH_PLAN.md`)

### Fixed

- TD-001: 7 InMemory repos migrated to PostgreSQL
- BUG-001: Search timeout (tsvector index, timeout guard)
- BUG-003: Neo4j connection leak (context managers everywhere)
- 57 RBAC argument-reversed calls
- CSRF protection middleware

---

## [1.0.0] - 2026-07-08

### Added

- Initial GA release
- Identity domain (JWT auth, RBAC, multi-tenant)
- Company Intelligence domain
- NBA Decision Platform
- Dashboard with Widget SDK v1.0
- AI Agents Engine
- Timeline and Activity tracking
- Workflow Automation
- Employee Intelligence
- Customer Success
- Monitoring system (Prometheus + Grafana)
- Docker Compose production setup
- CI/CD pipeline (GitHub Actions)

---

## [0.5.0] - 2026-07-12

### Summary

Production stabilization sprint. Completed 57 RBAC fixes, CSRF protection, search timeout resolution, pilot tenant provisioning, and migrated all remaining InMemory repositories to PostgreSQL. Test coverage increased from 74% to 93%.

---

## [0.4.0] - 2026-07-10

### Summary

Sprint 6 — GA Security Hardening. Added auth to all 9 runtime routers, implemented tiered rate limiting, hardened `.gitignore`, removed tracked secrets, updated all frontend dependencies, and published comprehensive documentation (admin, deployment, runbook, user guides + 26-file API portal).

---

## [0.3.0] - 2026-07-08

### Summary

Sprint 5 — Production Migration. Pilot launch with 3 tenants. Entity Resolution pipeline, Hybrid Search with RRF fusion, Feature Store, Knowledge Graph integration, and Search PostgreSQL repository all delivered.

---

## [0.2.0] - 2026-07-08

### Summary

Sprint 3 — Hardening & Coverage. Added monitoring and customer success domains, improved test coverage to 74% overall, fixed 14 `any` types, and completed pilot preparation guides.

---

## [0.1.0] - 2026-07-07

### Summary

Sprint 2 — Foundation Complete. Completed Decision Platform (ScoringEngine, DecisionProvider), AI Agents Engine, Timeline domain, Workflow domain with Container/View pattern, and Employee Intelligence. Architecture compliance reached 95% across all 9 domains.

---

## [0.0.2] - 2026-07-06

### Summary

Sprint 1 — Design System & UI Foundation. Delivered 22 foundation components, 15 restyled UI kit files, Tailwind theme with MUHIDE palette, global CSS with dark mode and RTL, font system (Viga + IBM Plex), and 340+ hardcoded color violations remediated.

---

## [0.0.1] - 2026-07-05

### Summary

Initial development setup. Project scaffolding, domain model design, and core infrastructure (FastAPI application shell, PostgreSQL schema, Neo4j graph setup, CI/CD pipeline).
