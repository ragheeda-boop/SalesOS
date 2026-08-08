# SECURITY — Secret Isolation Verification (staging vs prod)

**Run:** EAB-2026-08-06-003 · **Date:** 2026-08-07 · **Mode:** EXECUTE + VERIFY

## 1. What was fixed

| Secret | Before (2026-08-06) | After (2026-08-07) | Status |
|--------|---------------------|---------------------|--------|
| `JWT_SECRET_KEY` (staging) | `sha256=06823858C2` (== prod) | `sha256=BF9D04AA99` (NEW) | **Isolated** |
| `SECRET_KEY` (staging) | `sha256=73534985DF` (== prod) | `sha256=AB16182BED` (NEW) | **Isolated** |

- New values are 62-char random alphanumeric, generated locally, staged in `new-secrets.txt` (move to secure storage; never git).
- Verified applied on the running staging deployment (deployment `96128f69`, `/health` 200 after env change).

## 2. What was deliberately NOT copied from prod

| Var | Reason |
|-----|--------|
| `SSO_GOOGLE_CLIENT_ID` / `SSO_GOOGLE_CLIENT_SECRET` | Staging needs its **own Google OAuth app**; reusing prod's client would conflate OAuth audiences. **HUMAN TASK** — create a Google Cloud OAuth consent app for staging, set `GOOGLE_REDIRECT_URI=https://salesos-staging.up.railway.app/api/v1/integrations/google/callback`, and add both vars to the staging environment. |

## 3. Isolation that remains verified

| Resource | Staging hash | Prod hash | Status |
|----------|--------------|-----------|--------|
| `DATABASE_URL` / DB creds | `67E6C68423` / `246F5CB1FF` | `971975109E` / `D7A9844452` | Isolated |
| `REDIS_URL` | `ABA243FF78` | `B83804E4EE` | Isolated |

## 4. Open security item

- **Rotate the staging Postgres password** (value beginning `VPGcEjKY…`) — it was exposed once in a session transcript. Do at the next human touchpoint; do not reuse in git.

## 5. Non-secret prod vars now mirrored on staging

`DEBUG=false`, `FRONTEND_URL=https://sales-os-jet.vercel.app`, `FEATURE_HTTPONLY_ACCESS_COOKIE=false`, `GOOGLE_REDIRECT_URI` (staging-scoped).
