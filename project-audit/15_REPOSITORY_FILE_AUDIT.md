# 15 — Repository & File Audit

**Purpose:** classify every notable directory, identify duplicates / stale / dead / hygiene issues. **No deletions performed.** Recommendations only.

---

## 1. Top-level classification

| Path | Class | Purpose | Recommendation |
|------|-------|---------|----------------|
| `.ai/` | Governance | Retired AI agent registry (moved to `.cursor/rules/` per rules) | Confirm archived; do not use for new agent config |
| `.claude/` | Meta / agent | Claude-specific config | Keep |
| `.cursor/` | Meta / agent | Cursor rules + workflows | Keep — active |
| `.engineering/` | Retired governance | 30+ EOS/engineering catalog files (deleted in staged git) | **Retire visibly** — mark `DEPRECATED.md` inside |
| `.github/` | CI | 9 workflows + CODEOWNERS + dependabot.yml | Keep — actively used |
| `.git/` | VCS | Local git store | Keep |
| `AGENTS.md` | Governance | Agent essentials + 39 session summaries (78 KB) | Keep — authoritative |
| `PRODUCT_BIBLE.md` | Product | Product narrative | Keep + reconcile with `AI_HONESTY.md` (dual-bible hazard EAB-001-P1-DOC-01) |
| `README.md` | Public | Repo README | **Rewrite Domains table** (see gap G-03) |
| `RUNBOOK.md` | Ops | System runbook | Verify freshness |
| `.env.example` (root) | Config | Root env template (4.9 KB) | Keep |
| `.env.local` | Config | Local dev env — assumed gitignored | Verify `.gitignore` |
| `docker-compose.yml` (root) | Infra | Lighter local dev stack | Keep + document scope |
| `Dockerfile.railway`, `.railway.celery` | Infra | Railway build | Keep |
| `railway.json` + `railway.beat.json` + `railway.worker.json` | Infra | Railway service configs | Keep |
| `.gitleaks.toml`, `.semgrepignore`, `.trivyignore` | Security | Scanner ignores | Keep |
| `.gitmodules` | VCS | engineering-os submodule | Keep or retire (see below) |
| `salesos/` | Application | Main product tree | Keep — canonical |
| `docs/` | Docs | 27 subfolders (adr, ai, api, audit, architecture, backend, compliance, current-state, data, design, frontend, incidents, migration, operations, ops, program, reality-check, reference, releases, reports, roadmap, security, ux, v2, vnext, docs, archive) | **Hygiene sprint** — see §3 |
| `packages/` | Shared | scrapers, data pipelines, widget-template — **and nested `packages/packages/data`** | **Cleanup nested duplicate** |
| `engineering-os/` | Governance submodule | ADRs / kernel / governance | Confirm live or archive; verify `.gitmodules` valid |
| `infrastructure/` | Infra | Contains only README + nested `infrastructure/infrastructure/` | **Cleanup nested duplicate** |
| `migration-log/` | History | phase-01..10.md restructure logs | Keep — historical |
| `archive/` | Retired | data-files, engineering-recovery, legacy-configs, old-outputs, sales-os — **plus nested `archive/archive/`** | Verify `.gitignore`; cleanup nested duplicate |
| `assets/` | Brand/marketing | Presentations, reports, branding | Keep |
| `scripts/` | Ops | Root-level scripts | Keep |
| `salesos_test_export/` | Data | `salesos_test.dump` for Phase 7-A restore | Keep during pilot; move to secure storage before production |
| `project-audit/` | Audit | This audit (created 2026-09-12) | Ephemeral audit artifact |

---

## 2. `salesos/` sub-inventory

