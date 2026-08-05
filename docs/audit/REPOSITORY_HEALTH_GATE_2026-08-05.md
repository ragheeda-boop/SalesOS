# Repository Health Gate — 2026-08-05

**Scope:** Read-only. No files modified, moved, or deleted to produce this report.
**Purpose:** Approval gate before ADR-100 Phase 3 (Legacy Isolation).
**Repo root (git):** `Muhide/` — branch `master`, HEAD `54daec3`

---

## 1. Repository structure

Current state after ADR-100 Phases 1–2 (Safe Cleanup, Repository Documentation):

- **Canonical application:** `salesos/` — unchanged, fully populated, only tree with real `package.json`/`pyproject.toml`.
- **Governance layers (frozen/generated, per ADR-036):** `.ai/` (frozen), `.engineering/` (generated).
- **Submodule:** `engineering-os/` — tracked in `.gitmodules`, independent remote.
- **Shared tooling:** `packages/` (scrapers, data, widget-template stub), `data/` (pipeline artifacts).
- **Documentation:** `docs/` (product/audit/ADR layer, now includes `docs/audit/legacy-reports/`), `assets/` (now includes populated `assets/reports/`).
- **Archive:** `archive/sales-os/` — properly populated (Phase 1 correction).
- **Root loose Markdown:** reduced from 16 to 5 (`README.md`, `AGENTS.md`, `PRODUCT_BIBLE.md`, `RUNBOOK.md`, `REPO_TOPOLOGY_AUDIT.md`) — all intentionally retained per Phase 2's stated reasoning.
- **Not yet addressed (deferred by explicit user constraint):** root `infrastructure/` (empty scaffold), root `railway.json` + `Dockerfile.railway` (conflicting deploy config).

Structure is internally consistent with ADR-100. No new topology conflicts found since Phase 2.

## 2. Git integrity

| Check | Result |
|---|---|
| `git fsck --connectivity-only` | **PASS** — clean, no dangling/missing objects reported |
| `HEAD` | `54daec3eb175453118178b2972532e7c972589d3` on `master` |
| Submodule status | `engineering-os` → `b82b9fbee2781fa72357a61fe8dfc8a25b8de3bf` (heads/main), no `+`/`-` prefix — in sync, no uncommitted submodule changes |
| Nested `.git` dirs | Only `.git` (root) and `engineering-os/.git` (submodule) — no stray nested repos |
| Working tree state | Multiple modified/untracked files from Phases 1–2 (expected — not yet committed by user); no unexpected changes outside touched paths (re-verified scoped to `salesos/` and `engineering-os/`: **empty**, confirming zero code/runtime drift) |

**Note:** a full unscoped `git status` over the entire working tree times out in this sandbox (large repo, many untracked data/report files) — all integrity checks above were run either repo-wide via `git fsck` (fast, authoritative) or path-scoped (fast, targeted). No blind spots identified, but flagging the tooling limitation for transparency.

## 3. Configuration files

| File | Status |
|---|---|
| `salesos/docker-compose.yml`, `.prod.yml`, `.test.yml`, `frontend/docker-compose.yml`, `infra/staging/*.yml` | Valid YAML (parsed clean) |
| Root `docker-compose.yml` | Valid YAML; confirmed intentionally distinct dev-only profile (documented in README as of Phase 2) |
| `salesos/frontend/package.json` | Valid JSON, scripts present and coherent (`dev`, `build`, `test`, `typecheck`, etc.) |
| `salesos/backend/pyproject.toml` | Valid TOML; declares `python = "^3.12"` — sandbox only has Python 3.10.12 available, so `poetry install`/`lock` could not be executed here (environment limitation, not a repo defect) |
| `.env*` files (11 total, root + `salesos/`) | **PASS on hygiene** — only `.example`/`.template` variants are git-tracked; all real `.env`, `.env.local`, `.env.production`, `.env.staging`, `.env.staging.local` are untracked. No secret-bearing file found committed to git. |
| `.semgrepignore`, `.gitleaks.toml`, `.trivyignore`, `.pre-commit-config.yaml` | Present at root, correctly scoped repo-wide; `.semgrepignore` already updated in Phase 1 to remove the stale `sales-os/` entry |

## 4. Build entry points

| Entry point | Status |
|---|---|
| `salesos/Makefile` | Present — `install`, `dev`, `test`, `lint`, `migrate`, `build`, `up`/`down` targets defined, reference `backend/` and `frontend/` correctly (relative to `salesos/`) |
| `salesos/start.sh`, `start.bat`, `setup.ps1` | Present, assume `cwd = salesos/` — consistent with README's documented Quick Start (`cd salesos` first) |
| `salesos/frontend/package.json` scripts | `dev`, `build`, `start`, `test`, `test:e2e`, `typecheck`, `storybook` — all present, no obviously broken script references |
| `salesos/backend/pyproject.toml` | Poetry-managed; could not execute `poetry install`/`check` in this sandbox (no network-capable poetry resolve, Python version mismatch as above) — **not validated end-to-end this pass** |
| Root — no `package.json`/`Makefile`/entry point | **By design** — confirmed intentional per ADR-100; all tooling entry points live inside `salesos/` |

