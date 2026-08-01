---
EngineeringOS: v3
GeneratedAt: 2026-08-01T12:11:50Z
RepositoryCommit: c89025a
RepositoryBranch: master
Generator: OpenCode
Status: Corrected (EOS v3.1 cycle)
EvidenceLevel: Heuristic
Revalidation: Pending
---

# 05 â€” FILE CATALOG

> Catalog of every important file in the repository (no artificial cap). Rows: path Â· purpose Â· type Â· module Â· role (runtime/CI/deploy) Â· owner Â· AI-modifiable Â· priority. Locked paths marked **ðŸ”’** (see `22_FILE_LOCKS.json`).

## 1. Root

| Path | Purpose | Owner | AI-mod | Prio |
|---|---|---|---|---|
| `AGENTS.md` | agent operating instructions (ðŸ”’) | Human | No | P0 |
| `README.md` | repo readme | Human | No | P0 |
| `PRODUCT_BIBLE.md` | SalesOS bible (product scope) | Human | No | P0 |
| `RUNBOOK.md` | runbook | Human | No | P1 |
| `SALESOS_PRODUCTION_READINESS_AUDIT_*.md` | readiness audit (SUPERSEDED by ga-audit) | Human | No | P2 |
| `GO_NO_GO_DECISION.md` | SUPERSEDED GO claim | Human | No | P2 |
| `GA_CHECKLIST.md` | SUPERSEDED GO claim | Human | No | P2 |
| `docker-compose.yml` | root dev compose | Ops | Yes | P1 |
| `Dockerfile.railway`, `railway.json` | railway deploy | Ops | Yes | P1 |
| `scripts/backup.sh` | backup | Ops | Yes | P2 |

## 2. Backend â€” core

| Path | Purpose | Role | Owner | AI-mod | Prio |
|---|---|---|---|---|---|
| `salesos/backend/app/main.py` | app factory, health routes | runtime | Backend/Cursor | Yes (gated) | P0 |
| `salesos/backend/app/boot/routers.py` | 67 include_router | runtime | Backend/Cursor | Yes (gated) | P0 |
| `salesos/backend/app/boot/startup.py` | startup hooks | runtime | Backend/Cursor | Yes (gated) | P0 |
| `salesos/backend/app/boot/security_headers.py` | security headers middleware | runtime | Backend/Cursor | Yes (gated) | P0 |
| `salesos/backend/app/config.py` | settings; `feature_ai_copilot=False` | runtime | Backend/Cursor | Yes (gated) | P0 |
| `salesos/backend/app/database.py` | engine/session helpers | runtime | Backend/Cursor | Yes (gated) | P0 |
| `salesos/backend/app/dependencies.py` | shared deps | runtime | Backend/Cursor | Yes (gated) | P0 |
| `salesos/backend/app/celery_app.py` | Celery `-A app.celery_app`, beat (9 jobs) | runtime | Backend/Cursor | Yes (gated) | P1 |
| `salesos/backend/app/health.py` | health checks | runtime | Backend/Cursor | Yes | P1 |
| `salesos/backend/pyproject.toml` | Poetry manifest | build | Backend/Cursor | Yes (gated) | P0 |
| `salesos/backend/alembic.ini` | Alembic config | build | Backend/Cursor | Yes (gated) | P0 |
| `salesos/backend/Dockerfile` / `Dockerfile.backend` | image build | deploy | Ops | Yes (gated) | P0 |
| `salesos/backend/docker-entrypoint.sh` | container entry (DB check) | deploy | Ops | Yes (gated) | P0 |
| `salesos/backend/.env` | **ðŸ”’ SECRETS** | runtime | Ops | No | P0 |
| `salesos/backend/.env.production.template` | template | build | Backend/Cursor | Yes | P1 |

## 3. Backend â€” modules & routers

