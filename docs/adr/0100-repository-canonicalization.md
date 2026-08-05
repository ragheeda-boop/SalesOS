# ADR-100: Repository Canonicalization

**Status**: Accepted — governing architectural decision for repository topology
**Date**: 2026-08-05
**Author**: Principal Platform Engineer (Cowork session)
**Related**: ADR-036 (Engineering Organization — Layer Separation), `REPO_TOPOLOGY_AUDIT.md` (2026-08-05)
**Supersedes**: `docs/architecture/REPOSITORY_RESTRUCTURE_PLAN.md` v2.0 (2026-08-05) — **only** where the two conflict (its Phase 7 submodule-archival step; see Governance & Reconciliation below). Non-conflicting phases of that document are not superseded and remain valid reference material.
**Depends on**: `migration-log/phase-01.md` … `phase-04.md` (reorg in progress; Phase 04 executed 2026-08-05 under this ADR)

> Architecture first. Migration second. Execution last. This ADR is Architecture. No file was moved, renamed, or deleted to produce this document; execution is tracked separately in `migration-log/`.

---

## Governance & Reconciliation (added 2026-08-05, post-approval)

**ADR-100 is the single governing architectural decision for repository directory topology.** Where any other document — past or future — disagrees with it on canonical root, directory ownership, or migration disposition, ADR-100 controls unless a later ADR explicitly supersedes it.

**Documents audited for conflicting repository-restructuring decisions:**

| Document | Role | Disposition |
|---|---|---|
| `docs/adr/0100-repository-canonicalization.md` (this file) | Governing architectural decision | **Canonical authority.** |
| `docs/architecture/REPOSITORY_RESTRUCTURE_PLAN.md` v2.0 | Earlier, independently-approved 12-phase execution plan (predates this ADR; author unaware of it at drafting time) | **Partially superseded.** Conflicts with ADR-100 on one point: its Phase 7 archives the `engineering-os/` submodule and drops it from `.gitmodules` — ADR-100 §2–3 keeps it as a submodule, unchanged. That step must not be executed. Its remaining phases (4/5/6/8–12) were not evaluated against ADR-100 and require re-review before execution, but are not otherwise rescinded. See the reconciliation banner at the top of that document. |
| `REPO_TOPOLOGY_AUDIT.md` (root) | Read-only findings that led to ADR-100 | **Historical input, not a decision document.** Superseded as a source of *decisions* by ADR-100 (it made none); retained as-is for its findings, with one factual correction noted inline (see below) rather than rewritten. |
| `migration-log/phase-01.md` – `phase-03.md` | Execution record of the pre-ADR-100 reorg | **Historical, not superseded** — these are records of work already done, not competing decisions. `phase-02.md` created two destination directories (`archive/engineering-os/`, `archive/engineering-recovery/`) in anticipation of `REPOSITORY_RESTRUCTURE_PLAN.md`'s Phase 7; those directories were removed in `phase-04.md` under ADR-100 authority. Annotated in place, not rewritten. |
| `migration-log/phase-04.md` | First execution phase under ADR-100 | **Current record**, not superseded. |
| `salesos/CANONICAL_ARCHITECTURE.md`, `docs/CAPABILITY_CATALOG.md` | Product/capability architecture (domains, objects, capabilities) | **Out of scope** — different subject matter (product architecture, not repository directory topology). No conflict with ADR-100. |

No historical document was deleted or rewritten as part of this reconciliation. Corrections and supersession notices were added as banners/annotations, consistent with this repository's existing convention of appending correction notes rather than editing history silently (e.g. `.engineering/24_REPOSITORY_MANIFEST.json` `correction_note` field).

---

## Context

`REPO_TOPOLOGY_AUDIT.md` (2026-08-05) established that `Muhide/salesos/` is the sole canonical application — confirmed by root `README.md`, freshest mtimes, and the only tree with real `package.json`/`pyproject.toml`. It also found the repository mid-way through an undocumented-scope reorganization (`migration-log/` phases 1–3, all dated today, no phase declares completion), leaving:

- One un-archived duplicate product (`sales-os/` vs `archive/sales-os/`).
- Two broken, empty archive stubs (`archive/engineering-os/`, `archive/engineering-recovery/`).
- Migration destinations created but not populated (`packages/widget-template/`, and possibly root `infrastructure/`).
- Two same-named-but-different `docker-compose.yml` files and two conflicting Railway deploy configs.
- ~35 MB of loose decks/zips and 7+ overlapping audit/roadmap markdown files sitting at repo root.

ADR-036 already defines a four-layer model for *how the system should be engineered* (`docs/program` → Business Truth, `.engineering/` → Engineering Spec, `.ai/` → AI Runtime, `salesos/` → Implementation). ADR-100 does not change that model. It answers a narrower, physical question ADR-036 leaves open: **for every directory that actually exists at the `Muhide/` git root today, who owns it, and where does it belong?**

---

## Decision

### 1. Canonical repository root

`Muhide/` (the git root, HEAD `54daec3` on `master`) remains the single canonical repository. It is not renamed, split, or re-rooted. `salesos/` remains the single canonical **application** within it, matching ADR-036's "Implementation" layer. No competing application root is permitted at any level.

### 2. Repository boundaries

Three boundary types, none of which change as a side effect of this ADR:

| Boundary | Definition | Members |
|---|---|---|
| **In-repo, first-party** | Code/docs owned and versioned directly in `Muhide/` | `salesos/`, `docs/`, `packages/`, `data/`, root tooling config |
| **In-repo, submodule** | Externally versioned, vendored by reference | `engineering-os/` (`.gitmodules` → `salesos-engineering-os.git`) |
| **Out-of-repo** | Not part of this git tree; referenced only | Railway/Vercel dashboards, CI runners, staging/prod databases |

`engineering-os/` stays a submodule — it already has independent versioning and a separate remote; collapsing it into the main tree would be a second, unrelated architectural decision and is out of scope here.

### 3. Ownership of every top-level directory