| Path | Class | Notes |
|------|-------|-------|
| `salesos/backend/app/` | Application | 37 modules + 20 routers + boot |
| `salesos/backend/domains/` | Application | 18 DDD domain packages |
| `salesos/backend/intelligence/` | Application | Copilot agents + evaluation + governance |
| `salesos/backend/runtime/` | Application | 18 runtime engines |
| `salesos/backend/pipeline/` | Application | Data pipelines |
| `salesos/backend/sdk/` | Application | Auth JWKS etc. |
| `salesos/backend/application/` | Application | Dashboard router + orchestration |
| `salesos/backend/platform/` | Application | Cross-cutting engines |
| `salesos/backend/memory/` | Docs | Technical-debt catalog |
| `salesos/backend/cli/` | Application | CLI tools |
| `salesos/backend/mcp_server/` | Integration | MCP protocol server |
| `salesos/backend/knowledge-packs/` | Content | Signal Marketplace packs |
| `salesos/backend/scripts/` | Ops | Ingestion, seeding, dry-run, safety, drift gate scripts |
| `salesos/backend/tests/` | Testing | Unit/integration/evaluation/perf tests |
| `salesos/backend/docs/` | Docs | Internal SalesOS docs |
| `salesos/backend/data/` | Data | Test fixtures, samples |
| `salesos/backend/benchmark/` + `benchmarks/` | Perf | **Two benchmark directories** — investigate consolidation |
| `salesos/backend/demo/` | Demo | Demo fixtures |
| `salesos/backend/design_tokens/` | UI tokens | Backend-side token exports |
| `salesos/backend/outputs/` | Runtime output | Should be `.gitignored` |
| `salesos/backend/orphan_dump.txt` (~2026-08-28) | Diagnostic | Verify still needed; move to `outputs/` or delete |
| `salesos/backend/test_reg.py`, `test_store.py`, `direct_import.py` | Scratch | Verify still needed |
| `salesos/backend/celerybeat-schedule` | Runtime | Ephemeral state; `.gitignore` |
| `salesos/backend/.tmp-runs-tip8.json` | Scratch | Delete or `.gitignore` |
| `salesos/backend/.coverage` | Coverage | `.gitignore` |
| `salesos/backend/.env` | Config | Verify `.gitignore` |
| `salesos/backend/.mypy_cache_*` × 12 | Cache | **Should be `.gitignored`; remove from disk** |
| `salesos/backend/.ruff_cache` | Cache | `.gitignore` |
| `salesos/backend/.venv/` | Python venv | **Must NOT be in repo tree; move outside** |

| Path | Class | Notes |
|------|-------|-------|
| `salesos/frontend/src/app/` | Application | Next.js App Router |
| `salesos/frontend/src/app/v3/` | Application | Canonical UI (40 pages) |
| `salesos/frontend/src/app/(dashboard)/` | Legacy | 78 pages — retain / retire decision needed |
| `salesos/frontend/src/app/(auth)/` | Application | Login/register |
| `salesos/frontend/src/app/api/` | Application | 2 route handlers |
| `salesos/frontend/src/app/fe-sec-02/` | Diagnostic | FE-SEC-02 vertical slice per config; verify still needed |
| `salesos/frontend/src/app/system/` | Diagnostic | `/system` for build parity checks |
| `salesos/frontend/packages/` | Shared FE | design-language, ui, widget-sdk, decision-STUB, agents-STUB, tokens |
| `salesos/frontend/apps/` | Multi-app | verify |
| `salesos/frontend/e2e/` | Testing | Playwright |
| `salesos/frontend/tests/` | Testing | Jest + Playwright shared |
| `salesos/frontend/coverage/` | Coverage | `.gitignore` |
| `salesos/frontend/playwright-report/` | Report | `.gitignore` |
| `salesos/frontend/test-results/` | Report | `.gitignore` |
| `salesos/frontend/.npm-cache-dom/` | Cache | `.gitignore` |
| `salesos/frontend/.tmp-dom-pack/` | Cache | `.gitignore` or delete |
| `salesos/frontend/node_modules/` | Deps | must be `.gitignored` |
| `salesos/frontend/tsconfig.tsbuildinfo` + `tsconfig.test.tsbuildinfo` | Cache | `.gitignore` |
| `salesos/frontend/PRODUCT_*.md` (3 files) | Docs | Verify freshness or archive |