| Path | Purpose | Owner | AI-mod | Prio |
|---|---|---|---|---|
| `app/modules/identity/routes.py` | IAM endpoints (12) | Backend/Cursor | Yes (gated) | P0 |
| `app/modules/identity/jwks.py` | RS256 JWKS | Backend/Cursor | Yes (gated) | P0 |
| `app/modules/identity/_keys/rsa_private.pem` | **ðŸ”’ private key** | Ops | No | P0 |
| `app/modules/identity/_keys/rsa_public.pem` | **ðŸ”’ public key** | Ops | No | P0 |
| `app/modules/company/` | company CRUD | Backend/Cursor | Yes | P1 |
| `app/modules/contact/` | contact CRUD | Backend/Cursor | Yes | P1 |
| `app/modules/revenue_execution/` | revenue exec | Backend/Cursor | Yes | P1 |
| `app/modules/entity_resolution/` | ER module | Backend/Cursor | Yes | P1 |
| `app/modules/decision/` | decision center | Backend/Cursor | Yes | P1 |
| `app/routers/search.py` | search API | Backend/Cursor | Yes | P1 |
| `app/routers/opportunities.py` | opportunity API | Backend/Cursor | Yes | P1 |
| `app/routers/workflows.py` | workflow API | Backend/Cursor | Yes | P1 |
| `app/routers/analytics.py` | analytics API | Backend/Cursor | Yes | P1 |
| `app/routers/ai.py`, `app/routers/copilot.py` | AI/copilot APIs | Backend/Cursor | Yes | P1 |
| `app/routers/mcp.py` | MCP server | Backend/Cursor | Yes | P1 |
| `app/routers/source_of_truth.py` | SOT + capabilities | Backend/Cursor | Yes | P1 |
| `app/graphql/schema.py` | GraphQL schema | Backend/Cursor | Yes | P2 |
| `app/application/admin/data_quality.py` | **SQLi sink (SEC finding)** | Backend/Cursor | Yes (gated) | P0 |
| `app/modules/revenue_execution/service.py` | **SQLi sink (SEC finding)** | Backend/Cursor | Yes (gated) | P0 |

## 4. Backend â€” domains (17 under domains/ + app/domains/customer_success)

| Path | Purpose | Owner | AI-mod | Prio |
|---|---|---|---|---|
| `domains/search/` | search domain | Backend/Cursor | Yes | P1 |
| `domains/commercial/` (+`pipeline/`) | opportunities/pipeline | Backend/Cursor | Yes | P1 |
| `domains/revenue/` (+`forecast/`) | revenue/forecast | Backend/Cursor | Yes | P1 |
| `domains/analytics/` | analytics/KPIs | Backend/Cursor | Yes | P1 |
| `domains/decision/`, `domains/decision_center/` | decision logic | Backend/Cursor | Yes | P1 |
| `domains/ai/` | AI domain | Backend/Cursor | Yes | P1 |
| `domains/scoring/` | scoring | Backend/Cursor | Yes | P1 |
| `domains/timeline/` | timeline | Backend/Cursor | Yes | P1 |
| `domains/data_fabric/` | data fabric | Backend/Cursor | Yes | P2 |
| `domains/feature_store/` | feature store | Backend/Cursor | Yes | P2 |

## 5. Backend â€” runtime (27 engine dirs; 10 single-file dirs, stub status not individually proven)

| Path | Status | Purpose | Owner | AI-mod | Prio |
|---|---|---|---|---|---|
| `runtime/search_runtime/` | real | search engine | Backend/Cursor | Yes | P0 |
| `runtime/timeline_runtime/` | real | timeline | Backend/Cursor | Yes | P1 |
| `runtime/knowledge_graph_runtime/` | real (Neo4j) | kgraph | Backend/Cursor | Yes | P1 |
| `runtime/data_fabric_runtime/` | real | data fabric | Backend/Cursor | Yes | P2 |
| `runtime/feature_store_runtime/` | real | feature store | Backend/Cursor | Yes | P2 |
| `runtime/decision_runtime/` | real | decision engine | Backend/Cursor | Yes | P1 |
| `runtime/nba_engine/` | real | next-best-action | Backend/Cursor | Yes | P2 |
| `runtime/pipeline_analytics/` | real | pipeline analytics | Backend/Cursor | Yes | P1 |
| `runtime/capability_framework/` | real | decorator registry | Backend/Cursor | Yes | P0 |
| `runtime/workflow_runtime/` | **stub** | workflow engine | Backend/Cursor | Yes | P1 |
| `runtime/agent_runtime/` | **stub (1-line)** | agent runtime | Backend/Cursor | Yes | P2 |
| `runtime/simulation_runtime/` | **stub** | simulation | Backend/Cursor | Yes | P2 |
| `runtime/ux_runtime/` | real | UX | Backend/Cursor | Yes | P2 |
| `runtime/ui_schema_engine/` | real | UI schema | Backend/Cursor | Yes | P2 |
| `runtime/widget_engine/` | real | widget registry | Backend/Cursor | Yes | P1 |
| `runtime/object_viewer.py` | real | object viewer | Backend/Cursor | Yes | P2 |

## 6. Backend â€” SDK & intelligence & scripts

