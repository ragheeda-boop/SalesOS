# SalesOS — Live QA Re-Check (Same-Day Follow-Up)

**Date:** 2026-07-30 (later same day as [`LIVE-QA-E2E-VALIDATION-2026-07-30.md`](LIVE-QA-E2E-VALIDATION-2026-07-30.md))
**Trigger:** Requester asked to re-run the check ("اعد الفحص الان"). A new deployment had shipped in between — confirmed via changed JS chunk hashes (e.g. dashboard page chunk `page-5eec6c54f07f8ea1.js` → `page-6611fc53f827eee9.js`; companies page chunk also changed) and a changed post-login landing route (this session landed on `/v3` by default; the original session landed on `/dashboard`).

---

## Headline: New regression is more severe than anything in the original report

**The entire legacy `(dashboard)` route tree (~25 pages: Dashboard, Companies, Employees, Contacts, Opportunities, Pipeline, Admin, and everything else under that route group) now crashes to the same full application-level error on every single page tested — including pages that were completely clean (no bugs at all) in the original report.**

| Page | Original report | This re-check |
|---|---|---|
| `/dashboard` | 🔴 Widgets showed "failed to load" (page itself rendered, sidebar worked) | 🔴🔴 **Full app crash** — blank white screen, no sidebar, no chrome at all |
| `/companies` | ✅ Fully working (list, search, filters all passed) | 🔴🔴 **Full app crash** — same total failure |
| `/employees` | ✅ Fully working, no issues found | 🔴🔴 **Full app crash** — same total failure |
| `/admin` | 🟠 Functional but with broken i18n (BUG-011/012) | 🔴🔴 **Full app crash** — same total failure |

All four produce the identical, uninformative message: *"Application error: a client-side exception has occurred while loading sales-os-jet.vercel.app (see the browser console for more information)."* — this is the same failure mode as the original report's **BUG-015** (the most severe finding in that report, previously triggered only by submitting a Create form as an unprivileged user). It is now apparently the default state of the entire legacy tree on ordinary navigation, not just on that one specific action.

