# FE support — STORY-14-04 / 14-05 CSRF + auth client surface

> **Date:** 2026-08-03  
> **Owner:** Frontend Lead (support Security; Security owns pentest/SOC2 close)  
> **Tip base:** `34f4a81` (ancestry under absolute tip `118f1b5`+)  
> **Honesty:** Not Production GO. `feature_ai_copilot` False. Decision STUB unchanged.  
> `TenantList.tsx` untouched. Does **not** close 14-04/14-05.  
> **Validation:** Focused Jest CSRF helpers — **4 PASS · light validated** (this tip).  
> **Security ingest:** FE-SEC-01 → Fixed; FE-SEC-02/03/04 → Open residual in [`FINDINGS_TRACKER.md`](../../salesos/docs/pentest/FINDINGS_TRACKER.md). 14-04 in-repo pack **CLOSED (in-repo)**; AC zero-criticals still **not validated**.

## Sprint acceptance (FE-relevant)

| Story | Sprint | FE role |
|-------|--------|---------|
| STORY-14-04 pentest | 24 | Align browser client with tip CSRF; surface auth storage honesty for findings register |
| STORY-14-05 SOC2 Type I | 25 | Evidence pointers only — Type I assembly is Security/Program; no FE invent |

## Findings (pre-fix)

| ID | Severity | Finding |
|----|----------|---------|
| FE-SEC-01 | **P0** | Shared axios client had **zero** CSRF mint/attach; tip BE requires `X-CSRF-Token` == `csrf_token` cookie on non-exempt POST/PUT/PATCH/DELETE |
| FE-SEC-02 | Pen-test class | Access + refresh JWTs in **localStorage**; access also mirrored to non-httpOnly cookie for middleware — XSS session theft surface (not fixed this tip; document for Security) |
| FE-SEC-03 | Non-P0 | Client logout clears LS/cookie only — no BE session revoke call |
| FE-SEC-04 | Non-P0 | BE httponly refresh cookie unused by FE |

## Landed (minimal)

| Piece | Detail |
|-------|--------|
| Helpers | `salesos/frontend/src/lib/auth/csrf.ts` |
| Client | Mint `GET /api/v1/identity/csrf-token`, attach `X-CSRF-Token` on mutating calls; one retry on CSRF 403 |
| Tests | Focused Jest csrf helpers |

## Non-goals

- Closing 14-04 “zero unresolved criticals” / external firm
- Closing 14-05 Type I audit
- httpOnly cookie migration / full session redesign
- Chaos/load/14-xx harness UI invent
- Weakening CSRF / auth / RBAC

## Validation

Focused Jest csrf helpers — **light validated**. Live browser CSRF round-trip against Railway — **not validated**.