| Path | Purpose | Owner | AI-mod | Prio |
|---|---|---|---|---|
| `sdk/capability_registry.py` | ~25 SDK capabilities | Backend/Cursor | Yes (gated) | P0 |
| `sdk/events/` | AuditEvent + domain events | Backend/Cursor | Yes | P0 |
| `sdk/telemetry/` | telemetry | Backend/Cursor | Yes | P1 |
| `intelligence/providers/` | AI providers | Backend/Cursor | Yes | P1 |
| `intelligence/data_fabric/` | fabric logic | Backend/Cursor | Yes | P2 |
| `scripts/arch-compliance.py` | 5 arch rules | Backend/Cursor | Yes | P1 |
| `scripts/check-coverage.py` | coverage gate | Backend/Cursor | Yes | P1 |
| `scripts/generate_rls_policies.py` | RLS gen (55 policies) | Backend/Cursor | Yes | P1 |
| `scripts/sync_capability_registries.py` | registry sync | Backend/Cursor | Yes | P2 |
| `scripts/validate_capability_registries.py` | registry drift check | Backend/Cursor | Yes | P2 |
| `scripts/lint.sh` / `update_env_template.sh` / `generate_api_docs.sh` | maintenance | Backend/Cursor | Yes | P2 |

## 7. Backend â€” tests (220 files via git ls-files test_*.py / *_test.py; method-dependent, sample of pillars)

| Path | Purpose | Owner | AI-mod | Prio |
|---|---|---|---|---|
| `tests/test_architecture.py` | 5 arch rules (SDK-import, kernel-commercial) | Backend/Cursor | Yes | P0 |
| `tests/test_integration.py` | API integration | Backend/Cursor | Yes | P1 |
| `tests/conftest.py` | fixtures | Backend/Cursor | Yes | P1 |
| `tests/unit/` (sample) | unit pillar | Backend/Cursor | Yes | P1 |
| `tests/contract/` | contract pillar | Backend/Cursor | Yes | P1 |
| `tests/e2e/` | backend e2e | Backend/Cursor | Yes | P2 |
| `tests/evaluation/` | eval harness | Backend/Cursor | Yes | P2 |
| `tests/support/` | fixtures incl. mock keypair | Backend/Cursor | Yes | P2 |

## 8. Frontend â€” core & config

| Path | Purpose | Owner | AI-mod | Prio |
|---|---|---|---|---|
| `frontend/src/app/layout.tsx` | root layout | Claude | Yes | P0 |
| `frontend/src/middleware.ts` | route protection | Claude | Yes (gated) | P0 |
| `frontend/src/lib/api/client.ts` | API client (browser token injection) | Claude | Yes (gated) | P0 |
| `frontend/src/lib/auth/` | auth utils | Claude | Yes | P0 |
| `frontend/src/application/` | app wiring | Claude | Yes | P1 |
| `frontend/src/components/` | shared UI | Claude | Yes | P1 |
| `frontend/next.config.js` | build config | Claude | Yes (gated) | P0 |
| `frontend/tailwind.config.ts` | styling | Claude | Yes | P1 |
| `frontend/tsconfig.json` | TS config | Claude | Yes | P0 |
| `frontend/jest.config.js` | unit config | Claude | Yes | P1 |
| `frontend/playwright.config.ts` | e2e config | Claude | Yes | P1 |
| `frontend/vercel.json` | vercel routing | Claude | Yes | P1 |
| `frontend/Dockerfile*`, `nginx.conf` | FE container | Ops | Yes | P1 |
| `frontend/server/server.js` | mock server, permissive CORS (review) | Shared | Yes (with approval) | P2 |
| `frontend/.env.local` | **ðŸ”’ SECRETS** | Ops | No | P0 |

## 9. Frontend â€” features (13)

| Path | Purpose | Owner | AI-mod | Prio |
|---|---|---|---|---|
| `features/company-intelligence/` | CI feature incl. company-360 widgets | Claude | Yes | P1 |
| `features/customer-success/` | CS feature | Claude | Yes | P1 |
| `features/ai-copilot-v3/` | copilot UI | Claude | Yes | P2 |
| `features/decision/` | decision UI | Claude | Yes | P2 |
| `features/opportunities/`, `forecast/`, `analytics/`, `pipeline/`, `search/`, `auth/`, `dashboard/`, `workflows/`, `settings/` | feature modules | Claude | Yes | P1 |

## 10. Frontend â€” packages (21)

| Path | Status | Owner | AI-mod | Prio |
|---|---|---|---|---|
| `packages/platform/decision/index.ts` | **STUB (throws)** | Shared | Yes | P2 |
| `packages/widget-sdk/`, `workspace/`, `search/`, `renderer/` | production | Shared | Yes | P1 |
| `packages/platform/` (kernel+contracts) | contract shell | Shared | Yes | P1 |
| `packages/design-system/`, `charts-v3/`, `layouts/`, `providers/`, `theme/`, `tokens/`, `widgets/`, `workspace-generator/`, `platform/decision/` | stub/empty (no imports) | Shared | Yes | P2 |
| `apps/` (4) | EMPTY shells | Shared | Yes | P2 |

