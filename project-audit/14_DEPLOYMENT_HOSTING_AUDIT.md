# 14 — Deployment & Hosting Audit

**Scope:** where and how SalesOS runs, from static config only. **Live services NOT probed this audit.**

---

## 1. Hosting matrix (evidence-based)

| Layer | Provider | Region | Config source | Live status |
|-------|----------|--------|---------------|-------------|
| Backend API | Railway | US | `Dockerfile.railway`, `railway.json` | UNKNOWN this audit (last verified `/health` in AGENTS.md §32 = OK) |
| Backend Celery Worker | Railway | US | `Dockerfile.railway.celery`, `railway.worker.json` | UNKNOWN |
| Backend Celery Beat | Railway | US | `railway.beat.json` | UNKNOWN |
| Frontend | Vercel | `iad1` (US East) | `salesos/frontend/vercel.json` | UNKNOWN |
| PostgreSQL primary | Railway managed | US | Env vars | Prod schema `g1h2i3j4k5l6` (2026-08-21 per FINAL_GO_NOGO); LIVE state UNKNOWN |
| Redis | Railway managed | US | Env vars | Ephemeral only per Governance Reconciliation |
| Neo4j | Railway managed | US | Env vars | **OFFLINE per ADR-108** but deployed (governance gap `NEO4J_GOVERNANCE_GAP.md`) |
| Kafka | not required | — | `event_bus_type=in_memory` default | Not part of critical path |
| Object storage | UNKNOWN | — | Not configured in current audit read | UNKNOWN |
| Meilisearch | optional | — | `meili_url` in config; not core | UNKNOWN |
| Sentry | not configured | — | `sentry_dsn=""` default | Empty |
| CDN | Vercel | iad1 | Vercel default | Live |
| DNS / SSL | Railway + Vercel subdomains | — | Not custom-domain evidence | UNKNOWN |
| WAF / Firewall | Not evidenced | — | — | UNKNOWN |

**Non-KSA hosting:** Railway (US) + Vercel (US East). This is a **blocker for KSA Enterprise sales** requiring PDPL data residency. Enterprise tier will need VPC-in-KSA (K8s manifests exist under `salesos/infra/k8s/` but quarantined per DEC-149).

---

## 2. Railway service configs

### 2.1 `railway.json` (main API)

- Builder: DOCKERFILE
- Dockerfile: `Dockerfile.railway`
- Start command: dispatches by `RAILWAY_SERVICE_NAME` — cases: `*celery-worker*`, `*celery-beat*`, default `uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}`
- Healthcheck: `/health`
- Restart policy: ON_FAILURE, max 3 retries
- **preDeployCommand:** NOT set in `railway.json` on disk (should be `alembic upgrade head` per FINAL_GO_NOGO recommendation; live Railway is set to `init_db()` — drift)

### 2.2 `railway.worker.json` / `railway.beat.json`

Present. Purposes = Celery worker + Celery beat service definitions. Not audited in detail this session.

---

## 3. Vercel `vercel.json`

- Framework: `nextjs`
- Install: `npm install`
- Build: sets `NEXT_PUBLIC_BUILD_COMMIT / DATE / ID` from `VERCEL_GIT_COMMIT_SHA` — enables build parity checks per FINAL_GO_NOGO §Build provenance
- Regions: `["iad1"]`
- Headers (applied `/(*)`):
  - `X-Content-Type-Options: nosniff`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `X-Frame-Options: DENY`
  - `Permissions-Policy: camera=(), microphone=(), geolocation=()`

**Missing (from vercel.json):**
- CSP (relies on Next.js runtime CSP per ADR-102 — verified in code, not vercel.json)
- HSTS (Vercel default OK)
- Explicit rewrite rules for backend proxy (relies on Next.js `next.config.js`)

---

## 4. Docker

### 4.1 Root `docker-compose.yml`

11 KB — "lighter local/dev-only profile" per README. Includes root-level Loki/OTel per audit history (00-EXECUTIVE-SUMMARY notes).

### 4.2 `salesos/docker-compose.yml`

