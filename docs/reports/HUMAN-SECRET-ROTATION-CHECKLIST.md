# Human secret rotation checklist (residual)

**Date:** 2026-08-12  
**Owner:** Human / ops (agents do **not** rotate these)  
**Rule:** Never paste secret values into chat, git, or evidence docs. Record **name + done timestamp** only.  
**Companion:** [`docs/ops/CREDENTIAL_ROTATION_RUNBOOK.md`](../ops/CREDENTIAL_ROTATION_RUNBOOK.md) · evidence template [`docs/audit/ga-engineering-audit/completion/CREDENTIAL-ROTATION-EVIDENCE-TEMPLATE.md`](../audit/ga-engineering-audit/completion/CREDENTIAL-ROTATION-EVIDENCE-TEMPLATE.md)

## Why still human-required

These credentials sit outside safe agent revoke paths (Google Cloud OAuth console, Railway account tokens, GitHub PATs). Railway MCP revoke-without-exposure is **not** available for this residual. Treat as **open** until a human ticks Done.

## Checklist (no values)

| # | Action | Where | Done |
|---|--------|-------|:----:|
| 1 | **Rotate** `SSO_GOOGLE_CLIENT_SECRET` (create new secret in Google Cloud OAuth client → set on Railway production env → restart/redeploy SalesOS → confirm Google SSO login) | Google Cloud Console → Railway Variables (name only) | ☐ |
| 2 | **Revoke** compromised / long-lived `RAILWAY_API_TOKEN` (account API token used by CLI/agents); mint a new token only if still needed; store out-of-band | Railway → Account → Tokens | ☐ |
| 3 | **Revoke** compromised / long-lived `GH_TOKEN` / PAT used by agents or local shells; mint replacement only if still needed; update GH Actions secrets if that PAT was wired | GitHub → Settings → Developer settings → Tokens | ☐ |

## Post-checks (after each item)

- [ ] `/health` returns 200 on production
- [ ] No secret strings in `git status` / committed files
- [ ] Old token/secret **revoked** at the provider (not only replaced in env)
- [ ] Redacted evidence note filed off-git or via CREDENTIAL-ROTATION evidence template (fingerprints / key ids only)

## Agent / automation boundaries

- Do **not** dump `railway variable` / env values into logs or PRs.
- Do **not** claim Production GO after rotation — GA remains **NO-GO** until full audit DoD.
- Prefer this checklist over ad-hoc chat instructions.

**Validation:** **docs only** (rotation itself = **not validated** until human completes).