**Evidence checked and ruled out:**
- Not a network/CDN failure — every JS chunk for every crashing page returned `200`, including the `(dashboard)/layout.js` chunk itself
- Not a backend failure — API calls that did fire before the crash (`/api/v1/executive/dashboard`, `/api/v1/companies`, `/api/v1/opportunities` on the dashboard route) all returned `200`
- **Could not capture a specific console stack trace this time** despite repeated attempts — the browser console reader returned no entries even immediately after the crash, unlike every crash in the original report (which all had clear, specific `TypeError`/`Error` traces). This itself is worth flagging to engineering: whatever changed appears to fail even earlier/harder than the previous per-page crashes (possibly a hydration-time failure in the shared `(dashboard)` layout itself, before React's own error boundaries and the app's error listeners are even attached) — recommend checking server-side error tracking (Sentry, per this repo's own dependency list) for the actual stack trace, since black-box browser testing could not extract one this time.

**Confirmed unaffected: the `/v3` tree works correctly.** `/v3/companies` rendered a full, real data grid (141,221 results), correctly self-labeled *"Enterprise Data Grid lite — Design Program v3. Legacy /companies is unchanged."* This is a precise, useful signal: whatever broke is isolated to the legacy `(dashboard)` route group specifically (its shared layout, a provider it depends on, or a dependency shared across that whole tree) — the `/v3` tree, the API layer, and auth all remain healthy.

**Also notable:** the default post-login landing route appears to have changed from `/dashboard` to `/v3` between the two sessions. Whether intentional (a deliberate cutover to v3 as the new default) or incidental, this is worth confirming with the team — if intentional, it may make the legacy-tree crash lower-urgency for real users (who'd land on the working `/v3` by default) though still a serious problem for anyone who navigates into it via a bookmark, shared link, or the sidebar.

---

## New data-quality finding: duplication is worse than originally scoped

The original report flagged 8 exact-duplicate "Jacobs" records as a narrow, single-company anomaly. Browsing `/v3/companies`'s full list this session shows the same pattern at scale across seemingly most/all of the 141,221-record database — spot-checked examples: "100 Eyes" ×8, "10x تن اكس" ×8, "12 Cups" ×8, "1337Agency" ×8, "1957 Ventures" ×7, "199X" ×6, all identical in every visible field except CR number. **Revise the original report's framing from "an isolated data-quality note" to "likely a systemic bulk-import/deduplication failure affecting a large share of the company database"** — worth a direct database-level count of `COUNT(*) / COUNT(DISTINCT name)` to quantify the real scope before treating this as low-priority.

---

## Recommendation update

The original report's verdict (**NO-GO**) stands and is now reinforced rather than softened: whatever shipped since the original test has taken a partially-broken-but-mostly-functional legacy surface and made it **completely inaccessible**. If `/v3` is indeed now the intended default landing experience, prioritize confirming that explicitly and consider whether the legacy tree should be gated off entirely (a broken page a user can still navigate to is worse than no page at all) until it's fixed or formally retired — this connects directly to the standing recommendation in this repo's own frontend architecture review to commit to a dated `/v3` cutover rather than running both trees in parallel indefinitely.

**Immediate next step for engineering:** check server-side error tracking for the actual exception in the `(dashboard)` layout — this black-box session could not extract a stack trace this time, which is itself informative (the failure now happens at a point earlier/lower-level than the specific per-page bugs found in the original pass).

---

## Update (same-day, later): Dashboard crash fixed; new finding on Google OAuth

**Dashboard regression is resolved.** Re-tested `/dashboard` after a fresh login: it now renders correctly with an honest **"لا توجد بيانات بعد" (No data yet)** state on all 8 core widgets, replacing both the earlier "failed to load" error state (original report) and the full-app crash (this document, above). This is the correct behavior for a zero-data tenant and should be considered fixed.

**New observation on the same dashboard load:** 5 additional widgets are visible for the first time — Company Engagement (تفاعل الشركة), Email Intelligence (ذكاء البريد الإلكتروني), Calendar Intelligence (ذكاء التقويم), Follow-up Center (مركز المتابعة), and Company Scoring (تقييم الشركات) — all stuck on **"جاري التحميل..." (Loading...)** with no resolution after several seconds of observation. This independently confirms, via live browser testing, a specific gap identified earlier from source-code review alone (in `FRONTEND-ARCHITECTURE-REVIEW-2026-07-30.md`): these widget keys are registered in the dashboard's UI layer but are not wired into the data-mapping layer, so they can never resolve out of their loading state. Recommend either completing the data wiring or removing these widgets from the dashboard until they're ready.

### Google OAuth — tested per requester's direct request ("Google OAuth جاهز — يحتاج اختبار فعلي من المتصفح")

Navigated to `/v3/settings?tab=integrations` (the legacy `/settings` page has no Integrations tab at all — only the v3 Settings page does).

**The OAuth connection itself is real and functional:** the Google Workspace panel shows **Connected**, with a genuine account (`ragheed.a@ratlfintech.com`), a real historical sync timestamp (`7/29/2026, 7:17:47 PM` — the day before this test), and "5 permissions granted." This is credible, non-fabricated state — consistent with actual OAuth token storage, not a mock. Historical contact-sync evidence from the original QA pass (44 contacts sourced via `calendar_sync`/`gmail_sync`) corroborates that a real sync has happened at some point.

**However, the manual "Sync Gmail" and "Sync Calendar" buttons appear non-functional:** clicking each one individually produced **zero observable effect** — no network request fired (checked immediately after each click), no console activity, no loading indicator, no error message, and the "Last sync" timestamp did not update. Both buttons behave identically: clicking them does nothing detectable at all.

**Verdict on "Google OAuth is ready":** partially — the underlying connection/authorization is genuinely established and was clearly functional at some point (the historical sync data proves it). But the on-demand manual sync trigger in the UI does not work right now, which is the part a real user would actually interact with day-to-day. This needs a fix before calling the feature "ready" — recommend checking whether the button's click handler is wired to a real mutation/endpoint at all, or whether it's calling an endpoint that's silently failing before any network request is even dispatched (e.g., a client-side guard/condition preventing the call).

**Not tested (intentionally):** the "Disconnect" button — clicking it would break a live, working connection for no testing benefit, so it was left alone. The initial OAuth "Connect" flow (redirect to Google's consent screen) also wasn't exercised here since the account was already connected; that flow was previously confirmed at the code level (in `EXEC-ARCHITECTURE-PRODUCT-REVIEW-2026-07-30.md`) to correctly gate on missing config rather than fail silently — worth a live test on a fresh, never-connected account if one becomes available.

---

## Update (same-day, later still): Independent verification of the engineering team's fix claims

The engineering team reported 15 of the original 16 bugs fixed (BUG-010 reclassified as a false positive — the translation was found to genuinely exist). Every claim below was independently re-tested live in the browser against the original repro steps, not accepted on the strength of the report alone.

| Bug | Claimed | Independently verified | Evidence |
|---|---|---|---|
| BUG-015 — Add Company crashes app | ✅ Fixed | ✅ **Confirmed** | "Add Company" is now inert for this role — no dialog opens, no request fires, no crash. (Not the most elegant fix — ideally the button would be hidden/disabled with an explanation rather than silently doing nothing — but the crash path is gone.) |
| BUG-003/007/008 — Pipeline/Meetings/Automation crash | ✅ Fixed | ✅ **Confirmed, all 3** | All three render cleanly with honest empty states; zero console errors |
| BUG-000 — Company Detail crashes | ✅ Fixed | ✅ **Confirmed, substantially** | Now renders a full, rich Company 360 view (DNA scores, AI recommendations, buying journey, relationships) — a genuinely built-out page, not just a crash fix |
| BUG-001/002 — Dashboard widgets fail | ✅ Fixed | ✅ **Confirmed** | All 8 original widgets show honest "لا توجد بيانات بعد" (no data yet). Note: 5 newer widgets (Company Engagement, Email/Calendar Intelligence, Follow-up Center, Company Scoring) are still permanently stuck loading — a separate, already-tracked issue, not part of this claim |
| BUG-004 — Forecast 403 shown as "Server error" | ✅ Fixed | ✅ **Confirmed** | Now shows "Access denied" — correct, honest permission messaging |
| BUG-006 — Decisions NaN% | ✅ Fixed | ✅ **Confirmed** | Shows "Rejection Rate: 0%" now |
| BUG-009 — Customer Success silent failure | ✅ Fixed | ✅ **Confirmed, backend-level** | `/api/v1/admin/telemetry/overview` now returns **200** (was 500) — the actual backend bug was fixed, not just papered over on the frontend; full page renders with real content |
| BUG-011 — Admin tab labels broken i18n keys | ✅ Fixed | ✅ **Confirmed** | All 9 tabs (note: a new "AI Audit Log" tab has been added) show real text |
| BUG-012 — Admin sub-tabs hardcoded Arabic | ✅ Fixed | ⚠️ **PARTIALLY confirmed** | Tenants and Users tabs are now correctly in English. **System Health tab is still hardcoded Arabic** ("صحة النظام", "مدة التشغيل", "لا توجد بيانات تاريخية") — matches the fix commit's stated scope (TenantList, UserList, PlanManager) exactly, which didn't include whatever renders the Health tab. Not fully fixed. |
| BUG-014 — Marketplace fake "Installed" plugins | ✅ Fixed | ✅ **Confirmed, cleanly** | Now shows "0 installed," all 8 plugins correctly show "Install" — the honesty gap is closed |
| BUG-016 — No logout control | ✅ Fixed | ⚠️ **INCONCLUSIVE** | A "User menu" button now exists in the header (a real improvement — no such element was discoverable at all in the original test). However, this session could not get it to open any menu via multiple programmatic interaction methods (synthetic mouse events, keyboard focus+Enter), and the browser pane was not rendering to allow a real trusted click to rule out a testing-method artifact. **Recommend the team manually click-test this themselves** rather than treat it as confirmed from this session alone. |
| BUG-010 — Missing translation key | Reclassified as false positive | ✅ **Confirmed false positive** | `/settings` → API Keys tab now shows "No API keys configured. Create one to get started." — a real, correctly-resolving translation |

### Not in the fix list — checked anyway

| Item | Status | Evidence |
|---|---|---|
| BUG-005 — Universal Search backend 500 | ❌ **Still broken** | `GET /api/v1/search?...strategy=hybrid` → 500, `strategy=fulltext` → 500, both reproduced just now. This was not mentioned in the fix report and is not fixed. Given Search is one of the product's own stated P0 features, this should likely be considered the outstanding item behind "15 of 16." |
| BUG-013 — RAG documents backend 500 | ✅ **Now fixed** (bonus, untracked) | `GET /api/v1/rag/documents` → **200** (was 500). Appears to have been resolved as a side effect of other backend work, though it wasn't explicitly claimed. |

### Also independently re-confirmed
The full-legacy-tree crash found in the earlier part of this same-day recheck (§ above — every `(dashboard)` page crashing at once) is **resolved**. Eleven distinct legacy-tree pages were re-tested this pass (Dashboard, Companies, Company Detail, Pipeline, Meetings, Automation, Forecast, Decisions, Customer Success, Admin, Settings) and all render without crashing.

**On the deployment/service claims** (Vercel 200, Railway 200, GitHub commit range `cd73723..29008fe`): Vercel and Railway being live and responsive is corroborated throughout this entire session — every test above hit both successfully. The GitHub commit-range claim is outside what browser-only testing can verify and was not independently checked.

### Net assessment (as of the second verification pass)
The fix pass was real and substantial — not a cosmetic pass. Every P0 crash-level bug from the original report is genuinely gone, including the most severe one (BUG-015), and one backend fix (Customer Success telemetry) went deeper than the frontend symptom.

---

## Final update: remaining gaps closed and independently re-verified

All three open items from the previous verification pass were addressed and re-tested live. **All three are now confirmed fixed.**

| Item | Fix applied (per engineering) | Independently re-verified |
|---|---|---|
| **BUG-005 — Search 500** | Root cause: `SET LOCAL statement_timeout = :timeout` was being parameterized by asyncpg into `$1`, which PostgreSQL rejects for `SET LOCAL` — fixed by using an f-string literal in `postgres_repo.py` (2 locations); secondary fix: a `rows, total, _cursor` vs `rows, total` unpacking mismatch in `__init__.py:324` | ✅ **Confirmed via direct API call**: `GET /api/v1/search?q=Jenan&strategy=hybrid` → **200**, `total: 8`, real matched results (e.g. "Jenan Real Estate" with correct `matched_fields`/scoring); `strategy=fulltext` → **200** as well, `total: 8`. Both previously-500 code paths now return correct, real data — this reads as a genuine, well-diagnosed root-cause fix, not a workaround. |
| **BUG-012 — System Health tab hardcoded Arabic** | `HealthDashboardView.tsx`: 11 hardcoded Arabic strings converted to `useTranslation`; 10 new keys added to both `en.json`/`ar.json` | ✅ **Confirmed**: tab now reads "System Health / Uptime / System components / Healthy / Past checks / Component status / Health history (last 24h) / No historical data" — fully English, matching session locale. BUG-012 is now fully closed (Tenants + Users were already confirmed in the prior pass). |
| **BUG-016 — Logout control** | Claimed already working, no change needed | ✅ **Confirmed with a real trusted click** (my earlier synthetic-event attempts had been the limitation, not the product — this specific dropdown component doesn't respond to programmatically dispatched events, only genuine pointer input). A real click on "User menu" reveals a visible, properly-rendered "Logout" button (178×33px) in the dropdown. Not clicked through to avoid ending the session again unnecessarily — presence and visibility is sufficient confirmation. |

**Infrastructure claims also independently corroborated:** hit `https://salesos-production-96c0.up.railway.app/health` directly — **200**, `status: ok`, database/cache/graph/redis all `connected`, `uptime_seconds: ~779` (~13 minutes), which is directly consistent with the claimed fresh redeploy (`dockerfilePath` fix + `preDeployCommand` syntax fix + redeploy from `salesos/backend/`). Vercel's 200 status was already corroborated continuously throughout this entire multi-hour testing session. The GitHub commit-range claim (`cd73723..29008fe`) remains outside what browser-based testing can verify.

One minor, non-blocking discrepancy noted in passing: Railway's own `/health` reports `kafka: in_memory`, while the in-app `/monitoring` page (checked earlier in this document) displayed `kafka: active` — a small inconsistency between what the two surfaces report, not one of the items being verified here, flagged for awareness only.

### Final verdict
**16 of 16 original bugs are now confirmed resolved** (15 direct fixes + BUG-010 correctly reclassified as a false positive), all independently re-tested against live behavior rather than accepted on report alone. Combined with the earlier confirmation that the full-legacy-tree crash regression is also resolved, the application has moved from the original report's **NO-GO** state to a materially healthier one. A fresh, full end-to-end pass (beyond spot-checking the 16 tracked items) is the natural next step before any production/GA declaration, since this session's re-verification was targeted at the fix list rather than a repeat of the original exhaustive crawl — but every specific, previously-broken path checked in this document now works correctly.