Staging/prod-shaped stack: Postgres + Redis + Neo4j + Kafka + backend + frontend + supporting. This is the canonical local-dev setup for `npm run/pytest` in Docker.

### 4.3 `salesos/docker-compose.prod.yml` + `salesos/docker-compose.test.yml`

Production-shaped + test-shaped variants.

### 4.4 `salesos/docker-compose.windows.yml`

Windows-specific dev overrides.

### 4.5 `salesos/infra/docker/backup/Dockerfile`

Backup service (Postgres + Neo4j backup scripts). COPY paths fixed per Phase 4 P4-6 (was `scripts/`, corrected to `infra/scripts/`).

---

## 5. CI/CD pipelines

### 5.1 `.github/workflows/`

| Workflow | Purpose |
|----------|---------|
| `ci.yml` (39 KB) | Main CI: lint, tsc, unit, integration |
| `deploy.yml` (28 KB) | Production deploy |
| `deploy-production.yml` (11 KB) | Production deploy variant |
| `deploy-staging.yml` (11 KB) | Staging deploy |
| `docker-smoke.yml` | Docker image smoke |
| `e2e-stage7.yml` | E2E for STAGE 7 |
| `fitness-ci-subset.yml` | Fitness gates (FF-07 / AIGOV / etc.) per AI_HONESTY §8 |
| `release-gates.yml` | Release gates |
| `security-scan.yml` | Trivy/semgrep/gitleaks |

**Recent fixes:**
- Schema-drift-gate uses `--local-only` flag (no Railway CLI from GHA runners) — commit `6f27699`
- Removed Railway CLI dep from staging deploy — commit chain in FINAL_GO_NOGO §10

**Fitness CI subset per AI_HONESTY.md §8:** FF-07/AIGOV + light FF-14 + FF-DUP-01 — verifies AI honesty invariants; `salesos/scripts/fitness-ci-subset.sh`.

---

## 6. Deploy path (from code + FINAL_GO_NOGO)

```
1. Push to GitHub → GitHub Actions triggers
2. CI runs: lint + tsc + unit tests + integration + schema-drift (local-only)
3. On success, deploy-production / deploy-staging invokes `railway up --ci -y`
4. Railway builds Dockerfile.railway
5. Railway spins up new service revision
6. preDeployCommand runs (drift: `init_db()` on live vs `alembic upgrade head` in `railway.json`)
7. Health check `/health` polled
8. If healthy → traffic shift
9. `/api/v1/version` verifiable — returns `schema_version` + `build_commit`
10. Vercel deploys frontend on same commit push (webhook)
```

**Rollback:**
- Manual script `scripts/railway_rollback.sh` with dry-run + confirmation (created 2026-08-21)
- Railway history-based rollback via CLI or dashboard

**Observability during deploy:**
- Health check pass
- Alembic version match check
- Schema drift boot warning if DB stamp != repo head

---

## 7. Environments

| Env | URL (per README + AGENTS.md) | Status | Notes |
|-----|------------------------------|--------|-------|
| Local dev | `docker compose up` from `salesos/` | Manual | Preferred (staging-shaped) |
| Staging | `salesos-staging.up.railway.app` | Live per 2026-08-21 deploy 32482172944 | schema `g1h2i3j4k5l6` |
| Production | `salesos-production-96c0.up.railway.app` | Live per FINAL_GO_NOGO | schema `g1h2i3j4k5l6` |
| OAuth staging | Google Cloud Console app | **BLOCKED — human action** | Per FINAL_GO_NOGO §4 |

---

## 8. Backup / DR posture

- **pg_dump + Neo4j backup scripts:** functional (`salesos/infra/scripts/*`)
- **DR drill:** simulated non-prod per Phase 4 P4-6
- **RPO/RTO:** RPO < 1h, RTO < 4h per DR_RUNBOOK.md §1 + OPS-01 row 8 ACCEPTED 2026-08-24
- **Railway managed backup schedule:** **NOT ENABLED** (row 3b BLOCKED-HUMAN)
- **Offsite backup:** Not evidenced in this audit
- **Test restore drill:** simulated only, no evidence of real production restore