| Path | Class | Notes |
|------|-------|-------|
| `salesos/infra/caddy/` | Infra | Caddy config for TLS termination (per README rc1) |
| `salesos/infra/docker/` | Infra | Backup Dockerfile + others |
| `salesos/infra/k8s/` | Infra | K8s manifests — quarantined per DEC-149 |
| `salesos/infra/monitoring/` | Infra | Prometheus/Grafana/Loki configs |
| `salesos/infra/scripts/` | Infra | Backup + restore scripts |
| `salesos/infra/staging/` | Infra | Staging-specific |
| `salesos/infra/terraform/` | Infra | Terraform modules (AWS me-south-1 per README) |
| `salesos/platform/` | Shared | Cross-cutting engines (server-side) |
| `salesos/application/` | Application | Additional application code |
| `salesos/knowledge-packs/` | Content | Signal marketplace source packs |
| `salesos/memory/` | Docs | Memory catalog |
| `salesos/reports/` | Reports | Runtime reports |
| `salesos/cli/` | Tools | CLI helpers |
| `salesos/tests/` | Testing | Cross-cutting integration |

---

## 3. `docs/` sub-inventory

**27 subfolders + `docs/docs/`** (nested self-duplicate).

| Subfolder | Purpose | Freshness | Recommendation |
|-----------|---------|-----------|----------------|
| `adr/` | ~40+ Architecture Decision Records | Actively maintained | Keep |
| `ai/` | AI-specific docs | Mixed | Keep |
| `api/` | API docs including OPENAPI.md | Verify freshness | Keep |
| `architecture/` | Architecture docs | Older | Keep as historical |
| `archive/` | Retired docs | Historical | Keep archived |
| `audit/` | 10 audit sub-trees (current-state, evidence-review, evidence-review-peer, execution, final-production-decision, final-release-board, **ga-engineering-audit**, legacy-reports, production-gap-closure, star-audit) | ga-engineering-audit is LIVE authority; others historical | Keep |
| `backend/` | Backend docs | Verify | Keep |
| `compliance/` | Compliance docs | Verify | Keep |
| `current-state/` | 19 files (2026-07-15 snapshot) | **STALE** for page/feature counts | Add "STALE — see PAGE_MAP_SALESOS.md" header |
| `data/` | Phase 6 + Phase 7 data intelligence (22 + 12 files) | LIVE authority for data | Keep |
| `design/` | Design docs | Verify | Keep |
| `frontend/` | Frontend docs | Verify | Keep |
| `incidents/` | Incident reports | Sparse | Keep |
| `migration/` | Migration docs | Historical | Keep |
| `operations/` + `ops/` | **Two ops folders** | Confusion — potentially duplicates | Consolidate |
| `program/` | Program docs (DEC-107 etc.) | Actively maintained | Keep |
| `reality-check/` | Reality-check docs | Verify | Keep |
| `reference/` | Reference schemas | Verify | Keep |
| `releases/` | Release notes (v5.1.0-rc1) | Live | Keep |
| `reports/` | Session reports (many) | Actively maintained | Keep + prune old |
| `roadmap/` | Roadmap docs | Verify freshness | Keep |
| `security/` | Security docs | Verify | Keep |
| `ux/` | UX docs | Verify | Keep |
| `v2/` | v2-planning-era docs | Historical | Move to `archive/` |
| `vnext/` | Includes SUPERSEDED `GO_NO_GO_DECISION.md` + `GA_CHECKLIST.md` | SUPERSEDED — retained per policy | Add "SUPERSEDED" banner |
| `docs/` (nested) | Self-duplicate | Cleanup |

**Recommendation:** create `docs/INDEX.md` that codifies which subtrees are LIVE authority, which are STALE, which are SUPERSEDED, which are ARCHIVED. Current `docs/audit/INDEX.md` may partly do this.

