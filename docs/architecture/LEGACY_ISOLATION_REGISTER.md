# Legacy Isolation Register

**Date:** 2026-08-05
**Authority:** [`ADR-100: Repository Canonicalization`](../adr/0100-repository-canonicalization.md), Phase 3 (Legacy Isolation)
**Scope of this phase:** Documentation and governance markers only. No file was deleted, moved, or renamed. No code, deployment, Docker, Railway, or CI/CD configuration was modified to produce this register.
**Inputs:** `REPO_TOPOLOGY_AUDIT.md`, `docs/audit/REPOSITORY_HEALTH_GATE_2026-08-05.md`, `migration-log/phase-01.md` – `phase-05.md`

---

## 1. Legacy Inventory

Every item currently classified as a legacy or pending candidate anywhere in the ADR-100 governance chain, consolidated in one place.

| # | Item | Location | First identified in | Current status |
|---|---|---|---|---|
| L1 | `infrastructure/cloud/`, `infrastructure/observability/`, `infrastructure/scripts/` | Repo root | `REPO_TOPOLOGY_AUDIT.md` | PENDING REMOVAL — marked this phase (`infrastructure/README.md`) |
| L2 | Root `railway.json` + `Dockerfile.railway` | Repo root | `REPO_TOPOLOGY_AUDIT.md` | LEGACY CANDIDATE — marked this phase (`docs/ops/RAILWAY_CONFIG_LEGACY_NOTICE.md`) |
| L3 | `WidgetTemplate/` (root, populated) vs. `packages/widget-template/` (empty destination) | Repo root / `packages/` | `REPO_TOPOLOGY_AUDIT.md` | **RESOLVED** — moved to `packages/widget-template/`, root copy removed (`migration-log/phase-07.md`) |
| L4 | `engineering-recovery/` (root, 14 files) | Repo root | `docs/audit/REPOSITORY_HEALTH_GATE_2026-08-05.md` §7 | **RESOLVED** — archived to `archive/engineering-recovery/`, root copy removed (2026-08-05) |
| L5 | `salesos/security-audit-report.json`, `-final.json`, `-latest.json`, `-v2.json` | `salesos/` (canonical app) | `docs/audit/REPOSITORY_HEALTH_GATE_2026-08-05.md` §7 | PENDING — inside canonical app, outside this ADR's directory-topology scope |
| L6 | `salesos/benchmark.db` | `salesos/` (canonical app) | `docs/audit/REPOSITORY_HEALTH_GATE_2026-08-05.md` §7 | PENDING — likely regenerable artifact, not verified against `.gitignore` |
| L7 | `salesos/.tmp-alembic-revs.txt`, `.tmp-ci22-*.txt`, `.tmp-staging-schema.sql` | `salesos/` (canonical app) | `docs/audit/REPOSITORY_HEALTH_GATE_2026-08-05.md` §7 | PENDING — matches pattern already cleaned elsewhere per `migration-log/phase-01.md` |
| L8 | `./__pycache__/.tmp_land_fe_*.pyc` (3 files) | Repo root | `docs/audit/REPOSITORY_HEALTH_GATE_2026-08-05.md` §7 | PENDING — regenerable bytecode cache, low risk |
| L9 | Broken references: `output/SALESOS_*.md` (×4), `notion_analysis.md` | Referenced only from `docs/audit/current-state/15-documentation-audit.md` | Phase 2 (`migration-log/phase-05.md`) | MARKED BROKEN — no file exists to act on; reference itself is the only remaining artifact |
| L10 | `sales-os/` (root, duplicate product tree) | — (resolved) | `REPO_TOPOLOGY_AUDIT.md` | **RESOLVED** — archived to `archive/sales-os/`, root copy removed (Phase 1) |
| L11 | `archive/engineering-os/`, `archive/engineering-recovery/` (empty stubs) | — (resolved) | `REPO_TOPOLOGY_AUDIT.md` | **RESOLVED** — deleted, confirmed empty and unreferenced (Phase 1) |

Items L10–L11 are included for completeness of the historical record; they require no further action.

## 2. Ownership Matrix

| Item | Layer (per ADR-036) | Decision owner | Why this owner |
|---|---|---|---|
| L1 — `infrastructure/` | Implementation (repo topology) | Repository owner (Ragheed) | Pure directory-structure call; no external system involved |
| L2 — Railway configs | Implementation (deployment) | Repository owner (Ragheed), informed by Railway dashboard state | Requires out-of-repo information only the account holder can retrieve |
| L3 — `WidgetTemplate/` | Implementation (shared tooling) | Repository owner (Ragheed) | Non-blocking, low-risk; execution already approved as ADR-100 Phase 4 |
| L4 — `engineering-recovery/` | Engineering Spec (historical record) | Repository owner (Ragheed) | Historical document disposition, no external dependency |
| L5 — `security-audit-report*.json` | Implementation (canonical app, security tooling) | Repository owner + whoever owns the security-scan CI job | Need to confirm which file (if any) is consumed by `security-scan.yml` before touching |
| L6 — `benchmark.db` | Implementation (canonical app) | Repository owner (Ragheed) | Likely local artifact; low-risk but unverified against `.gitignore` |
| L7 — `.tmp-*` files in `salesos/` | Implementation (canonical app) | Repository owner (Ragheed) | Same cleanup pattern already approved once (`migration-log/phase-01.md`) |
| L8 — root `__pycache__` | Implementation (repo root) | Repository owner (Ragheed) | Trivial, regenerable |
| L9 — broken doc references | Business Truth (documentation) | Repository owner (Ragheed) | Documentation-only decision |