## 5. Deployment configuration

| Config | Status |
|---|---|
| `salesos/railway.json` | Builds via `salesos/backend/Dockerfile`; handles `celery-worker`/`celery-beat` service variants; includes `preDeployCommand: alembic upgrade head` |
| Root `railway.json` + `Dockerfile.railway` | Builds backend-only via `Dockerfile.railway` (which `COPY`s from `salesos/backend/...`); no celery variant handling, no pre-deploy migration step | 
| **Conflict status** | **Unresolved** — cannot determine from repo contents alone which one Railway's dashboard actually builds from. Flagged in ADR-100 as a blocking item; still blocking. **Do not delete either without out-of-band confirmation.** |
| `salesos/docker-compose.prod.yml` | Present, not evaluated this pass (out of scope — deployment content review, not topology) |
| `salesos/infra/k8s/*` (37 manifests) | Present, referenced by README and `.engineering/24_REPOSITORY_MANIFEST.json`; not evaluated this pass |
| `salesos/infra/terraform/*` | Present (`main.tf`, `outputs.tf`, `variables.tf`); not evaluated this pass |
| `.github/workflows/` | 7 workflows: `ci.yml`, `deploy.yml`, `deploy-staging.yml`, `deploy-production.yml`, `docker-smoke.yml`, `security-scan.yml`, `e2e-stage7.yml` — presence confirmed, contents not audited this pass |
| `salesos/frontend/vercel.json` | Present; `.vercel/project.json` at repo root also present — Vercel deploys frontend directly via GitHub integration per `docs/program/decisions/DEC-149-CANONICAL-DEPLOY-RAILWAY-VERCEL.md` (found during reference checks) |

## 6. Empty directories

Repo-wide automated scan was inconclusive in this sandbox (times out on the full tree even with standard prune exclusions — likely mount/IO characteristics, not a repo defect). **Directly verified** the known candidates instead:

| Directory | Empty? |
|---|---|
| `infrastructure/cloud/` | **Yes — empty** |
| `infrastructure/observability/` | **Yes — empty** |
| `infrastructure/scripts/` | **Yes — empty** |
| `packages/widget-template/` | **Yes — empty** (destination stub for the still-pending `WidgetTemplate/` move) |
| `archive/engineering-os/`, `archive/engineering-recovery/` | N/A — deleted in Phase 1, confirmed absent |
| `archive/sales-os/` | **No — populated** (14 files, Phase 1 correction) |

No other empty directories were found among manually spot-checked candidates. Full exhaustive coverage of the entire tree was not achieved this pass — noted as a tooling limitation, not asserted as a clean bill of health beyond what was checked.

## 7. Legacy candidates — classification

| Item | Classification | Rationale |
|---|---|---|
| Root `infrastructure/{cloud,observability,scripts}/` (empty) | **PENDING** | Blocked on user confirmation of intent (dead scaffold vs. future `salesos/infra/` destination) — explicit user constraint from ADR-100 approval: treat as "Pending Removal," do not delete yet. |
| Root `railway.json` + `Dockerfile.railway` | **PENDING** | Blocked on confirming which config Railway's dashboard actually builds from — explicit user constraint: treat as "Legacy Candidate," do not remove either. |
| `WidgetTemplate/` (root, has content) vs. `packages/widget-template/` (empty stub) | **MOVE** | Non-conflicting, no blocking dependency identified; scheduled as ADR-100 Phase 4 ("Pending Migration Completion"). Not yet executed. |
| `engineering-recovery/` (root, 14 files) | **ARCHIVE** (tentative — not yet actioned) | Historical incident post-mortem, no longer active; `docs/audit/current-state/15-documentation-audit.md` already classifies it 🟢 Historical. Candidate for `archive/engineering-recovery/` in a future phase — not part of the four phases already scoped under ADR-100's current execution order. |
| `salesos/security-audit-report.json`, `-final.json`, `-latest.json`, `-v2.json` (4 files) | **PENDING** | Four point-in-time security scan snapshots inside the canonical app. Likely superseded-by-latest pattern (similar to the SALESOS_*.md audits already archived), but disposition requires knowing which is actually consumed by CI/tooling before any action — inside `salesos/`, out of this ADR's directory-topology scope; flagged for a separate decision. |
| `salesos/benchmark.db` | **PENDING** | Looks like a generated/local artifact (SQLite benchmark output) committed or left in the working tree; likely `DELETE` candidate but not verified against `.gitignore` coverage this pass. |
| `salesos/.tmp-alembic-revs.txt`, `.tmp-ci22-*.txt`, `.tmp-staging-schema.sql` | **PENDING** (likely DELETE) | Naming matches the exact pattern `migration-log/phase-01.md` already used to justify deleting ~300 similar `.tmp_*` artifacts elsewhere in the repo. Inside `salesos/`, out of this ADR's scope to unilaterally remove; flagged for consistency review. |
| `./__pycache__/.tmp_land_fe_*.pyc` (root, 3 files) | **DELETE** (low risk) | Compiled bytecode cache for already-cleaned `.tmp_*` source scripts (per `migration-log/phase-01.md`); regenerable, gitignored by convention. Not executed this pass — flagged for Phase 3/4 or a dedicated hygiene pass. |
| `output/SALESOS_*.md` (×4), `notion_analysis.md` | **DELETE** (as broken references) | Confirmed these paths do not exist anywhere in the repository. Already flagged 🔴 BROKEN in `docs/audit/current-state/15-documentation-audit.md` (Phase 2). No file to delete — only the stale *reference* should eventually be removed once acknowledged; currently marked, not removed, per "do not delete historical documents." |
| `sales-os/` (root, duplicate product tree) | **ARCHIVE — done** | Resolved in Phase 1: properly copied to `archive/sales-os/`, root copy removed. No further action. |
| `archive/engineering-os/`, `archive/engineering-recovery/` (empty stubs) | **DELETE — done** | Resolved in Phase 1. No further action. |
| `docs/PROJECT_BIBLE.md` vs. root `PRODUCT_BIBLE.md` | **KEEP** (both, as-is) | Confirmed genuinely different documents (Project = engineering authority, ratified v5.1.0-rc1; Product = product vision, v1) via header inspection — not duplicates. Naming similarity is a navigation hazard, not a structural defect; no action taken, flagged for awareness only. |
| Root `docker-compose.yml` vs. `salesos/docker-compose.yml` | **KEEP** (both) | Confirmed intentionally different profiles (dev-lite vs. staging/prod-shaped); documented in README as of Phase 2. Not a duplicate. |
| `REPO_TOPOLOGY_AUDIT.md` (root) | **KEEP** (for now) | Actively cross-referenced by ADR-100's governance chain; relocation deferred to avoid immediate link churn (Phase 2 decision). |

