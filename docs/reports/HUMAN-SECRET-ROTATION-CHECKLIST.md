# Human secret rotation checklist (residual)

**Date:** 2026-08-12  
**Owner:** Human / ops (agents do **not** rotate these)  
**Rule:** Never paste secret values into chat, git, or evidence docs. Record **name + done timestamp** only.  
**Companion:** [`docs/ops/CREDENTIAL_ROTATION_RUNBOOK.md`](../ops/CREDENTIAL_ROTATION_RUNBOOK.md) · evidence template [`docs/audit/ga-engineering-audit/completion/CREDENTIAL-ROTATION-EVIDENCE-TEMPLATE.md`](../audit/ga-engineering-audit/completion/CREDENTIAL-ROTATION-EVIDENCE-TEMPLATE.md)

## Why still human-required

These credentials sit outside safe agent revoke paths (Google Cloud OAuth console, Railway account tokens, GitHub PATs). Railway MCP revoke-without-exposure is **not** available for this residual. Treat as **open** until a human ticks Done **and** agent/ops can verify what is safely verifiable without reading secret values.

## Checklist (no values)

| # | Action | Where | Done |
|---|--------|-------|:----:|
| 1 | **Rotate** `SSO_GOOGLE_CLIENT_SECRET` (create new secret in Google Cloud OAuth client → set on Railway production env → restart/redeploy SalesOS → confirm Google SSO login) | Google Cloud Console → Railway Variables (name only) | human claimed; browser SSO not validated |
| 2 | **Revoke** compromised / long-lived `RAILWAY_API_TOKEN` (account API token used by CLI/agents); mint a new token only if still needed; store out-of-band | Railway → Account → Tokens | human claimed; provider revoke not independently verified |
| 3 | **Revoke** compromised / long-lived `GH_TOKEN` / PAT used by agents or local shells; mint replacement only if still needed; update GH Actions secrets if that PAT was wired | GitHub → Settings → Developer settings → Tokens | human claimed; provider revoke not independently verified |

## Post-rotation operational health (2026-08-12 ~21:15 +03) — **light validated**

Project: `responsible-comfort` · API: `https://salesos-production-96c0.up.railway.app`  
(No secret values read; Railway MCP unauthenticated — CLI status/logs only.)

| Check | Result |
|-------|--------|
| `GET /health` | **200** · `status=ok` · `database/cache/redis=connected` · `version=5.1.0-rc1` |
| SalesOS service | ● Online · deploy `2dd0408d…` **SUCCESS** (2026-08-12 21:05 +03) |
| celery-worker (Copy 3091) | ● Online · deploy `00314d12…` **SUCCESS** (21:05 +03) · `celery@… ready` · Redis connected |
| celery-beat (Copy 5338) | ● Online · deploy `70b258c8…` **SUCCESS** (20:58 +03) · scheduler sending due tasks |
| Worker dispatch smoke | Safe observed traffic: `agent_dispatch_all` **succeeded** (`tenants_processed=57`, `errors=[]`); `worker_health_ping` **succeeded** (`status=ok`, `database=connected`) |
| Browser Google SSO login | **not validated** |
| Provider-side old token revoke | **not independently verified** (out of agent revoke path) |

## Post-checks (after each item)

- [x] `/health` returns 200 on production (**light validated** 2026-08-12)
- [x] No secret strings in `git status` / committed files (checklist/status docs only; no values)
- [ ] Old token/secret **revoked** at the provider (not only replaced in env) — **human claim; not independently verified**
- [ ] Redacted evidence note filed off-git or via CREDENTIAL-ROTATION evidence template (fingerprints / key ids only)

## Agent / automation boundaries

- Do **not** dump `railway variable` / env values into logs or PRs.
- Do **not** claim Production GO after rotation — GA remains **NO-GO** until full audit DoD.
- Prefer this checklist over ad-hoc chat instructions.
- Do **not** flip `feature_ai_copilot`; do **not** run `alembic upgrade head` for this residual.

**Validation:** post-rotation runtime health = **light validated**; SSO browser + provider revoke = **not validated** / human-claimed only.
