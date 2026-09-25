# D: Drive Migration Audit — AISalesOS Full Restructure

> **Date:** 2026-09-05
> **Current Path:** `C:\Users\raghe\Documents\Muhide`
> **Target Path:** `D:\AISalesOS`
> **Git Branch:** `fix/login-and-keys` (4 modified + 14 untracked files)
> **Verdict:** **READY WITH CONDITIONS** (P0 path fixes required before copy)

---

## Executive Summary

This audit covers the complete relocation of the AISalesOS project from `C:\Users\raghe\Documents\Muhide` to `D:\AISalesOS`. The project is a large monorepo with a FastAPI backend (108 Alembic migrations, 38 modules, 20 AI agents), Next.js frontend (21 packages, 109 pages), 8 Docker Compose files, 3 Dockerfiles, 5 Railway configs, 9 GitHub Actions workflows, and 248 test files.

**Key finding:** The Docker infrastructure uses exclusively relative paths and named volumes — fully relocatable. However, **17 hardcoded absolute paths exist in Python scripts and test files** that will break on host-side execution after relocation.

**Recommended approach:** Full restructure with:
1. Commit pending changes
2. Fix 17 P0 hardcoded paths
3. Archive loose/temporary files
4. Copy to `D:\AISalesOS`
5. Verify and test

---

## 1. Project Inventory

### 1.1 Directory Structure Map

```
C:\Users\raghe\Documents\Muhide\ (ROOT)
│
├── salesos/                          # PRIMARY PRODUCT (FastAPI + Next.js)
│   ├── backend/                      # Python 3.12 FastAPI backend
│   │   ├── app/                      # Main app (alembic, modules, routers, config)
│   │   ├── domains/                  # Domain layer (20 domains)
│   │   ├── intelligence/             # AI agents + providers (20 agents)
│   │   ├── runtime/                  # Runtime engines (33 subdirectories)
│   │   ├── sdk/                      # SDK layer (30 items)
│   │   ├── pipeline/                 # Data pipeline
│   │   ├── mcp_server/              # MCP server
│   │   ├── scripts/                 # 50+ operational scripts
│   │   ├── tests/                   # 248 test files
│   │   ├── pyproject.toml           # Poetry config
│   │   ├── alembic.ini              # DB migration config
│   │   └── Dockerfile               # Backend container
│   │
│   ├── frontend/                     # Next.js 15 + React 19
│   │   ├── src/                     # App Router (34 dashboard + 28 v3 pages)
│   │   ├── packages/               # 21 internal packages
│   │   ├── apps/                   # 4 standalone apps
│   │   ├── e2e/                    # 33 Playwright tests
│   │   ├── node_modules/           # 514 MB (EXCLUDE from copy)
│   │   ├── package.json            # Dependencies
│   │   └── Dockerfile              # Frontend container
│   │
│   ├── infra/                       # Infrastructure as Code
│   │   ├── docker/                 # Docker configs (postgres, backup, monitoring)
│   │   ├── k8s/                    # 23 Kubernetes manifests
│   │   ├── terraform/              # Terraform IaC
│   │   ├── staging/               # Staging compose files
│   │   ├── scripts/               # 8 infra scripts (backup, restore, deploy)
│   │   └── caddy/                 # Reverse proxy config
│   │
│   ├── knowledge-packs/            # 10 industry knowledge packs
│   ├── docker-compose.yml          # Authoritative dev compose (475 lines)
│   ├── docker-compose.prod.yml     # Production compose (559 lines)
│   ├── docker-compose.test.yml     # Test compose (62 lines)
│   ├── Makefile                    # Build automation
│   ├── railway.json                # Railway deployment
│   ├── scripts/                    # FE/BE scripts (50+ deploy/smoke/load)
│   ├── docs/                       # SalesOS-specific docs (66 items)
│   └── .env*                       # Environment files (8 files with secrets)
│
├── docs/                            # All documentation
│   ├── audit/                      # 42 audit items (400+ files)
│   │   ├── ga-engineering-audit/   # Authoritative GA audit (94 files)
│   │   └── star-audit/            # STAR audit (33 files)
│   ├── adr/                        # 29 Architecture Decision Records
│   ├── data/                       # Data pipeline docs (phase6, phase7)
│   ├── ops/                        # 23 ops runbooks
│   ├── program/                    # 166 program management files
│   ├── releases/                   # Release notes (v5.1.0, rc-1, v1.0.0-ga)
│   └── reports/                    # 21 reports
│
├── packages/                        # Internal packages
│   ├── data/                       # Data pipeline (20 scripts, multiple data stages)
│   ├── scrapers/                   # Web scrapers (balady, najiz, rega, taqeem)
│   └── widget-template/           # Widget template
│
├── archive/                         # Legacy code
│   ├── sales-os/                   # Legacy sales-os code
│   └── engineering-recovery/       # Recovery docs
│
├── infrastructure/                  # Stub (real infra in salesos/infra/)
├── engineering-os/                  # Git submodule (engineering governance)
├── migration-log/                   # 10 phase migration logs
├── scripts/                         # 6 root utility scripts
├── outputs/                         # Generated outputs (1 file)
├── assets/                          # Branding, presentations, reports
│
├── .github/                         # CI/CD
│   ├── workflows/                  # 9 GitHub Actions
│   └── dependabot.yml              # Dependabot config
│
├── .ai/ .claude/ .cursor/          # IDE configs
├── .engineering/                    # Engineering metadata
├── .vercel/ .vercelignore          # Vercel deployment
│
├── AGENTS.md                        # Agent instructions (authoritative)
├── PRODUCT_BIBLE.md                 # Product bible
├── README.md                        # Project readme
├── RUNBOOK.md                       # Operational runbook
├── docker-compose.yml               # Root legacy compose
├── Dockerfile.railway               # Railway deployment
├── Dockerfile.railway.celery        # Railway Celery worker
├── railway.json / .beat.json / .worker.json  # Railway configs
├── .env.example / .env.local        # Environment templates
│
├── FOOD.csv / FOOD - ENRICHED.csv / FOOD - MOBILE.xlsx  # Data files (LOOSE)
├── LEAD GRN/                        # Loose directory
└── get-docker.sh                    # Docker installer script
```

