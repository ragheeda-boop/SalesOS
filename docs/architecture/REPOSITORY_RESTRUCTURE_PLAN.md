# Repository Migration Framework

> **Version:** 2.0 (Final)  
> **Author:** Architecture Agent + ChatGPT Review + User Approval  
> **Date:** 2026-08-05  
> **Status:** SUPERSEDED where it conflicts with ADR-100 (2026-08-05) — see note below. Non-conflicting phases remain valid reference material.
> **Scope:** Entire Muhide repository filesystem reorganization  
> **Principle:** Do not change architectural boundaries during structural cleanup.

> **Reconciliation note (2026-08-05):** [`ADR-100: Repository Canonicalization`](../adr/0100-repository-canonicalization.md) governs repository topology going forward. Where this document and ADR-100 disagree, **ADR-100 wins** — confirmed by explicit user decision. The one known conflict: **Phase 7 of this document** (below) archives the `engineering-os/` submodule and drops it from `.gitmodules`; **ADR-100 §2–3 keeps `engineering-os/` as a submodule, unchanged.** Do not execute Phase 7's submodule-archival step. The `archive/engineering-os/` and `archive/engineering-recovery/` directories this document's Phase 2 pre-created as destinations for that step were removed as stale scaffolding on 2026-08-05 (ADR-100 execution, Phase "Safe Cleanup" — see `migration-log/phase-04.md`). Phases 4/5/6/8/9/10/11/12 below were not evaluated against ADR-100 and should be re-reviewed before execution rather than assumed compatible.

---

## Table of Contents

