# Progress — Wave 0 FE (PROD-W0-*) + FE notes for Wave 4

**Date:** 2026-07-22  
**Owner:** Frontend agent  
**Product:** SalesOS (platform)  
**Validation classification:** **build validated** (FE package only)

## Summary

Wave 0 frontend unblockers are closed: `npm run lint`, `npx tsc --noEmit`, and `npm run build` all exit **0** in `salesos/frontend`. Runtime 404s for GA routes (`/copilot`, `/analytics`, …) were **FE image drift** (PROD-W4-001) — **resolved** by rebuilding `salesos-frontend:local` and recreating the container (see `PROGRESS-WAVE4-FE-IMAGE.md`).

## Items

| ID | Status | Notes |
|----|--------|-------|
| PROD-W0-001 | **Done** | Hooks + other ESLint errors fixed (see files) |
| PROD-W0-002 | **Done** | 3 TypeScript errors fixed |
| PROD-W0-003 | **Done** (local) | `npm run build` exit 0; standalone copy warning noted |
| PROD-W4-001 (FE source check) | **N/A source / open infra** | Routes present in app router + build output; running container image still stale |

## Files changed

1. `salesos/frontend/src/features/admin/widgets/TenantList.tsx` — extract `TenantRow`; call `useUpdateAdminTenant` at component top level (rules-of-hooks)
2. `salesos/frontend/src/features/admin/__tests__/admin-queries.test.tsx` — named wrapper + `displayName`
3. `salesos/frontend/src/features/dashboard/_layout/dashboard-metrics-header.tsx` — replace raw `<a>` with Next `Link`
4. `salesos/frontend/src/features/search/components/SearchHeader.tsx` — escape quotes (`&quot;`)
5. `salesos/frontend/src/app/(dashboard)/automation/analytics/page.tsx` — use `WorkflowType` instead of Lucide `Workflow` as a type
6. `salesos/frontend/src/features/automation/widgets/workflow-builder/ExecutionTimeline.tsx` — safe `toStepResultEntry` mapper (no unsafe cast)
7. `salesos/frontend/src/features/dashboard/_layout/dashboard-loading.tsx` — use Skeleton `height` prop instead of invalid `style`
8. `salesos/frontend/src/app/(dashboard)/admin/flags/page.tsx` — stop calling `useUpdateAdminFeatureFlag` inside callback
9. `salesos/frontend/src/lib/hooks/adminQueries.ts` — `useUpdateAdminFeatureFlag()` takes `{ id, … }` in mutate payload
10. `salesos/frontend/src/app/(dashboard)/automation/analytics/__tests__/AutomationAnalyticsPage.test.tsx` — MockLink `displayName`
11. `salesos/frontend/src/app/(dashboard)/automation/workflows/new/__tests__/NewWorkflowPage.test.tsx` — MockLink `displayName`

## Commands run (evidence)

| Command | Cwd | Exit | Result |
|---------|-----|-----:|--------|
| `npm run lint` | `salesos/frontend` | **0** | No ESLint Errors (Tailwind/`exhaustive-deps` Warnings remain; non-blocking) |
| `npx tsc --noEmit` | `salesos/frontend` | **0** | Clean |
| `npm run build` | `salesos/frontend` | **0** | Compiled; 51 static pages; routes include `/copilot`, `/analytics`, `/marketplace`, `/employees`, `/knowledge`, `/signals`, `/rules`, `/activities` |

**Not run:** full monorepo test suite, Docker FE image rebuild, alembic, deploy, browser E2E.

## Build caveat (honest)

During `next build` standalone finalize, a **non-fatal** warning appeared:

`Failed to copy traced files … page_client-reference-manifest.js` (`ENOENT`) under `.next/standalone` for `(dashboard)/page.js`.

Build still exited **0** and route table was emitted. Likely Windows/OneDrive/`output: 'standalone'` path quirk. **Needs verify** on CI/Linux image build before treating standalone artifact as production-ready.

## Wave 4 FE route note

Audit 404s on running compose FE image are **image/source mismatch**, not absent `page.tsx` files. Source + local production build include the routes. Closing PROD-W4-001 requires rebuilding/redeploying the FE image from a commit that includes this source (owned by infra/Wave 4 — not done here).

## Remaining blockers (outside this agent’s closed scope)

- **PROD-W4-001:** Rebuild/redeploy FE Docker image for route parity on runtime
- Backend Wave 0+/1–3: Alembic drift, security P0, pytest failures (other agents)
- Standalone copy warning on Windows host — verify on CI
- Many ESLint **Warnings** (Tailwind color classes) — P3/P4, not blocking lint exit

## Validation labels

| Gate | Label |
|------|--------|
| FE lint | **build validated** (exit 0) |
| FE tsc | **build validated** (exit 0) |
| FE production build | **build validated** with conditions (exit 0; standalone ENOENT warning) |
| Runtime route smoke on Docker FE | **not validated** (image not rebuilt) |
| Production readiness overall | **production no-go** (platform score unchanged; Wave 0 FE gate only) |
