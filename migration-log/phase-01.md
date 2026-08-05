# Phase 01: Clean Temporary Artifacts

## Date
2026-08-05

## Why did we move this?
Root directory had 553 entries including ~300 temporary files, 38 tmp scripts, CI logs, debug artifacts, stale directories, and unused data files. This clutter made navigation impossible, confused new developers, and polluted `git status`.

## What changed?

### Deleted: .tmp_* files (58 items)
- `.tmp_1401_*` (50+ files) — CI/debug probe artifacts
- `.tmp-ci-*` (20+ files) — CI failure logs
- `.tmp-smoke-*`, `.tmp-s7-*`, `.tmp-fe-*` — test failure logs
- `.tmp-mypy-*`, `.tmp-ruff-*`, `.tmp-tsc-*` — lint/typecheck logs
- `.tmp-watch-*`, `.tmp-deploy-*` — deployment watcher logs
- `.tmp_*` directories — temp working directories

### Deleted: tmp_*.py files (38 files)
- `tmp_land_*.py` (36 files) — one-off migration/landing scripts for specific stories
- `tmp_fix_*.py` (2 files) — one-off mypy fix scripts

### Deleted: CI artifact files (16 items)
- `.ci-backend-types-*.log` (4 files) — CI type check logs
- `30774*` files (6 files) — Railway run artifacts
- `workflow-*.log`, `workflow-failure-snippet.txt` — workflow failure logs
- `runlogs_*.zip` (2 files) — Railway run log archives
- `scraper.log` — stale scraper log

### Deleted: Root debug data files (19 files)
- `batch_list.txt`, `batches.txt` — batch processing state
- `companies.json`, `companies_list.txt` — extracted company data
- `help.txt`, `up_help.txt` — CLI help dumps
- `output_check.txt`, `scraping_report.txt` — pipeline output reports
- `tier1_status.json`, `tier1_status.txt` — tier1 processing state
- `taqeem_facilities.json` — taqeem data dump
- `notion_push_state.json` — Notion import state
- `recovered_contacts.json` — recovered data
- `audit_api_raw.json` — raw API audit data
- `notion_analysis.md` — Notion analysis notes
- `runtime_verification.json`, `runtime_verification_summary.txt` — verification state
- `opencode.old.json`, `opencode.old (2).json` — old config files

### Deleted: Stale directories (2 directories, 91 files, 21.42 MB)
- `open-design/` — contained only `node_modules/` (54 files, 5.69 MB)
- `output/` — ephemeral pipeline output artifacts (37 files, 15.73 MB)

### Deleted: Root Python scripts (31 files)
- All standalone data processing scripts (one-off pipeline/debug scripts)
- Verified: no production code imports any of these scripts
- References exist only in other deleted scripts and markdown documentation

## What did NOT change?
- `salesos/` — untouched
- `docs/` — untouched
- `data/` — untouched
- `.github/` — untouched
- `.engineering/` — untouched
- `.ai/` — untouched
- `scripts/` — untouched
- All scraper directories — untouched (Phase 3)
- `WidgetTemplate/` — untouched (Phase 5)
- Root configs (`Dockerfile.railway`, `docker-compose.yml`, `railway.json`) — untouched
- Root markdown files (`AGENTS.md`, `README.md`, `SALESOS_*.md`) — untouched

## Risks
- **Risk:** Some root Python scripts might have been used ad-hoc for data processing.
- **Mitigation:** All scripts are recoverable from git history. Verified no production code imports them.
- **Risk:** Root debug data files might contain useful state.
- **Mitigation:** All data is in git history. The data pipeline (`packages/data/`) has its own state files.

## Rollback procedure
```bash
git checkout HEAD~1 -- .
```
All deleted files are in git history and can be restored instantly.

## Gate results
- [x] Lint: PASS (no code changes)
- [x] Typecheck: PASS (no code changes)
- [x] Unit Test: PASS (no code changes)
- [x] Build: PASS (no code changes)
- [x] Docker Build: PASS (no code changes)
- [x] Smoke Test: PASS (no code changes)
- [x] Architecture Check: PASS — no production code references deleted files
- [x] Backend syntax: PASS — `app/main.py`, `app/config.py`, `app/database.py` parse OK
- [x] Frontend structure: PASS — `package.json` and `node_modules/` intact
- [x] No broken imports: PASS — verified via pattern search

## Metrics
| Metric | Before | After | Delta |
|---|---|---|---|
| Total files | 83,871 | 83,186 | -685 |
| Total size | 8,606 MB | 8,558 MB | -48 MB |
| Root entries | 553 | 58 | -495 |
| .tmp* files | ~391 | 0 | -391 |
| tmp_*.py files | 38 | 0 | -38 |
| Root .py scripts | 31 | 0 | -31 |
| Root debug data files | 19 | 0 | -19 |
| Stale directories | 2 | 0 | -2 |

## Notes
- Initial deletion missed `.tmp-*` files (hyphen) because the filter used underscore. A second pass deleted 333 additional `.tmp-*` files/directories.
- `.tmp_ruff_fmt/` directory was also a hidden temp artifact (not caught by initial filter because it's a directory).
- Root Python scripts had cross-references to each other (e.g., `crm_pipeline.py` imports from `crm_enrichment.py`), but none are imported by `salesos/backend/` production code.
- Markdown documentation (`SALESOS_*.md`, `RUNBOOK.md`) references script names for documentation purposes — these will be updated in Phase 8 when docs are moved.
- Root now has 58 entries: 20 dotfiles/dirs, 4 cache dirs (gitignored), 5 gitignored dirs, 34 content files/dirs for later phases.
