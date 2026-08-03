# FE-SEC-02 — Flags-on field enable checklist

> **Date:** 2026-08-03  
> **Owner:** Frontend Lead + BE (cookie contract) + Security (retest)  
> **Base slice:** `63d60f8` · checklist/Jest `79d5cb7` · Evidence #1 tip **`63f6ad2`**  
> **Honesty:** Finding remains **Open** until flags-on field verify + XSS residual accepted/fixed.  
> Flags remain **OFF**. Do **not** invent flags-on field PASS.  
> `feature_ai_copilot` False. TenantList untouched. **No Production GO.** Stage 6 SKIPPED ≠ gate.

## Preconditions (flags stay OFF until all boxes checked)

| # | Check | Owner | Status |
|---|-------|-------|--------|
| 1 | Tip includes `63d60f8` ancestry (`salesos_access` helpers + FE dual-read) | FE/BE | **landed** |
| 2 | Dual-path Jest (flag OFF + ON persist/middleware) PASS | FE | **landed** @ `79d5cb7` (+ middleware-only / flag-helper coverage this tip) |
| 3 | https tip (not http) — BE cookie `Secure=True` | DevOps | **not validated** |
| 4 | BE env `FEATURE_HTTPONLY_ACCESS_COOKIE=true` (or settings equiv) | BE/DevOps | **not enabled** |
| 5 | FE env `NEXT_PUBLIC_FEATURE_HTTPONLY_ACCESS_COOKIE=true` (same deploy) | FE/DevOps | **not enabled** |
| 6 | Login → response Set-Cookie `salesos_access` HttpOnly | Field | **not validated** |
| 7 | Next middleware allows `/dashboard` with only `salesos_access` (no JS `access_token` cookie) | Field | **not validated** (unit coverage only) |
| 8 | Axios mutating calls still succeed with Bearer from LS + CSRF | Field | **not validated** |
| 9 | Logout clears `salesos_access` + refresh cookie + LS | Field | **not validated** (FE-SEC-03 live verify may cover logout) |
| 10 | Refresh rotates `salesos_access` | Field | **not validated** |
| 11 | Security notes residual: LS access JWT still XSS-class until Bearer-or-cookie + drop LS | Security | open |

## Enable order (coordinated)

1. Deploy tip with flags still **false** (Evidence #1 line green).  
2. Confirm checklist 1–2 green.  
3. Flip **BE then FE** (or both in one deploy) on https only — Board/DevOps owned.  
4. Run checks 6–10; record evidence paths in FINDINGS_TRACKER retest log.  
5. Do **not** claim FE-SEC-02 **Fixed** until LS access removal path is boarded (Bearer-or-cookie `verify_token` + CSRF) or CTO Accepts residual.

## Blocked next (not this tip)

Flags-on field verify requires DevOps env flip on https tip. FE cannot claim PASS from unit tests alone.

## Non-goals this tip

- Enabling flags in production/Railway  
- Changing `verify_token` to accept cookies  
- Removing localStorage access JWT  
- Touching BE `identity/service.py`  
- Production GO / firm zero-criticals claim
