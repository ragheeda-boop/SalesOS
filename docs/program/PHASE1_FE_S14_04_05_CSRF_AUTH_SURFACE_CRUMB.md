# FE support — STORY-14-04 / 14-05 CSRF + auth client surface

> **Date:** 2026-08-03  
> **Owner:** Frontend Lead (+ BE cookie contract for FE-SEC-02 slice)  
> **Honesty:** Not Production GO. `feature_ai_copilot` False. Decision STUB unchanged.  
> `TenantList.tsx` untouched.

## Findings status

| ID | Severity | Status |
|----|----------|--------|
| FE-SEC-01 | Medium | **Fixed** (CSRF mint/attach) |
| FE-SEC-02 | High | **Open** — vertical slice landed; **flags OFF by default** |
| FE-SEC-03 | Medium | **Fixed** (tip logout revoke) |
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

Enable only after coordinated https tip field verify (BE + FE flags together).

## Validation

Focused Jest + BE unit cookie helpers — **light validated**. Flag-on live Railway — **not validated**.
