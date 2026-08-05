# Phase 05: Repository Documentation (ADR-100 execution, Phase 2 of 4)

## Date
2026-08-05

## Authority
[`ADR-100: Repository Canonicalization`](../docs/adr/0100-repository-canonicalization.md), Execution Order Phase 2 — "Repository Documentation." Scope constrained to documentation only per explicit instruction: reorganize/relocate Markdown, update indexes/links/diagrams, improve navigation. Explicitly disallowed and not touched: source code, code directory renames, imports, Docker, CI/CD, deployment config, project structure.

## 1. Documentation inventory — before / after

| Location | Before | After |
|---|---|---|
| Repo root loose `.md` files | 16 (`AGENTS.md`, `PRODUCT_BIBLE.md`, `README.md`, `REPO_TOPOLOGY_AUDIT.md`, `RUNBOOK.md`, 7× `SALESOS_*.md`, 4× `muhide_*`/`ultimate_deck_specification.md`) | 5 (`AGENTS.md`, `PRODUCT_BIBLE.md`, `README.md`, `REPO_TOPOLOGY_AUDIT.md`, `RUNBOOK.md`) |
| `docs/audit/legacy-reports/` | did not exist | 7 files (the relocated `SALESOS_*.md` set) |
| `assets/reports/` | existed, empty | 4 files (relocated `muhide_*`/`ultimate_deck_specification.md`) |
| `docs/audit/current-state/15-documentation-audit.md` | O1–O7, O15–O18, O20 pointed to now-stale root/`sales-os/` paths; O9–O12, O19 pointed to a non-existent `output/` dir and a non-existent file, both unflagged | All paths corrected to new locations; broken references explicitly marked 🔴 **BROKEN** with verification date rather than silently left or deleted |
| `README.md` | Platform Architecture diagram showed scrapers at repo root (stale since `migration-log/phase-03.md`, 2026-08-05) and did not distinguish the two `docker-compose.yml` files | Diagram reflects current tree (`packages/`, `data/`, `assets/`, `archive/`); explicit note added distinguishing root vs. `salesos/` compose files; Key Documents table gained 3 rows (ADR-100, Product Bible, Runbook) |

## 2. Files relocated

| File | From | To | Reason |
|---|---|---|---|
| `SALESOS_ARCHITECTURE_AUDIT.md` | repo root | `docs/audit/legacy-reports/` | Classified 🔴 OUTDATED by `15-documentation-audit.md` prior to this phase |
| `SALESOS_COMPLETE_AUDIT_AND_ROADMAP.md` | repo root | `docs/audit/legacy-reports/` | Same |
| `SALESOS_OPERATING_PLAN.md` | repo root | `docs/audit/legacy-reports/` | Same |
| `SALESOS_PRODUCTION_READINESS_AUDIT.md` | repo root | `docs/audit/legacy-reports/` | Same |
| `SALESOS_REMEDIATION_BACKLOG.md` | repo root | `docs/audit/legacy-reports/` | Same |
| `SALESOS_REVISED_ROADMAP.md` | repo root | `docs/audit/legacy-reports/` | Same |
| `SALESOS_V1_ENTERPRISE_RELEASE_READINESS.md` | repo root | `docs/audit/legacy-reports/` | Same |
| `muhide_3version_comparative_report.md` | repo root | `assets/reports/` | Classified 🟡 External reference; matches destination already specified (and otherwise unexecuted) in `docs/architecture/REPOSITORY_RESTRUCTURE_PLAN.md` Phase 6 |
| `muhide_comparative_analysis_report.md` | repo root | `assets/reports/` | Same |
| `muhide_pitch_deck_analysis_report.md` | repo root | `assets/reports/` | Same |
| `ultimate_deck_specification.md` | repo root | `assets/reports/` | Same |