### 1.2 File Count Summary

| Category | Count | Notes |
|----------|-------|-------|
| Backend Python modules | 38 | Under `salesos/backend/app/modules/` |
| Intelligence agents | 20 | Under `salesos/backend/intelligence/agents/` |
| Runtime engines | 33 | Under `salesos/backend/runtime/` |
| Alembic migrations | 108 | Under `salesos/backend/app/alembic/versions/` |
| Unit test files | 211 | Under `salesos/backend/tests/unit/` |
| Integration test files | 37 | Under `salesos/backend/tests/integration/` |
| E2E test files | 33 | Under `salesos/frontend/e2e/` |
| Frontend pages | 62 | 34 dashboard + 28 v3 |
| Frontend packages | 21 | Under `salesos/frontend/packages/` |
| Docker Compose files | 8 | Root + salesos + prod + test + staging (3) + FE |
| Dockerfiles | 5 | Root (2) + backend + frontend + backup |
| Railway configs | 5 | Root (3) + salesos (1) + beat |
| GitHub Actions workflows | 9 | CI, deploy (2), Docker, E2E, security, fitness, gates |
| Documentation files | 400+ | Under `docs/` |
| Knowledge packs | 9 sectors + tests | Under `salesos/knowledge-packs/` |
| Python scripts | 56+ | Under `salesos/backend/scripts/` + root `scripts/` |

---

## 2. Critical Files Inventory

### 2.1 Configuration Files (DO NOT MODIFY without testing)

| File | Purpose | Path-Dependent? |
|------|---------|-----------------|
| `salesos/backend/pyproject.toml` | Python deps (Poetry) | No — no host paths |
| `salesos/backend/alembic.ini` | DB migration config | No — `prepend_sys_path = .` |
| `salesos/frontend/package.json` | Node deps (npm workspaces) | No — relative paths |
| `salesos/frontend/next.config.js` | Next.js config | No — env vars only |
| `salesos/frontend/tsconfig.json` | TypeScript config | No — relative aliases |
| `salesos/docker-compose.yml` | Dev stack (authoritative) | No — relative mounts |
| `salesos/docker-compose.prod.yml` | Production stack | No — relative mounts |
| `salesos/docker-compose.test.yml` | Test stack | No — relative mounts |
| `salesos/backend/Dockerfile` | Backend container | No — relative COPY |
| `salesos/frontend/Dockerfile` | Frontend container | No — relative COPY |
| `railway.json` (root) | Railway deploy | No — relative Dockerfile |
| `salesos/railway.json` | Railway deploy (salesos) | No — relative Dockerfile |
| `.github/dependabot.yml` | Dependabot paths | **Yes** — `/salesos/frontend`, `/salesos/backend` |
| `.github/workflows/*.yml` | CI/CD | Check each workflow |

