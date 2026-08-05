# Phase 06: Legacy Isolation (ADR-100 execution, Phase 3 of 4)

## Date
2026-08-05

## Authority
[`ADR-100: Repository Canonicalization`](../docs/adr/0100-repository-canonicalization.md), Execution Order Phase 3. Scope: documentation/governance markers only. Explicitly disallowed and not touched: delete, move, rename, code, deployment, Docker, Railway, CI/CD.

## What did we do?

### Added: `infrastructure/README.md`
Marks the empty `infrastructure/{cloud,observability,scripts}` scaffold "PENDING REMOVAL," explains the two possible origins (dead scaffold vs. undocumented future `salesos/infra/` destination), states the default recommendation (delete) without executing it, and points to the register for the unblocking condition.

### Added: `docs/ops/RAILWAY_CONFIG_LEGACY_NOTICE.md`
Marks root `railway.json` + `Dockerfile.railway` as a "LEGACY CANDIDATE" alongside `salesos/railway.json`, tables the concrete config differences (build source, celery service handling, pre-deploy migration step, restart policy), and states plainly that neither file may be touched until the live Railway build source is confirmed out-of-band.

### Added: `docs/architecture/LEGACY_ISOLATION_REGISTER.md`
The five requested deliverables in one document:
1. **Legacy Inventory** — 11 items (L1–L11), consolidating every legacy/pending candidate surfaced across the topology audit, ADR-100, and the health gate, including three not previously part of any approved phase (`salesos/security-audit-report*.json`, `benchmark.db`, `.tmp-*` files — all inside the canonical app, flagged but explicitly out of this ADR's scope).
2. **Ownership Matrix** — decision owner per item, mapped to the ADR-036 layer model.
3. **Pending Removal Register** — 6 items, each with its specific blocking condition.
4. **Pending Migration Register** — 2 items (`WidgetTemplate/`, `engineering-recovery/`), with destination and blocker.
5. **Future Execution Checklist** — ordered, checkbox-tracked list showing Phases 1–3 complete and every remaining item's precondition.

## What did NOT change?
- `railway.json`, `Dockerfile.railway`, `salesos/railway.json` — byte-for-byte unchanged (verified via `git status`, empty diff)
- `infrastructure/cloud/`, `infrastructure/observability/`, `infrastructure/scripts/` — still empty; only a `README.md` was added at the `infrastructure/` top level, not inside the subdirectories
- No file was deleted, moved, or renamed
- No Docker, CI/CD, or deployment configuration was opened for writing
- `salesos/` and `engineering-os/` — untouched (consistent with every prior phase)

## Risks
- None identified. Every change this phase is a net-new file; nothing existing was altered.

## Rollback procedure
```bash
rm infrastructure/README.md
rm docs/ops/RAILWAY_CONFIG_LEGACY_NOTICE.md
rm docs/architecture/LEGACY_ISOLATION_REGISTER.md
```
(All three are new, untracked files — deleting them fully reverts this phase with no residual state.)

## Gate results
- [x] No files deleted: PASS
- [x] No files moved: PASS
- [x] No directories renamed: PASS
- [x] No code modified: PASS
- [x] No deployment/Docker/Railway/CI config modified: PASS (`git status` on all three Railway-related files is empty)
- [x] Repository behavior unchanged: PASS

## Notes
- Next: Phase 4 (Pending Migration Completion) — move `WidgetTemplate/` into `packages/widget-template/`, per the Pending Migration Register's confirmation that this item has no outstanding blocker.
- Three new open items were surfaced this phase that are **not** part of ADR-100's four-phase execution order (`salesos/security-audit-report*.json`, `benchmark.db`, `.tmp-*` files) — they live inside the canonical application, which every phase so far has left untouched by design. Recommend treating them as a separate, smaller-scoped follow-up rather than folding them into this ADR.
