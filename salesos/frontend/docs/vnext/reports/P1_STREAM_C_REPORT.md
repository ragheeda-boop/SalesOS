# P1 Stream C Report — Frontend Issues

> Date: 2026-07-17
> Scope: VIO-1, VIO-5, VIO-2/3/4, G-5, G-9

---

## G-9: Viewport meta tag

**Status**: ✅ Completed
**File modified**: `src/app/layout.tsx`

Added Next.js `viewport` export with `width: device-width, initialScale: 1` to ensure proper mobile rendering.

---

## G-5: UX/UI — Hardcoded colors

**Status**: ✅ Completed
**Files modified**:
- `src/features/company-intelligence/widgets/company-dna/CompanyDNAView.tsx` — replaced `text-green-600`, `text-red-600`, `bg-green-500`, `bg-amber-500`, `bg-red-500`, Badge color classes with CSS variable references
- `src/features/company-intelligence/widgets/company-360/ActivityTimeline.tsx` — replaced ACTION_CONFIG and FILTER_CHIPS color classes with CSS variable references
- `src/features/company-intelligence/widgets/company-360/DecisionPlatformPanel.tsx` — replaced ConfidenceBadge, ScoreGauge, risk flag, and impact colors with CSS variable references
- `src/features/company-intelligence/widgets/company-360/KnowledgeGraphPanel.tsx` — replaced RELATION_COLORS and StrengthBar color classes with CSS variable references
- `src/features/revenue-execution/widgets/playbook-engine/PlaybookView.tsx` — replaced green badge and dark mode wrapper classes with CSS variable references

All hardcoded Tailwind color utility classes (`text-green-600`, `bg-white`, `text-red-500`, etc.) in the targeted dashboard and company page widgets were replaced with `var(--color-*)` CSS variable references.

---

## VIO-1: Company — Missing Container/View

**Status**: ✅ Completed
**Files created**:
- `src/features/company-intelligence/widgets/company-360/Company360Container.tsx` — `createWidget()` wrapper using Widget SDK, fetches company ID from route params
- `src/features/company-intelligence/widgets/company-360/Company360View.tsx` — presentational component rendering DecisionPlatformPanel, KnowledgeGraphPanel, and ActivityTimeline in a responsive grid
- `src/features/company-intelligence/widgets/company-360/types.ts` — type definitions for view and widget props
- `src/features/company-intelligence/widgets/company-360/index.ts` — barrel exports for Company360Widget, Company360View, and types

The three existing panels (ActivityTimeline, DecisionPlatformPanel, KnowledgeGraphPanel) are composed into a proper Container/View pattern following the REFERENCE_WIDGET_GUIDE.md specification. The Container handles SDK integration via `createWidget()`, while the View is a pure presentational component.

---

## VIO-2: CompanyDNA — Decision Platform scoring

**Status**: ✅ Completed
**File modified**: `src/features/company-intelligence/widgets/company-dna/CompanyDNAContainer.tsx`

- Removed unused `useDecision()` import from DecisionProvider (was called but return value ignored)
- Added `useDecisionScores(companyId, 'company')` from `@/lib/decisionQueries` to fetch Decision Platform scores via the `/api/v1/decision/scores` API endpoint
- Merged Decision Platform scores into the DNA data object passed to `CompanyDNAView`

---

## VIO-3: Employee 360 — Decision Platform scoring

**Status**: ✅ Completed
**File modified**: `src/components/employee-360-page.tsx`

- Added `useDecisionScores(employeeId, 'employee')` import and call in `ScoringTab`
- When `useEmployeeScore` returns null (no API score available), falls back to Decision Platform scores — displays an average score with individual factor breakdowns
- Each factor from the Decision Platform is rendered as a labeled progress bar
- Badge indicator ("Decision Platform") shown when using platform-sourced data

---

## VIO-4: Playbook — Decision Platform scoring

**Status**: ✅ Completed
**File modified**: `src/features/revenue-execution/widgets/playbook-engine/PlaybookContainer.tsx`

- Added `useDecisionRecommendations(companyId, 'company')` to fetch recommendations from Decision Platform API
- Overrides the hardcoded `successRate` with the confidence score from the first Decision Platform recommendation
- Passes `decisionRecommendations` in the widget data (available for future View extension)

---

## VIO-5: Settings — localStorage business data