### 2.2 Environment Files (CONTAIN SECRETS — handle with care)

| File | Contains | Risk |
|------|----------|------|
| `salesos/.env` | Railway tokens, OpenAI API key, DB password | **HIGH** — real secrets |
| `salesos/.env.staging` | Postgres, Neo4j, JWT, Grafana passwords | **HIGH** — real staging secrets |
| `salesos/.env.staging.local` | Local staging overrides | **MEDIUM** |
| `salesos/.env.production` | Full production secrets | **HIGH** — production secrets |
| `salesos/backend/.env` | Dev DB URL, Google keys | **MEDIUM** — dev only |
| `.env.local` (root) | Vercel OIDC token | **MEDIUM** |
| `salesos/frontend/.env.local` | Vercel OIDC token | **MEDIUM** |
| `.env.example` (root) | Template — no secrets | Safe |
| `salesos/.env.example` | Template — no secrets | Safe |
| `salesos/.env.production.template` | Template — no secrets | Safe |
| `salesos/.env.staging.example` | Template — no secrets | Safe |

### 2.3 Generated Artifacts / Cache (EXCLUDE from copy)

| Path | Size | Purpose |
|------|------|---------|
| `salesos/frontend/node_modules/` | **514 MB** | npm dependencies (regenerate) |
| `.mypy_cache/` | **~9 MB** | Python type check cache |
| `.next/` | <1 MB | Next.js build cache |
| `.pytest_cache/` | <1 MB | Pytest cache |
| `.ruff_cache/` | <1 MB | Ruff linter cache |
| `__pycache__/` | <1 MB | Python bytecode |
| `salesos/backend/outputs/` | Variable | Agent reach enrichment outputs |
| `outputs/` | Variable | Generated evidence files |
| `.vercel/` | Variable | Vercel deployment cache |

### 2.4 Loose/Untracked Data Files (Review before archiving)

| File/Dir | Location | Recommendation |
|----------|----------|----------------|
| `FOOD.csv` | Root | Archive to `archive/data-files/` |
| `FOOD - ENRICHED.csv` | Root | Archive to `archive/data-files/` |
| `FOOD - MOBILE.xlsx` | Root | Archive to `archive/data-files/` |
| `LEAD GRN/` | Root | Archive to `archive/data-files/` |
| `get-docker.sh` | Root | Archive (standard Docker installer) |
| `outputs/` | Root | Archive (generated evidence) |
| `REPO_TOPOLOGY_AUDIT.md` | Root | Archive (superseded by this audit) |

---

## 3. Hardcoded Path Findings

### 3.1 P0 — WILL BREAK on host-side execution (17 files)

#### Python Scripts (13 files)

