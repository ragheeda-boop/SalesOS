# Staging Google OAuth setup (A-09 Human-Gate prep)

**ID:** A-09 / HG-02b-P1  
**Audience:** Platform / human ops  
**Status:** PREPARE ONLY — does **not** close A-09 or claim SSO PASS  
**Related:** [staging-parity-checklist.md](./staging-parity-checklist.md) · [HUMAN-GATE-CARD.md](../completion/HUMAN-GATE-CARD.md) · [A09-CHECKLIST-7-HUMAN-GATE-2026-08-13.md](../completion/evidence/wave-20260808-2/staging-parity/A09-CHECKLIST-7-HUMAN-GATE-2026-08-13.md)

> Agents cannot create Google Cloud OAuth clients or write org secrets. This runbook is the exact human path.

---

## Why

Staging password login can PASS while Google SSO remains unset. Parity checklist residual **P1** requires a **dedicated staging** OAuth app (never reuse production client IDs/secrets).

---

## Exact actions (human)

1. Google Cloud Console → create (or select) a project for **SalesOS staging**.  
2. APIs & Services → Credentials → **Create OAuth client ID** (Web application).  
3. Authorized redirect URIs — include staging callback(s) used by SalesOS (confirm against current `GOOGLE_REDIRECT_URI` / SSO routes on staging). Typical shapes:
   - `https://salesos-staging.up.railway.app/...` (API callback if backend-hosted)
   - Staging FE origin callback if applicable (`sales-os-jet.vercel.app` or dedicated staging FE — **confirm before saving**)
4. Copy **Client ID** and **Client secret** into Railway → project → environment **`staging`** → SalesOS service variables:
   - `SSO_GOOGLE_CLIENT_ID`
   - `SSO_GOOGLE_CLIENT_SECRET`
   - Set `GOOGLE_REDIRECT_URI` to the exact authorized URI (staging-only)
5. Redeploy SalesOS staging (CLI or CI after token rotate).  
6. Browser: Google SSO login → land in app as staging principal.  
7. Deposit **redacted** evidence under `completion/evidence/wave-20260808-2/staging-parity/` (screenshot of success URL host + timestamp; **no** client secret, **no** tokens).

---

## Do not

- Reuse production `SSO_GOOGLE_*` values on staging  
- Commit secrets to git or paste into chat  
- Claim A-09 CLOSED after OAuth alone  

---

## Done when

| Check | Evidence |
|-------|----------|
| Staging vars present (names only in docs) | Railway UI screenshot redacted **or** CLI `railway variables` redacted |
| Browser Google login succeeds on staging | Dated redacted note + human name |
| Prod client unchanged | Explicit confirmation in evidence |

**Validation after human execute:** **not validated** until evidence deposited.
