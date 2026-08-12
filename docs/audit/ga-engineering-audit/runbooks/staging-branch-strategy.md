# Staging branch strategy (A-09)

**Status:** Documented + branch created 2026-08-12  
**Does not grant:** staging parity CLOSE · Wave 11 soak claim · Production GO  
**Authority:** [A09_STAGING_PARITY.md](../star-audit/A09_STAGING_PARITY.md) · [deploy-staging.yml](../../../.github/workflows/deploy-staging.yml)

---

## Model (Railway env ≠ git branch)

| Track | Truth |
|-------|--------|
| **Production host** | Railway env `production` · CD via `deploy.yml` on `master` |
| **Staging host** | Railway env `staging` (`5ce7864a-…`) · `https://salesos-staging.up.railway.app` |
| **Git** | Default branch `master`. Long-lived **`staging`** branch exists for dispatch ref + optional staging-targeted PRs |

Deploy target is the **Railway environment**, not “whatever branch name matches.”  
`deploy-staging.yml` is **manual `workflow_dispatch` only** (no auto-push) to avoid dual-fire with production CD.

---

## Policy

1. **`master`** — production-bound; production CD remains push-triggered.  
2. **`staging`** — long-lived; keep periodically fast-forwarded from `master` (or merge selected commits). Prefer dispatching **Deploy Staging** from `staging` when exercising CI.  
3. Do **not** auto-deploy staging on every `master` push.  
4. Secrets stay in GitHub Environment `staging` + repo `RAILWAY_STAGING_*` — never in git.  
5. `railway up` uses `--environment staging` (**name**), not UUID-only (CLI 5.x GHA failure mode 2026-08-09).

---

## Operator: create / refresh branch

```bash
git fetch origin
git checkout -B staging origin/master   # or: git checkout staging && git merge --ff-only origin/master
git push -u origin staging
```

Dispatch:

```bash
gh workflow run deploy-staging.yml --ref staging \
  -f confirm_staging=CONFIRM-STAGING-DEPLOY \
  -f skip_frontend_cli=true
```

---

## Still human

- OAuth staging app, WAL/PITR/offsite, `max_connections`, rollback tabletop, ENV label fix (`ENV` still `production` on staging service — mislabel), soak claim flip.

*Evidence governs. A-09 remains OPEN until Human-Gate residuals close.*
