# Progress — Waves 4, 8, 9 (Infra / Observability / Secrets)

**Date:** 2026-07-22  
**Owner scope:** config/code only — no production deploy, no real `.env` secrets committed  
**Product:** SalesOS platform  
**Validation class:** **light validated** (compose `config` parse) — **not** runtime-proven health matrix

---

## Summary

| Wave | IDs | Outcome |
|------|-----|---------|
| **4** Runtime/infra | PROD-W4-001…004 | Compose healthchecks + env wiring + FE image notes; Kafka documented as optional/degraded |
| **8** Observability | PROD-W8-001…002 | Loki/OTel wired in root compose; salesos profile `observability`; SLO/alert skeleton docs |
| **9** Secrets | PROD-W9-001…002 | Hardcoded scrape JWT removed; env refs; gitleaks/trivy stubs; hygiene checklist |

---

## Compose / infra changes

### Root `docker-compose.yml`
- Secrets → `${VAR:-dev_default}` (dev-only defaults preserved for local DX)
- Neo4j healthcheck → HTTP `wget` probe + `start_period: 45s` (avoids cypher-shell password subst flakiness)
- Postgres/Redis healthchecks → longer interval + `start_period`
- `api` / `worker` wait for `neo4j` **healthy**; wire `REDIS_URL`, `EVENT_BUS_TYPE`, `NEO4J_*`, OTel endpoint
- Optional Kafka via `--profile kafka`
- Frontend service under `--profile frontend` with `BUILD_ID` / `IMAGE_TAG` (no long rebuild executed)
- Prometheus uses `prometheus.compose-root.yml` targeting **`api:8000`** (was wrongly `backend`)
- OTel uses `otel-collector-config.local.yaml` (no external tracing vendor)
- Loki + Promtail + Grafana Loki datasource included

### `salesos/docker-compose.yml`
- Same Neo4j HTTP healthcheck + Kafka healthcheck
- Backend depends on neo4j/kafka **healthy**; explicit Redis/Neo4j/event-bus env
- FE build args + `image: salesos-frontend:${IMAGE_TAG:-local}`
- Profile `observability`: loki, otel-collector, promtail
- Prometheus mounts `prometheus-token.example` (no real JWT in git)

### Staging
- `salesos/infra/staging/docker-compose.staging.yml` Neo4j healthcheck aligned to HTTP probe

### Backend health accuracy (minimal)
- `app/main.py` — graph/kafka statuses: `unavailable` / `in_memory` vs misleading `not_configured`
- `modules/monitoring/router.py` — cache check uses `app.state.cache` (was wrongly `event_runtime`)

---

## Observability (Wave 8)

| Artifact | Role |
|----------|------|
| `salesos/infra/monitoring/prometheus.compose-root.yml` | Root scrape config |
| `salesos/infra/monitoring/otel-collector-config.local.yaml` | Local OTel (debug + Loki + Prometheus exporter) |
| `salesos/infra/monitoring/grafana/datasources/prometheus.yml` | Prometheus + Loki datasources |
| `docs/ops/SLO_ALERTS.md` | SLI/SLO/alert skeleton |
| `docs/ops/RUNTIME_STACK.md` | Canonical stack + enablement matrix |
| Existing `alerts.yml` / Alertmanager | Unchanged rules; documented |

**Cloud vendors:** not required.

---

## Secrets hygiene (Wave 9)

| Change | Detail |
|--------|--------|
| Removed | Committed JWT in `prometheus-token` |
| Added | `prometheus-token.example`, gitignore for real `prometheus-token` |
| Added | `.gitleaks.toml`, `salesos/.gitleaks.toml`, `.trivyignore` |
| CI | `security-scan.yml` — forbid committed prometheus-token + gitleaks step (`continue-on-error`) |
| Docs | `docs/ops/SECRETS_HYGIENE.md` |
| Compose | `frontend/docker-compose.yml` requires `JWT_SECRET` / `PG_PASSWORD` (no fake prod default) |
| Examples | Root + `salesos/.env.example` — `EVENT_BUS_TYPE`, OTel, longer JWT placeholders |

---

## Verified running vs config-only

| Check | Result |
|-------|--------|
| `docker compose config` (root) | **Pass** (parse) |
| `docker compose config` (salesos, with `POSTGRES_PASSWORD` set) | **Attempted** — treat as config-only if env incomplete |
| Stack `up` + `/health/detailed` | **Not run** (low-load; no approval for long bring-up) |
| FE image rebuild | **Not run** (documented only; Wave 0 build is separate) |
| Scanner full run (pip-audit/trivy) | **Not run** — stubs + workflow wiring only |
| Live SLIs 72h | **Needs verify** (Wave 11) |

---

## Residual gaps

1. **FE route parity** — still needs approved image rebuild after Wave 0 green (PROD-W4-001).
2. **`/metrics` scrape auth** — still JWT-gated (PROD-W5-004); local Prometheus may 401 until scrape token or Wave 5.
3. **Kafka for GA** — product sign-off that `in_memory` is acceptable degraded (documented).
4. **Neo4j healthy end-to-end** — config fixed; runtime proof needs `docker compose up` + `/health/dependencies`.
5. **Postgres flapping on Docker Desktop** — mitigated with `start_period`; Linux staging verify pending (PROD-W4-004).
6. **Alertmanager receivers** — still need real webhooks/SMTP for staging (env only).
7. **Gitleaks CI** — `continue-on-error: true` until org token/policy confirmed.
8. **Real secret rotation** in GH Environments / K8s — checklist only (human T-0).

---

## Files touched (primary)

- `docker-compose.yml`
- `salesos/docker-compose.yml`, `salesos/frontend/docker-compose.yml`
- `salesos/infra/staging/docker-compose.staging.yml`
- `salesos/backend/app/main.py`, `salesos/backend/app/modules/monitoring/router.py`
- `salesos/infra/monitoring/*` (prometheus compose-root, otel local, datasources, README, token example)
- `.env.example`, `salesos/.env.example`
- `.gitleaks.toml`, `salesos/.gitleaks.toml`, `.trivyignore`, `salesos/.gitignore`
- `salesos/.github/workflows/security-scan.yml`
- `docs/ops/RUNTIME_STACK.md`, `SLO_ALERTS.md`, `SECRETS_HYGIENE.md`
- `docs/audit/ga-engineering-audit/PROGRESS-WAVE4-8-9-INFRA.md` (this file)

**Honest label:** config delivered; **production no-go unchanged** until runtime evidence + later waves.