---

## 4. Duplicates / nested self-references (repo hygiene P1)

| Pattern | Location | Impact |
|---------|----------|--------|
| Nested self-duplicate | `packages/packages/` (packages folder inside packages) | Confusion; risk of double-import |
| Nested self-duplicate | `archive/archive/` | Wasted disk; visual noise |
| Nested self-duplicate | `infrastructure/infrastructure/` | Confusion |
| Nested self-duplicate | `docs/docs/` | Confusion |
| Nested self-duplicate | `engineering-os/engineering-os/` (from listing) | Investigate |
| Nested self-duplicate | `migration-log/migration-log/` | Investigate |
| Dual FE shells | `salesos/frontend/src/app/v3/` + `salesos/frontend/src/app/(dashboard)/` | Product decision needed |
| Dual benchmark dirs | `salesos/backend/benchmark/` + `salesos/backend/benchmarks/` | Consolidate |
| Dual ops docs | `docs/operations/` + `docs/ops/` | Consolidate |
| 12× `.mypy_cache_*` in `salesos/backend/` | Various names for CI stages | Delete; add to `.gitignore` |
| `.venv/` in `salesos/backend/` | Committed / on disk | Move outside repo |

---

## 5. Stale / diagnostic files (verify still needed)

- `salesos/backend/orphan_dump.txt` (2026-08-28)
- `salesos/backend/test_reg.py`, `test_store.py`, `direct_import.py`
- `salesos/backend/celerybeat-schedule`
- `salesos/backend/.tmp-runs-tip8.json`
- `salesos/frontend/.tmp-dom-pack/`
- `salesos/frontend/tsconfig.tsbuildinfo` + `tsconfig.test.tsbuildinfo`
- `salesos/frontend/apps/` (verify if actively used)
- `salesos/frontend/src/app/fe-sec-02/`
- Docs superseded: `docs/vnext/GO_NO_GO_DECISION.md`, `docs/vnext/GA_CHECKLIST.md`
- Backup file: `salesos/backend/app/alembic/versions/0afbf3e6ae53_enable_rls_all_tenant_tables.py.bak`

---

## 6. Git repository state (CRITICAL)

- Branch: `fix/login-and-keys` (ahead of origin/master by 2 commits)
- HEAD: `3bfa6adb`
- Status: **4,748 files staged as deleted**; **27 top-level entries untracked**
- Files exist on disk
- Diagnosis: consistent with `git rm --cached -r .` never reversed
- **DANGER:** any `git commit` from current state will purge the tracked tree
- **Recommendation (not executed by this audit):**
  ```
  # 1. Backup current disk state (already stable — files exist)
  # 2. Reset index without touching working tree
  git reset HEAD -- .
  # 3. Re-verify status; now files should show as tracked/modified/unchanged based on real diff
  # 4. Only then commit / push
  ```
- **Dependabot:** 15+ open remote branches for docker/GHA/npm updates — process after index repair

---

## 7. Files/dirs that should be `.gitignored` and verified

Cross-check with `.gitignore`:

- `salesos/backend/.venv/`
- `salesos/backend/.mypy_cache_*` (all 12)
- `salesos/backend/.ruff_cache/`
- `salesos/backend/.coverage`
- `salesos/backend/.tmp-*`
- `salesos/backend/celerybeat-schedule`
- `salesos/backend/outputs/`
- `salesos/backend/orphan_dump.txt`
- `salesos/backend/test_reg.py` (if temporary)
- `salesos/frontend/node_modules/`
- `salesos/frontend/coverage/`
- `salesos/frontend/playwright-report/`
- `salesos/frontend/test-results/`
- `salesos/frontend/tsconfig*.tsbuildinfo`
- `salesos/frontend/.tmp-*/`
- `.env.local`, `.env`, `.env.staging`, `.env.production*`
- Any `*.dump`, `*.sql` snapshots outside `salesos_test_export/` (already gitignored per policy)

