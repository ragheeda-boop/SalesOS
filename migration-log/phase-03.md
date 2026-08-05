# Phase 03: Move Scrapers

## Date
2026-08-05

## Why did we move this?
Four scraper directories (`balady_scraper/`, `najiz_scraper/`, `rega_scraper/`, `taqeem_scraper/`) were scattered at the repository root, mixed with unrelated files. Consolidating them under `packages/scrapers/` creates a clear shared-packages layer and removes root clutter.

## What changed?

### Moved: balady_scraper/ → packages/scrapers/balady/ (19 files)
- All files moved: api.py, check_notion.py, config.py, export.py, main.py, notion_import.py, parser.py, scraper.py, utils.py, verify_output.py + CSV/JSON/XLSX outputs + __pycache__
- **Import fix:** `notion_import.py` line 7 — updated `sys.path.insert` from `../salesos/backend` to `../../.. /salesos/backend`

### Moved: najiz_scraper/ → packages/scrapers/najiz/ (16 files)
- All files moved: api.py, config.py, main.py, notion_sync.py, scraper.py, storage.py + data/ (CSV/JSON/XLSX) + __pycache__
- No import changes needed (self-contained)

### Moved: rega_scraper/ → packages/scrapers/rega/ (5 files)
- All files moved: __init__.py, scraper.py + CSV/XLSX output + screenshots/ + scraper.log
- No import changes needed (self-contained)

### Moved: taqeem_scraper/ → packages/scrapers/taqeem/ (27 files)
- All files moved: forensic.py, forensic_report.py, scraper.py + CSV/JSON/XLSX outputs + archive/ (15 files) + HTML/ TXT debug files
- No import changes needed (self-contained)

### Updated: data/scripts/clean_all.py
- Line 95: `balady_scraper/` → `packages/scrapers/balady/`
- Line 142: `taqeem_scraper/` → `packages/scrapers/taqeem/`
- Line 187: `rega_scraper/` → `packages/scrapers/rega/`
- Line 244: `najiz_scraper/data/` → `packages/scrapers/najiz/data/`

## What did NOT change?
- `salesos/` — untouched
- `docs/` — untouched
- `data/` — untouched (except scripts/clean_all.py path update)
- `.github/` — untouched
- No Python imports within scrapers changed (all internal)
- No business logic changed

## Risks
- **Risk:** `clean_all.py` uses hardcoded Windows path (`C:\Users\raghe\OneDrive...`). The path update follows the same pattern.
- **Mitigation:** File paths are relative to `BASE_DIR`, which is configurable.

## Rollback procedure
```bash
# Move everything back
mv packages/scrapers/balady/* balady_scraper/
mv packages/scrapers/najiz/* najiz_scraper/
mv packages/scrapers/rega/* rega_scraper/
mv packages/scrapers/taqeem/* taqeem_scraper/
# Restore clean_all.py
git checkout HEAD~1 -- data/scripts/clean_all.py
# Restore notion_import.py
git checkout HEAD~1 -- packages/scrapers/balady/notion_import.py
```

## Gate results
- [x] Lint: PASS (no new code, only moves)
- [x] Typecheck: PASS
- [x] Unit Test: PASS
- [x] Build: PASS
- [x] Docker Build: PASS
- [x] Smoke Test: PASS
- [x] No old scraper directories: PASS
- [x] All new directories populated: PASS
- [x] No imports to old paths: PASS
- [x] Backend syntax: PASS
- [x] Frontend structure: PASS
- [x] No duplicate modules: PASS

## Metrics
| Metric | Before | After | Delta |
|---|---|---|---|
| Root entries | 62 | 58 | -4 (removed 4 scraper dirs) |
| Scraper files moved | 0 | 67 | +67 |
| Files updated | 0 | 2 | +2 (notion_import.py, clean_all.py) |

## Notes
- Each scraper was moved individually with verification after each move (per user instruction).
- Scraper Python files are NOT fully independent packages yet (no pyproject.toml). This is intentional — the plan says "do not change architectural boundaries during structural cleanup." Package-ization can happen in a future phase.
- `__pycache__/` directories were moved along with source files. They are gitignored and harmless.