| # | File | Line | Hardcoded Path | Fix Strategy |
|---|------|------|----------------|--------------|
| 1 | `salesos/backend/scripts/muhide_v1_enrichment.py` | 39 | `C:\Users\raghe\Downloads\v1_linked_v2.parquet` | CLI arg / env var |
| 2 | `salesos/backend/scripts/muhide_v1_enrichment.py` | 40 | `C:\Users\raghe\Downloads\v1_unlinked_v2.parquet` | CLI arg / env var |
| 3 | `salesos/backend/scripts/muhide_v1_enrichment.py` | 41 | `C:\Users\raghe\Downloads\MUHIDE_extracted\02_Master_Contacts.csv` | CLI arg / env var |
| 4 | `salesos/backend/scripts/muhide_ingest_real.py` | 28 | `C:\Users\raghe\Downloads\MUHIDE_extracted` | CLI arg / env var |
| 5 | `salesos/backend/scripts/muhide_ingest_real.py` | 29 | `C:\Users\raghe\Downloads\MUHIDE_resolution_candidates.csv` | CLI arg / env var |
| 6 | `salesos/backend/scripts/muhide_ingest_real.py` | 30 | `C:\Users\raghe\Downloads\04_ER_Review\04_Entity_Resolution_Review.csv` | CLI arg / env var |
| 7 | `salesos/backend/scripts/fix_false_cr.py` | 9 | `sys.path.insert(0, r"C:\Users\raghe\Documents\Muhide\salesos\backend")` | Use `Path(__file__).resolve().parents[1]` |
| 8 | `salesos/backend/scripts/classify_identity.py` | 3 | `sys.path.insert(0, r"C:\Users\raghe\Documents\Muhide\salesos\backend")` | Use `Path(__file__).resolve().parents[1]` |
| 9 | `salesos/backend/scripts/agent_reach_missing_data_completion_plan.py` | 72 | `r"C:\Users\raghe\Documents\Muhide\salesos\backend\outputs"` | Use relative path |
| 10 | `salesos/backend/scripts/agent_reach_human_review_queue.py` | 55 | `r"C:\Users\raghe\AppData\Local\Programs\Python\Python312\python.exe"` | Use `sys.executable` |
| 11 | `salesos/backend/scripts/agent_reach_human_review_queue.py` | 57 | `r"C:\Users\raghe\Documents\Muhide\salesos\backend\outputs"` | Use relative path |
| 12 | `salesos/backend/scripts/agent_reach_domain_correction_review.py` | 48 | `r"C:\Users\raghe\Documents\Muhide\salesos\backend\outputs"` | Use relative path |
| 13 | `salesos/backend/scripts/agent_reach_domain_correction_review.py` | 52 | `r"C:\Users\raghe\AppData\Local\Programs\Python\Python312\python.exe"` | Use `sys.executable` |

#### Test Files (4 files, 9 occurrences)

| # | File | Line(s) | Hardcoded Path | Fix Strategy |
|---|------|---------|----------------|--------------|
| 14 | `salesos/backend/tests/integration/test_muhide_rehousing_db.py` | 83, 162, 266, 357, 416, 502 | `cwd=r"C:\Users\raghe\Documents\Muhide\salesos\backend"` (6x) | Use `Path(__file__).resolve().parents[N]` |
| 15 | `salesos/backend/tests/integration/test_cr_normalization_safety_db.py` | 48, 61 | `base = r"C:\Users\raghe\Documents\Muhide\salesos\backend"` (2x) | Use `Path(__file__).resolve().parents[N]` |
| 16 | `salesos/backend/tests/integration/test_muhide_ingestion_db.py` | 554 | `csv_path = r"C:\Users\raghe\Downloads\MUHIDE_resolution_candidates.csv"` | Use env var / fixture |

#### PowerShell Script (1 file)

| # | File | Line | Hardcoded Path | Fix Strategy |
|---|------|------|----------------|--------------|
| 17 | `salesos/scripts/probe-wave13-api-residuals.ps1` | 100 | `C:\Users\raghe\OneDrive - RATL Technology Ltd\Muhide\docs\...` | Use relative path |

### 3.2 P1 — Secrets in env files (8 files)

See Section 2.2 above. These files must be copied securely and **never committed to public repos**.

### 3.3 P2 — Documentation references (25+ files, 100+ occurrences)

Documentation files with hardcoded `C:\Users\raghe\...` paths. These won't break runtime but will be inaccurate after relocation. **Fix during or after migration as batch find-replace.**

Key files:
- `.engineering/03_REPOSITORY_MAP.md`
- `.engineering/11_AGENT_BOOTSTRAP.md`
- `docs/audit/10-devops-architecture.md` (14 occurrences)
- `docs/audit/ga-engineering-audit/MASTER_REPORT.md`
- `docs/audit/ga-engineering-audit/completion/SOAK-HARNESS-INSTRUCTIONS.md` (5 occurrences)
- `docs/ops/A09-OPS01-LIVE-VERIFICATION-2026-08-20.md`
- `docs/reports/OPS-EXECUTION-RUNBOOK-2026-08-24.md`
- `salesos/security-audit-report.json` (50+ occurrences)
- `salesos/security-audit-report-v2.json` (50+ occurrences)
- Plus 15+ more files

### 3.4 Safe Paths (NO FIX NEEDED)

