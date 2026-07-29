# Site A–Z crawl — 2026-07-29 (authenticated)

**Target:** `https://sales-os-jet.vercel.app` → API `https://salesos-production-96c0.up.railway.app`  
**Session:** logged-in browser (tenant with Google Connected)  
**Validation:** **light validated** (browser crawl + response-shape code review). Not Production GO.

## Working

| Area | Evidence |
|------|----------|
| Auth session | v3 shell + legacy dashboard reachable |
| Google OAuth | Settings → Integrations: **Connected** `ragheed.a@ratlfintech.com`, last sync 2026-07-29 6:32 PM; Sync Gmail/Calendar actions present |
| Contacts v3 | **43 results**, list + company links |
| People v3 | **2 shown** (admin + user) |
| Activities v3 | Intelligence metrics (Emails 100 / Meetings 116); feed rows empty (honest empty) |
| Tasks v3 | Empty honest (`0` tasks) |
| CRM v3 | Board loads; **0 deals** (data empty, not crash) |
| Employees legacy | List loads (2 profiles) |
| Revenue legacy | Page loads (ARR/NRR zeros) |
| Health (prior) | DB/Redis/Cache/graph connected |

## Broken / degraded (live)

| Area | Severity | Finding |
|------|----------|---------|
| Companies list (v3 + legacy) | **P0 UX** | `total=141221` but grid empty (“No companies”). Root cause: `GET /api/v1/companies` returns **CursorResponse.`data`**, FE `searchCompanies` expected **PaginatedResponse.`items`**. |
| Home metrics | P1 | Executive dashboard **403** for role `user` (missing `executive.read`) |
| Analytics v3 / CS v3 | P1 | Same **403** on executive-backed metrics |
| Admin v3 users | Expected | **403** for non-admin `user` role |
| Company 360 v3 | P1 | Detail route showed **Network Error** for known company id (needs re-check after list fix / API) |
| `/v3/employee-360` | Info | **404** — Emp360 lives at `/employees/[id]` and `/v3/people/[id]` |
| Settings `?tab=integrations` | P2 | Deep-link landed on Notifications until Integrations clicked |
| Notifications prefs | P2 | Prior crawl: could not load notifications API |
| Activity feed vs Google metrics | Info | Sync intelligence populated; activities table empty |

## Fixes prepared locally (not yet production-deployed in this pass)

1. `salesos/frontend/src/lib/api/company.ts` — normalize CursorResponse → PaginatedResponse items  
2. `salesos/frontend/src/lib/__tests__/api.contract.test.ts` — contract for `data` shape  
3. `salesos/backend/sdk/permissions.py` — grant `user` → `executive.read`  
4. `salesos/frontend/src/app/v3/_components/domain-workbench.tsx` + `settings/page.tsx` — `?tab=` deep-link sync  

**Deploy gate:**
- BE: `railway up` started for SalesOS production (`00747343-…`) — `executive.read` for role `user`.
- FE companies/tab fixes are **local only** until commit + Vercel production deploy (blocked without explicit user approval).

## Additional crawl notes

- People 360 (`/v3/people/{id}`) **works** (profile + KPIs).
- Company 360 (`/v3/companies/{id}`) showed **Network Error** (API host healthy; unauthenticated probe returns 401 — likely client/timeout or per-id failure; re-check after list fix).
- Revenue legacy loads with zero metrics (empty data, not crash).

## Verdict

Platform is **pilot-usable with conditions** for Contacts / People / Google connect, but **Companies list is a show-stopper UX bug** until FE client normalize ships. Overall GA remains **production no-go**.
