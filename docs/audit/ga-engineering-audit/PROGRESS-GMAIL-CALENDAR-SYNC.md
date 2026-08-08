# Progress — Gmail / Calendar Sync Buttons (2026-08-06)

**Product:** SalesOS  
**UI path:** `/v3/settings?tab=integrations` → Google Workspace panel  
**Validation:** **build validated (targeted)** for click→API wiring; **light validated** for live Docker routes  
**Production GA:** **NO-GO** (unchanged)  
**Commit:** none

---

## Root cause of prior “no response”

Handlers were **already wired** (`handleSyncGmail` / `handleSyncCalendar` → `POST /api/v1/integrations/google/sync` and `…/calendar-sync`). Live QA ([LIVE-QA-RECHECK-2026-07-30.md](./LIVE-QA-RECHECK-2026-07-30.md)) reported zero network / no loading after click.

**Most likely:** synthetic / automation clicks (same class of false-negative as BUG-016 logout dropdown in that report) — not dead handlers. Backlog note matches: «الأرجح إن اللا-استجابة كانت طريقة اختبار».

**Not the root cause (ruled out this session):** missing OpenAPI routes, FE rewrite broken, or stub sync endpoints. Routes exist and execute.

---

## Fixes applied (minimal)

| Change | Why |
|--------|-----|
| Immediate `setSyncMessage("Syncing…")` + `aria-live` / `data-testid` on Sync buttons | Visible proof handler ran before CSRF mint / network |
| `extractApiDetail` for error banners | Clearer failure text (entitlement / sync errors) |
| Show `oauth_configured` / `config_missing` when disconnected | Honest local gap when Google client secrets missing |
| Rename FastAPI body param `request` → `body` on sync endpoints | Avoid Request-name confusion; no security change |
| Jest suite `google-panel.test.tsx` | Proves click → `client.post` to correct paths |

Left OAuth `?google=error` URL cleanup to sibling (already present as `clearOauthReturnParams` in the same panel).

---

## Live proof evidence

### 1) FE unit (targeted)

```text
npm test -- --testPathPattern=google-panel --no-coverage
→ 4/4 passed
```

- Click Sync Gmail → `POST /api/v1/integrations/google/sync`
- Click Sync Calendar → `POST /api/v1/integrations/google/calendar-sync`
- Console: `[GooglePanel] handleSyncGmail fired` / `handleSyncCalendar fired`
- Error path surfaces API `detail`

### 2) Backend + FE rewrite (Docker local)

| Call | Result |
|------|--------|
| OpenAPI paths for `/api/v1/integrations/google/{sync,calendar-sync}` | present (`post`) |
| Unauth POST | **403** CSRF (middleware engaged — not silent) |
| Free-plan tenant POST | **403** DOM-021 entitlement (handler reached entitlement gate) |
| Enterprise tenant + JWT + CSRF → `POST …/sync` | **400** `No active Google account connected` |
| Same for `…/calendar-sync` | **400** same |
| Via FE `:3000` rewrite (same auth) | **400** same (proxy OK) |

Status on same tenant: `connected:false`, `oauth_configured:false`, missing `SSO_GOOGLE_CLIENT_ID` / `SSO_GOOGLE_CLIENT_SECRET`.

### 3) Residual — full Google round-trip

| Gap | Status |
|-----|--------|
| Local Google OAuth client credentials | **MISSING** — Connect cannot complete |
| Local `google_accounts` rows | **0** — Sync returns 400 until Connect |
| Browser trusted click on Sync while Connected | **Not run** here (no connected account locally); Jest covers click wiring |
| Prod muhide.com Google connect | Still separate from ratlfintech-connected tenant (see GA_STATUS) |

**Honest:** sync **handlers and routes fire**. Full Gmail/Calendar data sync needs Google OAuth credentials + connected account (external).

---

## Files changed

- `salesos/frontend/src/app/v3/settings/integrations/google-panel.tsx`
- `salesos/frontend/src/app/v3/settings/integrations/__tests__/google-panel.test.tsx` (new)
- `salesos/backend/app/modules/communication_hub/router.py` (body param rename)
- This note; GA_STATUS blocker line refreshed

Temp probe script used for curl proof was removed after evidence capture.

---

## Validation label

**build validated (targeted)** — Jest 4/4 + Docker route probes through FE rewrite.  
**Not claimed:** browser E2E with live Google consent, production GO, or data sync of real mailbox.

*Gmail/Calendar sync button proof — 2026-08-06 — production no-go — no commit*