## 3. Pending Removal Register

Items where the eventual action is expected to be **delete**, blocked on an explicit condition.

| Item | Blocking condition | Unblocks when |
|---|---|---|
| L1 — `infrastructure/{cloud,observability,scripts}` | User has not confirmed whether this is dead scaffolding or an intended future destination for `salesos/infra/` | User states intent explicitly |
| L2 — one of {root `railway.json`+`Dockerfile.railway`, `salesos/railway.json`} | Which config Railway's dashboard actually builds from is unknown from repo contents alone | User checks the Railway dashboard and reports the active build source |
| L6 — `salesos/benchmark.db` | Not yet verified whether it's `.gitignore`-covered or intentionally committed | A dedicated `salesos/`-internal hygiene pass (out of this ADR's scope) |
| L7 — `salesos/.tmp-*` files | Same pattern as `migration-log/phase-01.md`'s cleanup, but inside the canonical app, not yet authorized for this ADR | A dedicated `salesos/`-internal hygiene pass (out of this ADR's scope) |
| L8 — root `__pycache__/.tmp_land_fe_*.pyc` | No blocker — low risk, simply not yet executed | Any future hygiene pass; safe to include opportunistically |
| L9 — broken doc references (`output/*.md`, `notion_analysis.md`) | No file exists to delete; only the *reference* in `15-documentation-audit.md` could eventually be removed | Optional cleanup once repository owner acknowledges these were never real |

## 4. Pending Migration Register

Items where the eventual action is expected to be **move**, not delete.

| Item | From | To | Blocking condition | Unblocks when |
|---|---|---|---|---|
| L3 — `WidgetTemplate/` | Repo root | `packages/widget-template/` (destination already exists, empty) | None identified — reference check (ADR-100 Phase A) already covered this path | Already approved as ADR-100 Phase 4; ready to execute on request |
| L4 — `engineering-recovery/` | Repo root | `archive/engineering-recovery/` (previously deleted as an empty stub in Phase 1 — would need to be recreated for real content this time) | Not yet scoped into the current 4-phase execution order | Repository owner decides whether to add this as a Phase 5 |

## 5. Future Execution Checklist

Ordered by dependency, not urgency. Checked items are complete; unchecked items require repository-owner action before execution.

- [x] Phase 1 — Safe Cleanup (`sales-os/` retired, empty archive stubs removed) — `migration-log/phase-04.md`
- [x] Phase 2 — Repository Documentation (loose root docs relocated, README fixed, indexes updated) — `migration-log/phase-05.md`
- [x] Repository Health Gate — `docs/audit/REPOSITORY_HEALTH_GATE_2026-08-05.md`
- [x] Phase 3 — Legacy Isolation (this register + markers) — no repository behavior changed
- [x] Phase 4 — Pending Migration Completion: `WidgetTemplate/` → `packages/widget-template/`, root copy removed — `migration-log/phase-07.md`
- [x] **Archive `engineering-recovery/`** (L4): archived to `archive/engineering-recovery/`, root copy removed (2026-08-05)
- [ ] **Confirm Railway build source** (L2): check Railway dashboard, report back which config is live, then delete the other.
- [ ] **Confirm `infrastructure/` intent** (L1): state whether it should be deleted or reserved for a future `salesos/infra/` relocation (which would need its own ADR).
- [ ] **`salesos/`-internal hygiene pass** (L5–L8): separate, smaller-scoped review of `security-audit-report*.json` duplication, `benchmark.db`, and `.tmp-*` files inside the canonical app — requires its own authorization since it touches the app tree ADR-100 has otherwise left untouched throughout every phase so far.
- [ ] **Broken reference cleanup** (L9): low-priority, optional — remove or further annotate the `output/*.md` and `notion_analysis.md` rows in `15-documentation-audit.md` once acknowledged as permanently dead.

---

## Confirmation: no repository behavior changed

This phase added three new files (`infrastructure/README.md`, `docs/ops/RAILWAY_CONFIG_LEGACY_NOTICE.md`, this register) and modified zero existing files. `railway.json`, `Dockerfile.railway`, `salesos/railway.json`, every Docker/compose file, every CI workflow, and all code under `salesos/` remain byte-for-byte unchanged. `git status` scoped to those paths confirms no diff.