## 11. CI/CD, infra, deploy

| Path | Purpose | Owner | AI-mod | Prio |
|---|---|---|---|---|
| `.github/workflows/ci.yml` | main CI | Ops | Yes (gated) | P0 |
| `.github/workflows/security-scan.yml` | gitleaks + SAST | Ops | Yes (gated) | P0 |
| `.github/workflows/docker-smoke.yml` | docker smoke | Ops | Yes (gated) | P1 |
| `.github/workflows/deploy.yml` | deploy (undeclared outputs `slot`, `image_tag` â€” SEC finding) | Ops | Yes (gated) | P0 |
| `.github/workflows/deploy-staging.yml`, `deploy-production.yml` | stage/prod deploy | Ops | Yes (gated) | P1 |
| `.github/dependabot.yml` | dep updates | Ops | Yes | P2 |
| `salesos/infra/k8s/` (37) | K8s manifests | Ops | Yes (gated) | P1 |
| `salesos/infra/terraform/` (3) | IaC | Ops | Yes (gated) | P1 |
| `salesos/infra/monitoring/` (21) | Prometheus/Grafana; `prometheus-token` ðŸ”’ | Ops | Yes (gated) | P2 |
| `salesos/infra/staging/` | staging stack | Ops | Yes (gated) | P2 |
| `salesos/infra/docker/`, `infra/caddy/` | compose/reverse proxy | Ops | Yes (gated) | P2 |
| `salesos/docker-compose*.yml` (7) | compose stacks | Ops | Yes (gated) | P0 |
| `salesos/scripts/` | deploy/smoke/backup/pilot/security/staging-virtual | Ops | Yes (gated) | P1 |
| `salesos/railway.json`, `Makefile` | railway/make | Ops | Yes | P1 |

## 12. Docs (governance; ðŸ”’ all)

| Path | Purpose | Owner | AI-mod | Prio |
|---|---|---|---|---|
| `docs/audit/ga-engineering-audit/00-EXECUTIVE-SUMMARY.md` | canonical NO-GO | Human | No | P0 |
| `docs/audit/ga-engineering-audit/GA_STATUS.md` | GA status | Human | No | P0 |
| `docs/audit/ga-engineering-audit/PRODUCTION_PLAN.md` | Waves 0â€“14 | Human | No | P0 |
| `docs/audit/ga-engineering-audit/AI_HONESTY.md` | AI honesty | Human | No | P0 |
| `docs/adr/` (6 tracked) | ADR-030..035 + index | Human | No | P1 |
| `docs/ADR-Data-001-identity-resolution-v3.md` | identity ADR | Human | No | P1 |
| `docs/CAPABILITY_CATALOG.md` | 40 capabilities | Human | No | P1 |
| `docs/vnext/DECISIONS.md` | D-001..016 | Human | No | P1 |
| `docs/vnext/TECHNICAL_DEBT.md` | tech debt registry | Human | No | P1 |
| `docs/vnext/WORK_ORDERS/` | WO-* | Human | No | P2 |
| `docs/program/decisions/` | DEC-* (e.g. DEC-107) | Human | No | P1 |
| `docs/ops/` | runbooks, SLOs, secrets hygiene | Human | No | P1 |
| `engineering-os/adr/` (6) | submodule ADRs | Human | No | P0 |
| `engineering-os/kernel/capability-registry.yaml` | governance registry (DIRTY) | Human | No | P0 |
| `engineering-os/ENGINEERING_CONSTITUTION.md` | submodule constitution | Human | No | P0 |

## 13. Data & legacy

| Path | Purpose | Owner | AI-mod | Prio |
|---|---|---|---|---|
| `data/scripts/phase4_identity_v4.py` | identity import | Data team | Yes | P2 |
| `data/scripts/phase3_normalize.py` | normalize | Data team | Yes | P2 |
| `balady_scraper/`, `taqeem_scraper/`, `najiz_scraper/`, `rega_scraper/` | scrapers | Data team | Yes | P2 |
| `sales-os/` | LEGACY | â€” | No (prefer salesos/) | P2 |

## 14. How to use this catalog

1. Find your file by section; read `Owner` + `AI-mod` before editing.
2. `AI-mod = No` â†’ never touch (governance/secrets).
3. `P0` files are blast-radius-critical: any change requires approval + evidence + test.
4. Cross-ref: `03` (map), `04` (directories), `24` (JSON manifest), `22` (locks).
