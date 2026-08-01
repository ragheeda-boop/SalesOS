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

# 01 â€” PROJECT OVERVIEW

## What this is

**AQLIYA** is the intended **Private Governed Institutional Intelligence Platform**. **SalesOS** is its first operational product: an enterprise company-intelligence / revenue-intelligence platform for the Gulf market (Arabic/RTL first). Core principle: **AI assists. Humans decide. Evidence governs.**

| Product | Role | Code reality (at commit 3749c30) |
|---|---|---|
| SalesOS | First operational product | `salesos/` monorepo (backend + frontend + infra) |
| AuditOS | Vision (shared Core) | Not a shipped tree |
| DecisionOS | Vision (shared Core) | Not a shipped tree |
| LocalContentOS | Vision (shared Core) | Not a shipped tree |

SalesOS GA work is **not** "AQLIYA multi-product GA". Do not describe the platform as AuditOS-only, SaaS-only, or a chatbot.

## Repo at a glance (evidence: 23_PROJECT_FINGERPRINT.json)

- **Backend:** FastAPI modular monolith (Python 3.12, SQLAlchemy 2 async, Alembic, Celery). `salesos/backend`. 1188 tracked `.py` files (repo-wide, `git ls-files`).
- **Frontend:** Next.js 15 App Router (React 19, TypeScript, npm workspaces). `salesos/frontend`. ~933 tracked files under src/packages/apps/e2e/tests.
- **Infra:** Docker Compose (7 files), Kubernetes (37 manifests), Terraform (3), monitoring (21), Railway + Vercel configs.
- **CI/CD:** 6 workflows in `.github/workflows/`.
- **Governance:** `docs/audit/ga-engineering-audit/` is canonical; `engineering-os/` submodule holds constitution + some ADRs.

## Products of the backend (evidence: backend agent report)

| Layer | Path | Contents |
|---|---|---|
| Application | `salesos/backend/app` | main, boot (startup/routers/middleware), 23 feature modules |
| Domains | `salesos/backend/domains` | 17 DDD domains (commercial, search, decision, revenue, workflow, ...) + `app/domains/customer_success` |
| Runtime | `salesos/backend/runtime` | 27 engine dirs (event, search, timeline, KG, decision, data-fabric, capability-framework, ux, action/form/plugin/ui-schema, nba, pipeline-analytics, ...); 10 single-file dirs â€” stub status not individually proven |
| SDK | `salesos/backend/sdk` | cross-domain SDK, capability registry, events, telemetry |
| Intelligence | `salesos/backend/intelligence` | AI providers, activity intelligence, data fabric, agents |

## Products of the frontend

| Area | Path | Contents |
|---|---|---|
| App Router | `salesos/frontend/src/app` | (auth), (dashboard), v3 route groups + one API route (google oauth callback) |
| Features | `salesos/frontend/src/features` | 13 feature packages (admin, analytics, automation, company-intelligence, customer-success, dashboard, demo, monitoring, rag, revenue-execution, rules, scoring, search) |
| Packages | `salesos/frontend/packages` | 21 workspace packages; 13 with `src`, 8 without (stub/empty status heuristic) |
| Tests | `salesos/frontend/e2e`, `src/**/__tests__` | Playwright (31 e2e files), Jest |

## Governance status (frozen)

- **GA = `production no-go`.** Do not claim ready-for-production, do not claim soak done, do not forge signatures. (Evidence: `docs/audit/ga-engineering-audit/GA_STATUS.md`; 30_ENGINEERING_BOOTSTRAP_REPORT.md.)
- Security audit latest: **51.6/100, 30 critical failures** (`salesos/security-audit-report-latest.json`).
- CI ops blockers: **CI-08** (GHCR 403), **CI-09** (VPS/SSH secrets).

## Key identifiers for this repo (used across `.engineering`)

| Identifier | Meaning | Source |
|---|---|---|
| `DIR: <path>` | Directory | `04_DIRECTORY_CATALOG.md` |
| `FILE: <path>` | File | `05_FILE_CATALOG.md` |
| `CAP-###` | Capability (catalog numbering) | `29_CAPABILITY_REGISTRY.md` |
| `ADR-###` | Architectural decision | `27_ADR_INDEX.md` |
| `DB: <table>` | Database table | `13_DATABASE_CATALOG.md` |
| `TST: <path>` | Test | `17_TESTING_MAP.md` |
| `CI: <workflow>#<job>` | CI job | `12_CI_CATALOG.md` |
| `DEP: <target>` | Deployment target | `16_DEPLOYMENT_MAP.md` |
| Owner labels | Cursor / Claude / OpenCode / Human / Shared | `09_OWNERSHIP_MAP.md` |

## When this file changes

- On major product/architecture changes (new application, new product line, monorepo restructuring).
- On governance posture change. Otherwise read-only.

## Who reads this first

- Any new agent joining the repository: read this file, then `11_AGENT_BOOTSTRAP.md`, then `10_AI_CONTEXT_INDEX.md`.