Confirmed present in root `.gitignore` (per `AGENTS.md` §10): `cookies.txt`, `login.json`, `railway-status.json`.

**Recommendation:** produce a hygiene commit that adds any missing entries + removes any accidentally-tracked cache files.

---

## 8. Documentation supersession chain (documented but scattered)

| Doc | Status | Superseded by |
|-----|--------|--------------|
| `docs/vnext/GO_NO_GO_DECISION.md` | SUPERSEDED | `ga-engineering-audit/00-EXECUTIVE-SUMMARY.md` |
| `docs/vnext/GA_CHECKLIST.md` | SUPERSEDED | Same |
| `docs/vnext/MASTER_PLAN.md` | SUPERSEDED (for closure order) | `SALESOS_MASTER_CLOSURE_SEQUENCE.md` |
| `docs/audit/current-state/*` | STALE for feature counts | `PHASE1-4 evidence packs` |
| `docs/audit/current-state/09-screen-inventory.md` | STALE (30 screens vs 54 today) | Nav-based inventory |
| `docs/audit/ga-engineering-audit/PAGE_MAP_SALESOS.md` | 2026-07-22 | Needs v3-first refresh |
| `docs/PROJECT_BIBLE.md` | Present | See below note |
| `PRODUCT_BIBLE.md` (root) | LIVE | Product narrative primary source |
| `AGENTS.md` (root) | LIVE | Session ledger + agent essentials |

**Dual-bible hazard EAB-001-P1-DOC-01:** `docs/PROJECT_BIBLE.md` and root `PRODUCT_BIBLE.md` may drift. Confirm which is canonical or merge.

---

## 9. Language / naming inconsistencies

- Mix of `PRODUCT_BIBLE.md` (root) vs `docs/PROJECT_BIBLE.md` (docs)
- Mix of camelCase (`checkAlembicHead.py`?) and snake_case in scripts
- Mix of `-` and `_` in folder names (e.g., `knowledge-packs`, `master_data`)
- Wave naming: WAVE0..WAVE21 in progress docs — consistent but overwhelming (21 waves)
- ADR naming: `0001..0117` — clean sequence

---

## 10. Recommended repository hygiene sprint (2 weeks)

**Week 1:**
1. Repair `fix/login-and-keys` git working tree (0.5d)
2. Add missing `.gitignore` entries; audit + remove any tracked cache files (1d)
3. Move `.venv/` outside repo (0.5d)
4. Delete 12 `.mypy_cache_*` dirs (0.5d)
5. Consolidate `benchmark/` + `benchmarks/` (0.5d)
6. Consolidate `docs/operations/` + `docs/ops/` (0.5d)
7. Investigate & fix nested self-duplicates (packages/packages, archive/archive, infrastructure/infrastructure, docs/docs, engineering-os/engineering-os, migration-log/migration-log) (1d)

**Week 2:**
1. Rewrite `README.md` §Domains to match reality (0.5d)
2. Add STALE / SUPERSEDED banners to identified docs (0.5d)
3. Rewrite `PAGE_MAP_SALESOS.md` for v3-first (1d)
4. Product decision: retire legacy `(dashboard)` shell or keep both — commit visible outcome (2d)
5. Confirm engineering-os submodule live vs archive (0.5d)
6. `docs/INDEX.md` codifying LIVE / STALE / SUPERSEDED / ARCHIVED (1d)
7. `.dockerignore` + `.vercelignore` audit (0.5d)

---

## 11. Naming / labeling recommendations

- Adopt **AQLIYA** as workspace-level identity (per user rules) — root README + Product Bible
- Keep **SalesOS** as product name
- Retire **Muhide** as external-facing (it's internal codename for dataset ingest)

---

*Repository audit — read-only, hygiene-focused. Cleanup is recommended, NOT executed by this audit.*
