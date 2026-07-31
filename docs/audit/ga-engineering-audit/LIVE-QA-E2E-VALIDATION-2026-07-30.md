# SalesOS — Live End-to-End QA Validation Report

**Date:** 2026-07-30
**Tester stance:** Staff QA Engineer / Principal Frontend Engineer / Enterprise Product Acceptance Tester
**Method:** Browser-only, black-box testing against the live application. No source code was consulted to decide what to test or how to interpret results — only observed behavior (rendered UI, console, network) was used as evidence. (Root-cause hypotheses reference file names surfaced directly in stack traces, or knowledge already established independently in this session's separate architecture review — never used to guess what to click next.)
**Environment:** `https://sales-os-jet.vercel.app/` — account `ragheed.a@muhide.com`, role `user` (per the account's own employee record)
**Scope discipline:** Per explicit agreement with the requester before testing began: Create actions were limited to one clearly-labeled test record (`QA-TEST-DoNotUse-20260730`), which the platform itself rejected (see BUG-015) so no cleanup was needed. No pre-existing record was deleted. No password-change or other credential-affecting form was submitted.

> **STATUS UPDATE (same-day, later):** All 16 bugs documented in this report were subsequently fixed and independently re-verified live — see [`LIVE-QA-RECHECK-2026-07-30.md`](LIVE-QA-RECHECK-2026-07-30.md) for the full re-verification trail (including a fix that went deeper than the frontend symptom for BUG-009, and a genuine root-cause fix — not a workaround — for BUG-005's Postgres `SET LOCAL` parameterization issue). The **NO-GO** verdict in §13 below reflects the state of the application *at the time of this report* and is superseded by the recheck's findings. This document is kept as-is, unedited below this notice, as the historical record of what was found and why — see the recheck document for current status.

---

## 1. Executive Summary

This is a substantially-built product with a good visual/interaction foundation (fast client-side navigation, a consistent dark theme, honest empty states in most places) sitting on top of a frontend that **hard-crashes on a majority of its core workflows**. In a single, unhurried pass through the primary navigation, six distinct pages produced full error-boundary or worse crashes (Dashboard, Company Detail, Pipeline, Meetings, Automation, and — most severely — the entire application on a routine Create-record attempt), three backend endpoints returned genuine `500` errors (Search, Customer Success telemetry, RAG documents), and the Admin section's internationalization is broken across every tab it has. None of this required adversarial testing — every failure was found on the first, default, straight-line path a real user would take.

The single most important page in the product by the vendor's own stated vision — **Company Intelligence Workspace / Company 360** — does not render at all, for any company, 100% of the time. **Universal Search**, the product's stated #2 priority feature, returns a server error on every query. These are not edge cases; they are the front door.

The most severe individual finding is **BUG-015**: submitting the "Add Company" form as a `user`-role account (who lacks create permission) does not show a permission error — it crashes the entire single-page application past its own error boundary, to a blank white screen with no recovery path except a hard reload. The button that triggers this is fully visible and enabled for this role.

**Recommendation: NO-GO for production use in its current deployed state.** The issues found are concentrated and specific enough to be fixable quickly (see Immediate Actions), but as currently deployed, a new real user logging in for the first time will very likely hit a full-page crash within their first two or three clicks.

---

## 2. Coverage

**Tested directly, this session:** 30 distinct URLs/UI-states across every one of the 22 primary sidebar navigation items (100% of primary nav) plus 5 additional deep-linked routes not present in the sidebar (`/rag`, `/ai`, `/copilot`, `/knowledge`, `/marketplace`), 2 company-detail records, 1 employee-detail record, 4 Settings tabs, 5 of 8 Admin tabs, 1 full Create-record functional test, 1 search functional test (2 query strategies), and an auth-guard/session test.

**Not tested this pass (explicitly, honestly, not silently skipped):** the `/v3/*` route tree (not reachable from this account's sidebar — a separate, parallel UI known to exist from independent architecture review, out of scope for a black-box crawl that follows visible navigation), sub-routes not linked from any visible UI (`/decisions/templates`, `/revenue/quotas`, `/revenue/territories`, `/pipeline/analytics`, `/search/analytics`, 5 `/analytics/*` drill-downs, `/automation/{analytics,workflows/new}`, `/knowledge/connectors`, `/marketplace/{id}/config`, `/copilot/telemetry`), `/opportunities/{id}` detail (no opportunities exist in this tenant to open), remaining 3 Admin tabs (Plans/Flags/Jobs/AI-Costs — 4 actually, one miscounted), Settings → Data Settings tab body, and any workflow requiring pre-existing pipeline/opportunity data this tenant doesn't have. A follow-up pass should cover these plus the `/v3` tree.

**Why this is still a valid, high-confidence result:** every core P0/P1 feature named in the product's own priority documentation (Company Workspace, Universal Search, Dashboard, Navigation) was reached and tested, and the crash rate on that core set alone (3 of 4) is severe enough that expanding coverage further would refine the picture, not change the verdict.

---

## 3. Login, Session, and Auth

| Check | Result |
|---|---|
| Landing page renders | PASS — Arabic-first landing page, SalesOS branding, clean Login/Register CTAs |
| Login | Performed manually by the requester (agent does not enter credentials — hard policy boundary); `POST /api/v1/identity/login` → 200 |
| Redirect after login | PASS — lands on `/dashboard` |
| Session persistence | PASS — remained authenticated across 30+ page navigations over the full session with zero unexpected logouts |
| Logout control | **NOT FOUND** — see BUG-016. Searched full sidebar (22 items), Command Palette ("logout" → No results), all header buttons. One `"Open menu"` DOM element exists but is non-interactive/off-screen at desktop viewport (1280×720) — likely mobile-only. |
| Auth guard on cleared session | PASS (tested as a proxy for logout) — clearing `access_token`/`refresh_token` from localStorage and navigating to a protected route correctly redirected to `/login`, which rendered cleanly |
| Re-login | Not performed — session intentionally ended at the close of testing; would require the requester to re-authenticate |

---

## 4. Full Bug Register

Severity: **P0** = core feature totally broken / crashes app. **P1** = feature broken or genuine backend fault, workaround may exist. **P2** = visible defect, degrades trust/professionalism, not blocking. **P3** = cosmetic/minor.

### BUG-015 — P0 — CRITICAL — Add Company on a 403 crashes the entire application
- **Category:** Reliability / Error Handling / RBAC
- **Steps:** As a `user`-role account, go to `/companies` → click "Add Company" (visible, enabled) → fill Company Name + CR Number with clearly-labeled test data → click Save
- **Expected:** A permission-denied message, or the button hidden/disabled for this role
- **Actual:** `POST /api/v1/companies` → `403 Forbidden`, then the **entire single-page app crashes** to a blank white screen: *"Application error: a client-side exception has occurred while loading sales-os-jet.vercel.app"* — not the app's own recoverable error boundary (seen elsewhere in this report), a level below that, requiring a full page reload to recover
- **Evidence:** Network: `POST /api/v1/companies → 403`. Screenshot: blank white page, single line of browser-native error text, no app chrome at all.
- **Likely root cause:** the create-company mutation's error handler throws a second, unhandled error while processing the 403 response (e.g., reading a field that doesn't exist on this error shape), escaping the React error boundary entirely
- **Suggested fix:** (1) defensively fix the mutation's error handler; (2) hide/disable "Add Company" for roles without create permission; (3) audit other create/update/delete flows for the same error-handling code path
- **Estimated complexity:** Low (1) + Low (2) + Medium (3, audit scope)
- **Verified safe:** re-searched for the test company name after recovery — zero results, confirming no orphaned data

### BUG-000 — P0 — CRITICAL — Company Detail / Company 360 page crashes 100% of the time
- **Category:** Reliability / Core Feature
- **Steps:** Click "Details" on any company in `/companies`, or navigate directly to `/companies/{any-id}`
- **Expected:** Company 360 workspace renders (per product's stated #1 feature)
- **Actual:** Error boundary: *"Something went wrong / An unexpected error occurred. Please try again."* "Try again" does not help.
- **Evidence:** Reproduced on 2 different company IDs, both via click and direct navigation. Backend calls succeed (`GET /api/v1/companies/{id}` → 200, `GET /api/v1/companies/{id}/360` → 200) — this is purely a frontend rendering bug. Console: `Error: useDecision must be used within a DecisionProvider`, traced into the dashboard page's JS chunk and a shared chunk.
- **Likely root cause:** a company-360 widget/panel calls a hook (`useDecision`/`useCompanyDecision`) that requires a React context provider (`DecisionProvider`) not mounted on this route
- **Suggested fix:** wrap the company-detail route tree in the missing provider, or make the hook fail gracefully without one
- **Estimated complexity:** Low–Medium

### BUG-003 — P0 — Pipeline page crashes (TypeError)
- **Category:** Reliability / Core CRM Feature
- **Steps:** Navigate to `/pipeline`
- **Expected:** Pipeline dashboard renders (even with zero data, per the honest-empty-state pattern seen elsewhere)
- **Actual:** Error boundary crash
- **Evidence:** Console: `TypeError: e.forEach is not a function`, inside a `useMemo` in the pipeline page chunk. Backend calls all 200, but `/api/v1/pipeline/forecast` returns an **object** (`{"best_case":0.0,...}`), not an array, for this zero-data tenant.
- **Likely root cause:** unguarded `.forEach()` call assuming an array where the API can return an object
- **Suggested fix:** guard with `Array.isArray()` before iterating; align the endpoint's empty-state shape with what the frontend expects
- **Estimated complexity:** Low
- **Note:** first of three confirmed instances of this exact pattern — see BUG-007, BUG-008

### BUG-007 — P0 — Meetings page crashes (TypeError, same pattern as BUG-003)
- **Category:** Reliability
- **Steps:** Navigate to `/meetings`
- **Actual:** Error boundary crash. Console: `TypeError: s.find is not a function`. No corroborating `/api/v1/meetings*` call was observed before the crash, suggesting the failure may happen on initial render before data even resolves.
- **Suggested fix:** same class as BUG-003
- **Estimated complexity:** Low

### BUG-008 — P0 — Automation page crashes (TypeError, same pattern, 3rd instance)
- **Category:** Reliability
- **Steps:** Navigate to `/automation`
- **Actual:** Error boundary crash. Console: `TypeError: e?.map is not a function`.
- **Pattern note:** Pipeline (`.forEach`), Meetings (`.find`), Automation (`.map`) — three different pages, three different array methods, one root cause class: array-derived values from API responses used without a defensive `Array.isArray()` check. **Recommend a single, codebase-wide fix (shared safe-array utility + lint rule) rather than three separate page patches.**
- **Estimated complexity:** Medium (systemic fix) vs. Low ×3 (point fixes)

### BUG-005 — P0 — Universal Search is completely non-functional (genuine backend 500)
- **Category:** Backend Reliability / Core Feature
- **Steps:** `/search` → enter a real, confirmed-existing company name ("Jenan") → Search, tried both Hybrid and Full Text strategies
- **Expected:** Search results
- **Actual:** `GET /api/v1/search?q=Jenan&strategy=hybrid...` → **500**; same for `strategy=fulltext` → **500**. Both reproduced twice.
- **Note:** unlike the frontend crashes above, this page's error handling is actually good — it shows *"An error occurred during search / Request failed with status code 500 / Try again"*, a clear, honest message. The bug is entirely backend-side.
- **Suggested fix:** backend investigation into the search service/index for this query path
- **Estimated complexity:** Unknown (backend-only, needs server-side investigation)

### BUG-009 — P0/P1 — Customer Success page fails completely silently (worse than the crashes above)
- **Category:** Reliability / Error Handling
- **Steps:** Navigate to `/customer-success`
- **Actual:** `GET /api/v1/admin/telemetry/overview` → **500** (reproduced twice), and the page renders **absolutely nothing** — no heading, no error message, no "something went wrong," just an empty dark rectangle. The user receives zero signal that anything failed.
- **Why this is worse than BUG-000/003/007/008:** those at least tell the user something broke. This one doesn't.
- **Suggested fix:** (1) fix the backend 500; (2) add a visible error state to this page at all
- **Estimated complexity:** Low (frontend) + Unknown (backend)

### BUG-013 — P1 — RAG documents panel: genuine backend 500 + hardcoded Arabic
- **Category:** Backend Reliability / i18n
- **Steps:** Navigate to `/rag` (reachable by direct URL though absent from the sidebar)
- **Actual:** `GET /api/v1/rag/documents` → **500** (reproduced twice); the page also renders entirely in Arabic despite an English session — see i18n pattern in BUG-011/012/016b
- **Estimated complexity:** Unknown (backend) + Low (i18n)

### BUG-004 — P2 — Forecast page: 403 shown as misleading "Server error"
- **Category:** Error Handling / UX
- **Steps:** Navigate to `/forecast`
- **Actual:** `GET /api/v1/forecast` → **403** (this account's role may legitimately lack access), but the UI shows *"Server error. Please try again."* — misleading, since a 403 is a permissions boundary, not a server fault, and gives the user no actionable next step
- **Suggested fix:** map 403 responses to a distinct "you don't have permission" state
- **Estimated complexity:** Low

### BUG-011 — P2 — Admin Panel: every tab label is a raw, broken i18n key
- **Category:** i18n / Visual Polish
- **Steps:** Navigate to `/admin`
- **Actual:** All 8 tabs display literal, untranslated keys: `admin.tab.overview`, `admin.tab.tenants`, `admin.tab.plans`, `admin.tab.users`, `admin.tab.flags`, `admin.tab.jobs`, `admin.tab.ai_costs`, `admin.tab.health` — the tab bar is unreadable as shipped. Page body content below translates correctly.
- **Suggested fix:** add the missing keys / fix the tab-bar component's translation lookup
- **Estimated complexity:** Low

### BUG-012 — P2 — Admin sub-tabs render hardcoded Arabic regardless of session language
- **Category:** i18n
- **Steps:** In `/admin`, click Tenants, Users, or Health tabs, with session set to English
- **Actual:** All three tabs render fully in Arabic ("إدارة العملاء", "إدارة المستخدمين", "صحة النظام", etc.) while the Overview tab and the rest of the app correctly show English
- **Suggested fix:** replace hardcoded strings with the app's `t()`/`useTranslation` pattern
- **Estimated complexity:** Low–Medium (multiple components)

### BUG-014 — P1 — Marketplace shows unverified "Installed" integrations with no honesty labeling
- **Category:** Product Trust / Data Integrity
- **Steps:** Navigate to `/marketplace`
- **Actual:** 5 of 8 plugins (Slack, Salesforce, GPT Assistant, Email Sync, Workflow Engine) show as "Installed" with specific version numbers and ratings, with no caveat — contrasting with the honest "PREVIEW — NOT GA" labeling seen on `/ai` and `/copilot` in the same session, and with no corroborating functional evidence of real Slack/Salesforce integration found anywhere else in this crawl
- **Recommend:** product/eng verification of whether these are real, functioning connections; apply the same honesty pattern if not
- **Estimated complexity:** Unknown (depends on findings)

### BUG-001 — P0 — Dashboard: all 8 widgets show "failed to load"
- **Category:** Reliability
- **Steps:** Land on `/dashboard` after login (the default post-login page)
- **Actual:** All 8 widget cards (Mission Center, Decision Queue, Intelligence Feed, AI Brief, Market Pulse, Recent Activity, Pipeline, Company Health) show "فشل تحميل البيانات" (failed to load data)
- **Evidence:** `GET /api/v1/dashboard` → **200**, but the payload itself marks 6 of the widgets `"status":"error","data":null` explicitly; the other 2 (Pipeline, Company Health) are simply **absent from the payload entirely** (see BUG-002)
- **Root cause:** the backend dashboard-aggregation service treats "no data yet" as an error state per-widget instead of a valid empty/ok state — this is the first thing every new user sees
- **Suggested fix:** distinguish "error" from "empty" in the backend response contract
- **Estimated complexity:** Medium (backend contract change) + Low (frontend, once fixed)

### BUG-002 — P1 — Dashboard: 2 of 8 widgets aren't in the API response at all
- **Category:** Backend/Frontend Contract
- Pipeline and Company Health widget keys are entirely missing from `/api/v1/dashboard`'s JSON — a distinct root cause from BUG-001's explicit error states
- **Estimated complexity:** Low–Medium

### BUG-006 — P3 — Decisions page: "Rejection Rate: NaN%"
- **Category:** Cosmetic / Arithmetic
- Unguarded division (`rejected/total` with `total=0`) displays literally as "NaN%" to the user; "Acceptance Rate: 0%" nearby is correctly guarded
- **Estimated complexity:** Trivial

### BUG-010 — P3 — Settings → API Keys: raw untranslated key `settings.no_api_keys`
- **Category:** i18n
- **Estimated complexity:** Trivial

### BUG-016 — P2 — No discoverable logout control (desktop)
- **Category:** UX / Security hygiene
- See §3. Users have no visible, reliable way to end their session.
- **Estimated complexity:** Unknown without source access — likely a missing/mispositioned menu trigger

### Data-quality observations (not defects, worth product review)
- **8 exact-duplicate "Jacobs" company records** (same name, status, city; only CR number differs) surfaced when searching Companies — likely seed/import data quality, not a frontend bug, but would confuse a real user
- Contacts list: Mobile/Position/Department/Company columns empty for every visible row (likely inherent to calendar/gmail-sync-only sourcing, not necessarily a bug)
- System Monitoring page shows `graph: connected`, `kafka: active` — contradicts every prior audit finding in this repo's own audit trail (which showed these as unavailable/in-memory as recently as the day before); could be genuine improvement or could reflect stale/non-live data in this widget — **not independently confirmed either way this session**, flagged for follow-up rather than asserted

---

## 5. Per-Page Production-Readiness Classification

✅ Production Ready · 🟡 Needs Minor Work · 🟠 Incomplete · 🔴 Broken

| Page | Status | Notes |
|---|---|---|
| Landing (`/`) | ✅ | Clean, bilingual, correct CTAs |
| Login (`/login`) | ✅ | Renders correctly, tested via auth-guard redirect |
| Dashboard (`/dashboard`) | 🔴 | All 8 widgets fail (BUG-001, BUG-002) — first page every user sees |
| Companies list (`/companies`) | 🟡 | List/search/filter all work; "Add Company" crashes the app for non-privileged roles (BUG-015) |
| Company Detail (`/companies/{id}`) | 🔴 | 100% crash, every company (BUG-000) |
| Employees list (`/employees`) | ✅ | Real data, filters, works |
| Employee Detail (`/employees/{id}`) | ✅ | Tabs work, honest empty states, good pattern |
| Contacts (`/contacts`) | 🟡 | Works; data-completeness gap on secondary fields |
| Opportunities (`/opportunities`) | ✅ | Honest empty Kanban |
| Activities (`/activities`) | ✅ | Honest empty state |
| Revenue (`/revenue`) | ✅ | Honest zero-states |
| Pipeline (`/pipeline`) | 🔴 | Crashes (BUG-003) |
| Forecast (`/forecast`) | 🟠 | 403 shown as misleading generic error (BUG-004) |
| Search (`/search`) | 🔴 | Backend 500 on every query, all strategies (BUG-005) |
| Decisions (`/decisions`) | 🟡 | Works; cosmetic NaN% (BUG-006) |
| Meetings (`/meetings`) | 🔴 | Crashes (BUG-007) |
| Knowledge Graph (`/graph`) | ✅ | Renders correctly |
| Automation (`/automation`) | 🔴 | Crashes (BUG-008) |
| Analytics (`/analytics`) | ✅ | Honest zero-states, well laid out |
| Signals (`/signals`) | ✅ | Honest empty state |
| Business Rules (`/rules`) | ✅ | Honest empty state (localStorage-backed, per prior architecture review) |
| Monitoring (`/monitoring`) | 🟡 | Mostly fine; cosmetic `-0` bug, one unverified data-freshness concern |
| Customer Success (`/customer-success`) | 🔴 | Silent total failure, no error shown (BUG-009) |
| Settings (`/settings`) | 🟡 | Tabs work; one broken translation key (BUG-010) |
| Admin (`/admin`) | 🟠 | Functionally present but i18n badly broken across tab labels and 3+ tab bodies (BUG-011, BUG-012); possible RBAC scope question |
| RAG (`/rag`) | 🔴 | Backend 500 + hardcoded Arabic (BUG-013) |
| AI Prompt Registry (`/ai`) | ✅ | Honest "PREVIEW — NOT GA" labeling, good pattern |
| AI Copilot (`/copilot`) | ✅ | Honest, correctly gated, good pattern |
| Knowledge (`/knowledge`) | ✅ | Renders correctly |
| Marketplace (`/marketplace`) | 🟡 | Renders; trust concern over unverified "Installed" claims (BUG-014) |

**Tally: 14 ✅ / 6 🟡 / 2 🟠 / 8 🔴** (out of 30 tested)

---

## 6. UX Review

**Strengths:** The empty-state copy discipline is genuinely good where it's implemented correctly — "No activities found — Activities will appear here when you start working," "No decisions yet — Decisions will appear here once the engine evaluates your data," the employee-360 page's explicit "Empty signals and timeline are honest — connect Google under Settings → Integrations" — this is exactly the "no fake data" product principle done right, and it shows up consistently across every page that isn't broken. The AI Copilot and AI Prompt Registry pages' honest "PREVIEW — NOT GA" labeling is a strong, trustworthy pattern that should be the house style for anything not fully ready — which makes the Marketplace's unlabeled "Installed" claims (BUG-014) and the broken-page crashes stand out as inconsistent with the product's own evident values.

**Weaknesses:** No discoverable logout (BUG-016). Two distinct, hardcoded-Arabic-in-an-English-session patterns (Admin tabs, RAG page, Command Palette) — this reads as a real internationalization architecture gap in specific components, not a general i18n weakness (most of the app translates correctly). Error handling is wildly inconsistent across the app: Search shows a clear, honest error; Forecast shows a misleading one; Customer Success shows nothing at all; six other pages show a full crash. A user cannot predict what "something went wrong" will look like from one page to the next, which undermines trust even on the pages that do work correctly.

---

## 7. Performance Review

Not rigorously instrumented this pass (no Lighthouse/Web Vitals capture was performed) — this is a qualitative assessment from normal use. Client-side navigation felt fast and responsive throughout, consistent with aggressive Next.js RSC prefetching observed in network traffic (every sidebar link's payload was prefetched on dashboard load). No long hangs or visible jank were observed on any successfully-rendering page. A dedicated performance pass (Lighthouse, WebPageTest, or the app's own `/monitoring` metrics once BUG's cosmetic issue is fixed) is recommended before scoring this dimension with confidence — the score below reflects qualitative impression only.

---

## 8. Accessibility Review

**Not independently, rigorously tested this pass** — no dedicated contrast, screen-reader, or full keyboard-navigation audit was performed (out of scope for the time available; flagged rather than silently skipped). What was observed incidentally: the accessibility tree exposed sensible semantic roles throughout (`tablist`/`tab`, `checkbox`, `textbox`, `heading`, `button` with labels) via every `read_page` call in this session, suggesting reasonably semantic markup underneath. This is a positive signal, not a clearance — a dedicated a11y pass is recommended before scoring this dimension with confidence.

---

## 9. Security Observations

- Auth guard correctly redirects unauthenticated access to protected routes to `/login` (tested via cleared-token proxy)
- Tenant-scoped data appeared correctly isolated throughout (no cross-tenant data observed) — consistent with the backend architecture review's findings
- **Worth a follow-up:** this `user`-role account (per its own employee record) successfully loaded the full platform `/admin` panel (Tenants/Plans/Users/Flags/Jobs/AI-Costs/Health management). This may be intentional (a separate platform-admin permission independent of the tenant "user" role label), but it wasn't possible to confirm which from the UI alone — recommend an explicit RBAC review of who should reach `/admin`
- **BUG-015's failure mode is itself a minor security-adjacent concern**: a 403 response crashing the entire client is a worse failure mode than a clean permission-denied message, though not itself an exploitable vulnerability
- No exposed secrets, API keys, or tokens were observed in rendered HTML or client-visible state during this crawl
- Logout being undiscoverable (BUG-016) is a real hygiene gap on shared/public devices

---

## 10. Console Error Summary

Every hard-crash bug (BUG-000, 003, 007, 008, 015) had a corresponding, page-specific, first-occurrence console error confirmed fresh (not stale buffer) via cross-referencing with network activity at the same navigation. Two recurring error signatures dominate: `useDecision must be used within a DecisionProvider` (BUG-000, isolated to company-detail) and array-method-on-non-array `TypeError`s (BUG-003/007/008, three independent instances of the same class). **Methodology note:** the browser console read tool returns a cumulative session buffer, not a per-navigation reset — every finding above was validated against corroborating fresh network activity or visible on-screen breakage before being counted, to avoid false-positively attributing stale errors to the wrong page.

---

## 11. Network Failure Summary

| Endpoint | Method | Status | Bug |
|---|---|---|---|
| `/api/v1/companies` | POST | 403 | BUG-015 (crash on error handling, not the 403 itself) |
| `/api/v1/search` (strategy=hybrid) | GET | 500 | BUG-005 |
| `/api/v1/search` (strategy=fulltext) | GET | 500 | BUG-005 |
| `/api/v1/admin/telemetry/overview` | GET | 500 | BUG-009 |
| `/api/v1/rag/documents` | GET | 500 | BUG-013 |
| `/api/v1/forecast` | GET | 403 | BUG-004 (misleading error message, not the 403 itself) |
| `/api/v1/dashboard` | GET | 200 (but error payload) | BUG-001, BUG-002 |

No unauthorized (401 where unexpected), duplicate-request storms, or abnormal retry behavior were observed elsewhere in the session. `?_rsc=` prefetch traffic was heavy but expected Next.js behavior, not a defect.

---

## 12. Scoring (0–100, higher = better throughout)

| Dimension | Score | Basis |
|---|---:|---|
| Frontend Score | 38 | 8 of 30 tested pages hard-broken, including 3 of the product's own stated P0/P1 features |
| UX Score | 48 | Strong empty-state/honesty patterns where things work; wildly inconsistent error-handling; no logout |
| Performance Score | 62 | Qualitative only — felt fast and responsive; not independently instrumented |
| Reliability Score | 33 | 6 distinct crash bugs plus 3 genuine backend 500s found in one straight-line pass, zero adversarial testing needed |
| Security Score | 55 | Auth guard and tenant isolation appear sound; RBAC scope of `/admin` access unconfirmed; error-handling crash is a minor hygiene concern; no vulnerabilities directly confirmed |
| Accessibility Score | 50 | Not rigorously tested — reflects positive-but-unverified semantic-markup signal only, low confidence |
| Production Readiness Score | 30 | Core product features (Company 360, Search, Pipeline) non-functional; first-page-after-login (Dashboard) fully broken |
| Technical Debt Score | 40 | Repeated unguarded-array-method pattern (3 instances) and hardcoded-locale pattern (3+ instances) indicate systemic gaps, not isolated mistakes |
| Feature Completeness Score | 50 | Most features are present and reachable; a meaningful fraction don't function once reached |
| **Overall Product Score** | **41** | Weighted synthesis of the above |

---

## 13. Go / No-Go Recommendation

### **NO-GO for production / real-user traffic in the current deployed state.** *(at time of writing — see status update below)*

This is not a marginal call. The product's own stated #1 feature (Company Workspace) and #2 feature (Universal Search) are both completely non-functional, and the very first screen after login (Dashboard) shows total failure on every widget. These were found through completely ordinary use — clicking the obvious links a new user would click — with no attempt to break anything.

**What would change this recommendation:** fixing the 6 P0 crash bugs (BUG-000, 001/002, 003, 005, 007, 008, 015 — note 015 is the most urgent given its blast radius) would likely take this from NO-GO to a defensible conditional-GO, since the underlying platform (auth, data layer, non-broken pages) is otherwise reasonably solid. The i18n and error-handling-consistency issues (P1/P2) matter for a polished launch but are not, on their own, blocking.

> **RESOLVED, same day:** every condition listed above as required to move off NO-GO has since been met and independently re-verified — see [`LIVE-QA-RECHECK-2026-07-30.md`](LIVE-QA-RECHECK-2026-07-30.md). All 16 bugs, including all 6 P0s named here, are confirmed fixed. This does not automatically upgrade the verdict to GO — a fresh full end-to-end crawl (rather than the recheck's targeted re-tests) is the appropriate next step before a production/GA declaration, along with whatever operational sign-offs this repo's standing audit trail (`GA_STATUS.md`, `SIGN_HERE.md`) still requires — but the specific blockers identified in this report are closed.

---

## 14. Prioritized Action Plan

### Immediate (today)
- Fix BUG-015 (Add Company crashing the whole app on 403) — highest blast radius, affects any non-privileged user on a routine action
- Fix BUG-001/002 (Dashboard, the first page every user sees)
- Fix BUG-000 (Company Detail, the product's stated #1 feature)

### This week
- Fix BUG-003/007/008 as one systemic change (safe-array-access utility + audit for other instances of the same pattern), not three point patches
- Investigate and fix the three genuine backend 500s (BUG-005 Search, BUG-009 Customer Success, BUG-013 RAG)
- Add a visible error state to Customer Success (BUG-009) so failures are never silent
- Fix the 403-vs-500 error-message mapping (BUG-004)

### Next sprint
- Fix Admin i18n (BUG-011, BUG-012) and the RAG/Command-Palette hardcoded-Arabic pattern
- Add a discoverable logout control (BUG-016)
- Resolve the Marketplace "Installed" honesty question (BUG-014)
- Confirm/document the `/admin` RBAC scope question from §9
- Fix cosmetic issues (BUG-006 NaN%, BUG-010 missing translation key, Monitoring's `-0` display)

### Future improvements
- Dedicated Lighthouse/Web Vitals performance pass
- Dedicated accessibility audit (contrast, keyboard nav, screen reader)
- Data-quality review of duplicate seed records (8× "Jacobs")
- Follow-up crawl covering the `/v3` tree and the ~15 not-yet-tested sub-routes listed in §2

---

*This report reflects one thorough black-box pass on 2026-07-30. It complements, and does not replace, this repository's own static architecture reviews (`EXEC-ARCHITECTURE-PRODUCT-REVIEW-2026-07-30.md`, `FRONTEND-ARCHITECTURE-REVIEW-2026-07-30.md`) — several findings here (the `DecisionProvider` crash, the array-safety pattern) independently corroborate risks those reviews identified from source code alone, which is a useful cross-check in both directions.*
