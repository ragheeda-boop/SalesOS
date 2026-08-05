# Phase 09: docs/ Restructure — EXECUTED THEN REVERTED (ADR-100 conflict) + CI/CD updates

## Date
2026-08-05

## Why did we revert?
Plan Phase 9 called for moving 9 runbooks from `docs/ops/` → `docs/guides/` and removing empty
`docs/ops/`. The 8 existing runbooks were moved and 2 reference files updated. Then a repo-wide
reference scan (`git grep`) revealed **~30 cross-references to `docs/ops/*`** across the
**READ-ONLY canonical GA audit tree** (`docs/audit/ga-engineering-audit/**`, incl.
`PRODUCTION_PLAN.md`), plus live config/docs references.

Per the RESTRUCTURE_PLAN reconciliation note, remaining phases "were not evaluated against ADR-100
and should be re-reviewed before execution rather than assumed compatible." This review found the
move incompatible: editing READ-ONLY governance docs to fix broken links would violate their
governance status. **Decision: revert the move; runbooks stay in `docs/ops/`. Plan Phase 9 is
documented as NOT executed (reverted).**

## What changed (and was reverted)
- `docs/ops/{GO_LIVE_RUNBOOK,DR_RUNBOOK,HYPERCARE_RUNBOOK,SECRETS_HYGIENE,STAGING_PARITY,
  DEGRADED_MODE_MATRIX,SLO_ALERTS,RUNTIME_STACK}.md` → moved to `docs/guides/` then **moved back**
  → `docs/ops/` (byte-identical restore).
- `docs/guides/` created then **deleted**.
- `docs/ops/RUNTIME_STACK.md` + `docs/program/PHASE1_SPRINT26_GO_LIVE_HYPERCARE_CRUMB.md` link
  edits made then **reverted**.
- `.engineering/03_REPOSITORY_MAP.md` + `04_DIRECTORY_CATALOG.md`: `docs/guides/` rows corrected
  back to `docs/ops/` (runbooks) with an annotation.

## What changed (kept) — plan Phase 11 CI/CD & config
| File | Change |
|---|---|
| `.github/CODEOWNERS` | Added owners for `packages/`, `migration-log/`, `infrastructure/`, `archive/`, `assets/`. `engineering-os/` kept (submodule per ADR-100). |
| `.gitignore` | `archive/` added; `engineering-recovery/` → covered by `archive/`; `packages/data/` explicit. |
| `.semgrepignore` | `taqeem_scraper/` → `packages/scrapers/` (security-scan path fix). |
| `.engineering/03_REPOSITORY_MAP.md` | Rewritten for new layout. |
| `.engineering/04_DIRECTORY_CATALOG.md` | Sections 5/6 updated: scrapers → `packages/scrapers/`, runbooks stay in `docs/ops/`, added new dirs. |
| `.engineering/05_FILE_CATALOG.md` | Scraper + data pipeline rows → `packages/...`. |
| `AGENTS.md` | §8 preferred paths updated (scrapers, data pipelines, migration-log). |
| `README.md` | Structure tree updated for new layout. |
| `RUNBOOK.md` | Scraper paths → `packages/scrapers/...` (2 spots). |
| `salesos/docs/CURRENT_ARCHITECTURE.md`, `salesos/docs/ARCHITECTURE_BOOK.md` | Scraper + `WidgetTemplate/` paths updated. |

## Risks / residual
- Historical audit/decision records (`docs/program/DECISION_LOG.md`, `docs/audit/*`,
  `salesos/docs/audit/ga-engineering-audit/CI_19_SEMGREP_TRIAGE.md`, `docs/ARCHITECTURE_AUDIT_REPORT.md`,
  `docs/COMPLIANCE_AUDIT_REPORT.md`, `docs/audit/05-design-system.md`) still describe old root paths
  as historical snapshots. **Left intentionally** per the register's L9 precedent (historical record,
  not live links).

## Rollback procedure
```bash
git checkout HEAD~1 -- .github/CODEOWNERS .gitignore .semgrepignore .engineering/ AGENTS.md README.md RUNBOOK.md
git checkout HEAD~1 -- salesos/docs/CURRENT_ARCHITECTURE.md salesos/docs/ARCHITECTURE_BOOK.md
```

## Gate results
- [x] `git grep` stale-path scan: only historical/audit records remain (documented above)
- [x] Runbook paths resolve again (`docs/ops/*`) — canonical GA docs unbroken
- [x] README / RUNBOOK / .engineering consistent with new layout
- [x] CODEOWNERS covers all new top-level dirs
- [x] `.semgrepignore` points at `packages/scrapers/`
