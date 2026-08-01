# DEC-067 — Jest Stage 3 holdout support package (docs; R-23)

> **Status:** **Accepted** — support inventory recorded; holdout **code** ownership remains Frontend Lead / holdout agent  
> **Date:** 2026-08-01  
> **Board:** Frontend / Jest-debt (SalesOS / AQLIYA)  
> **Story / risk:** Sprint 01 Jest-debt / **R-23** (not CI-14)  
> **Authority:** CI-13 baseline DEC-035 · field verify `30677189129` / `1c33c1b` (11 failing) · contract remediations `4fdc1d8`  
> **Out of scope this land:** holdout `.test.tsx` edits · `package.json` / Jest major (CI-14 Slice 3) · Stage 3 green claim · CI-22 / Railway

---

## 1. Why this package

Stage 3 field verify (`30677189129`) left **11** failing suites — authoritative over light-validated ≤4 ceilings. Three of those (#5 Onboarding, #7 widget.store, #8 analytics) were remediated under stale production-contract category at `4fdc1d8` (**light validated** only). The remaining **8** are the **Stage 3 holdout set**.

Parallel agents were already touching holdout files. Program needs a **single support inventory** so remediations do not collide and so the next Stage 3 field verify has a clear expected ceiling.

---

## 2. Holdout set (8) — post-`4fdc1d8` expected

Authoritative parent inventory: `JEST_BASELINE.md` §8. Expected field ceiling after contract land: **11 → ≤8** (pending next CI Stage 3 capture).

| # | Suite (path under `salesos/frontend/`) | §8 failure class |
|---|---|---|
| H1 | `src/app/(dashboard)/settings/__tests__/settings-page.test.tsx` | `useQueryClient` mock gap (light `54597d7` did not hold) |
| H2 | `src/features/revenue-execution/widgets/nba-widget/__tests__/NBAWidget.test.tsx` | refetch call-count assertion |
| H3 | `src/app/(dashboard)/automation/analytics/__tests__/AutomationAnalyticsPage.test.tsx` | stale UI-text / missing testids |
| H4 | `src/features/automation/widgets/workflow-builder/__tests__/WorkflowBuilder.test.tsx` | `useWorkflowExecutions` undefined (light did not hold) |
| H5 | `src/app/(dashboard)/automation/workflows/new/__tests__/NewWorkflowPage.test.tsx` | DOM/selector light `9739a9e` did not hold |
| H6 | `src/features/revenue-execution/workspace/pipeline/__tests__/DealCard.test.tsx` | DOM/selector light `9739a9e` did not hold |
| H7 | `src/features/admin/__tests__/admin-workspace.test.tsx` | sidebar copy light did not hold |
| H8 | `src/features/analytics/__tests__/AnalyticsWorkspace.test.tsx` | `No QueryClient set` (light did not hold) |

**Not holdouts (pending field verify only):** Onboarding, widget.store, lib/analytics — remediated at `4fdc1d8`.

---

## 3. Ownership / anti-overlap rules

| Actor | May edit |
|---|---|
| **Holdout agent / Frontend Lead** | The 8 holdout suite files above (and minimal production code only if a test proves a real contract bug) |
| **Program / support docs** | `JEST_BASELINE.md` §9, this DEC, board / R-23 / DAG notes |
| **Parallel STOP** | Do **not** “help” by editing holdout files from CI-14 / CI-20 / CI-19 agents |

---

## 4. Field-verify recipe (next Stage 3 capture)

When tip includes holdout remediations + `4fdc1d8`:

1. Wait for GitHub Actions **CI** workflow on the tip SHA.  
2. Job: `Stage 3: Frontend Unit Tests` — record run id, job id, suite/test counts.  
3. Update `JEST_BASELINE.md` §8→§10 (new field verify) — failing list must be a subset of H1–H8 (plus any true regression, named).  
4. Expected: failing suites **≤8**; do **not** claim Stage 3 green or CI GREEN without that evidence.

Narrow local Jest on a single holdout is **light validated** only — never overrides field verify.

---

## 5. Decision

Accept this **docs-only** Stage 3 holdout support package. Record the 8-suite holdout inventory and ownership rules in `JEST_BASELINE.md` §9. Keep R-23 **Open — mitigating**. Do **not** close Jest-debt. Do **not** start CI-14 Slice 3 (Jest major).

---

## 6. Validation

| Check | Result |
|---|---|
| Holdout test file edits this land | **None** |
| Stage 3 / full Jest suite | **not run** |
| Label | **not validated** (docs only) |

**CI GREEN not met.**