## 8. Duplicate assets

| Asset | Duplication found? |
|---|---|
| `docker-compose.yml` (root vs. `salesos/`) | Same filename, **different content by design** — not a true duplicate (see §7) |
| `railway.json` (root vs. `salesos/`) | Same filename, **conflicting content** — genuine duplication risk, unresolved (see §5, §7) |
| `sales-os/` vs `archive/sales-os/` | Resolved in Phase 1 — no longer duplicated |
| `security-audit-report*.json` (4 variants in `salesos/`) | Likely duplicative snapshots — not diffed this pass (inside canonical app, out of topology scope); flagged PENDING above |
| `PRODUCT_BIBLE.md` vs `docs/PROJECT_BIBLE.md` | Confirmed **not** duplicates — different documents, similar names |
| `RUNBOOK.md` (root) vs `engineering-os/RUNBOOK.md` (submodule) | Byte-identical header; full-file diff not performed this pass. Not classified as actionable duplication since `engineering-os/` is an external submodule — out of repo's direct control. |

## 9. Broken references

Carried forward from Phase 2's link validation (still accurate as of this gate — no new breaks introduced):

- `output/SALESOS_ENGINEERING_OPERATIONS_MANUAL.md`, `-ENTERPRISE_COMPANY_INTELLIGENCE_ARCHITECTURE.md`, `-IMPLEMENTATION_BLUEPRINT.md`, `-PRODUCT_DELIVERY_PLAYBOOK.md` — **BROKEN**, `output/` does not exist anywhere in the repo.
- `notion_analysis.md` — **BROKEN**, file does not exist anywhere in the repo.

Both already marked 🔴 in `docs/audit/current-state/15-documentation-audit.md`. No new broken references found during this gate's checks of README.md and AGENTS.md link targets (all resolved clean).

---

## Gate summary

| Category | Result |
|---|---|
| Repository structure | ✅ Consistent with ADR-100 |
| Git integrity | ✅ Clean (`fsck` clean, submodule in sync, no scope leakage into `salesos/`/`engineering-os/`) |
| Configuration files | ✅ Valid; secrets hygiene confirmed clean |
| Build entry points | ⚠️ Present and coherent; Python backend not executable end-to-end in this sandbox (environment limitation) |
| Deployment configuration | ⚠️ Railway config conflict remains unresolved (expected — blocked pending your confirmation) |
| Empty directories | ⚠️ 4 confirmed empty (`infrastructure/` ×3 subdirs, `packages/widget-template/`) — both already tracked as pending phases |
| Legacy candidates | 3 new PENDING items surfaced (`security-audit-report*.json` ×4, `benchmark.db`, `.tmp-*` files inside `salesos/`) — all inside the canonical app, out of ADR-100's directory-topology scope, flagged for a separate decision rather than actioned |
| Duplicate assets | 1 unresolved genuine duplication (Railway config); rest confirmed either resolved or not true duplicates |
| Broken references | 2 pre-existing, already flagged, no new breaks |

**No blocking issues found for proceeding to Phase 3 (Legacy Isolation) as scoped** — Phase 3 only marks `infrastructure/` and the Railway configs, which this gate confirms are still in the expected state (empty scaffold; unresolved conflicting deploy config). The newly surfaced `salesos/`-internal items (security reports, benchmark.db, `.tmp-*` files) are **not** part of Phase 3's scope and are called out here only for visibility — recommend a separate decision before touching them.