| Category | Assessment |
|----------|-----------|
| Docker Compose volume mounts | All use relative paths or named volumes |
| Dockerfiles | All use relative COPY commands |
| `alembic.ini` | Uses `prepend_sys_path = .` (relative) |
| `pyproject.toml` | No host paths |
| `.gitmodules` | Uses HTTPS URL + relative path |
| Railway configs | Use relative Dockerfile references |
| `app/config.py` | Uses `env_file=".env"` (relative to CWD) |
| `next.config.js` | No host paths |
| Most `sys.path.insert` calls | Use `Path(__file__).resolve()` pattern |
| Docker service hostnames | All internal DNS (`postgres`, `redis`, etc.) |
| API URLs | Use env vars with localhost defaults |

---

## 4. Proposed New Structure

### 4.1 Target Layout (`D:\AISalesOS`)

```
D:\AISalesOS\
│
├── salesos/                          # PRIMARY PRODUCT (UNCHANGED internal structure)
│   ├── backend/
│   ├── frontend/
│   ├── infra/
│   ├── knowledge-packs/
│   ├── scripts/
│   ├── docs/
│   ├── tests/
│   └── docker-compose*.yml
│
├── docs/                             # All documentation (UNCHANGED)
│
├── packages/                         # Internal packages (UNCHANGED)
│
├── archive/                          # ARCHIVED (moved from root + new entries)
│   ├── sales-os/                     # Legacy code (already here)
│   ├── engineering-recovery/         # Recovery docs (already here)
│   ├── data-files/                   # NEW: FOOD.csv, LEAD GRN/, etc.
│   ├── legacy-configs/               # NEW: get-docker.sh, root docker-compose.yml
│   └── old-outputs/                  # NEW: outputs/ from root
│
├── scripts/                          # Root utility scripts (UNCHANGED)
├── infrastructure/                   # Stub (UNCHANGED)
├── engineering-os/                   # Git submodule (UNCHANGED)
├── migration-log/                    # Phase logs (UNCHANGED)
├── assets/                           # Branding (UNCHANGED)
│
├── .github/                          # CI/CD (UNCHANGED)
├── .ai/ .claude/ .cursor/           # IDE configs (UNCHANGED)
├── .engineering/                     # Engineering metadata (UNCHANGED)
│
├── AGENTS.md                         # Agent instructions
├── PRODUCT_BIBLE.md
├── README.md
├── RUNBOOK.md
├── .env.example
├── .env.local
├── .gitignore
├── .gitattributes
├── .gitmodules
├── .gitleaks.toml
├── .semgrepignore
├── .trivyignore
├── .vercelignore
│
├── Dockerfile.railway                # Railway Dockerfiles (UNCHANGED)
├── Dockerfile.railway.celery
├── railway.json
├── railway.beat.json
├── railway.worker.json
│
└── docs/migration/                   # THIS AUDIT + migration logs
    └── D_DRIVE_MIGRATION_AUDIT.md
```

### 4.2 Files to Archive (NOT delete)

| Source | Destination | Reason |
|--------|-------------|--------|
| `FOOD.csv` | `archive/data-files/` | Loose data file, not part of app |
| `FOOD - ENRICHED.csv` | `archive/data-files/` | Loose data file |
| `FOOD - MOBILE.xlsx` | `archive/data-files/` | Loose data file |
| `LEAD GRN/` | `archive/data-files/` | Loose directory |
| `get-docker.sh` | `archive/legacy-configs/` | Standard Docker installer |
| `outputs/` | `archive/old-outputs/` | Generated evidence |
| `REPO_TOPOLOGY_AUDIT.md` | `archive/legacy-configs/` | Superseded by this audit |
| `docker-compose.yml` (root) | `archive/legacy-configs/` | Legacy compose (superseded by salesos/) |

### 4.3 Files/Directories to EXCLUDE from Copy

| Path | Size | Reason |
|------|------|--------|
| `salesos/frontend/node_modules/` | **514 MB** | Regenerate via `npm install` |
| `.mypy_cache/` | ~9 MB | Regenerate automatically |
| `.next/` | <1 MB | Regenerate via `npm run build` |
| `.pytest_cache/` | <1 MB | Regenerate automatically |
| `.ruff_cache/` | <1 MB | Regenerate automatically |
| `__pycache__/` | <1 MB | Regenerate automatically |
| `.vercel/` | Variable | Vercel cache, regenerate |
| `salesos/backend/outputs/` | Variable | Generated outputs (can archive) |
| `*.pyc` files | Variable | Bytecode cache |

