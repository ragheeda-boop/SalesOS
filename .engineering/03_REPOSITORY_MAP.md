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

# 03 â€” REPOSITORY MAP

> Complete topographic map of the repository at commit `c89025a` (re-pinned; prior pin `3749c30`). Every path is real and git-tracked (or an active untracked-sensitive file, marked).

```
C:\Users\raghe\Documents\Muhide
â”œâ”€â”€ AGENTS.md                          # Operating instructions for agents (authority: audit)
â”œâ”€â”€ README.md, PRODUCT_BIBLE.md        # Product / engineering bible
â”œâ”€â”€ RUNBOOK.md, SALESOS_*.md           # Operating plan, readiness audits (superseded GO claims inside)
â”œâ”€â”€ docker-compose.yml                 # Root dev stack
â”œâ”€â”€ Dockerfile.railway, railway.json   # Railway backend deploy (root)
â”œâ”€â”€ .github/                           # CI/CD (canonical location)
â”‚   â”œâ”€â”€ workflows/ (ci, security-scan, docker-smoke, deploy, deploy-staging, deploy-production)
â”‚   â””â”€â”€ dependabot.yml
â”œâ”€â”€ docs/
â”‚   â”œâ”€â”€ audit/ga-engineering-audit/    # CANONICAL GA source of truth (00-EXECUTIVE, GA_STATUS, PRODUCTION_PLAN, AI_HONESTY)
â”‚   â”œâ”€â”€ audit/                          # historical audits, sprint reports, security/architecture audits
â”‚   â”œâ”€â”€ adr/                           # ADR-030..035 + index
â”‚   â”œâ”€â”€ ADR-Data-001-identity-resolution-v3.md
â”‚   â”œâ”€â”€ CAPABILITY_CATALOG.md          # 40 capability cards
â”‚   â”œâ”€â”€ vnext/                         # roadmaps, work-orders WO-*, TECHNICAL_DEBT, DECISIONS
â”‚   â”œâ”€â”€ ops/                           # RUNTIME_STACK, DR_RUNBOOK, SECRETS_HYGIENE, SLO_ALERTS
â”‚   â””â”€â”€ program/                       # decisions DEC-* , risk register
â”œâ”€â”€ salesos/                           # === PRODUCT MONOREPO ===
â”‚   â”œâ”€â”€ backend/                       # FastAPI backend (Poetry, Python 3.12)
â”‚   â”‚   â”œâ”€â”€ app/ (main.py, boot/, config.py, database.py, dependencies.py, modules/, routers/, graphql/)
â”‚   â”‚   â”œâ”€â”€ app/alembic/versions/      # 66 migrations (head c9f4a21b6e08)
â”‚   â”‚   â”œâ”€â”€ domains/                   # 17 DDD domains (+ app/domains/customer_success)
â”‚   â”‚   â”œâ”€â”€ runtime/                   # 27 engine dirs (10 single-file)
â”‚   â”‚   â”œâ”€â”€ sdk/                       # capability registry, events, telemetry
â”‚   â”‚   â”œâ”€â”€ intelligence/              # AI providers, activity intelligence
â”‚   â”‚   â”œâ”€â”€ tests/                     # unit/integration/e2e/contract/evaluation/support
â”‚   â”‚   â”œâ”€â”€ scripts/                   # arch-compliance, check-coverage, generate_rls_policies, ...
â”‚   â”‚   â”œâ”€â”€ pyproject.toml, alembic.ini, Dockerfile*, docker-entrypoint.sh
â”‚   â”‚   â””â”€â”€ [SENSITIVE] .env, app/modules/identity/_keys/rsa_private.pem
â”‚   â”œâ”€â”€ frontend/                      # Next.js 15 App Router (npm workspaces)
â”‚   â”‚   â”œâ”€â”€ src/app/ (auth/dashboard/v3 + google callback route)
â”‚   â”‚   â”œâ”€â”€ src/features/ (13 features)
â”‚   â”‚   â”œâ”€â”€ src/lib/ (api client, auth, hooks, queries)
â”‚   â”‚   â”œâ”€â”€ src/components/, src/application/, src/middleware.ts
â”‚   â”‚   â”œâ”€â”€ packages/ (21 workspace packages)
â”‚   â”‚   â”œâ”€â”€ e2e/ (29 Playwright *.spec.ts; 31 files), tests/visual/, src/**/__tests__
â”‚   â”‚   â”œâ”€â”€ apps/ (4 EMPTY shells)
â”‚   â”‚   â”œâ”€â”€ .storybook/, playwright*.config.ts, jest.config.js, next.config.js, tailwind.config.ts
â”‚   â”‚   â”œâ”€â”€ Dockerfile*, nginx.conf, vercel.json, server/server.js (mock, permissive CORS)
â”‚   â”‚   â””â”€â”€ [SENSITIVE] .env.local
â”‚   â”œâ”€â”€ infra/                         # k8s (37), terraform (3), monitoring (21), staging/, docker/, caddy/
â”‚   â”œâ”€â”€ scripts/                       # deploy, smoke, backup, pilot, security, staging-virtual-*
â”‚   â”œâ”€â”€ docs/                          # ARCHITECTURE_BOOK, deployment_guide, SECURITY docs, vnext, pentest
â”‚   â”œâ”€â”€ platform/                      # constitution-like docs (CONSTITUTION, OPERATING_SYSTEM, ARB-001...)
â”‚   â”œâ”€â”€ docker-compose*.yml, .env*, railway.json, Makefile
â”‚   â””â”€â”€ [SENSITIVE] .env, .env.production, .env.staging.local
â”œâ”€â”€ engineering-os/                    # Governance SUBMODULE (branch main, HEAD b82b9fb, DIRTY)
â”‚   â”œâ”€â”€ adr/ (ADR-001/002/003/0032/012)
â”‚   â”œâ”€â”€ kernel/capability-registry.yaml (uncommitted drift)
â”‚   â”œâ”€â”€ ENGINEERING_CONSTITUTION.md, IMPLEMENTATION_ROADMAP.md, SPRINT_GATES.md, ...
â”œâ”€â”€ data/                              # Notion/identity import pipelines (NOT runtime GA path)
â”‚   â”œâ”€â”€ scripts/ (phase4_identity_v4.py, phase3_normalize.py, ...)
â”œâ”€â”€ balady_scraper/, taqeem_scraper/, najiz_scraper/, rega_scraper/   # scrapers (data-side)
â”œâ”€â”€ scripts/                           # root backup.sh
â”œâ”€â”€ output/, WidgetTemplate/           # generated playbooks, widget template
â”œâ”€â”€ sales-os/                          # LEGACY tree (prefer salesos/)
â”œâ”€â”€ *.py (pipeline_utils, sales_intel_pipeline, import_to_notion, ...)  # root data scripts
â””â”€â”€ [ARTIFACTS, DO NOT INDEX] .next/, __pycache__/, .pytest_cache/, .ruff_cache/, node_modules, *.pptx, *.zip, *.xlsx
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
| Where is infra? | `salesos/infra/` |
| Where are ADRs? | `docs/adr/`, `engineering-os/adr/` |
| Where is the capability catalog? | `docs/CAPABILITY_CATALOG.md` |
| Where is the GA audit? | `docs/audit/ga-engineering-audit/` |

## 4. When this file changes

- On structural change (new monorepo app, tree relocation). Updated alongside `24_REPOSITORY_MANIFEST.json`.