1. [Repository Audit](#1-repository-audit)
2. [Problems Found](#2-problems-found)
3. [Target Architecture](#3-target-architecture)
4. [Dependency Graph](#4-dependency-graph)
5. [Import Impact Matrix](#5-import-impact-matrix)
6. [CI/CD Compatibility Matrix](#6-cicd-compatibility-matrix)
7. [Migration Phases](#7-migration-phases)
8. [Migration Gate](#8-migration-gate)
9. [Policies](#9-policies)
10. [Success Metrics](#10-success-metrics)
11. [Decision Log Template](#11-decision-log-template)

---

# 1. Repository Audit

## 1.1 Current Topology

```
Muhide/                                # Root — 553 entries
├── .ai/                               # AI agent organization (frozen)
├── .claude/                           # Claude AI settings
├── .cursor/                           # Cursor IDE settings
├── .engineering/                      # Engineering OS governance (36 files)
├── .github/                           # CI/CD (6 workflows)
├── .tmp_*                             # ~300 temporary artifacts
├── tmp_*.py                           # ~38 temporary Python scripts
├── balady_scraper/                    # Balady municipality scraper
├── najiz_scraper/                     # Najiz legal scraper
├── rega_scraper/                      # REGA engineering offices scraper
├── taqeem_scraper/                    # Taqeem evaluation scraper
├── data/                              # Data import pipeline
├── docs/                              # Documentation (35 subdirs)
├── engineering-os/                    # Legacy governance submodule
├── engineering-recovery/              # Recovery audit trail
├── open-design/                       # Contains node_modules (stale)
├── output/                            # Pipeline output artifacts
├── sales-os/                          # LEGACY scraper (separate from salesos/)
├── salesos/                           # PRIMARY PRODUCT MONOREPO
├── scripts/                           # Single backup.sh
├── WidgetTemplate/                    # Widget SDK template
├── *.py                               # ~31 standalone Python scripts
├── *.md                               # ~15 root markdown files
├── *.pptx / *.zip                     # Presentation assets
├── *.json / *.txt / *.log             # Data/state/log files
├── Dockerfile.railway                 # Root Dockerfile
├── docker-compose.yml                 # Root compose
└── railway.json                       # Railway deployment config
```

## 1.2 Per-Directory Evaluation

| Directory | Purpose | Verdict | Reason |
|---|---|---|---|
| `balady_scraper/` | Municipality scraper (20 files) | **MOVE** → `packages/scrapers/balady/` | Group with other scrapers |
| `najiz_scraper/` | Legal scraper (8 files) | **MOVE** → `packages/scrapers/najiz/` | Group with other scrapers |
| `rega_scraper/` | Engineering offices scraper (7 files) | **MOVE** → `packages/scrapers/rega/` | Group with other scrapers |
| `taqeem_scraper/` | Evaluation scraper (13 files) | **MOVE** → `packages/scrapers/taqeem/` | Group with other scrapers |
| `sales-os/` | Legacy scraper (16 files) | **ARCHIVE** → `archive/sales-os/` | Dead code, separate from `salesos/` |
| `open-design/` | Contains only `node_modules/` | **DELETE** | Stale, no source code |
| `WidgetTemplate/` | Widget SDK template (6 files) | **MOVE** → `packages/widget-template/` | Alongside widget-sdk |
| `scripts/` | Single `backup.sh` | **MERGE** → `scripts/` (root, expanded) | Nearly empty |
| `engineering-os/` | Governance submodule (legacy) | **ARCHIVE** → `archive/engineering-os/` | Superseded by `.engineering/` |
| `engineering-recovery/` | Recovery audit trail (9 files) | **ARCHIVE** → `archive/engineering-recovery/` | Completed, historical |
| `output/` | Pipeline artifacts (21 files) | **DELETE** | Ephemeral, gitignored |
| `.engineering/` | Engineering OS governance (36 files) | **KEEP** | Canonical governance |
| `.ai/` | AI organization (frozen) | **KEEP** | Frozen per ADR-036 |
| `data/` | Data import pipeline | **MOVE** → `packages/data/` | Group shared packages |
| `docs/` | Documentation (35 subdirs) | **RESTRUCTURE** | Split by responsibility |
| `salesos/` | Primary monorepo | **KEEP** | Core product |
| Root `*.py` (31 scripts) | Standalone scripts | **DELETE** or **MOVE** → `scripts/` | One-off data scripts |
| Root `tmp_*.py` (38) | Temporary scripts | **DELETE** | Debug artifacts |
| Root `.tmp_*` (~300) | Temporary artifacts | **DELETE** | CI/debug artifacts |
| Root `*.pptx`, `*.zip` | Presentation assets | **MOVE** → `assets/` | Non-code assets |
| Root `*.md` (SalesOS) | SalesOS docs | **MOVE** → `salesos/docs/` | Product-specific |
| Root `*.log`, `*.err` | CI artifacts | **DELETE** | Ephemeral |
| Root `*.json`, `*.txt` | Data/state files | **DELETE** or **MOVE** → `data/` | Debug artifacts |

---

# 2. Problems Found

## 2.1 Critical

| ID | Problem | Severity | Impact |
|---|---|---|---|
| CRIT-01 | Root has 553 entries (~300 temp files) | Critical | Navigation, onboarding, git status |
| CRIT-02 | 4 duplicate scraper directories + legacy `sales-os/` | Critical | Maintenance, confusion |
| CRIT-03 | Documentation in 5+ locations | High | Truth fragmentation |
| CRIT-04 | Mixed responsibility at root (scripts, assets, configs, data) | High | Unclear ownership |

## 2.2 Structural

| ID | Problem | Impact |
|---|---|---|
| STR-01 | `sales-os/` vs `salesos/` confusion | New devs confuse them |
| STR-02 | `open-design/` contains only `node_modules/` | Wasted space |
| STR-03 | `WidgetTemplate/` isolated from `widget-sdk` | Fragmented widget ecosystem |
| STR-04 | Root Docker/configs alongside `salesos/` configs | Unclear canonical |
| STR-05 | `scripts/` nearly empty (1 file) | Confusion about script location |
| STR-06 | 338 temp files never cleaned | Git noise, disk bloat |
| STR-07 | Presentation assets at root | Root clutter |
| STR-08 | 3 overlapping governance systems | Unclear source of truth |

---

# 3. Target Architecture

## 3.1 Target Directory Tree

```
Muhide/
│
├── .ai/                                    # KEEP — AI organization (frozen)
├── .claude/                                # KEEP — Claude AI settings
├── .cursor/                                # KEEP — Cursor IDE settings
├── .engineering/                           # KEEP — Engineering OS governance
├── .github/                                # KEEP — CI/CD workflows
├── .gitignore                              # UPDATE
├── .gitleaks.toml                          # KEEP
├── .gitmodules                             # UPDATE — remove engineering-os
├── .env.example                            # KEEP
│
├── AGENTS.md                               # KEEP — agent instructions
├── README.md                               # REWRITE — project overview
│
├── salesos/                                # KEEP — primary product monorepo
│   ├── backend/                            # KEEP — FastAPI backend
│   ├── frontend/                           # KEEP — Next.js frontend
│   ├── infra/                              # KEEP — infrastructure
│   ├── docs/                               # CONSOLIDATED documentation
│   │   ├── architecture/                   # Architecture docs
│   │   ├── adr/                            # Architecture Decision Records
│   │   ├── api/                            # API documentation
│   │   ├── audit/                          # GA engineering audit
│   │   ├── compliance/                     # SOC2 compliance
│   │   ├── design/                         # Design docs
│   │   ├── ops/                            # Operations runbooks
│   │   ├── program/                        # Sprint management
│   │   ├── releases/                       # Release notes
│   │   └── vnext/                          # vNext planning
│   ├── scripts/                            # Operational scripts (46 files)
│   ├── knowledge-packs/                    # KEEP
│   ├── memory/                             # KEEP
│   ├── packages/                           # KEEP
│   ├── reports/                            # KEEP
│   ├── docker-compose*.yml                 # KEEP
│   ├── Makefile                            # KEEP
│   └── README.md                           # KEEP
│
├── packages/                               # NEW — shared packages
│   ├── scrapers/                           # MERGED from 4 scraper dirs
│   │   ├── __init__.py
│   │   ├── shared/                         # Common scraper utilities
│   │   ├── balady/                         # FROM balady_scraper/
│   │   ├── najiz/                          # FROM najiz_scraper/
│   │   ├── rega/                           # FROM rega_scraper/
│   │   └── taqeem/                         # FROM taqeem_scraper/
│   ├── data/                               # FROM root data/
│   │   ├── cleaned/
│   │   ├── golden/
│   │   ├── identity/
│   │   ├── import/
│   │   ├── normalized/
│   │   ├── notion_export/
│   │   ├── raw/
│   │   ├── reports/
│   │   └── scripts/
│   └── widget-template/                    # FROM WidgetTemplate/
│       ├── __tests__/
│       ├── index.ts
│       ├── types.ts
│       ├── YourWidgetContainer.tsx
│       └── YourWidgetView.tsx
│
├── docs/                                   # RESTRUCTURED — platform docs only
│   ├── architecture/                       # Platform architecture
│   │   ├── PROJECT_BIBLE.md
│   │   ├── DOMAIN_MAP.md
│   │   ├── RUNTIME_ARCHITECTURE.md
│   │   └── MASTER_BLUEPRINT.md
│   ├── adr/                                # Platform ADRs
│   ├── guides/                             # Ops runbooks
│   │   ├── GO_LIVE_RUNBOOK.md
│   │   ├── DR_RUNBOOK.md
│   │   ├── ONCALL_RUNBOOK.md
│   │   └── HYPERCARE_RUNBOOK.md
│   ├── program/                            # Program management
│   │   ├── PROGRAM_PLAN.md
│   │   ├── RELEASE_PLAN.md
│   │   ├── RISK_REGISTER.md
│   │   ├── TEST_STRATEGY.md
│   │   └── sprints/                        # Sprint crumbs
│   ├── compliance/                         # SOC2
│   │   └── soc2-type-i/
│   ├── incidents/                          # Incident reports
│   └── reference/                          # NEW — schemas, diagrams, glossary
│       ├── schemas/
│       ├── diagrams/
│       └── glossary.md
│
├── scripts/                                # CONSOLIDATED operational scripts
│   ├── backup.sh                           # FROM root scripts/
│   ├── deploy/                             # Deployment scripts
│   ├── maintenance/                        # Maintenance scripts
│   ├── migration/                          # Data migration scripts
│   └── verification/                       # Verification scripts
│
├── assets/                                 # NEW — non-code assets
│   ├── branding/                           # Logos, design systems
│   │   ├── MUHIDE Design System.zip
│   │   └── SalesOS Design Revolution.zip
│   ├── presentations/                      # Deck files
│   │   ├── MUHIDE_Ultimate_Deck.pptx
│   │   ├── MUHIDE_Ultimate_Deck_V2.pptx
│   │   ├── MUHIDE_Ultimate_Deck_V3.pptx
│   │   └── SalesOS_V2_Executive_Presentation.pptx
│   └── reports/                            # Analysis reports
│       ├── muhide_comparative_analysis_report.md
│       ├── muhide_pitch_deck_analysis_report.md
│       ├── muhide_3version_comparative_report.md
│       └── ultimate_deck_specification.md
│
├── infrastructure/                         # NEW — root-level infra
│   ├── containers/                         # Container definitions
│   │   └── docker/
│   │       ├── Dockerfile.railway          # FROM root
│   │       ├── docker-compose.yml          # FROM root
│   │       └── get-docker.sh              # FROM root
│   ├── cloud/                              # Cloud provisioning
│   │   └── terraform/                      # (future)
│   ├── deployment/                         # Platform deployment
│   │   ├── railway.json                    # FROM root
│   │   └── vercel.json                     # (future)
│   ├── observability/                      # Monitoring stack
│   │   ├── grafana/
│   │   ├── prometheus/
│   │   └── loki/
│   └── scripts/                            # Infra scripts
│
├── archive/                                # NEW — completed/historical
│   ├── engineering-os/                     # FROM root
│   ├── engineering-recovery/               # FROM root
│   └── sales-os/                           # FROM root (legacy)
│
└── migration-log/                          # NEW — decision log per phase
    ├── phase-01.md
    ├── phase-02.md
    ├── ...
    └── phase-12.md
```

## 3.2 Naming Conventions

| Context | Convention | Example |
|---|---|---|
| Python packages | `snake_case` | `balady_scraper/` |
| Frontend packages | `kebab-case` | `design-system/` |
| TypeScript files | `camelCase` | `queryKeys.ts` |
| React components | `PascalCase` | `AdminWorkspace.tsx` |
| Config files | `kebab-case` or `dotfile` | `.gitleaks.toml` |
| Documentation | `UPPER_SNAKE.md` or `kebab-case.md` | `GO_LIVE_RUNBOOK.md` |
| Shell scripts | `kebab-case.sh` | `backup.sh` |
| Docker files | `Dockerfile.<purpose>` | `Dockerfile.railway` |

## 3.3 Ownership Model

| Directory | Owner | Approver |
|---|---|---|
| `salesos/backend/` | Backend Lead | Architecture Reviewer |
| `salesos/frontend/` | Frontend Lead | Architecture Reviewer |
| `salesos/infra/` | DevOps Lead | Architecture Reviewer |
| `packages/scrapers/` | Data Lead | Backend Lead |
| `packages/data/` | Data Lead | Backend Lead |
| `docs/` | Documentation Lead | Architecture Reviewer |
| `.github/` | DevOps Lead | Engineering Validator |
| `.engineering/` | Architecture Lead | Engineering Validator |
| `.ai/` | AI Lead | Architecture Lead |
| `scripts/` | DevOps Lead | Backend Lead |
| `assets/` | Product Lead | Architecture Reviewer |

---

# 4. Dependency Graph

## 4.1 Forward Dependencies (A → B means "A imports/uses B")

```
salesos/backend/app/
    ├── salesos/backend/sdk/
    ├── salesos/backend/domains/
    ├── salesos/backend/runtime/
    └── salesos/backend/intelligence/

salesos/backend/domains/
    └── salesos/backend/sdk/

salesos/backend/runtime/
    └── salesos/backend/sdk/

salesos/backend/intelligence/
    └── salesos/backend/sdk/

salesos/frontend/
    └── @salesos/* packages (internal)

packages/scrapers/balady/notion_import.py
    └── salesos/backend/pipeline/notion.py

packages/data/scripts/clean_all.py
    ├── packages/scrapers/balady/ (reads CSV)
    ├── packages/scrapers/najiz/ (reads CSV)
    ├── packages/scrapers/rega/ (reads CSV)
    └── packages/scrapers/taqeem/ (reads CSV)

root pipeline_utils.py
    └── salesos/backend/pipeline/excel_utils.py

root push_to_notion.py
    ├── packages/scrapers/rega/ (reads CSV)
    └── sales-os/.env (reads token)
```

## 4.2 Reverse Dependencies (Who depends on X?)

| Component | Depended on by |
|---|---|
| `salesos/backend/sdk/` | `app/`, `domains/`, `runtime/`, `intelligence/` (4 consumers) |
| `salesos/backend/pipeline/` | `balady_scraper/notion_import.py`, root `pipeline_utils.py` (2 consumers) |
| `packages/scrapers/*/` | `packages/data/scripts/clean_all.py` (1 consumer each) |
| `salesos/backend/` | CI/CD (6 workflows), Docker (5 Dockerfiles), Dependabot (3 entries), CODEOWNERS |
| `salesos/frontend/` | CI/CD (4 workflows), Docker (2 Dockerfiles), Dependabot (2 entries), CODEOWNERS |
| `salesos/infra/monitoring/` | Root `docker-compose.yml`, `salesos/docker-compose*.yml` (4 compose files) |
| `salesos/infra/docker/postgres/init/` | 4 compose files + 3 CI workflows (7 consumers) |
| `.github/workflows/` | GitHub platform (6 workflows) |

## 4.3 Isolation Assessment

| Component | Imports from outside? | Safe to move? |
|---|---|---|
| `balady_scraper/` | 1 cross-dir import (`notion_import.py` → `salesos/backend`) | Yes, fix 1 import |
| `najiz_scraper/` | None | Yes, safe |
| `rega_scraper/` | None | Yes, safe |
| `taqeem_scraper/` | None | Yes, safe |
| `data/` | File path refs to scrapers (`clean_all.py`) | Yes, update paths |
| `WidgetTemplate/` | None | Yes, safe |
| `engineering-os/` | None (submodule) | Yes, archive |
| `engineering-recovery/` | None | Yes, archive |
| `sales-os/` | None | Yes, archive |
| Root `*.py` (31) | Some reference scrapers, `salesos/backend` | Delete most, archive few |
| Root `*.pptx`, `*.zip` | None | Yes, safe |
| Root `*.md` | None | Yes, safe |
| Root configs | CI/CD references | Update CI/CD first |

---

# 5. Import Impact Matrix

## 5.1 Files Affected Per Move

### Move: `balady_scraper/` → `packages/scrapers/balady/`

| File | Import to update | New import |
|---|---|---|
| `balady_scraper/notion_import.py` | `from pipeline.notion import MuhideNotion` | Path update via `sys.path.insert` or relative import |
| `data/scripts/clean_all.py` | File path: `balady_scraper/engineering_offices_full.csv` | `packages/scrapers/balady/engineering_offices_full.csv` |

### Move: `najiz_scraper/` → `packages/scrapers/najiz/`

| File | Import to update | New import |
|---|---|---|
| `data/scripts/clean_all.py` | File path: `najiz_scraper/data/lawyers.csv` | `packages/scrapers/najiz/data/lawyers.csv` |

### Move: `rega_scraper/` → `packages/scrapers/rega/`

| File | Import to update | New import |
|---|---|---|
| `data/scripts/clean_all.py` | File path: `rega_scraper/REGA_Qualified_Companies.csv` | `packages/scrapers/rega/REGA_Qualified_Companies.csv` |
| Root `push_to_notion.py` | File path: `rega_scraper/REGA_Qualified_Companies.csv` | `packages/scrapers/rega/REGA_Qualified_Companies.csv` |
| Root `check_licenses.py` | File path: `rega_scraper/REGA_Qualified_Companies.csv` | `packages/scrapers/rega/REGA_Qualified_Companies.csv` |
| Root `check_dates.py` | File path: `rega_scraper/REGA_Qualified_Companies.csv` | `packages/scrapers/rega/REGA_Qualified_Companies.csv` |
| Root `check_csv_months.py` | File path: `rega_scraper/REGA_Qualified_Companies.csv` | `packages/scrapers/rega/REGA_Qualified_Companies.csv` |

### Move: `taqeem_scraper/` → `packages/scrapers/taqeem/`

| File | Import to update | New import |
|---|---|---|
| `data/scripts/clean_all.py` | File path: `taqeem_scraper/taqeem_facilities.csv` | `packages/scrapers/taqeem/taqeem_facilities.csv` |

### Move: `data/` → `packages/data/`

| File | Import to update | New import |
|---|---|---|
| `data/scripts/clean_all.py` | Internal paths (relative) | No change needed (relative paths) |
| Root `*.py` scripts | `data/` file refs | `packages/data/` |

### Move: Root configs → `infrastructure/`

| File | Import to update | New import |
|---|---|---|
| `.github/workflows/ci.yml` | `salesos/backend`, `salesos/frontend` | No change (these don't move) |
| `.github/workflows/docker-smoke.yml` | `cd salesos` | No change |
| `.github/workflows/deploy.yml` | `railway_status.json` | Keep at root or update |
| `.github/workflows/deploy-production.yml` | `salesos/infra/k8s` | No change |
| `Dockerfile.railway` | `salesos/backend/*` COPY paths | No change (backend doesn't move) |
| Root `docker-compose.yml` | `./salesos/backend`, `./salesos/frontend`, `./salesos/infra/monitoring/*` | No change |

### Move: Root `*.md` → `salesos/docs/` or `docs/`

| File | Import to update | New import |
|---|---|---|
| None | No code imports markdown files | Safe to move |

## 5.2 Zero Broken Imports Policy

Before each phase completes:
- Run `python -c "import app"` in `salesos/backend/`
- Run `npx tsc --noEmit` in `salesos/frontend/`
- Run `grep -r "from balady_scraper" .` → must return 0 results
- Run `grep -r "from najiz_scraper" .` → must return 0 results
- Run `grep -r "from rega_scraper" .` → must return 0 results
- Run `grep -r "from taqeem_scraper" .` → must return 0 results

---

# 6. CI/CD Compatibility Matrix

## 6.1 Workflow Path Dependencies

| Workflow | Path References | Move Affected? | Action Required |
|---|---|---|---|
| `ci.yml` | `salesos/backend/`, `salesos/frontend/`, `salesos/scripts/`, `salesos/infra/docker/postgres/init/` | NO — `salesos/` doesn't move | None |
| `deploy.yml` | `railway_status.json`, `railway_deployments.json` | MEDIUM — root files | Keep at root or update |
| `deploy-production.yml` | `salesos/infra/k8s`, `salesos/backend/`, `salesos/frontend/`, `salesos/scripts/` | NO — `salesos/` doesn't move | None |
| `deploy-staging.yml` | Railway CLI (no explicit paths) | NO | None |
| `docker-smoke.yml` | `cd salesos`, `salesos/scripts/`, `salesos/.env` | NO — `salesos/` doesn't move | None |
| `e2e-stage7.yml` | `salesos/frontend/`, `salesos/backend/`, `salesos/infra/docker/postgres/init/` | NO — `salesos/` doesn't move | None |
| `security-scan.yml` | `salesos/backend/`, `salesos/frontend/` | NO — `salesos/` doesn't move | None |

## 6.2 Root Config Dependencies

| Config File | Referenced by | Move Affected? | Action Required |
|---|---|---|---|
| `Dockerfile.railway` | Railway platform, `.github/workflows/deploy.yml` | YES | Keep at root OR update Railway config |
| `docker-compose.yml` (root) | `docker-smoke.yml`, local dev | YES | Keep at root OR update workflow |
| `railway.json` | Railway platform | YES | Keep at root (Railway reads from root) |
| `.vercelignore` | Vercel platform | YES | Keep at root (Vercel reads from root) |
| `.gitleaks.toml` | `security-scan.yml` | NO | None |
| `.trivyignore` | `ci.yml`, `security-scan.yml` | NO | None |

## 6.3 Decision: Root Configs

**Decision:** Keep `Dockerfile.railway`, `docker-compose.yml`, `railway.json`, `.vercelignore` at root. These are platform entry points that must remain at root for Railway/Vercel to discover them. Do NOT move to `infrastructure/`.

**Updated `infrastructure/` structure:**
```
infrastructure/
├── cloud/                    # (future: terraform)
├── observability/            # (future: grafana, prometheus, loki)
└── scripts/                  # (future: infra scripts)
```

## 6.4 Dependabot Dependencies

| Ecosystem | Directory | Move Affected? |
|---|---|---|
| npm | `/salesos/frontend` | NO |
| pip | `/salesos/backend` | NO |
| docker | `/salesos/backend` | NO |
| docker | `/salesos/frontend` | NO |
| github-actions | `/` | NO |

## 6.5 CODEOWNERS Dependencies

| Pattern | Move Affected? |
|---|---|
| `salesos/backend/` | NO |
| `salesos/frontend/` | NO |
| `salesos/infra/` | NO |
| `salesos/scripts/` | NO |
| `docs/` | YES — update if docs restructured |
| `.engineering/` | NO |
| `.ai/` | NO |
| `engineering-os/` | YES — moving to archive |

---

# 7. Migration Phases

## Phase 1: Clean Temporary Artifacts

**Goal:** Remove all `.tmp_*`, `tmp_*.py`, CI logs, and debug artifacts from root.

**Actions:**
1. Delete all `.tmp_*` files (~300)
2. Delete all `tmp_*.py` files (~38)
3. Delete all `.ci-backend-types-*.log` files (4)
4. Delete all `30774*` files (6)
5. Delete `workflow-*.log`, `workflow-failure-snippet.txt`
6. Delete `runlogs_*.zip` (2)
7. Delete `scraper.log`
8. Delete `open-design/` (stale node_modules)
9. Delete `output/` (ephemeral artifacts)
10. Delete root debug files: `batch_list.txt`, `batches.txt`, `companies.json`, `companies_list.txt`, `help.txt`, `up_help.txt`, `output_check.txt`, `scraping_report.txt`, `tier1_status.json`, `tier1_status.txt`, `taqeem_facilities.json`, `notion_push_state.json`, `recovered_contacts.json`, `audit_api_raw.json`, `notion_analysis.md`, `runtime_verification.json`, `runtime_verification_summary.txt`
11. Delete `opencode.old.json`, `opencode.old (2).json`
12. Delete `get-docker.sh` (move to `infrastructure/` later, or delete if unused)
13. Delete root `tmp_fix_*.py` (2), `tmp_land_*.py` (~36)

**Files to DELETE:** ~380 files
**Files to MOVE:** 0

**Migration Gate:**
```
Lint:       N/A (no code changes)
Typecheck:  N/A
Test:       N/A
Build:      N/A
Docker:     N/A
Smoke:      N/A
Arch Check: git status shows only deletions, no moved code
```

**Rollback:** `git checkout HEAD~1 -- .` (restore all deleted files from git history)

**Decision Log:** `migration-log/phase-01.md`

---

## Phase 2: Create Directory Structure

**Goal:** Create empty target directories without moving anything.

**Actions:**
1. `mkdir -p packages/scrapers/{shared,balady,najiz,rega,taqeem}`
2. `mkdir -p packages/data`
3. `mkdir -p packages/widget-template`
4. `mkdir -p assets/{branding,presentations,reports}`
5. `mkdir -p archive/{engineering-os,engineering-recovery,sales-os}`
6. `mkdir -p migration-log`
7. `mkdir -p infrastructure/{cloud,observability,scripts}`
8. `mkdir -p docs/{reference/{schemas,diagrams}}`

**Files to CREATE:** 0 (directories only)
**Files to MOVE:** 0

**Migration Gate:**
```
Arch Check: All directories exist, no files moved yet
```

**Rollback:** `rmdir` all created directories

**Decision Log:** `migration-log/phase-02.md`

---

## Phase 3: Move Scrapers

**Goal:** Consolidate 4 scraper directories into `packages/scrapers/`.

**Actions:**
1. `mv balady_scraper/* packages/scrapers/balady/`
2. `mv najiz_scraper/* packages/scrapers/najiz/`
3. `mv rega_scraper/* packages/scrapers/rega/`
4. `mv taqeem_scraper/* packages/scrapers/taqeem/`
5. Create `packages/scrapers/__init__.py`
6. Create `packages/scrapers/shared/__init__.py`
7. Remove empty `balady_scraper/`, `najiz_scraper/`, `rega_scraper/`, `taqeem_scraper/`
8. Update `packages/scrapers/balady/notion_import.py` — fix `sys.path.insert` to point to `salesos/backend`
9. Update `data/scripts/clean_all.py` — update 4 CSV file paths

**Files to MOVE:** 48 files (20+8+7+13)
**Files to UPDATE:** 2 (`notion_import.py`, `clean_all.py`)

**Migration Gate:**
```
Lint:       python -m ruff check packages/scrapers/
Typecheck:  N/A (no type annotations)
Test:       N/A
Build:      N/A
Docker:     N/A
Smoke:      python -c "import packages.scrapers.balady" (if __init__.py present)
Arch Check: grep -r "from balady_scraper" . → 0 results
            grep -r "from najiz_scraper" . → 0 results
            grep -r "from rega_scraper" . → 0 results
            grep -r "from taqeem_scraper" . → 0 results
```

**Rollback:** `mv packages/scrapers/* balady_scraper/ najiz_scraper/ rega_scraper/ taqeem_scraper/` + restore 2 updated files from git

**Decision Log:** `migration-log/phase-03.md`

---

## Phase 4: Move Data Directory

**Goal:** Move `data/` to `packages/data/`.

**Actions:**
1. `mv data/* packages/data/`
2. Remove empty `data/`
3. Update root Python scripts that reference `data/` paths (if any remain after Phase 1)
4. Verify `packages/data/scripts/clean_all.py` still works (paths are relative within `packages/data/`)

**Files to MOVE:** ~50 files
**Files to UPDATE:** 0-5 (root scripts referencing `data/`)

**Migration Gate:**
```
Lint:       python -m ruff check packages/data/scripts/
Typecheck:  N/A
Test:       N/A
Build:      N/A
Docker:     N/A
Smoke:      python packages/data/scripts/clean_all.py --dry-run (if applicable)
Arch Check: grep -r "data/" . --include="*.py" | grep -v "packages/data" | grep -v "salesos/" | grep -v ".engineering/" → 0 results
```

**Rollback:** `mv packages/data/* data/` + restore updated files

**Decision Log:** `migration-log/phase-04.md`

---

## Phase 5: Move Widget Template

**Goal:** Move `WidgetTemplate/` to `packages/widget-template/`.

**Actions:**
1. `mv WidgetTemplate/* packages/widget-template/`
2. Remove empty `WidgetTemplate/`

**Files to MOVE:** 6 files
**Files to UPDATE:** 0

**Migration Gate:**
```
Arch Check: No references to `WidgetTemplate/` in codebase
```

**Rollback:** `mv packages/widget-template/* WidgetTemplate/`

**Decision Log:** `migration-log/phase-05.md`

---

## Phase 6: Move Presentation Assets

**Goal:** Move presentation files from root to `assets/`.

> **Partially executed under ADR-100 (2026-08-05):** actions 7–10 (the four `.md` report files) were executed exactly as written, into `assets/reports/`. Actions 1–6 (`.pptx`/`.zip` binaries) were **not** executed this phase — ADR-100 Phase 2 (Repository Documentation) was explicitly scoped to Markdown relocation only; binary asset relocation was left for a future pass. See `migration-log/phase-05.md`.

**Actions:**
1. `mv MUHIDE_Ultimate_Deck.pptx assets/presentations/`
2. `mv MUHIDE_Ultimate_Deck_V2.pptx assets/presentations/`
3. `mv MUHIDE_Ultimate_Deck_V3.pptx assets/presentations/`
4. `mv SalesOS_V2_Executive_Presentation.pptx assets/presentations/`
5. `mv "MUHIDE Design System.zip" assets/branding/`
6. `mv "SalesOS Design Revolution.zip" assets/branding/`
7. `mv muhide_comparative_analysis_report.md assets/reports/`
8. `mv muhide_pitch_deck_analysis_report.md assets/reports/`
9. `mv muhide_3version_comparative_report.md assets/reports/`
10. `mv ultimate_deck_specification.md assets/reports/`

**Files to MOVE:** 10 files
**Files to UPDATE:** 0

**Migration Gate:**
```
Arch Check: No references to moved files in codebase
```

**Rollback:** `mv assets/presentations/*.pptx .` + `mv assets/branding/*.zip .` + `mv assets/reports/*.md .`

**Decision Log:** `migration-log/phase-06.md`

---

## Phase 7: Move Governance to Archive

**Goal:** Archive completed/legacy governance directories.

**Actions:**
1. `mv engineering-os/* archive/engineering-os/`
2. `mv engineering-recovery/* archive/engineering-recovery/`
3. `mv sales-os/* archive/sales-os/`
4. Remove empty directories
5. Update `.gitmodules` — remove `engineering-os` submodule entry

**Files to MOVE:** 48 files (23+9+16)
**Files to UPDATE:** 1 (`.gitmodules`)

**Migration Gate:**
```
Arch Check: grep -r "engineering-os/" . --include="*.md" | grep -v "archive/" | grep -v ".git" → 0 results (except .engineering/ governance refs)
            grep -r "sales-os/" . --include="*.py" → 0 results
```

**Rollback:** `mv archive/engineering-os/* engineering-os/` + restore `.gitmodules`

**Decision Log:** `migration-log/phase-07.md`

---

## Phase 8: Move SalesOS Root Docs

**Goal:** Move SalesOS-specific markdown files from root into `salesos/docs/`.

> **Executed differently under ADR-100 (2026-08-05):** the 7 `SALESOS_*.md` files were relocated to `docs/audit/legacy-reports/` instead of `salesos/docs/architecture/` — ADR-100 classifies root-level audit/roadmap docs as belonging to the root `docs/` (product/audit) layer, not the `salesos/docs/` (engineering-specific) layer. `PRODUCT_BIBLE.md` and `RUNBOOK.md` were **not** moved — `docs/audit/current-state/15-documentation-audit.md` classifies both as 🟢 Current/authoritative root-level documents, contradicting this phase's original assumption that they should relocate. See `migration-log/phase-05.md` for the actual execution record.

**Actions (original plan, not executed as written):**
1. `mkdir -p salesos/docs/architecture`
2. `mv SALESOS_ARCHITECTURE_AUDIT.md salesos/docs/architecture/`
3. `mv SALESOS_COMPLETE_AUDIT_AND_ROADMAP.md salesos/docs/architecture/`
4. `mv SALESOS_OPERATING_PLAN.md salesos/docs/architecture/`
5. `mv SALESOS_PRODUCTION_READINESS_AUDIT.md salesos/docs/architecture/`
6. `mv SALESOS_REMEDIATION_BACKLOG.md salesos/docs/architecture/`
7. `mv SALESOS_REVISED_ROADMAP.md salesos/docs/architecture/`
8. `mv SALESOS_V1_ENTERPRISE_RELEASE_READINESS.md salesos/docs/architecture/`
9. `mv PRODUCT_BIBLE.md docs/architecture/`
10. `mv RUNBOOK.md docs/guides/`

**Files to MOVE:** 10 files
**Files to UPDATE:** 0

**Migration Gate:**
```
Arch Check: No broken links in README.md
```

**Rollback:** `mv salesos/docs/architecture/SALESOS_*.md .` + `mv docs/architecture/PRODUCT_BIBLE.md .` + `mv docs/guides/RUNBOOK.md .`

**Decision Log:** `migration-log/phase-08.md`

---

## Phase 9: Restructure Root docs/

**Goal:** Reorganize root `docs/` by responsibility.

**Actions:**
1. Create new subdirectories under `docs/`: `reference/schemas/`, `reference/diagrams/`
2. Move `docs/ops/GO_LIVE_RUNBOOK.md` → `docs/guides/` (if not already there)
3. Move `docs/ops/DR_RUNBOOK.md` → `docs/guides/`
4. Move `docs/ops/ONCALL_RUNBOOK.md` → `docs/guides/`
5. Move `docs/ops/HYPERCARE_RUNBOOK.md` → `docs/guides/`
6. Move `docs/ops/SECRETS_HYGIENE.md` → `docs/guides/`
7. Move `docs/ops/STAGING_PARITY.md` → `docs/guides/`
8. Move `docs/ops/DEGRADED_MODE_MATRIX.md` → `docs/guides/`
9. Move `docs/ops/SLO_ALERTS.md` → `docs/guides/`
10. Move `docs/ops/RUNTIME_STACK.md` → `docs/guides/`
11. Remove empty `docs/ops/`

**Files to MOVE:** 9 files
**Files to UPDATE:** 0

**Migration Gate:**
```
Arch Check: All docs subdirs have clear purpose
```

**Rollback:** `mv docs/guides/* docs/ops/`

**Decision Log:** `migration-log/phase-09.md`

---

## Phase 10: Consolidate Scripts

**Goal:** Merge root `scripts/` with operational scripts.

**Actions:**
1. Keep `scripts/backup.sh` at `scripts/backup.sh`
2. Move select `salesos/scripts/` operational scripts to `scripts/` (backup, deploy, maintenance)
3. Move `data/scripts/` archival scripts to `scripts/migration/`
4. Delete root Python scripts that are one-off data scripts (all 31 non-tmp `.py` files at root)

**Note:** Most `salesos/scripts/` are tightly coupled to `salesos/` (they `cd salesos/backend`). Moving them would break their working directory assumptions. **Decision: Keep `salesos/scripts/` as-is.** Only move truly root-level scripts.

**Files to MOVE:** 0-5 (only if clearly root-level)
**Files to DELETE:** ~31 root Python scripts

**Migration Gate:**
```
Arch Check: No orphan Python scripts at root
            grep -r "from pipeline_utils" . → 0 results (after deleting root scripts)
```

**Rollback:** `git checkout HEAD~1 -- *.py`

**Decision Log:** `migration-log/phase-10.md`

---

## Phase 11: Update CI/CD and Config

**Goal:** Update CI/CD references for any moved paths.

**Actions:**
1. Update `.github/CODEOWNERS` — change `engineering-os/` → `archive/engineering-os/`
2. Update `.github/dependabot.yml` — no changes needed (already points to `salesos/`)
3. Update root `.gitignore` — add `archive/`, `assets/`, clean up stale entries
4. Update root `.gitmodules` — already done in Phase 7
5. Update `.engineering/03_REPOSITORY_MAP.md` — reflect new structure
6. Update `.engineering/04_DIRECTORY_CATALOG.md` — reflect new structure
7. Update `AGENTS.md` — update preferred paths section

**Files to UPDATE:** 5-7 config files
**Files to MOVE:** 0

**Migration Gate:**
```
Lint:       N/A
Typecheck:  N/A
Test:       N/A
Build:      N/A
Docker:     N/A
Smoke:      N/A
Arch Check: All CI workflows reference valid paths
            grep -r "engineering-os/" .github/ → 0 results (after CODEOWNERS update)
```

**Rollback:** `git checkout HEAD~1 -- .github/ .gitignore .gitmodules .engineering/ AGENTS.md`

**Decision Log:** `migration-log/phase-11.md`

---

## Phase 12: Final Validation and Cleanup

**Goal:** Full validation, remove empty directories, write migration log.

**Actions:**
1. Remove all empty directories left behind
2. Run full validation suite (see Migration Gate below)
3. Write `migration-log/phase-12.md` with final status
4. Update root `README.md` with new structure
5. Commit all changes

**Files to UPDATE:** 1 (`README.md`)
**Files to DELETE:** Empty directories

**Migration Gate (FULL):**
```
Lint:
  cd salesos/backend && python -m ruff check app/ sdk/ domains/ runtime/ intelligence/
  cd salesos/frontend && npm run lint

Typecheck:
  cd salesos/backend && python -m mypy app/ sdk/ modules/
  cd salesos/frontend && npx tsc --noEmit

Test:
  cd salesos/backend && python -m pytest tests/ -x --tb=short
  cd salesos/frontend && npm test

Build:
  cd salesos/backend && python -m poetry build
  cd salesos/frontend && npm run build

Docker:
  cd salesos && docker compose build

Smoke:
  cd salesos && docker compose up -d
  # Wait 30s
  curl http://localhost:8000/health
  curl http://localhost:3000
  cd salesos && docker compose down

Arch Check:
  # No broken imports
  grep -r "from balady_scraper" . → 0
  grep -r "from najiz_scraper" . → 0
  grep -r "from rega_scraper" . → 0
  grep -r "from taqeem_scraper" . → 0
  grep -r "from sales_os" . → 0
  # No orphan modules
  find . -name "*.py" -path "*/root/*" → 0
  # No duplicate directories
  ls -d */ | sort | uniq -d → 0
  # Root entry count
  ls -1 | wc -l → <30
```

**Rollback:** `git revert <merge-commit>` or `git checkout HEAD~1 -- .`

**Decision Log:** `migration-log/phase-12.md`

---

# 8. Migration Gate

Every phase must pass ALL of the following before proceeding to the next:

```bash
# Gate 1: Lint
cd salesos/backend && python -m ruff check app/ sdk/ domains/ runtime/ intelligence/
cd salesos/frontend && npm run lint

# Gate 2: Typecheck
cd salesos/backend && python -m mypy app/ sdk/ modules/
cd salesos/frontend && npx tsc --noEmit

# Gate 3: Unit Test
cd salesos/backend && python -m pytest tests/ -x --tb=short
cd salesos/frontend && npm test

# Gate 4: Build
cd salesos/backend && python -m poetry build
cd salesos/frontend && npm run build

# Gate 5: Docker Build
cd salesos && docker compose build

# Gate 6: Smoke Test
cd salesos && docker compose up -d && sleep 30
curl -sf http://localhost:8000/health || exit 1
curl -sf http://localhost:3000 || exit 1
cd salesos && docker compose down

# Gate 7: Architecture Check
grep -r "from balady_scraper" . && exit 1
grep -r "from najiz_scraper" . && exit 1
grep -r "from rega_scraper" . && exit 1
grep -r "from taqeem_scraper" . && exit 1
grep -r "from sales_os" . && exit 1
```

**If ANY gate fails → STOP. Do not proceed to next phase. Diagnose and fix first.**

---

# 9. Policies

## 9.1 Zero Broken Imports Policy

No phase may complete if any import statement in the codebase references a path that no longer exists. Verification:
```bash
grep -rn "from " --include="*.py" . | grep -v node_modules | grep -v __pycache__ | while read line; do
  # Check if the imported module still exists
  ...
done
```

## 9.2 Zero Temporary Paths Policy

No symlinks, no temporary path aliases, no "we'll clean this up later" paths. Every move is final and complete within its phase.

## 9.3 Do Not Change Architectural Boundaries

This migration reorganizes **files and directories only**. It does NOT:
- Split `salesos/` into multiple apps
- Change Python package structure within `salesos/backend/`
- Change `@salesos/*` package structure within `salesos/frontend/`
- Modify business logic
- Change API endpoints
- Change database schemas
- Introduce new dependencies

## 9.4 Atomic Commits

Each phase = 1 commit. Commit message format:
```
refactor(migration): phase N — <description>

- Moved: <list of moves>
- Updated: <list of updates>
- Deleted: <count> files
- Gate: PASSED (lint, typecheck, test, build, docker, smoke, arch)
```

---

# 10. Success Metrics

| Metric | Before | After | Target |
|---|---|---|---|
| Root directory entries | 553 | — | <30 |
| `.tmp_*` files at root | ~300 | — | 0 |
| `tmp_*.py` files at root | ~38 | — | 0 |
| Scraper directories at root | 4 | — | 0 |
| Presentation files at root | 5 | — | 0 |
| Docker files at root | 3 | 3 (keep) | 3 |
| Markdown files at root | 15 | — | 3 |
| Python scripts at root | 31+ | — | 0 |
| Empty/stale directories | 3 | — | 0 |
| Broken imports | 0 | — | 0 |
| CI workflow failures | 0 | — | 0 |
| Developer onboarding time | ~30 min | — | ~10 min |

---

# 11. Decision Log Template

Each phase produces `migration-log/phase-NN.md`:

```markdown
# Phase NN: <Title>

## Date
YYYY-MM-DD

## Why did we move this?
<Reason for this phase>

## What changed?
- Moved: <list>
- Updated: <list>
- Deleted: <list>

## What did NOT change?
<List of things intentionally left alone>

## Risks
<Known risks and mitigations>

## Rollback procedure
<Exact steps to undo this phase>

## Gate results
- [ ] Lint: PASS/FAIL
- [ ] Typecheck: PASS/FAIL
- [ ] Unit Test: PASS/FAIL
- [ ] Build: PASS/FAIL
- [ ] Docker Build: PASS/FAIL
- [ ] Smoke Test: PASS/FAIL
- [ ] Architecture Check: PASS/FAIL

## Notes
<Any additional context>
```

---

## Appendix A: File Count Summary

| Category | Count |
|---|---|
| Files to DELETE (Phase 1) | ~380 |
| Files to MOVE (Phase 3) | 48 |
| Files to MOVE (Phase 4) | ~50 |
| Files to MOVE (Phase 5) | 6 |
| Files to MOVE (Phase 6) | 10 |
| Files to MOVE (Phase 7) | 48 |
| Files to MOVE (Phase 8) | 10 |
| Files to MOVE (Phase 9) | 9 |
| Files to DELETE (Phase 10) | ~31 |
| Files to UPDATE (Phase 11) | 5-7 |
| **Total operations** | **~597** |

## Appendix B: Rollback Quick Reference

| Phase | Rollback Command |
|---|---|
| 1 | `git checkout HEAD~1 -- .` |
| 2 | `rmdir` all created dirs |
| 3 | `mv packages/scrapers/* balady_scraper/ najiz_scraper/ rega_scraper/ taqeem_scraper/` |
| 4 | `mv packages/data/* data/` |
| 5 | `mv packages/widget-template/* WidgetTemplate/` |
| 6 | `mv assets/presentations/*.pptx .` etc. |
| 7 | `mv archive/engineering-os/* engineering-os/` etc. |
| 8 | `mv salesos/docs/architecture/SALESOS_*.md .` etc. |
| 9 | `mv docs/guides/* docs/ops/` |
| 10 | `git checkout HEAD~1 -- *.py` |
| 11 | `git checkout HEAD~1 -- .github/ .gitignore .engineering/ AGENTS.md` |
| 12 | `git revert <merge-commit>` |

---

**Status:** APPROVED — Ready for execution.  
**Execution:** Phase by phase, gate by gate, with decision log per phase.
