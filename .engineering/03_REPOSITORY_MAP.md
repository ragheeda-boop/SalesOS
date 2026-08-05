---
EngineeringOS: v3
GeneratedAt: 2026-08-05
RepositoryCommit: 54daec3
RepositoryBranch: master
Generator: OpenCode
Status: Corrected (repository restructure Phases 01-12)
EvidenceLevel: Measured
Revalidation: Active (DEC-142)
---

# 03 — REPOSITORY MAP

> Topographic map of the repository after the ADR-100 + RESTRUCTURE_PLAN migration (Phases 01–12, `migration-log/`). Every path is real and git-tracked (or an active untracked-sensitive file, marked).

```
C:\Users\raghe\Documents\Muhide
├── AGENTS.md                          # Operating instructions for agents (authority: audit)
├── README.md, PRODUCT_BIBLE.md        # Product / engineering bible
├── RUNBOOK.md                         # Operating runbook (authoritative, kept at root)
├── REPO_TOPOLOGY_AUDIT.md             # Historical topology audit (findings → ADR-100)
├── docker-compose.yml                 # Root dev stack
├── Dockerfile.railway, railway.json   # Railway backend deploy (root — Railway/Vercel discover these here)
├── get-docker.sh                      # One-off Docker Engine install script (tracked)
├── .github/                           # CI/CD (canonical location)
│   ├── workflows/ (ci, security-scan, docker-smoke, deploy, deploy-staging, deploy-production)
│   ├── dependabot.yml
│   └── CODEOWNERS
├── packages/                          # === SHARED PACKAGES LAYER ===
│   ├── scrapers/                      # Data-scraping packages (moved Phase 03)
│   │   ├── balady/ (19 files)
│   │   ├── najiz/  (16 files)
│   │   ├── rega/   (5 files)
│   │   └── taqeem/ (27 files)
│   ├── data/                          # Notion/identity import pipelines + cleaned datasets (moved Phase 04; gitignored)
│   │   └── scripts/clean_all.py
│   └── widget-template/               # Shared widget template (moved Phase 07)
├── infrastructure/                    # Cloud / observability / scripts scaffolding (intent pending L1)
│   └── README.md
├── archive/                           # Legacy / retired trees (gitignored; recoverable from history)
│   ├── sales-os/                      # LEGACY product tree (retired Phase 04)
│   └── engineering-recovery/          # Engineering recovery docs (archived 2026-08-05)
├── assets/                            # Branding / presentations / reports
│   ├── branding/ (2 zips)
│   ├── presentations/ (4 pptx)
│   └── reports/ (4 md reports)
├── migration-log/                     # Per-phase decision logs (phase-01 … phase-12)
├── docs/
│   ├── audit/ga-engineering-audit/    # CANONICAL GA source of truth (00-EXECUTIVE, GA_STATUS, PRODUCTION_PLAN, AI_HONESTY)
│   ├── audit/legacy-reports/          # Retired SALESOS_*.md audits (moved Phase 05)
│   ├── adr/                           # ADR-030..100 + index
│   ├── architecture/                  # RESTRUCTURE_PLAN, LEGACY_ISOLATION_REGISTER, impact reports
│   ├── guides/                         # (removed — runbooks stay in ops/ per ADR-100 review)
│   ├── ops/                            # RUNTIME_STACK, DR_RUNBOOK, SLO_ALERTS, RAILWAY_CONFIG_LEGACY_NOTICE, ...
│   ├── program/                       # decisions DEC-*, risk register
│   ├── reference/                     # schemas/, diagrams/
│   └── vnext/, ai/, api/, backend/, frontend/, compliance/, design/, incidents/, releases/, v2/
├── salesos/                           # === PRODUCT MONOREPO ===
│   ├── backend/                       # FastAPI backend (Poetry, Python 3.12)
│   │   ├── app/ (main.py, boot/, config.py, database.py, dependencies.py, modules/, routers/, graphql/)
│   │   ├── app/alembic/versions/      # migrations
│   │   ├── domains/                   # DDD domains
│   │   ├── runtime/                   # engine dirs
│   │   ├── sdk/                       # capability registry, events, telemetry
│   │   ├── intelligence/              # AI providers, activity intelligence
│   │   ├── tests/                     # unit/integration/e2e/contract/evaluation/support
│   │   ├── scripts/                   # arch-compliance, check-coverage, generate_rls_policies, ...
│   │   └── pyproject.toml, alembic.ini, Dockerfile*, docker-entrypoint.sh
│   ├── frontend/                      # Next.js 15 App Router (npm workspaces)
│   │   ├── src/app/, src/features/, src/lib/, src/components/, src/middleware.ts
│   │   ├── packages/ (21 workspace packages)
│   │   ├── e2e/ (Playwright specs), tests/visual/, .storybook/
│   │   └── Dockerfile*, nginx.conf, vercel.json, server/server.js
│   ├── infra/                         # k8s, terraform, monitoring, staging/, docker/, caddy/
│   ├── scripts/                       # deploy, smoke, backup, pilot, security, staging-virtual-*
│   ├── docs/                          # ARCHITECTURE_BOOK, deployment_guide, SECURITY docs, vnext, pentest
│   ├── platform/                      # constitution-like docs
│   └── docker-compose*.yml, .env*, railway.json, Makefile
├── engineering-os/                    # Governance SUBMODULE (kept per ADR-100; do NOT archive)
│   ├── adr/ (ADR-001/002/003/0032/012)
│   └── kernel/, ENGINEERING_CONSTITUTION.md, IMPLEMENTATION_ROADMAP.md, SPRINT_GATES.md, ...
├── scripts/                           # root backup.sh
└── [ARTIFACTS, DO NOT INDEX] .next/, __pycache__/, .pytest_cache/, .ruff_cache/, node_modules, *.pptx, *.zip, *.csv, *.xlsx, .env*
```