**Note on destination choice:** the 7 `SALESOS_*.md` files went to `docs/audit/legacy-reports/` (root `docs/` layer), not `salesos/docs/architecture/` as the older, partially-superseded `REPOSITORY_RESTRUCTURE_PLAN.md` Phase 8 specified — ADR-100 places root-level audit/roadmap documents in the product/audit layer (`docs/`), not the engineering-specific layer (`salesos/docs/`). Annotated at the source in that document.

## 3. Files left intentionally

| File | Why |
|---|---|
| `PRODUCT_BIBLE.md` (root) | `docs/audit/current-state/15-documentation-audit.md` classifies it 🟢 Current and "the authoritative source for product vision." The older restructure plan's Phase 8 assumed it should move to `docs/architecture/`; that assumption is contradicted by the repo's own documentation audit, so it was not moved. Distinct from — not a duplicate of — `docs/PROJECT_BIBLE.md` (an engineering-authority document, different scope, different date). Naming collision (Product vs. Project) noted but not resolved — that's a content decision, out of scope for a documentation-*reorganization* pass. |
| `RUNBOOK.md` (root) | Same audit classifies it 🟢 Current, bilingual, comprehensive. Byte-identical in header to `engineering-os/RUNBOOK.md` (the submodule) — expected, not a defect; submodule content is out of scope (external repo). |
| `AGENTS.md` (root) | Root-level agent-instructions convention file (read automatically by coding agents). Must stay at repo root to function; moving it would be a functional change disguised as documentation cleanup. |
| `REPO_TOPOLOGY_AUDIT.md` (root) | Actively cross-referenced by ADR-100's own Governance & Reconciliation section, `docs/adr/0100-repository-canonicalization.md`'s "Related" field, and `migration-log/phase-04.md`. Moving it now would immediately churn links inside the governance chain just established in the prior phase. Deferred to a future pass. |
| `MUHIDE_Ultimate_Deck*.pptx` (×3), `SalesOS_V2_Executive_Presentation.pptx`, `MUHIDE Design System.zip`, `SalesOS Design Revolution.zip` | Binary files, not Markdown. This phase's mandate was explicitly Markdown relocation. `REPOSITORY_RESTRUCTURE_PLAN.md` Phase 6 already specifies `assets/presentations/` and `assets/branding/` as destinations — left for a dedicated binary-asset pass rather than folded in here. |
| `engineering-recovery/` (root, 14 files) | A full directory, not a loose Markdown file; also out of the "relocate loose Markdown files" mandate as written. Left at root, flagged in the documentation audit table for a future decision (archive vs. keep). |

## 4. Link validation report

**Method:** repo-wide search (excluding `node_modules`, `.next`, `.git`) for every relocated filename, before and after the move.

**Before this phase (pre-existing, discovered — not caused by this phase):**
- `docs/audit/current-state/15-documentation-audit.md` referenced `output/SALESOS_*.md` (4 links, O9–O12) — `output/` does not exist anywhere in the repository. **Broken.**
- Same file referenced `notion_analysis.md` (O19) — file does not exist anywhere in the repository. **Broken.**
- Both were previously unflagged (no status indicator distinguishing them from valid links). **Fixed:** both now marked 🔴 **BROKEN**, verified 2026-08-05, left in the table rather than deleted (preserves audit history per "do not delete historical documents").

**Caused by this phase's moves — checked and resolved:**
- 3 files referenced the relocated filenames: `docs/architecture/REPOSITORY_RESTRUCTURE_PLAN.md` (its own Phase 6 and Phase 8 action lists), `docs/audit/current-state/15-documentation-audit.md` (O1–O7, O15–O18), and the moved `SALESOS_OPERATING_PLAN.md` itself (a self-referential mention of its own filename, not a path-based link — no fix needed).
- All resolved: `15-documentation-audit.md` paths updated to new locations; `REPOSITORY_RESTRUCTURE_PLAN.md` annotated in place (not rewritten) noting where actual execution diverged from its original plan.
- Post-move repo-wide re-search for all 11 relocated filenames confirms zero remaining unresolved references outside the new locations and the two annotated documents.