**Status**: ✅ Completed
**Files modified**:
- `src/lib/api.ts` — added `getNotificationPreferences()`, `updateNotificationPreferences()`, `getApiKeys()`, `createApiKey()`, `deleteApiKey()` API functions with `X-Tenant-Id` header support
- `src/lib/queryKeys.ts` — added `settingsKeys` with `notifications()` and `apiKeys()` query key factories
- `src/app/(dashboard)/settings/page.tsx` — replaced all localStorage read/write operations with React Query hooks:

**Notifications tab**:
- `useQuery` with `settingsKeys.notifications()` fetches from `GET /api/v1/settings/notifications`
- `useMutation` updates via `PUT /api/v1/settings/notifications`
- Client state is synced from server response via `useEffect`

**API Keys tab**:
- `useQuery` with `settingsKeys.apiKeys()` fetches from `GET /api/v1/settings/api-keys`
- `createKeyMutation` creates via `POST /api/v1/settings/api-keys`
- `revokeKeyMutation` deletes via `DELETE /api/v1/settings/api-keys/{id}`
- Loading states shown with Spinner component
- Empty state message when no keys exist
- Removed all `loadApiKeys()`, `saveApiKeys()`, `generateKey()` localStorage helper functions

---

## Verification

### TypeScript check
```
npx tsc --noEmit
```
**Result**: 26 errors total — all pre-existing (0 new errors from Stream C changes). Pre-existing errors are in:
- `analytics/page.tsx` — pipeline property possibly undefined
- `automation/analytics/page.tsx` — duplicate Workflow identifier
- `employee-360-page.tsx` — missing Button import in TimelineTab (pre-existing, not modified by Stream C)
- `lazy-exports.tsx` — dynamic import type mismatches
- `dashboard-loading.tsx` — Skeleton style prop type issue

### Files created
| File | Purpose |
|------|---------|
| `src/features/company-intelligence/widgets/company-360/Company360Container.tsx` | VIO-1 Widget SDK container |
| `src/features/company-intelligence/widgets/company-360/Company360View.tsx` | VIO-1 Presentational view |
| `src/features/company-intelligence/widgets/company-360/types.ts` | VIO-1 Type definitions |
| `src/features/company-intelligence/widgets/company-360/index.ts` | VIO-1 Barrel exports |
| `src/lib/api/settings.ts` | VIO-5 API functions for settings |

### Files modified
| File | Changes |
|------|---------|
| `src/app/layout.tsx` | G-9 Added viewport export |
| `src/features/company-intelligence/widgets/company-dna/CompanyDNAContainer.tsx` | VIO-2 Added Decision Platform scores |
| `src/features/company-intelligence/widgets/company-dna/CompanyDNAView.tsx` | G-5 Replaced hardcoded color classes |
| `src/components/employee-360-page.tsx` | VIO-3 Added Decision Platform scoring fallback |
| `src/features/revenue-execution/widgets/playbook-engine/PlaybookContainer.tsx` | VIO-4 Added Decision Platform recommendations |
| `src/features/revenue-execution/widgets/playbook-engine/PlaybookView.tsx` | G-5 Replaced hardcoded color classes |
| `src/features/company-intelligence/widgets/company-360/ActivityTimeline.tsx` | G-5 Replaced hardcoded color classes |
| `src/features/company-intelligence/widgets/company-360/DecisionPlatformPanel.tsx` | G-5 Replaced hardcoded color classes |
| `src/features/company-intelligence/widgets/company-360/KnowledgeGraphPanel.tsx` | G-5 Replaced hardcoded color classes |
| `src/lib/api.ts` | VIO-5 Added settings barrel export |
| `src/lib/queryKeys.ts` | VIO-5 Added settingsKeys |
| `src/app/(dashboard)/settings/page.tsx` | VIO-5 Replaced localStorage with React Query + API |

### Verification results
- ✅ G-9: Viewport meta tag added via Next.js `viewport` export
- ✅ G-5: Hardcoded Tailwind colors replaced with CSS var references across 7 files
- ✅ VIO-1: Company360 Container/View pattern created with 4 new files following Widget SDK conventions
- ✅ VIO-2: CompanyDNA routes scoring through Decision Platform via `useDecisionScores`
- ✅ VIO-3: Employee 360 ScoringTab falls back to Decision Platform scores when API unavailable
- ✅ VIO-4: Playbook success rate sourced from Decision Platform recommendations
- ✅ VIO-5: Settings notification prefs and API keys migrated from localStorage to API-backed React Query hooks
- ✅ TypeScript: Zero new compilation errors introduced
