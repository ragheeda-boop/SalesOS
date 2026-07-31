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

1. **Card component gap** — canonical `Card`/`CardHeader`/`CardContent` live in `@salesos/ui`; deprecated duplicate `src/components/foundation/card.tsx` still exists. `card.test.tsx` fails with `Test suite failed to run` (import/type mismatch), and Card-dependent suites (dashboard, admin, customer-success widgets, DealCard, etc.) fail on rendering assertions.
2. **Stale UI-text assertions** — scattered tests assert old copy that no longer matches current UI strings (e.g. `Expected substring: "Search failed"`, monitoring "DB connection failed" wiring, chart labels).
3. **jsdom missing browser APIs** — `scrollTo`/`scrollIntoView` not polyfilled (release-readiness item; known).

Representative log evidence (run `30664173050`): `TypeError: Cannot read properties of undefined (reading 'data')` (flow tests), `Test suite failed to run` (card), `Expected substring: "Search failed"` (search.api).

## 5. Use for CI-14 (dependency contract)

- Before/after gate: after any dependency bump, `Test Suites` failed count must be `<= 33` and `Tests` failed count `<= 163`; **no new failures** beyond this inventory are acceptable.
- Remediation of these suites is the Sprint 01 Jest-debt story (separate from CI-14's dependency modernization).
- Any suite in this list that becomes green during CI-14's work should be removed from this baseline with a note.

## 6. Record

- Story: **CI-13** (Jest suite baseline) — **CLOSED** per DEC-035. Program progress 14/19.