**Result: 0 broken links introduced by this phase. 5 pre-existing broken references discovered and flagged (not silently fixed, not deleted).**

## 5. Updated documentation map

```
Muhide/
├── README.md                          Entry point — Quick Start, Platform Architecture (now accurate), Key Documents
├── AGENTS.md                          Agent instructions (root, functional — unmoved)
├── PRODUCT_BIBLE.md                   Product vision (root, current/authoritative — unmoved)
├── RUNBOOK.md                         Bilingual ops runbook (root, current — unmoved)
├── REPO_TOPOLOGY_AUDIT.md             Topology findings (root, pending future relocation)
├── docs/
│   ├── adr/                           ADR registry — index.md, 0100-repository-canonicalization.md (governing)
│   ├── architecture/                  REPOSITORY_RESTRUCTURE_PLAN.md (partially superseded, annotated)
│   ├── audit/
│   │   ├── current-state/             15-documentation-audit.md (updated) + 18 other numbered audits
│   │   ├── ga-engineering-audit/       Canonical GA engineering audit series
│   │   └── legacy-reports/            NEW — 7 relocated SALESOS_*.md historical audits
│   ├── program/, ops/, compliance/, reference/, api/, ai/, backend/, frontend/, design/, v2/, vnext/, incidents/
│   └── PROJECT_BIBLE.md, ...          (root-of-docs/ loose files, unaffected this phase)
├── assets/
│   ├── branding/, presentations/      Unaffected this phase
│   └── reports/                       NEW population — 4 relocated muhide_*/ultimate_deck_specification.md
├── archive/sales-os/                  Populated Phase 1 (ADR-100)
├── packages/, data/, scripts/         Unaffected this phase
├── engineering-os/                    Submodule — unaffected
├── engineering-recovery/              Unaffected this phase (flagged for future decision)
└── salesos/                           Canonical application — completely unaffected this phase
```

## 6. Validation that no runtime behavior changed

- `git status`, scoped to every touched path, shows only: 3 modified Markdown files (`README.md`, `docs/adr/index.md`, `docs/audit/current-state/15-documentation-audit.md`) and new/moved Markdown files under `docs/audit/legacy-reports/`, `assets/reports/`, `docs/adr/`, `docs/architecture/`.
- `git status` scoped to `salesos/` and `engineering-os/` (the two trees containing all executable code, configs, Dockerfiles, and CI) returns **empty** — zero changes.
- No `Dockerfile`, `docker-compose*.yml`, CI workflow, `package.json`, `pyproject.toml`, or source file was opened for writing during this phase.
- No import statement was touched — the relocated files are documentation, not code, and were not imported by any application module (confirmed during Phase 1's reference check, which covered these same paths).

## Gate results
- [x] Documentation inventory: PASS (table above)
- [x] Files relocated: PASS (11 files, verified present at new locations, absent from root)
- [x] Files left intentionally: PASS (6 items, each with stated reason)
- [x] Link validation: PASS (0 new breaks; 5 pre-existing breaks surfaced and flagged)
- [x] Documentation map: PASS (above)
- [x] No runtime behavior changed: PASS (`salesos/`, `engineering-os/` git-diff empty; no code/config/CI files touched)

## Rollback procedure
```bash
# Move the 7 legacy reports back to root
mv docs/audit/legacy-reports/*.md .

# Move the 4 asset reports back to root
mv assets/reports/muhide_*.md assets/reports/ultimate_deck_specification.md .

# Revert the 3 modified files
git checkout -- README.md docs/adr/index.md docs/audit/current-state/15-documentation-audit.md
# (docs/architecture/REPOSITORY_RESTRUCTURE_PLAN.md annotations are additive to an untracked
#  file — no git history to revert to; re-edit manually if needed)
```

## Notes
- Next: Phase 3 (Legacy Isolation) — mark root `infrastructure/` as "Pending Removal" and both `railway.json`/`Dockerfile.railway` pairs as "Legacy Candidate," per explicit user constraint: no deletion, no migration into `infrastructure/`.
