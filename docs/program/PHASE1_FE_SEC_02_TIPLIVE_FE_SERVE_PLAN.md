# FE-SEC-02 #5 — tip-live FE serve path (DevOps)

> **Date:** 2026-08-04  
> **Status:** **STANDBY (Board)** — tip-live **route serve PASS** @ `b022460` / `dpl_C2TYVHq…`; **#5 bake prove FAIL** (free-tier cap / missing Actions Vercel secrets)  
> **Honesty:** Finding stays **Open**. Flags **OFF**. Stage 6 **SKIPPED**. **No Production GO.** Do **not** invent tip-line green or secrets.

## Tip-live status (`b022460`)

| Check | Result |
|-------|--------|
| Origin tip | `b022460` — probe at `src/app/fe-sec-02/httponly-flag` (off `/api/*`) |
| Tip-live FE | CLI deploy from **monorepo root** (VERCEL_DEPLOY Approach B) → aliased `sales-os-jet.vercel.app` |
| Probe A HTTP | `GET /fe-sec-02/httponly-flag` → **200** `application/json` |
| Probe A bake | `next_public_httponly_access_cookie_baked: false` — **FAIL** for #5 |
| Probe B | **not validated** (no invent) |
| **#5 verdict** | **FAIL** — evidence `.tmp-fesec02-window/verify_5_bake_b022460.json` |

## Why bake stayed false

1. Set Vercel Production `NEXT_PUBLIC_FEATURE_HTTPONLY_ACCESS_COOKIE=true` (+ server `FEATURE_…=true`).  
2. `vercel deploy --prod` / `vercel redeploy` → **`api-deployments-free-per-day` (100)** — blocked.  
3. Deploy Actions `Frontend (Vercel)` @ run `30861842550`: **`cli=skipped`** — `VERCEL_TOKEN` / `VERCEL_ORG_ID` / `VERCEL_PROJECT_ID` empty.  
4. Git-advisory job green ≠ tip-live bake with flags-on.

## VERCEL_TOKEN / Git-advisory gap (still open)

| Secret | Role |
|--------|------|
| `VERCEL_TOKEN` | CLI auth |
| `VERCEL_ORG_ID` | Team/org |
| `VERCEL_PROJECT_ID` | `sales-os` |

**Remediation (Board — STANDBY):** raise Vercel deploy quota **and/or** provision `VERCEL_TOKEN` + `VERCEL_ORG_ID` + `VERCEL_PROJECT_ID` on GitHub Environment `production` **out-of-band** (operators only — agents must **not** invent secret values). Ensure Git integration builds `master` FE changes. After Board unlock → DevOps re-run Probe A/B → restore flags OFF. Do **not** claim Production GO from Deploy Frontend success alone.

**Local CLI note:** Deploy from **repo root** when project Root Directory = `salesos/frontend`. Deploying from `salesos/frontend` doubles path → fail.

## Probe path (authoritative)

```http
GET https://sales-os-jet.vercel.app/fe-sec-02/httponly-flag
```

Must **not** use `/api/...` tip-live.

## Next prove window (when rebuild possible)

1. BE `FEATURE_HTTPONLY_ACCESS_COOKIE=true`  
2. FE `NEXT_PUBLIC_FEATURE_HTTPONLY_ACCESS_COOKIE=true` → **successful FE rebuild**  
3. Probe A → `next_public_httponly_access_cookie_baked: true`  
4. Probe B → post-login: no `access_token=` in `document.cookie`; `salesos_access` HttpOnly  
5. **Restore both flags OFF** + FE rebuild so bake returns false  
6. Honest PASS/PARTIAL/FAIL; finding stays Open (#11) even on #5 PASS

## Current posture

- **STANDBY (Board)** — no further #5 prove until quota and/or Actions Vercel secrets land  
- Flags **OFF** (BE `FEATURE_HTTPONLY_ACCESS_COOKIE=false`, AI false; FE httponly envs **removed** from Vercel Production)  
- Tip-live route **serves** tip JSON with bake **false**  
- #5 **FAIL** recorded — blocked on FE rebuild quota / missing Actions Vercel secrets (not invented)  

## Non-goals

- Invent tip-line green / Fixed / Production GO  
- Leave flags ON waiting for quota reset  
- Claim #5 PASS from env set without A+B  