---

## 5. Migration Steps

### Phase 0: Preparation (Before any changes)

1. **Commit pending changes** on `fix/login-and-keys` branch
   ```bash
   git add -A
   git commit -m "chore: agent reach enrichment scripts + tests"
   ```

2. **Create backup of current state**
   ```powershell
   # Create a full archive of current project (for rollback)
   # Use robocopy or tar to create backup at D:\Muhide_BACKUP_20260905\
   ```

3. **Verify target drive exists and has space**
   ```powershell
   Get-PSDrive D
   # Ensure D:\ has sufficient space (project ~1.5 GB excluding node_modules)
   ```

### Phase 1: Fix P0 Hardcoded Paths (17 files)

**Python scripts — convert hardcoded paths to relative/CLI:**

1. `muhide_v1_enrichment.py` — Change 3 `Path(r"C:\Users\raghe\Downloads\...")` to CLI args using `argparse` or `os.environ.get()` with fallback to relative paths
2. `muhide_ingest_real.py` — Same approach for 3 paths
3. `fix_false_cr.py` — Replace `sys.path.insert(0, r"C:\...")` with:
   ```python
   sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
   ```
4. `classify_identity.py` — Same fix
5. `agent_reach_human_review_queue.py` — Replace Python executable with `sys.executable`, replace outputs dir with relative path
6. `agent_reach_domain_correction_review.py` — Same fix
7. `agent_reach_missing_data_completion_plan.py` — Replace outputs dir with relative path

**Test files — use fixture-based paths:**

8. `test_muhide_rehousing_db.py` — Replace 6 occurrences of `cwd=r"C:\..."` with:
   ```python
   backend_root = str(Path(__file__).resolve().parents[2])
   ```
9. `test_cr_normalization_safety_db.py` — Same fix for 2 occurrences
10. `test_muhide_ingestion_db.py` — Replace CSV path with env var or fixture

**PowerShell:**

11. `probe-wave13-api-residuals.ps1` — Replace OneDrive path with relative path

### Phase 2: Archive Loose Files

1. Create `archive/data-files/` and move FOOD files + LEAD GRN/
2. Create `archive/legacy-configs/` and move root `docker-compose.yml`, `get-docker.sh`, `REPO_TOPOLOGY_AUDIT.md`
3. Create `archive/old-outputs/` and move root `outputs/`

### Phase 3: Copy to D:\AISalesOS

```powershell
# Step 3a: Create target directory
New-Item -ItemType Directory -Path "D:\AISalesOS" -Force

# Step 3b: Copy with exclusions (preserve structure)
$source = "C:\Users\raghe\Documents\Muhide"
$dest = "D:\AISalesOS"

# Use robocopy with exclusions
robocopy $source $dest /E /XD node_modules .next .mypy_cache .pytest_cache .ruff_cache __pycache__ .vercel /XF *.pyc /NFL /NDL /NJH /NJS /NC /NS /NP

# Step 3c: Copy .git directory separately (needed for git operations)
robocopy "$source\.git" "$dest\.git" /E /NFL /NDL /NJH /NJS /NC /NS /NP

# Step 3d: Copy .gitmodules and other dotfiles
Copy-Item "$source\.gitignore" "$dest\.gitignore" -Force
Copy-Item "$source\.gitattributes" "$dest\.gitattributes" -Force
Copy-Item "$source\.gitleaks.toml" "$dest\.gitleaks.toml" -Force
Copy-Item "$source\.semgrepignore" "$dest\.semgrepignore" -Force
Copy-Item "$source\.trivyignore" "$dest\.trivyignore" -Force
Copy-Item "$source\.vercelignore" "$dest\.vercelignore" -Force
```

### Phase 4: Verify Copy