**This is the single biggest infrastructure risk today.** No live paying customer should be onboarded before backup schedule is enabled.

---

## 9. Secrets management

- Env vars via Railway dashboard (backend + celery-worker + celery-beat services)
- Vercel env vars (frontend)
- `.env.example` template at both root and `salesos/`
- `.env.local`, `.env.staging`, `.env.production*` files present locally — expected to be `.gitignored`
- Owner-role vs App-role passwords separately configured
- Fernet key for OAuth tokens (`google_encryption_key`) + rotation (`google_encryption_key_previous`)
- Stripe live keys empty by default; production not yet activated
- No HashiCorp Vault / cloud KMS integration evidenced

---

## 10. Networking + edge

- Railway subdomains + Vercel subdomains — no evidence of custom domain
- TLS: managed by Railway + Vercel (LetsEncrypt)
- CSP: per Next.js config (ADR-102) — verified in Next.js code
- CORS: env-configurable (`ALLOWED_HOSTS`) + auto-merge from `EXTRA_CORS_ORIGINS`
- Rate limits enforced in-app (Redis-backed)
- Body size limit: 10 MB (in-app)

**Missing:** WAF (Cloudflare / Vercel Firewall), DDoS mitigation beyond Railway/Vercel defaults, TLS mutual auth.

---

## 11. Compliance-adjacent hosting facts

| Concern | State |
|---------|-------|
| Data residency (PDPL Art. 29 — cross-border transfer) | **NON-COMPLIANT for KSA Enterprise** — Railway US + Vercel iad1 US |
| Encryption in transit | TLS 1.2+ managed by Railway/Vercel |
| Encryption at rest | Postgres managed encryption + Fernet on OAuth tokens; app-level encryption for other PII: UNKNOWN this audit |
| Backup encryption | UNKNOWN |
| Audit log retention | 90 days default (`audit_retention_days`) |
| DPO named | NOT evidenced |
| Sub-processor list | NOT evidenced |
| Incident response runbook | `RUNBOOK.md` present; formal IR playbook UNKNOWN |
| Business continuity plan | `docs/ops/DR_RUNBOOK.md` present |

---

## 12. Cost model (from public pricing benchmarks + config observation)

**Not verified via billing invoices** — RECOMMENDATION-labeled.

Estimated monthly at pilot scale (1–3 tenants):
- Railway (backend + workers + Postgres + Redis + Neo4j): USD 500–1,500
- Vercel (FE + traffic): USD 100–400
- LLM provider (post-signing, e.g., OpenAI Enterprise / Azure OpenAI): USD 300–3,000
- Sentry (when activated): USD 100–300
- Domain + email: USD 30–50
- **Total:** USD 1,030–5,250/month ≈ SAR 46k–236k/year

At 10 tenants: roughly 2×–3× the above.

---

## 13. Recommended deployment actions (priority-ordered)

1. **P0** — Enable Railway managed backup schedule (row 3b)
2. **P0** — Sign production LLM contract + provision secret
3. **P0** — Set up OAuth staging + production in Google Cloud Console
4. **P0** — Align live `preDeployCommand` with `railway.json` (or vice versa) to close drift
5. **P1** — Provision Stripe live keys after pricing signed
6. **P1** — Provision Sentry DSN + enable live error stream
7. **P1** — Set up public status page (Betterstack / statuspage.io / self-hosted on Vercel)
8. **P1** — Enable Vercel Firewall / basic bot protection
9. **P2** — Custom domain (aqliya.sa or salesos.io etc.) with proper TLS
10. **P2** — Explore KSA-hosted Postgres for Enterprise-tier residency (Neom Tech, Amazon me-south-1)
11. **P2** — Un-quarantine K8s manifests + Terraform for Enterprise VPC (post-Enterprise-sale)
12. **P3** — Add Loki / OTel to salesos production compose profile (currently in root docker-compose)
13. **P3** — Add multi-region DR (post-Enterprise-scale)

---

*Deployment audit — read-only, config-based. Live probes recommended in a follow-up audit.*
