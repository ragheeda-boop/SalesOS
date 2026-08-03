# FE support — STORY-14-04 / 14-05 CSRF + auth client surface

> **Date:** 2026-08-03  
> **Owner:** Frontend Lead (support Security; Security owns pentest/SOC2 close)  
> **Tip base:** CSRF `34f4a81` · residuals follow-on near `a5b32df`  
> **Honesty:** Not Production GO. `feature_ai_copilot` False. Decision STUB unchanged.  
> `TenantList.tsx` untouched. Does **not** claim firm zero-criticals.

## Findings status

| ID | Severity | Status |
|----|----------|--------|
| FE-SEC-01 | Medium | **Fixed** (`34f4a81` CSRF mint/attach) |
| FE-SEC-02 | High | **Open** — access JWT stays in LS for Next middleware; mitigation proposed (`authSessionHonesty.ts`); no half-break httpOnly access |
| FE-SEC-03 | Medium | **Fixed** — `POST /api/v1/identity/logout` via `logoutSession` + dashboard logout |
| FE-SEC-04 | Low | **Fixed** — cookie-first `POST /refresh {}` with LS refresh fallback + 401 retry |

Tracker: [`salesos/docs/pentest/FINDINGS_TRACKER.md`](../../salesos/docs/pentest/FINDINGS_TRACKER.md)

## Landed

| Piece | Detail |
|-------|--------|
| CSRF | `csrf.ts` + axios interceptors |
| Logout | `identity.logoutSession` → tip logout |
| Refresh | `identity.refreshSession` cookie-first; client 401 one-shot refresh |
| Honesty | `authSessionHonesty.ts` FE-SEC-02 proposal |

## Non-goals

- Full httpOnly access JWT migration (would break middleware without BFF)
- Closing firm pentest AC / Production GO
- Weakening CSRF / auth / RBAC
- `feature_ai_copilot` enable

## Validation

Focused Jest (csrf + logout/refresh + honesty) — **light validated**. Live Railway logout/refresh — **not validated**.
