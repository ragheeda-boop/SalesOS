# FE-SEC-02 — Flags-on field enable checklist

> **Date:** 2026-08-04  
> **Owner:** Frontend Lead + BE (cookie contract) + DevOps (enable window) + Security (retest)  
> **Base slice:** `63d60f8` · checklist/Jest `79d5cb7` · middleware gate `100cce8` · lineage tip ~`3fccbe6`  
> **DevOps handoff:** [`PHASE1_FE_SEC_02_DEVOPS_FLAGS_ON_HANDOFF.md`](PHASE1_FE_SEC_02_DEVOPS_FLAGS_ON_HANDOFF.md)  
> **Honesty:** Finding remains **Open** until flags-on field verify + XSS residual accepted/fixed.  
> Flags remain **OFF** until DevOps **explicit enable window**. Do **not** invent flags-on field PASS.  
> `feature_ai_copilot` False. TenantList untouched. **No Production GO.** Stage 6 SKIPPED ≠ gate.

## Preconditions (flags stay OFF until all boxes checked)

| # | Check | Owner | Status |
|---|-------|-------|--------|
| 1 | Tip includes `63d60f8` ancestry (`salesos_access` helpers + FE dual-read) | FE/BE | **landed** |
| 2 | Dual-path Jest (flag OFF + ON persist/middleware) PASS | FE | **landed** @ `79d5cb7` / `100cce8` |
| 3 | https tip (not http) — BE cookie `Secure=True` | DevOps | **PASS** @ tip-live `bee3276` Deploy Active |
| 4 | BE env `FEATURE_HTTPONLY_ACCESS_COOKIE=true` (or settings equiv) | BE/DevOps | **PASS** during window; restored **OFF** (confirmed) |
| 5 | FE env `NEXT_PUBLIC_FEATURE_HTTPONLY_ACCESS_COOKIE=true` (same deploy) | FE/DevOps | **FAIL** @ `b022460` tip-live — route `GET /fe-sec-02/httponly-flag` **200 JSON** (rewrite closed); bake stayed `false` (deploy quota / Actions `cli=skipped`); Probe B not validated; flags OFF. Evidence `verify_5_bake_b022460.json` |
| 6 | Login → response Set-Cookie `salesos_access` HttpOnly | Field | **PASS** (HttpOnly; Secure; SameSite=Strict; Path=/) — reconfirmed flags-on @ `bbabe11`+ |
| 7 | Next middleware allows `/dashboard` with only `salesos_access` (no JS `access_token` cookie) | Field | **PASS** (200 with cookie; 307→login without) — reconfirmed |
| 8 | Axios mutating calls still succeed with Bearer from LS + CSRF | Field | **PASS** (`POST /load/run-all` 200 + CSRF) — reconfirmed |
| 9 | Logout clears `salesos_access` + refresh cookie + LS | Field | **PASS** (Max-Age=0 access+refresh); LS clear not browser-proven — reconfirmed |
| 10 | Refresh rotates `salesos_access` | Field | **PASS** flags-on @ `bbabe11`+ (login→refresh 200 + `salesos_access` rotated). Flags-OFF token path also PASS. |
| 11 | Security notes residual: LS access JWT still XSS-class until Bearer-or-cookie + drop LS | Security | open |

## Enable order (coordinated)

1. Tip-line green with flags still **false** (Evidence #1 lineage ~`100cce8`).  
2. Confirm checklist 1–2 green.  
3. DevOps opens enable window per handoff — flip **BE then FE** (or both in one coordinated deploy) on **https** only.  
4. Run checks 6–10 with FE support; record evidence in FINDINGS_TRACKER.  
5. Do **not** claim FE-SEC-02 **Fixed** until LS access removal path is boarded or CTO Accepts residual (#11).

## Active handoff

Soak r3 PASS closed (not Companion). Flags-on short retest @ tip-live **`bbabe11`+**: hard rows **#3/#4/#6/#7/#8/#9/#10 PASS**; **#5 PARTIAL** (not invent full #5). Flags restored **OFF**. Finding remains **Open** (#11). Do **not** invent Fixed / tip-line green / Production GO.

## Non-goals until Board says otherwise

- Enabling flags without DevOps enable window  
- Claiming Fixed / flags-on field PASS without #3–10 evidence  
- Changing `verify_token` to accept cookies / drop LS  
- Production GO / firm zero-criticals claim