```powershell
# Step 4a: File count comparison
$sourceCount = (Get-ChildItem -Path $source -Recurse -File -Exclude *.pyc | Where-Object { $_.FullName -notmatch 'node_modules|\.next|__pycache__|\.mypy_cache|\.ruff_cache|\.pytest_cache|\.vercel' }).Count
$destCount = (Get-ChildItem -Path $dest -Recurse -File -Exclude *.pyc | Where-Object { $_.FullName -notmatch 'node_modules|\.next|__pycache__|\.mypy_cache|\.ruff_cache|\.pytest_cache|\.vercel' }).Count
Write-Output "Source: $sourceCount files, Dest: $destCount files"

# Step 4b: Critical files check
$criticalFiles = @(
    "salesos\backend\pyproject.toml",
    "salesos\backend\alembic.ini",
    "salesos\frontend\package.json",
    "salesos\docker-compose.yml",
    "salesos\docker-compose.prod.yml",
    "salesos\backend\Dockerfile",
    "salesos\frontend\Dockerfile",
    "AGENTS.md",
    ".gitmodules"
)
foreach ($f in $criticalFiles) {
    if (Test-Path "$dest\$f") { Write-Output "OK: $f" } else { Write-Output "MISSING: $f" }
}
```

### Phase 5: Post-Copy Fixes

1. **Update documentation paths** — Batch find-replace:
   ```
   Find:    C:\Users\raghe\Documents\Muhide
   Replace: D:\AISalesOS
   ```
   (25+ files, ~100 occurrences — only in docs/, .engineering/, migration-log/)

2. **Update `.github/dependabot.yml`** if directory paths changed

3. **Update any CI workflow paths** if needed

4. **Re-install frontend dependencies** (node_modules excluded):
   ```bash
   cd D:\AISalesOS\salesos\frontend
   npm install
   ```

5. **Verify poetry dependencies** (should work since pyproject.toml is intact):
   ```bash
   cd D:\AISalesOS\salesos\backend
   poetry install
   ```

### Phase 6: Verification

```powershell
# Step 6a: Git status in new location
cd D:\AISalesOS
git status

# Step 6b: Check no absolute paths remain in code (except docs)
rg "C:\\Users\\raghe" --type py --type-add 'script:*.ps1' -g '!docs/' -g '!archive/' -g '!.engineering/' -g '!migration-log/' D:\AISalesOS

# Step 6c: Docker compose validation
cd D:\AISalesOS\salesos
docker compose config --quiet

# Step 6d: Backend smoke test
cd D:\AISalesOS\salesos\backend
python -c "from app.main import app; print('FastAPI import OK')"

# Step 6e: Frontend build
cd D:\AISalesOS\salesos\frontend
npx tsc --noEmit
npm run build

# Step 6f: Unit tests (narrow scope)
cd D:\AISalesOS\salesos\backend
python -m pytest tests/unit/ -x --timeout=30 -q
```

### Phase 7: Verify Old Project Unaffected

```powershell
# Original project should still be intact
cd C:\Users\raghe\Documents\Muhide
git status
docker compose -f salesos/docker-compose.yml config --quiet
```

---

## 6. Rollback Plan

If migration fails at any step:

| Step | Rollback Action |
|------|-----------------|
| Phase 0 (commit) | `git reset HEAD~1` (if not pushed) |
| Phase 1 (path fixes) | `git checkout -- <files>` (revert specific changes) |
| Phase 2 (archive) | Move files back from `archive/` subdirs |
| Phase 3 (copy) | `Remove-Item -Recurse D:\AISalesOS` (only if copy incomplete) |
| Phase 4-5 (verify/fix) | Continue fixing in `C:\Users\raghe\Documents\Muhide` |
| Any phase | Work continues in original location — nothing deleted |

**Critical rule:** The original `C:\Users\raghe\Documents\Muhide` is NEVER deleted or modified destructively. It remains as fallback.

---

## 7. Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| P0 hardcoded paths break scripts | **HIGH** | Fix before copy (Phase 1) |
| Secrets exposed during copy | **MEDIUM** | Use secure copy, don't commit .env files |
| Git history lost | **LOW** | Copy .git directory separately |
| Docker volumes reference old path | **LOW** | Named volumes are path-independent |
| node_modules regression | **LOW** | Delete and reinstall, version-locked |
| Alembic migration drift | **LOW** | alembic.ini uses relative paths, no impact |
| Submodule broken | **LOW** | .gitmodules uses HTTPS URL, re-init after copy |
| CI workflow paths wrong | **MEDIUM** | Audit .github/workflows/ after copy |
| Docker build context wrong | **LOW** | All Dockerfiles use relative COPY from their directory |

---

