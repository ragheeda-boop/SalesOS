# FE support — STORY-14-04 / 14-05 CSRF + auth client surface

> **Date:** 2026-08-03  
> **Owner:** Frontend Lead (+ BE cookie contract for FE-SEC-02 slice)  
> **Honesty:** Not Production GO. `feature_ai_copilot` False. Decision STUB unchanged.  
> `TenantList.tsx` untouched.

## Findings status

| ID | Severity | Status |
|----|----------|--------|
| FE-SEC-01 | Medium | **Fixed** (CSRF mint/attach) |
| FE-SEC-02 | High | **Open** — checklist ready @ Evidence #1 `63f6ad2`; **flags OFF**; not Fixed until flags-on field verify |
| FE-SEC-03 | Medium | **Fixed** @ `2148dd7` + `d9f0eba`; live tip-live @ `fe84441` **light validated** (logout 200 `sessions_revoked=1`; refresh 401) |
| FE-SEC-04 | Low | **Fixed** (cookie-first refresh) |

## FE-SEC-02 vertical slice (this tip)

| Piece | Detail |
|-------|--------|
| BE flag | `feature_httponly_access_cookie` default **False** |
| BE cookie | httpOnly `salesos_access` on login/register/refresh when flag on; clear on logout |
| Body tokens | `TokenResponse` unchanged; `verify_token` remains Bearer-only |
| FE flag | `NEXT_PUBLIC_FEATURE_HTTPONLY_ACCESS_COOKIE` default unset/false |
| FE middleware | Dual-read: `salesos_access` then legacy `access_token` |
| FE persist | When FE flag on: skip JS-writable access cookie mirror; keep LS for Bearer |
| Flags-on plan | [`PHASE1_FE_SEC_02_FLAGS_ON_FIELD_CHECKLIST.md`](PHASE1_FE_SEC_02_FLAGS_ON_FIELD_CHECKLIST.md) |

Enable only after coordinated https tip field verify (BE + FE flags together).

## Validation

Focused Jest + BE unit cookie helpers — **light validated**. Dual-path flag Jest — **light validated** (`79d5cb7`). Middleware-only + flag-helper Jest — **light validated** (this tip). Flag-on live Railway — **not validated**. Evidence #1 tip `63f6ad2`. Stage 6 SKIPPED.