| Path | Target class | Owner (in the ADR-036 layer model) | Disposition |
|---|---|---|---|
| `salesos/` | Canonical application | Implementation | **Keep.** No structural change. |
| `docs/` | Product/audit documentation, ADR registry | Business Truth + Engineering Spec (mixed — see Gap Analysis) | **Keep**, becomes the single destination for loose root docs. |
| `engineering-os/` | Submodule — governance, agent registry | Engineering Spec (external) | **Keep as submodule.** No change. |
| `.ai/` | AI runtime coordination (frozen) | AI Runtime | **Keep, untouched.** Explicitly frozen per its own README; ADR-100 does not open it. |
| `.engineering/` | Generated observation layer | Engineering Spec | **Keep, untouched.** Auto-generated; not hand-edited. |
| `packages/` (root) | Shared first-party tooling not specific to the `salesos/` app | Implementation (shared) | **Keep**, becomes the sole home for scrapers, data tooling, and widget templates. |
| `data/` | Scraper/pipeline data artifacts | Implementation (shared) | **Keep.** Feeds `packages/scrapers/*`. |
| `archive/` | Cold storage for retired trees | N/A (inert) | **Keep as the single archive location.** Every retirement in this ADR lands here or is deleted outright — never both a root copy and an archive copy. |
| `assets/` | Brand/deck/report assets | N/A (inert) | **Keep**, but large binaries (`*.pptx`, `*.zip`) should live here or in `docs/releases/`, not loose at root. |
| `scripts/` (root, `backup.sh` only) | Root-level operational scripts | Implementation (shared) | **Keep** as the single root-level scripts entry point; do not let it re-accumulate scattered one-off scripts. |
| `migration-log/` | Record of this and prior reorgs | Engineering Spec (historical) | **Keep permanently** as an append-only log. Never deleted, never treated as "done" without an explicit closing entry. |
| `sales-os/` (root) | Un-archived duplicate of `archive/sales-os/` | N/A | **Retire.** Delete the root copy once confirmed unreferenced; `archive/sales-os/` already holds the record. |
| `archive/engineering-os/` | Broken empty stub | N/A | **Delete.** Contains nothing; not a real archive. |
| `archive/engineering-recovery/` | Broken empty stub | N/A | **Delete stub**, then decide `engineering-recovery/` (root, 9 files, real content) separately: archive it for real, or leave at root if still actively referenced. |
| `WidgetTemplate/` (root) | Pending-move source, real content | Implementation (shared) | **Complete the move** into `packages/widget-template/` (already exists, empty) rather than leaving two locations live. |
| `infrastructure/` (root, empty) | Undocumented scaffold | Unknown | **Decide, don't guess** (see Gap Analysis §4). Default recommendation: delete — `salesos/infra/` is the real, populated, referenced infra tree, and no migration-log entry justifies duplicating it upward. |
| `docker-compose.yml` (root) | Deliberately lighter dev-profile stack, distinct from `salesos/docker-compose.yml` | Implementation | **Keep both**, but make the relationship explicit in root `README.md` (doc fix, not a file move). |
| `railway.json` + `Dockerfile.railway` (root) | Conflicts with `salesos/railway.json` | Implementation | **Pick one.** Requires confirming which config Railway's dashboard actually builds from before deleting the other (see Gap Analysis §5). |
| Loose root `SALESOS_*.md`, `PRODUCT_BIBLE.md`, `RUNBOOK.md`, `muhide_*_report.md`, decks, zips | Point-in-time snapshots | Business Truth (historical) | **Relocate** into `docs/audit/` or `docs/releases/`, which already exist with a clean numbered structure. |
| Root tooling config (`.gitleaks.toml`, `.semgrepignore`, `.trivyignore`, `.pre-commit-config.yaml`, `.github/`, `.cursor/`, `get-docker.sh`, `.env*`) | Repo-wide tooling | N/A (infrastructure of the repo itself) | **Keep at root.** These are correctly scoped to the whole repository and should not move. |

### 4. Target folder structure

```
Muhide/                            (git root — canonical)
├── salesos/                       Canonical application (Implementation layer, ADR-036)
│   ├── backend/  frontend/  infra/  docs/  ...          (unchanged)
├── docs/                          Product Truth + ADR registry (single destination for audits/roadmaps)
│   ├── adr/                       (unchanged — this file lands here as 0100-*.md)
│   ├── audit/                     (destination for relocated root SALESOS_*.md files)
│   └── releases/                  (destination for decks/zips)
├── engineering-os/                Submodule — unchanged
├── .ai/                           Frozen — unchanged
├── .engineering/                  Generated — unchanged
├── packages/                      Shared first-party tooling (single home)
│   ├── scrapers/{balady,najiz,rega,taqeem}/
│   ├── data/
│   └── widget-template/           (WidgetTemplate/ moved here)
├── data/                          Pipeline artifacts (unchanged)
├── scripts/                       Root operational scripts (unchanged)
├── assets/                        Brand/design assets (unchanged)
├── archive/                       Single cold-storage location
│   └── sales-os/                  (root sales-os/ retired here — already present)
├── migration-log/                 Permanent, append-only
└── [root tooling config]          Unchanged
```

Explicitly **not** in the target structure: root `sales-os/`, `archive/engineering-os/`, `archive/engineering-recovery/` (as empty stubs), root `infrastructure/` (pending decision), root `WidgetTemplate/` (once moved), loose root audit markdown/decks (once relocated).

### 5. Migration strategy

Every step is: (a) additive or subtractive only — never a rewrite, (b) independently reversible via `git revert` or restoring from `archive/`, (c) preceded by a reference check (`grep`/CI config scan) so nothing live gets deleted out from under a build. No step touches `salesos/` internals — this ADR is entirely about the directories *around* `salesos/`, consistent with "never rewrite working modules unnecessarily."

---

## Consequences

### Benefits

