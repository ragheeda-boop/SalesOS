# OAuth Staging Setup Instructions (2026-08-22)

**Purpose:** Create a staging Google OAuth client for SalesOS staging environment  
**Owner:** DevOps / Project Owner  
**Blocker:** Google Cloud Console access required  
**Status:** NOT STARTED

---

## Why Staging Needs Its Own OAuth App

Production and staging share the same Google OAuth client ID/secret — this is a security risk:
- Tokens issued for staging could be used in production (and vice versa)
- No isolation between environments
- Staging `DEBUG=true` + shared credentials = potential token leakage

**Fix:** Create a separate Google OAuth client for staging with its own redirect URI.

---

## Step-by-Step Instructions

### Step 1: Create Staging OAuth Client

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **APIs & Services** → **Credentials**
3. Click **Create Credentials** → **OAuth client ID**
4. Configure:
   - **Application type:** Web application
   - **Name:** `SalesOS Staging`
   - **Authorized JavaScript origins:**
     - `https://salesos-staging.up.railway.app`
     - `http://localhost:3000` (for local dev, optional)
   - **Authorized redirect URIs:**
     - `https://salesos-staging.up.railway.app/api/v1/auth/google/callback`

### Step 2: Set Environment Variables on Railway Staging

1. Go to [Railway Dashboard](https://railway.app/)
2. Select the staging project
3. Navigate to **Variables** tab
4. Add/update:
   ```
   SSO_GOOGLE_CLIENT_ID=<new staging client ID>
   SSO_GOOGLE_CLIENT_SECRET=<new staging client secret>
   ```

### Step 3: Verify

1. Run staging deploy (or trigger a new one)
2. Test Google login on staging:
   - Visit `https://salesos-staging.up.railway.app/login`
   - Click "Sign in with Google"
   - Verify redirect to Google consent screen
   - Verify callback completes successfully
3. Check staging logs for OAuth-related errors

### Step 4: Rotate Staging Postgres Password

The staging Postgres password was exposed in a transcript. Rotate it:
1. Go to Railway staging → Postgres service → Variables
2. Generate new password
3. Update `DATABASE_URL` on the backend service
4. Verify `/health` still returns `{"status":"ok"}`

---

## Environment Variables Reference

| Variable | Production | Staging (New) |
|----------|-----------|---------------|
| `SSO_GOOGLE_CLIENT_ID` | (existing) | (new staging client) |
| `SSO_GOOGLE_CLIENT_SECRET` | (existing) | (new staging client) |
| `SSO_GOOGLE_REDIRECT_URI` | `https://salesos.up.railway.app/api/v1/auth/google/callback` | `https://salesos-staging.up.railway.app/api/v1/auth/google/callback` |
| `FRONTEND_URL` | `https://salesos.up.railway.app` | `https://salesos-staging.up.railway.app` |

---

## Security Notes

- Never share OAuth client secrets across environments
- Staging OAuth client should have minimal scopes (email + profile only)
- Consider adding staging-specific consent screen branding
- Rotate secrets if exposure suspected

---

*This document is ready for human execution. Requires Google Cloud Console + Railway Dashboard access.*
