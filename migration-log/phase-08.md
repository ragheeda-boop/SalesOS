# Phase 08: Remaining Moves — data/, assets/, engineering-recovery/

## Date
2026-08-05

## Why did we do this?
Completes the plan's Phases 4 (Move Data), 6-remainder (Presentation Assets binaries), and the
owner-decision item L4 (archive `engineering-recovery/`). These were the last root-level content
moves still outstanding after Phases 01–07.

## What changed?

### Moved: data/ → packages/data/ (plan Phase 4)
- All contents moved (raw/, cleaned/, golden/, identity/, import/, normalized/, notion_export/,
  reports/, scripts/, canonical_dictionary.json, DATA_INVENTORY.md, NOTION_IMPORT_SPRINT.md).
- `packages/data/` was pre-created empty in Phase 02; now populated (154 items).
- Empty root `data/` deleted.
- **Path updates in `packages/data/scripts/clean_all.py`:**
  - `RAW_DIR/CLEANED_DIR/REPORTS_DIR` → `BASE_DIR/"packages"/"data"/...` (from `"data"/...`)
  - 4 scraper input CSV paths already pointed at `packages/scrapers/...` (Phase 03)
  - 4 root-level JSON inputs (`companies.json`, `audit_api_raw.json`, `recovered_contacts.json`,
    `tier1_status.json`) → `BASE_DIR/"packages"/"data"/"raw"/...`
- Root `.gitignore`: `packages/data/` added explicitly (root `data/` pattern already matched it).

### Moved: presentation binaries → assets/ (plan Phase 6, actions 1–6 previously not executed)
- `MUHIDE_Ultimate_Deck.pptx`, `_V2`, `_V3`, `SalesOS_V2_Executive_Presentation.pptx`
  → `assets/presentations/`
- `MUHIDE Design System.zip`, `SalesOS Design Revolution.zip` → `assets/branding/`
- (The 4 `.md` reports were already in `assets/reports/` from ADR-100 Phase 2 / phase-05.)

### Archived: engineering-recovery/ → archive/engineering-recovery/ (register item L4)
- 9 markdown files (01-inventory … 14-remaining-risks) moved; root dir deleted.
- `engineering-recovery/` and now `archive/` added to `.gitignore` (archived content recoverable
  from git history / prior root state; never tracked).
- `docs/architecture/LEGACY_ISOLATION_REGISTER.md` updated: L3 and L4 marked **RESOLVED**;
  Phase 4 + L4 disposition checkboxes checked.

## What did NOT change?
- `salesos/` untouched by this phase.
- Root `docs/` runbooks untouched (see phase-09 for the reverted docs/ restructure).
- No code imports changed — all moved files are data/config/docs, not runtime code.

## Risks
- `clean_all.py` uses an absolute `BASE_DIR` pointing at a OneDrive mirror
  (`C:\Users\raghe\OneDrive - RATL Technology Ltd\Muhide`). Path updates assume that mirror now
  mirrors the new `packages/` layout. Data pipelines are NOT on the SalesOS GA runtime path.
- `archive/` is now gitignored — archived content lives only in the working tree / history.

## Rollback procedure
```bash
# data
mv packages/data/* data/
# assets
mv assets/presentations/*.pptx . ; mv assets/branding/*.zip .
# engineering-recovery
mv archive/engineering-recovery/* engineering-recovery/
# gitignore
git checkout HEAD~1 -- .gitignore
```

## Gate results
- [x] Root `.py` orphan check: 0 root .py files
- [x] `clean_all.py` syntax + path audit (sub-agent): PASS after final 4 path fixes
- [x] Old locations removed: data/, engineering-recovery/ gone
- [x] No duplicates: 8 root Test-Path checks all False
- [x] `.semgrepignore` updated: `taqeem_scraper/` → `packages/scrapers/` (security-scan path fix)

## Metrics
| Item | Before | After |
|---|---|---|
| Root entries | (incl. data/, engineering-recovery/, 6 binaries) | −9 root entries |
| Files moved to packages/data/ | 0 | 154 items |
| Files moved to assets/ | 0 | 6 binaries |
| Files archived | 0 | 9 |

## Notes
- `get-docker.sh` (tracked, root) intentionally left in place — one-off install script, not in plan scope.
