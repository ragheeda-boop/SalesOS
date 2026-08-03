# FE-SEC-02 — DevOps handoff: flags-on https field verify

> **Date:** 2026-08-04  
> **From:** Frontend Lead (FE-SEC-02 residual)  
> **To:** DevOps (+ BE env owner)  
> **Tip lineage:** Evidence #1 ~`100cce8` / soak docs `3fccbe6` (settling)  
> **Authority:** [`PHASE1_FE_SEC_02_FLAGS_ON_FIELD_CHECKLIST.md`](PHASE1_FE_SEC_02_FLAGS_ON_FIELD_CHECKLIST.md)  
> **Honesty:** Finding stays **Open** until field evidence recorded. Do **not** claim Fixed or Production GO.  
> `feature_ai_copilot=False`. Decision STUB. Flags **OFF** until DevOps explicit enable window.

## FE readiness (already landed — no flip yet)

| Item | Tip | Status |
|------|-----|--------|
| Vertical slice (dual-read middleware, LS Bearer retained) | `63d60f8` | landed |
| Dual-path persist Jest + checklist | `79d5cb7` | landed |
| Middleware-only gate + flag-helper Jest | `100cce8` | landed · tip-line green |
| Soak r3 (unrelated Companion) | `3fccbe6` | PASS closed — **not** FE-SEC-02 field verify |

## Env contract (exact strings)

| Side | Variable | Value for enable window | Default today |
|------|----------|-------------------------|---------------|
| BE | `FEATURE_HTTPONLY_ACCESS_COOKIE` (settings: `feature_httponly_access_cookie`) | `true` | `False` / unset |
| FE (build-time for Next client) | `NEXT_PUBLIC_FEATURE_HTTPONLY_ACCESS_COOKIE` | `true` | unset / false |
| FE (optional server) | `FEATURE_HTTPONLY_ACCESS_COOKIE` | `true` | unset |

**Cookie BE emits when flag ON:** `salesos_access` · HttpOnly · Secure · SameSite=Strict · Path=`/`  
**Legacy FE cookie (flag OFF path):** non-httpOnly `access_token` — must **not** be written by FE when FE flag ON.

**Critical:** Enable **BE + FE together** on **https** tip only. Half-flip (BE on / FE off or reverse) risks confusing middleware vs document.cookie behavior.

## Enable window procedure (DevOps-owned)

1. Confirm tip deploy includes `100cce8` ancestry; tip-live is **https**.  
2. Announce enable window (FE + Security on standby for #6–10).  
3. Set BE `FEATURE_HTTPONLY_ACCESS_COOKIE=true` → redeploy/restart BE.  
4. Set FE `NEXT_PUBLIC_FEATURE_HTTPONLY_ACCESS_COOKIE=true` → **rebuild/redeploy FE** (NEXT_PUBLIC is build-time).  
5. Run acceptance #3–10 below; paste evidence into FINDINGS_TRACKER retest log.  
6. On any fail: flip both flags **OFF**, redeploy, record FAIL — do not leave half-on.  
7. Even on PASS for #3–10: finding stays **Open** until LS drop / Bearer-or-cookie `verify_token` boarded **or** CTO Accepts residual XSS (checklist #11).

## FE acceptance criteria (checklist #3–10)

### #3 — https tip / Secure cookie surface
- **PASS:** Tip-live URL is `https://…`. Login/refresh `Set-Cookie` for `salesos_access` includes `Secure`.  
- **FAIL:** http tip, or cookie missing `Secure`.

### #4 — BE flag enabled
- **PASS:** BE settings/`/meta` or deploy vars show httponly access cookie feature true; login without flag previously did **not** set `salesos_access`, with flag **does**.  
- **FAIL:** Env set but no `salesos_access` on login.

### #5 — FE flag enabled (same window)
- **PASS:** After FE rebuild, client does **not** write JS-readable `access_token` cookie post-login (Application → Cookies: `access_token` absent or not set by document; `salesos_access` present as HttpOnly).  
- **FAIL:** FE still mirrors `access_token` via `document.cookie` while FE flag claims on.

### #6 — Login Set-Cookie `salesos_access`
- **PASS:** `POST /api/v1/identity/login` (or register) response includes `Set-Cookie: salesos_access=…; HttpOnly; Secure; SameSite=Strict; Path=/`. Body still returns `access_token` (Bearer retained by design).  
- **FAIL:** No Set-Cookie, or cookie not HttpOnly.

### #7 — Middleware gate with only `salesos_access`
- **PASS:** Clear any non-httpOnly `access_token` cookie in browser; keep `salesos_access`; navigate to `/dashboard` (or protected route) → **200 / page loads** (not redirected to `/login`).  
- **FAIL:** Redirect to login despite valid `salesos_access`.  
- **Note:** Unit coverage exists @ `100cce8`; this row is **field** only.

### #8 — Mutating API still works (Bearer + CSRF)
- **PASS:** Authenticated mutating call (e.g. CSRF-gated POST via app axios) returns success (2xx). Bearer from localStorage still attached; CSRF mint/attach still works (FE-SEC-01).  
- **FAIL:** 401/403 regressions attributable to flag flip (CSRF or missing Bearer).

### #9 — Logout clears access cookie + session
- **PASS:** Logout → `salesos_access` cleared (Set-Cookie max-age=0 / deleted); refresh cookie cleared; LS tokens cleared; subsequent refresh **401** (aligns FE-SEC-03 light validate pattern).  
- **FAIL:** `salesos_access` remains usable after logout.

### #10 — Refresh rotates `salesos_access`
- **PASS:** `POST /api/v1/identity/refresh` (cookie-first empty body) returns new tokens **and** new `Set-Cookie: salesos_access=…`.  
- **FAIL:** Refresh succeeds but no access cookie rotation while BE flag on.

## Evidence capture (required for any PASS claim on #3–10)

Record in `salesos/docs/pentest/FINDINGS_TRACKER.md` retest log:

- Tip SHA + tip-live URL  
- Enable window start/end UTC  
- Redacted cookie attribute lines (no raw JWT)  
- Screenshot or HAR note for #7 (middleware) and #8 (mutating)  
- Explicit: **FE-SEC-02 still Open** (LS residual #11) unless Board Accepts

## FE support during window

- FE on standby to interpret middleware / axios failures.  
- Do **not** change BE `identity/service.py` in this handoff.  
- Do **not** invent Production GO / Fixed from unit Jest alone.

## Rollback

Both flags → unset/`false` → redeploy BE + rebuild FE → confirm login no longer sets `salesos_access` and FE resumes legacy `access_token` mirror.