## 2. Canonical entry points

| Purpose | Path |
|---|---|
| Backend entry | `salesos/backend/app/main.py` |
| Router registry | `salesos/backend/app/boot/routers.py` |
| Backend startup | `salesos/backend/app/boot/startup.py` |
| Frontend entry | `salesos/frontend/src/app/layout.tsx` |
| Frontend middleware | `salesos/frontend/src/middleware.ts` |
| API client | `salesos/frontend/src/lib/api/client.ts` |
| CI | `.github/workflows/ci.yml` |
| GA source of truth | `docs/audit/ga-engineering-audit/GA_STATUS.md` |
| Restructure plan | `docs/architecture/REPOSITORY_RESTRUCTURE_PLAN.md` |
| Migration logs | `migration-log/` |

## 3. What lives where (quick finder)

| Question | Answer (path) |
|---|---|
| Where are API routes registered? | `salesos/backend/app/boot/routers.py` |
| Where are feature modules? | `salesos/backend/app/modules/` |
| Where are DDD domains? | `salesos/backend/domains/` |
| Where are runtime engines? | `salesos/backend/runtime/` |
| Where are DB migrations? | `salesos/backend/app/alembic/versions/` |
| Where is the capability framework? | `salesos/backend/runtime/capability_framework/` |
| Where is the FE API client? | `salesos/frontend/src/lib/api/client.ts` |
| Where are FE features? | `salesos/frontend/src/features/` |
| Where are FE packages? | `salesos/frontend/packages/` |
| Where is E2E? | `salesos/frontend/e2e/` |
| Where is CI? | `.github/workflows/` |
| Where is infra? | `salesos/infra/`, `infrastructure/` (scaffolding) |
| Where are ADRs? | `docs/adr/`, `engineering-os/adr/` |
| Where is the GA audit? | `docs/audit/ga-engineering-audit/` |
| Where are scrapers? | `packages/scrapers/` |
| Where is shared widget template? | `packages/widget-template/` |
| Where are retired trees? | `archive/` |
| Where is branding/presentations? | `assets/` |

## 4. When this file changes

- On structural change (new monorepo app, tree relocation). Updated alongside `24_REPOSITORY_MANIFEST.json`.