1. One unambiguous canonical app (`salesos/`), one unambiguous archive location (`archive/`), zero same-named duplicates once executed.
2. Every top-level directory has a declared owner — no more "is this real or leftover" judgment calls for new developers or agents.
3. Closes out the in-flight, undocumented-scope migration instead of leaving it permanently half-done.
4. No change to `salesos/` internals, `.ai/`, `.engineering/`, or the submodule — zero risk to build/deploy/runtime behavior.

### Trade-offs

1. Requires two external confirmations before execution can complete (Railway build source; root `infrastructure/` intent) — this ADR cannot fully close without them.
2. Deleting `sales-os/`, empty archive stubs, and loose root docs is judgment-call territory if any of them turn out to be referenced by a script or CI job not surfaced in this audit — mitigated by the reference-check gate in every phase below.

---

## 1. Current State

See `REPO_TOPOLOGY_AUDIT.md` (2026-08-05) for the full classification table. Summary: one canonical app (`salesos/`), one submodule (`engineering-os/`), two frozen/generated meta-layers (`.ai/`, `.engineering/`), one in-flight migration (3 of unknown-total phases done), one un-archived duplicate (`sales-os/`), two broken archive stubs, one incomplete move (`WidgetTemplate/`), one undocumented empty scaffold (`infrastructure/`), two conflicting deploy configs, two same-named-different-purpose compose files, and ~7 loose audit/roadmap docs plus ~35 MB of loose binaries at root.

## 2. Target State

As defined in §3–4 above: every top-level directory mapped to exactly one of {Keep unchanged, Keep + become single destination, Retire (delete), Complete pending move, Decide-then-act}. No directory has an undeclared purpose in the target state.

## 3. Gap Analysis

| # | Gap | Current | Target | Blocking? |
|---|---|---|---|---|
| 1 | `sales-os/` duplicated | Live at root + archived | Archived only | No — safe to close after reference check |
| 2 | Two empty archive stubs | `archive/engineering-os/`, `archive/engineering-recovery/` exist but are empty | Deleted, or genuinely populated | No |
| 3 | `WidgetTemplate/` move incomplete | Content at root, empty destination in `packages/` | Content in `packages/widget-template/` only | No |
| 4 | `infrastructure/` intent unknown | Empty scaffold, no migration-log entry explains it | Either deleted or a documented future destination for `salesos/infra/` | **Yes — needs your decision** |
| 5 | Two Railway configs disagree | Root builds backend-only via `Dockerfile.railway`; `salesos/` builds via `salesos/backend/Dockerfile` + handles celery worker/beat | One authoritative config | **Yes — needs to know what Railway's dashboard actually points to (out-of-repo state)** |
| 6 | Root `docker-compose.yml` ambiguity | Real but different stack from `salesos/docker-compose.yml`, same filename | Same files, but README explicitly documents the split | No — doc-only fix |
| 7 | Loose root docs/binaries | 7+ markdown files, 2 zips, 4 pptx at root | Filed under `docs/audit/`, `docs/releases/`, or `assets/` | No |
| 8 | `migration-log/` has no completion marker | Phases 1–3 only | A phase-04+ entry closing out this ADR's execution | No — resolved by executing this ADR |

## 4. Migration Roadmap

Each phase is atomic and independently reversible. No phase depends on a later phase succeeding.