## 8. Files to Modify (Pre-Migration)

| # | File | Change |
|---|------|--------|
| 1 | `salesos/backend/scripts/muhide_v1_enrichment.py` | Replace 3 hardcoded paths with CLI args |
| 2 | `salesos/backend/scripts/muhide_ingest_real.py` | Replace 3 hardcoded paths with CLI args |
| 3 | `salesos/backend/scripts/fix_false_cr.py` | Replace `sys.path.insert` with `Path(__file__).resolve()` |
| 4 | `salesos/backend/scripts/classify_identity.py` | Same fix |
| 5 | `salesos/backend/scripts/agent_reach_human_review_queue.py` | Replace Python exe + outputs dir |
| 6 | `salesos/backend/scripts/agent_reach_domain_correction_review.py` | Same fix |
| 7 | `salesos/backend/scripts/agent_reach_missing_data_completion_plan.py` | Replace outputs dir |
| 8 | `salesos/backend/tests/integration/test_muhide_rehousing_db.py` | Replace 6 hardcoded `cwd=` |
| 9 | `salesos/backend/tests/integration/test_cr_normalization_safety_db.py` | Replace 2 hardcoded paths |
| 10 | `salesos/backend/tests/integration/test_muhide_ingestion_db.py` | Replace CSV path |
| 11 | `salesos/scripts/probe-wave13-api-residuals.ps1` | Replace OneDrive path |

---

## 9. Files to Archive

| Source | Destination |
|--------|-------------|
| `FOOD.csv` | `archive/data-files/` |
| `FOOD - ENRICHED.csv` | `archive/data-files/` |
| `FOOD - MOBILE.xlsx` | `archive/data-files/` |
| `LEAD GRN/` | `archive/data-files/` |
| `get-docker.sh` | `archive/legacy-configs/` |
| `outputs/` | `archive/old-outputs/` |
| `REPO_TOPOLOGY_AUDIT.md` | `archive/legacy-configs/` |
| `docker-compose.yml` (root) | `archive/legacy-configs/` |

---

## 10. Verification Commands (Post-Migration)

```bash
# 1. Git works from new location
cd D:\AISalesOS && git status && git log --oneline -3

# 2. No hardcoded old paths in code (except docs/archive)
rg "C:\\Users\\raghe" --type py -g '!docs/' -g '!archive/' D:\AISalesOS

# 3. Docker compose validates
cd D:\AISalesOS\salesos && docker compose config --quiet

# 4. Backend imports
cd D:\AISalesOS\salesos\backend && python -c "from app.main import app; print('OK')"

# 5. Frontend TypeScript check
cd D:\AISalesOS\salesos\frontend && npx tsc --noEmit

# 6. Frontend build
cd D:\AISalesOS\salesos\frontend && npm run build

# 7. Backend unit tests (narrow)
cd D:\AISalesOS\salesos\backend && python -m pytest tests/unit/ -x -q --timeout=30

# 8. Original project untouched
cd C:\Users\raghe\Documents\Muhide && git status
```

---

## 11. Decision

| Gate | Status | Evidence |
|------|--------|----------|
| Docker infrastructure relocatable | **PASS** | All relative paths, named volumes |
| Python code relocatable | **CONDITIONAL** | 17 P0 hardcoded paths must be fixed first |
| Git history preserveable | **PASS** | Copy .git directory |
| Secrets handling | **PASS** | env files copied securely, not committed |
| Docs accuracy | **CONDITIONAL** | 25+ files need path updates (P2) |
| Rollback plan | **PASS** | Original location preserved |
| **OVERALL** | **READY WITH CONDITIONS** | Fix P0 paths → copy → verify |

---

## 12. Remaining Human Actions

| Priority | Action | Owner | Blocker |
|----------|--------|-------|---------|
| P1 | Review and approve path fixes before migration | PO | This audit |
| P1 | Ensure D:\ drive has sufficient space (~2 GB) | PO | Hardware |
| P1 | Rotate any secrets that were in committed .env files | DevOps | Security |
| P2 | Update docs with new paths after migration | Data | Migration complete |
| P2 | Consider adding `.env.staging` and `.env.production` to `.gitignore` explicitly | DevOps | Security review |

---

*Audit conducted: 2026-09-05 | Agent: opencode | Branch: fix/login-and-keys*
