# Phase 04: Safe Cleanup (ADR-100 execution, Phase 1 of 4)

## Date
2026-08-05

## Authority
[`ADR-100: Repository Canonicalization`](../docs/adr/0100-repository-canonicalization.md) — Approved. Execution ordered: Safe Cleanup → Repository Documentation → Legacy Isolation → Pending Migration Completion. Deployment-related phases (Railway config, `salesos/infra/` migration) explicitly out of scope for this phase and deferred pending user confirmation.

## Plan conflict discovered and resolved
`docs/architecture/REPOSITORY_RESTRUCTURE_PLAN.md` (v2.0, status "APPROVED — Pending Execution", dated 2026-08-05) already existed in the repo and was not known to the author of ADR-100 at drafting time. It conflicts with ADR-100 on one point: its Phase 7 archives the `engineering-os/` submodule and drops it from `.gitmodules`; ADR-100 keeps `engineering-os/` as a submodule, unchanged. User decision: **ADR-100 governs where the two disagree.** A reconciliation note was added to the top of `REPOSITORY_RESTRUCTURE_PLAN.md` pointing to ADR-100 and flagging that its Phase 7 submodule-archival step must not be executed. Phases 4/5/6/8–12 of that document were not evaluated against ADR-100 and are marked for re-review before any future execution.

## What did we do?

### Deleted: `archive/engineering-os/`, `archive/engineering-recovery/` (empty stubs)
Both were empty destination directories pre-created by the older plan's Phase 2, meant to receive an `engineering-os/` submodule archival that ADR-100 does not authorize, and an `engineering-recovery/` archival that was never executed. Confirmed empty (`find ... -mindepth 1` → 0 results) before deletion. Only doc references found (`REPO_TOPOLOGY_AUDIT.md`, `docs/adr/0100-*.md`, `migration-log/phase-02.md`, `docs/architecture/REPOSITORY_RESTRUCTURE_PLAN.md`) — no code or CI references.

### Corrected: `archive/sales-os/` was also empty, not a real backup
The original `REPO_TOPOLOGY_AUDIT.md` stated `archive/sales-os/` was "a clean archived snapshot" of root `sales-os/`. That was a misreading of the audit's own `diff -rq` output — re-verification immediately before this phase's execution showed `archive/sales-os/` contained **zero files**, identical to the other two stubs.

**Self-correction during execution:** root `sales-os/` was deleted first on the (incorrect) premise that a backup already existed, then immediately restored via `git checkout -- sales-os/` after `git status` confirmed the files were git-tracked and recoverable. No source file was permanently lost. Two untracked, gitignored local artifacts were not recoverable and were not meant to be: `.env` (local secrets — not in git, not archived anywhere; flagged to the user directly) and `__pycache__/` (regenerable).

### Moved (properly, this time): `sales-os/` → `archive/sales-os/`, then root deleted
All 14 git-tracked files (`README.md`, `config.py`, `main.py`, `notion_api.py`, `completeness_scorer.py`, `dedup_scanner.py`, `priority_assigner.py`, `run_on_suppliers.py`, `sfda_sync_checker.py`, `stale_detector.py`, `requirements.txt`, `.gitignore`, `.env.example`, `.github/workflows/run.yml`) copied into `archive/sales-os/` and verified byte-identical (`diff -rq` clean) before root `sales-os/` was deleted.

### Updated: `.semgrepignore`
Line 56 (`sales-os/` ignore pattern) removed and replaced with a comment noting the retirement date and reason — the pattern is now a no-op since the path no longer exists at root.

## What did NOT change?
- `salesos/` — untouched
- `.ai/`, `.engineering/` — untouched (frozen/generated layers)
- `engineering-os/` submodule — untouched, still active per ADR-100
- Root `infrastructure/` — untouched (Pending Removal per user constraint, not deleted this phase)
- Root `railway.json`, `Dockerfile.railway` — untouched (Legacy Candidate per user constraint, not deleted this phase)
- No code imports were touched — reference check confirmed neither `sales-os/` nor the two empty archive stubs were imported by any application code

## Risks
- **Risk:** the false-positive backup assumption that caused the transient deletion of `sales-os/` shows the earlier audit's `diff` output was not re-verified carefully enough the first time. **Mitigation applied:** every subsequent deletion in this phase was preceded by an immediate, fresh verification step (not a reference to the earlier audit), and this phase's own log documents the correction rather than silently fixing it.
- **Risk:** `.env` local secrets file for the old `sales-os/` product is now unrecoverable from this repository. **Mitigation:** flagged directly to user; `.env.example` (the template) is preserved in both the restored history and the new archive copy.

## Rollback procedure
```bash
# Restore sales-os/ at root (git history has full content regardless of archive state)
git log --diff-filter=D -- sales-os/README.md   # find the commit before deletion
git checkout <commit>~1 -- sales-os/

# Restore the two empty archive stubs (no content to lose — just recreate)
mkdir -p archive/engineering-os archive/engineering-recovery

# Revert .semgrepignore
git checkout <commit>~1 -- .semgrepignore

# Revert the REPOSITORY_RESTRUCTURE_PLAN.md reconciliation note (uncommitted file — no git history to restore from; re-add manually if needed)
```

## Gate results
- [x] Reference check: PASS (no code/CI references to deleted paths, only documentation mentions)
- [x] Git status: PASS — `sales-os/` deletions are clean tracked deletions; `archive/sales-os/*` are new untracked additions; no unexpected changes outside touched paths
- [x] Import validation: PASS — nothing imports `sales-os/`, `archive/engineering-os/`, or `archive/engineering-recovery/`
- [x] Content integrity: PASS — `archive/sales-os/` now byte-identical to the deleted root copy (git-tracked files only)
- [ ] Docker/bootstrap validation: **not run** — explicitly out of scope per user instruction ("Do not begin Docker or Bootstrap work until repository canonicalization is complete")

## Metrics
| Metric | Before | After | Delta |
|---|---|---|---|
| Root top-level dirs | 14 (incl. `sales-os/`) | 13 | -1 |
| `archive/` subdirectories | 3 (all empty) | 1 (populated) | -2 dirs, +14 files |
| Duplicate/collision-risk product trees | 1 (`sales-os/` vs `salesos/`) | 0 | -1 |
| Documented plan conflicts | 1 (undiscovered) | 1 (discovered, reconciled, logged) | resolved |

## Notes
- This phase intentionally did not touch `infrastructure/` or the Railway configs — both are explicitly deferred per user constraint, tracked as "Pending Removal" and "Legacy Candidate" respectively for Phase 3 (Legacy Isolation), which marks but does not delete them.
- Next: Phase 2 (Repository Documentation) — relocate loose root audit/report files into `docs/audit/`/`docs/releases/`, fix the stale Platform Architecture section in root `README.md`.