- **Phase A — Reference check (read-only).** Grep the full repo (including CI YAML, Dockerfiles, docs) for references to `sales-os/`, `WidgetTemplate/` (root path), `infrastructure/`, and both `railway.json` files. Produces a go/no-go list for Phases B–E. No files touched.
- **Phase B — Delete broken archive stubs.** Remove `archive/engineering-os/` and `archive/engineering-recovery/` (empty, zero content loss). Independently reversible via `git revert`.
- **Phase C — Retire duplicate `sales-os/`.** Delete root `sales-os/` once Phase A confirms no references; `archive/sales-os/` already preserves it.
- **Phase D — Complete `WidgetTemplate/` move.** Move root `WidgetTemplate/` content into `packages/widget-template/`, update any import paths Phase A found, delete the now-empty root dir.
- **Phase E — Relocate loose root docs/binaries.** Move `SALESOS_*.md`, `PRODUCT_BIBLE.md`, `RUNBOOK.md`, `muhide_*_report.md` into `docs/audit/` or `docs/releases/`; move decks/zips into `assets/` or `docs/releases/`. Pure hygiene.
- **Phase F — Root `README.md` doc fix.** Update the Platform Architecture section (currently stale — still shows `balady_scraper/` etc. at root, predating Phase 03 of the prior migration) and clarify the two-`docker-compose.yml` relationship. Doc-only, no code risk.
- **Phase G — Resolve `infrastructure/` (blocked on your decision).** Either delete the empty scaffold, or open a dedicated follow-up ADR/migration-log phase if the intent is to eventually relocate `salesos/infra/`.
- **Phase H — Resolve Railway config conflict (blocked on your input).** Confirm which `railway.json`/`Dockerfile.railway` pair is live in the Railway dashboard, then delete the other.
- **Phase I — Close the loop.** Append a `migration-log/phase-04.md` (or next available number) documenting Phases B–H as the completion of the reorg started 2026-08-05, and update `docs/adr/index.md` to mark ADR-100 Accepted.

## 5. Execution Order

Lowest-risk and fully-unblocked phases first; blocked phases deferred to the end without stalling the rest:

1. **Phase A** (reference check — read-only, unblocks everything else)
2. **Phase B** (delete empty stubs — zero content risk)
3. **Phase C** (retire `sales-os/` — content already preserved in archive)
4. **Phase D** (complete `WidgetTemplate/` move)
5. **Phase E** (relocate loose docs/binaries)
6. **Phase F** (README doc fix)
7. **Phase G** (`infrastructure/` — only after you confirm intent)
8. **Phase H** (Railway config — only after you confirm the live dashboard config)
9. **Phase I** (close the migration log, mark this ADR Accepted)

---

## Risk Assessment

| Phase | Risk | Severity | Mitigation |
|---|---|---|---|
| A | None — read-only | None | — |
| B | Deleting something that isn't actually empty | Low | Re-verify emptiness immediately before delete |
| C | A script/CI job references root `sales-os/` by relative path | Low–Medium | Gated by Phase A's grep; do not proceed if any hit is found without review |
| D | Import paths inside `WidgetTemplate/` assume its old root location | Medium | Update paths as part of the same atomic commit as the move; verify with `tsc`/lint after |
| E | A doc is linked from elsewhere by its root-relative path | Low | Phase A grep covers markdown link references too |
| F | None — documentation only | None | — |
| G | Moving `salesos/infra/` (if that turns out to be the intent) touches k8s/terraform/CI | High | Explicitly deferred; requires its own ADR/migration-log phase, not bundled here |
| H | Deleting the wrong Railway config breaks a live deploy | High | Explicitly deferred until dashboard config is confirmed out-of-band |

## Rollback Plan

- **Every phase is a single, atomic commit.** `git revert <commit>` undoes it in isolation; no phase is squashed with another.
- **Nothing is deleted without a prior archive or git history copy.** `sales-os/` root copy is redundant with `archive/sales-os/` before deletion — no unique content is ever destroyed. Empty stubs (Phase B) have nothing to roll back to lose.
- **`migration-log/` entries are written before execution, not after**, so a rollback also has a paper trail of intent, matching the existing convention in `phase-01.md`–`phase-03.md`.
- **Phases G and H are not executed until their blocking confirmation is received** — there is no rollback needed for work that hasn't started.

---

## Next step

This ADR is a design document only — **Status: Proposed**, no file operations performed. Once you approve it (and answer the two blocking gaps — `infrastructure/` intent and the live Railway config), I'll run **Phase A (reference check)** first, since every other phase depends on its output, then proceed one atomic phase at a time per the Execution Order above.
