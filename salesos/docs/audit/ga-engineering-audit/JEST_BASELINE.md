# Jest Suite Baseline (CI-13)

> **Purpose:** Fixed-point baseline of the frontend Jest suite, captured from a real GitHub Actions run, so that CI-14 (Frontend Dependency Modernization — the Jest/ESLint/ts-jest major leg) and the Sprint 01 Jest-debt story can be measured before/after without re-deriving the failing inventory each time.
> **Source of truth:** Real CI run evidence (not local claims). Command evidence: CI job `Stage 3: Frontend Unit Tests` (`.github/workflows/ci.yml` → `npm run test -- --coverage --forceExit`).
> **Status:** BASELINE — this document is intentionally a snapshot, not a remediation.

## 1. Capture metadata

| Field | Value |
|---|---|
| CI run | `30664173050` (workflow: CI, commit `d48cc80`, master) |
| Captured | 2026-07-31 |
| Job | `Stage 3: Frontend Unit Tests` (job conclusion: `failure`) |
| Command | `cd salesos/frontend && npm run test -- --coverage --forceExit` |

## 2. Counts

```
Test Suites: 33 failed, 161 passed, 194 total
Tests:       163 failed, 1 skipped, 2092 passed, 2256 total
```

Identical to the Sprint 01 closing numbers and the Sprint 04 CI triage (#7) — **pre-existing, deterministic, not a regression** (triage: `salesos/docs/audit/ga-engineering-audit/SPRINT_04_CI_TRIAGE.md` #7).

## 3. Failing suites (33)

| # | Suite |
|---|---|
| 1 | `src/__tests__/end-to-end.test.tsx` |
| 2 | `src/components/__tests__/pipeline-kanban.test.tsx` |
| 3 | `src/features/dashboard/widgets/mission-center/__tests__/MissionCenter.test.tsx` |
| 4 | `src/app/(dashboard)/settings/__tests__/settings-page.test.tsx` |
| 5 | `src/features/revenue-execution/widgets/nba-widget/__tests__/NBAWidget.test.tsx` |
| 6 | `src/app/(dashboard)/automation/analytics/__tests__/AutomationAnalyticsPage.test.tsx` |
| 7 | `src/components/__tests__/executive-dashboard.test.tsx` |
| 8 | `src/features/automation/widgets/workflow-builder/__tests__/WorkflowBuilder.test.tsx` |
| 9 | `src/application/revenue-execution/__tests__/opportunity.store.test.tsx` |
| 10 | `src/features/admin/widgets/__tests__/HealthDashboard.test.tsx` |
| 11 | `src/components/__tests__/copilot-panel.test.tsx` |
| 12 | `src/features/customer-success/workspace/customer-success/__tests__/CustomerSuccessWorkspace.test.tsx` |
| 13 | `src/components/guidance/__tests__/Onboarding.test.tsx` |
| 14 | `src/app/(dashboard)/monitoring/__tests__/monitoring.test.tsx` |
| 15 | `src/app/(dashboard)/automation/workflows/new/__tests__/NewWorkflowPage.test.tsx` |
| 16 | `src/application/revenue-execution/__tests__/task.store.test.tsx` |
| 17 | `src/components/foundation/__tests__/error-boundary.test.tsx` |
| 18 | `src/application/dashboard/__tests__/widget.store.test.tsx` |
| 19 | `src/lib/__tests__/analytics.test.tsx` |
| 20 | `src/features/revenue-execution/workspace/pipeline/__tests__/DealCard.test.tsx` |
| 21 | `src/features/admin/__tests__/admin-workspace.test.tsx` |
| 22 | `src/application/search/__tests__/search.hooks.test.tsx` |
| 23 | `src/application/api/__tests__/hooks.test.tsx` |
| 24 | `src/application/company-intelligence/__tests__/useCompanyIntelligence.test.tsx` |
| 25 | `src/components/foundation/__tests__/card.test.tsx` |
| 26 | `src/features/customer-success/widgets/customer-success/__tests__/TenantHealthList.test.tsx` |
| 27 | `src/features/analytics/__tests__/AnalyticsWorkspace.test.tsx` |
| 28 | `src/application/search/__tests__/search.api.test.tsx` |
| 29 | `src/features/analytics/__tests__/Analytics.test.tsx` |
| 30 | `src/features/customer-success/widgets/customer-success/__tests__/ActiveUsersWidget.test.tsx` |
| 31 | `src/features/customer-success/widgets/customer-success/__tests__/HealthScoreCard.test.tsx` |
| 32 | `src/features/rag/workspace/rag/__tests__/RagWorkspace.test.tsx` |
| 33 | `src/features/analytics/__tests__/Feedback.test.tsx` |

## 4. Root-cause categories (from triage #7 / Sprint 01 / release-readiness)

1. **Card component gap** — canonical `Card`/`CardHeader`/`CardContent` live in `@salesos/ui`; deprecated duplicate `src/components/foundation/card.tsx` still exists. `card.test.tsx` fails with `Test suite failed to run` (import/type mismatch), and Card-dependent suites (dashboard, admin, customer-success widgets, DealCard, etc.) fail on rendering assertions. **Partial remediation:** `9577c98` (see §6).
2. **Stale UI-text / i18n assertions** — scattered tests assert old copy that no longer matches current UI strings (e.g. `Expected substring: "Search failed"`, monitoring "DB connection failed" wiring, chart labels). **Category remediated** at `a93bc48` (14 suites; narrow Jest light validated — see §6); full CI inventory not re-run.
3. **jsdom missing browser APIs** — `scrollTo`/`scrollIntoView` not polyfilled (release-readiness item; known). **Category remediated** at `b9b96eb` (global stubs in `jest.setup.ts`) + `cd24a49` (copilot `onClose` selector); full CI inventory not re-run.
4. **Stale fetch/API mocks** — suites mocked `global.fetch` or package-level `axios` while production code uses `@/lib/api` (axios instance); incomplete `put` handlers and snake_case↔camelCase response mapping caused `reading 'data'` failures. **Category remediated** (see §6); full CI inventory not re-run.
5. **Incomplete React Query / query-hook mocks** — suites omitted `useQueryClient` from `@tanstack/react-query` mocks, left `useWorkflowExecutions` unconfigured after `ExecutionTimeline` mounted, or rendered live-query workspaces without mocking `useExecutiveDashboard` / chart stubs. **Category remediated** (see §6); full CI inventory not re-run.
6. **Stale DOM/selector assertions** — suites asserted removed markup (DealCard `rounded-full` score badge when `healthScore` missing), stale sidebar copy (`الرئيسية` / `الباقات والتراخيص` vs current `admin.tab.*` Arabic), or obsolete palette click indexes (NewWorkflow assumed a second `"إرسال بريد"`). **Category remediated** (see §6); full CI inventory not re-run.

Representative log evidence (run `30664173050`): `TypeError: Cannot read properties of undefined (reading 'data')` (flow tests), `Test suite failed to run` (card), `Expected substring: "Search failed"` (search.api).

## 5. Use for CI-14 (dependency contract)

- Historical baseline gate (CI-13 capture): failing suites `<= 33`, failing tests `<= 163`; **no new failures** beyond the §3 inventory.
- **Post-remediation expected ceiling (local / CI-like evidence; full Stage 3 inventory not re-run):** failing suites **`<=0`** after `4fdc1d8` (-3) + `5bba606` H2/H3 (-2) + `556304d` six-holdout re-fix (-6) vs section 8 field count **11**. Field verify section 8 (`30677189129` / `1c33c1b`): **11** was CI-authoritative until section 10. **Section 10 field verify** (`30679804383` / `465c638`, Stage 3 job `91314523292`): **0** failing suites - supersedes section 8 for Stage 3 counts. Do **not** claim whole-pipeline CI GREEN from Stage 3 alone.
- Remediation of remaining suites is the Sprint 01 Jest-debt story (separate from CI-14's dependency modernization).
- Any suite in this list that becomes green should be removed from this baseline with a note.

## 6. Remediation progress (post CI-13)

| Date | Commit | Category | Suites recovered | Evidence | Notes |
|---|---|---|---|---|---|
| 2026-07-31 | `9577c98` | Card component gap | 1 | Narrow / related Card primitives landing | Aids foundation `card.test.tsx` recovery; **full CI inventory not re-run** |
| 2026-08-01 | `a93bc48` | Stale UI-text / i18n assertions | 14 | Narrow Jest: **14 suites / 197 tests passed** (**light validated**) | i18n mock / stale copy category remediation |
| 2026-08-01 | `b9b96eb` + `cd24a49` | jsdom missing browser APIs | 2 (inventory) | Narrow Jest: **4 suites / 54 tests passed** (1 skipped) — `copilot-panel`, `RagChat`, `RagWorkspace`, `packages/ui` a11y (**light validated**) | Global `scrollTo`/`scrollIntoView` stubs; per-file hacks removed. Of the 4, **2** were in CI-13 §3 inventory (`copilot-panel`, `RagWorkspace`); `RagChat` / a11y were not in the 33. Ceiling −2 only. |
| 2026-08-01 | `fea37c8` | Stale fetch/API mocks (`global.fetch` / bare `axios` vs `@/lib/api`) | 6 | Narrow Jest: **6 suites / 50 tests passed** — `hooks.test`, `search.hooks`, `useCompanyIntelligence`, `opportunity.store`, `task.store`, `end-to-end` (**light validated**) | Hooks/stores now mock `@/lib/api` axios client; snake_case request → camelCase response mapping; `put` stage/complete handlers. Full CI inventory not re-run. |
| 2026-08-01 | `54597d7` | Incomplete React Query / query-hook mocks | 3 | Narrow Jest: **3 suites / 33 tests passed** — `settings-page`, `WorkflowBuilder`, `AnalyticsWorkspace` (**light validated**) | Landed **after** §8 SHA `1c33c1b`. Tip CI later skipped Stage 3 while Prettier red until `9ec79e9`. |
| 2026-08-01 | `9739a9e` | Stale DOM/selector assertions | 3 | Narrow Jest: **3 suites / 21 tests passed** — `admin-workspace`, `DealCard`, `NewWorkflowPage` (**light validated**) | Landed **after** §8 SHA `1c33c1b`. §8 “did not hold” was chronological (pre-fix field SHA). |
| 2026-08-01 | `4fdc1d8` | Stale production contract assertions | 3 | Narrow Jest: **3 suites / 22 tests passed** — `widget.store`, `lib/analytics`, `Onboarding` (**light validated**) | Targets section 8 #5/#7/#8. Expected field ceiling **11 → ≤8**. Full CI inventory not re-run. |
| 2026-08-01 | `5bba606` | §8 residual — NBAWidget refetch + AutomationAnalytics async wait | 2 | Narrow Jest: **2 suites / 27 tests passed** — `NBAWidget`, `AutomationAnalyticsPage` (**light validated**) | Targets section 8 #2/#3. |
| 2026-08-01 | `556304d` | §8 six-holdout re-fix (CI-like) | 6 | CI-like Jest: **6 suites / 54 tests passed** — `settings-page`, `WorkflowBuilder`, `AnalyticsWorkspace`, `admin-workspace`, `DealCard`, `NewWorkflowPage` (`--coverage --forceExit`, **light validated**) | Hardened mocks/selectors + Prettier-clean. Root causes: re-bind `useQueryClient` after `clearAllMocks`; `useWorkflowExecutions` `mockImplementation`; executiveDashboard mockImplementation; pinned `admin.tab.*` i18n; tolerant em-dash / palette clicks. (Landed in same tip as CI-19 Wave 3 SHA-pin.) Expected field ceiling **11 → ≤0** with `4fdc1d8`+`5bba606`. Full Stage 3 inventory not re-run. |

**Revised expected failing-suite ceiling (post holdout re-fix, light):** **≤0** vs section 8 field count **11**. **Met** by §10 field verify (`30679804383`): **0** failing suites. Do **not** claim whole-pipeline CI GREEN.

## 7. Record

- Story: **CI-13** (Jest suite baseline) — **CLOSED** per DEC-035. Program progress 14/19.
- Jest-debt remediation continues under Sprint 01 (not CI-14); see §6.

## 8. Field verify — Stage 3 after Prettier unblock (`1c33c1b`)

| Field | Value |
|---|---|
| CI run | `30677189129` (workflow: CI, commit `1c33c1b`, master) |
| Captured | 2026-08-01 |
| Job | `Stage 3: Frontend Unit Tests` (job id `91306867714`, conclusion: `failure`) |
| Stage 1 Frontend Lint | **success** (ESLint + Prettier check) — Prettier unblock on `copilot-panel.test.tsx` held |
| Command | `cd salesos/frontend && npm run test -- --coverage --forceExit` |

### Counts (field-verified)

```
Test Suites: 11 failed, 185 passed, 196 total
Tests:       51 failed, 1 skipped, 2227 passed, 2279 total
```

- vs CI-13 fixed-point (section 2): **33 → 11** failing suites (net recovery held in full CI).
- vs observer gate ceiling **≤10**: **11** — **over by 1** (do not treat Stage 3 as within ceiling).
- vs post-remediation expected **≤4** (sections 5–6, light-validated only): **not met** — several section 6 “narrow Jest” recoveries did not hold under full CI coverage/`forceExit`.

### Failing suites (11) — all subset of section 3 inventory (debt, not `1c33c1b` regression)

| # | Suite | Notes (CI log) |
|---|---|---|
| 1 | `src/app/(dashboard)/settings/__tests__/settings-page.test.tsx` | `useQueryClient is not a function` — pre-`54597d7` at this SHA; **re-fixed** in `556304d` (pending next field verify) |
| 2 | `src/features/revenue-execution/widgets/nba-widget/__tests__/NBAWidget.test.tsx` | refetch call-count — **remediated** in `5bba606` (pending next field verify) |
| 3 | `src/app/(dashboard)/automation/analytics/__tests__/AutomationAnalyticsPage.test.tsx` | stale UI-text / testids — **remediated** in `5bba606` (pending next field verify) |
| 4 | `src/features/automation/widgets/workflow-builder/__tests__/WorkflowBuilder.test.tsx` | `useWorkflowExecutions` undefined — pre-`54597d7` at this SHA; **re-fixed** in `556304d` (pending next field verify) |
| 5 | `src/components/guidance/__tests__/Onboarding.test.tsx` | localStorage / progress copy — **remediated** (`4fdc1d8`; pending next field verify) |
| 6 | `src/app/(dashboard)/automation/workflows/new/__tests__/NewWorkflowPage.test.tsx` | pre-`9739a9e` at this SHA; **re-fixed** in `556304d` (pending next field verify) |
| 7 | `src/application/dashboard/__tests__/widget.store.test.tsx` | `deriveStatus` / widget inventory — **remediated** (`4fdc1d8`; pending next field verify) |
| 8 | `src/lib/__tests__/analytics.test.tsx` | Blob JSON parse — **remediated** (`4fdc1d8`; pending next field verify) |
| 9 | `src/features/revenue-execution/workspace/pipeline/__tests__/DealCard.test.tsx` | pre-`9739a9e` at this SHA; **re-fixed** in `556304d` (pending next field verify) |
| 10 | `src/features/admin/__tests__/admin-workspace.test.tsx` | sidebar copy — pre-`9739a9e` at this SHA; **re-fixed** in `556304d` (pending next field verify) |
| 11 | `src/features/analytics/__tests__/AnalyticsWorkspace.test.tsx` | `No QueryClient set` — pre-`54597d7` at this SHA; **re-fixed** in `556304d` (pending next field verify) |

### Classification

| Class | Finding |
|---|---|
| Regression from `1c33c1b` | **None** — format-only Prettier on `copilot-panel.test.tsx`; Stage 1 lint/Prettier green |
| Pre-existing Jest debt | **All 11** — each path appears in CI-13 section 3 list |
| Ceiling | **11 > 10** (observer) and **11 > 4** (section 5 expected) |

Do **not** claim full CI GREEN. Backend Stage 1/2 and Stage 5 gates remain red on this run (out of scope for this observer note).

## 9. Stage 3 holdout support (post-`4fdc1d8`) — DEC-067

> **Docs-only.** Holdout **code** ownership: Frontend Lead / holdout agent. Program agents must not edit the eight suite files below while a holdout remediator owns them. Companion: [`docs/program/decisions/DEC-067-JEST-STAGE3-HOLDOUT-SUPPORT.md`](../../../../docs/program/decisions/DEC-067-JEST-STAGE3-HOLDOUT-SUPPORT.md).

### 9.1 Expected ceiling

| Basis | Failing suites |
|---|---:|
| §8 field verify (`30677189129` / `1c33c1b`) | **11** |
| Minus §6 stale production contract (`4fdc1d8`) — #5/#7/#8 light PASS | **−3** |
| Minus §6 residual H2/H3 (`5bba606`) — light PASS | **−2** |
| Minus §6 six-holdout re-fix (`556304d`) — H1/H4–H8 CI-like PASS | **−6** |
| **Expected next field ceiling** | **≤0** |
| **Section 10 field verify (30679804383 / 465c638)** | **0** |

§10 field-verified **0** failing suites (holds). Still do **not** treat Stage 3 alone as whole-pipeline GREEN.

### 9.2 Holdout inventory (H1–H8)

| ID | Suite | Notes |
|---|---|---|
| H1 | `src/app/(dashboard)/settings/__tests__/settings-page.test.tsx` | **re-fixed** in `556304d` — `useQueryClient` re-bind |
| H2 | `src/features/revenue-execution/widgets/nba-widget/__tests__/NBAWidget.test.tsx` | **remediated** in `5bba606` |
| H3 | `src/app/(dashboard)/automation/analytics/__tests__/AutomationAnalyticsPage.test.tsx` | **remediated** in `5bba606` |
| H4 | `src/features/automation/widgets/workflow-builder/__tests__/WorkflowBuilder.test.tsx` | **re-fixed** in `556304d` |
| H5 | `src/app/(dashboard)/automation/workflows/new/__tests__/NewWorkflowPage.test.tsx` | **re-fixed** in `556304d` |
| H6 | `src/features/revenue-execution/workspace/pipeline/__tests__/DealCard.test.tsx` | **re-fixed** in `556304d` |
| H7 | `src/features/admin/__tests__/admin-workspace.test.tsx` | **re-fixed** in `556304d` |
| H8 | `src/features/analytics/__tests__/AnalyticsWorkspace.test.tsx` | **re-fixed** in `556304d` |

**Field verify section 10:** Onboarding / widget.store / lib/analytics (`4fdc1d8`) + H1-H8 held under full Stage 3 — **0** failing suites.

### 9.3 Next Stage 3 field-verify recipe

**Completed 2026-08-01** — see **§10**. Prior steps (kept for audit trail):

1. Tip SHA must include `4fdc1d8` + `5bba606` + `556304d` + Prettier tip (`11470b1` Onboarding format fix after `9ec79e9`) so Stage 1 Frontend Lint is green and Stage 3 runs.  
2. Capture GitHub Actions CI → job `Stage 3: Frontend Unit Tests` (run id, counts, failing paths).  
3. Append a new §10 field-verify block; expected failing paths **empty** if remediations hold (or name any true regression).  
4. Update R-23 / board with the captured count. **Never** claim Stage 3 green from narrow Jest alone / whole-pipeline GREEN from Stage 3 alone.

## 10. Field verify - Stage 3 after holdout harden + Prettier Onboarding gate (`465c638`)

| Field | Value |
|---|---|
| CI run | `30679804383` (workflow: CI, commit `465c638`, master; includes `556304d` holdouts + `11470b1` Onboarding Prettier) |
| Captured | 2026-08-01 |
| Job | `Stage 3: Frontend Unit Tests` (job id `91314523292`, conclusion: `success`) |
| Stage 1 Frontend Lint | **success** (ESLint + Prettier check) — prior tip red on `Onboarding.test.tsx` until `11470b1` |
| Command | `cd salesos/frontend && npm run test -- --coverage --forceExit` |

### Counts (field-verified)

```
Test Suites: 196 passed, 196 total
Tests:       1 skipped, 2278 passed, 2279 total
```

- vs §8 field verify (`30677189129` / `1c33c1b`): **11 → 0** failing suites.
- vs light expected ceiling **≤0** (`4fdc1d8` + `5bba606` + `556304d`): **met**.
- Failing suite paths: **none**.

### Classification

| Class | Finding |
|---|---|
| Holdout regression (H1-H8 + Onboarding/widget.store/analytics) | **None** — Stage 3 job success; 0 failed suites |
| Stage 3 field ceiling | **0** (authoritative supersedes §8 **11**) |
| Whole-pipeline CI | **Still failure** on this run — Backend Lint/Types, pip-audit, Secrets Scan red; Stage 3/6+ downstream skipped or out of FE scope |

**Do not claim whole-pipeline GREEN.** Stage 3 Frontend Unit Tests field-verified success only.
