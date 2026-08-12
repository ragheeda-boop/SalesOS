# A-09 — Deploy Staging Unauthorized diagnosis (2026-08-13)

**Validation:** **light validated** (GH Actions failed-log + `gh secret list` timestamps — **no secret values read**)  
**Claims:** `staging_parity_complete=false` · `soak_complete_claim=false` · `production_go=false`  
**Constraints:** No `feature_ai_copilot` flip · No secret dumps · No invented `RAILWAY_TOKEN` · No workflow claim of fix without proof

---

## Subject run

| Field | Value |
|-------|-------|
| Run | https://github.com/ragheeda-boop/SalesOS/actions/runs/31648777919 |
| Ref | `staging` @ `df5028cc649a22ff7616938c2a8dab55d1f4e563` |
| Human claim | Token «تم التدوير» before this run |
| Gate | **SUCCESS** (all four Railway secrets non-empty) |
| `railway up` | **FAIL** — `Unauthorized. Please check that your RAILWAY_TOKEN is valid and has access…` |
| Health gate | skipped |

CLI invocation (secrets redacted by Actions):

```text
railway up --ci -y \
  --project "***" \
  --environment staging \
  --service "***"
```

`RAILWAY_TOKEN` was present in the job env (masked). Failure is auth/authorization, not missing secret / not “Environment not found”.

---

## Workflow inventory (`.github/workflows/deploy-staging.yml`)

| Item | Exact value |
|------|-------------|
| GitHub Environment | `staging` (all deploy jobs) |
| Auth secret | `secrets.RAILWAY_TOKEN` |
| Project | `secrets.RAILWAY_PROJECT_ID` |
| Service | `secrets.RAILWAY_STAGING_SERVICE_ID` |
| Env flag | **name** `staging` (not UUID) |
| Inventory-only | `RAILWAY_STAGING_ENVIRONMENT_ID` required by gate; **not** passed to `railway up` |
| Health | `vars.RAILWAY_STAGING_HEALTH_URL` (fallback secret) |

Compare production (`deploy.yml`): uses Environment `production` (empty) → **repo** secrets; `--environment` = `RAILWAY_ENVIRONMENT_ID` (UUID). Recent prod Railway up: **SUCCESS** (e.g. run `31648471066`).

---

## Evidence IDs (CLI-authoritative — `responsible-comfort`)

| ID | Value |
|----|-------|
| Project | `96032c9a-38cf-4792-8168-b78d5353e26b` |
| Staging environment | `5ce7864a-27c5-43c7-847d-667aecfbf773` |
| SalesOS service | `668122aa-523b-4ec3-a7d8-c3b579c90f66` |
| Production environment | `652c450a-1473-4445-98e4-15aceefd49c3` |

Do **not** use user-supplied UUIDs previously rejected by CLI (`1ef5b31a…`, `29252eae…` — not in workspace).

---

## Smoking gun — GitHub secret `updatedAt` (names only)

`gh secret list` (2026-08-13 probe):

| Scope | Secret | `updatedAt` (UTC) |
|-------|--------|-------------------|
| **Repository** | `RAILWAY_TOKEN` | **2026-08-01T22:59:29Z** |
| **Environment `staging`** | `RAILWAY_TOKEN` | **2026-08-09T18:13:07Z** |
| Environment `staging` | `RAILWAY_PROJECT_ID` | 2026-08-09T18:04:28Z |
| Environment `staging` | `RAILWAY_STAGING_SERVICE_ID` | 2026-08-09T18:04:29Z |
| Environment `staging` | `RAILWAY_STAGING_ENVIRONMENT_ID` | 2026-08-12T18:57:21Z |
| Environment `production` | *(none)* | — |

Run `31648777919` started **2026-08-12T22:53:20Z**. Neither repo nor Environment `staging` `RAILWAY_TOKEN` was updated after the claimed rotate. Jobs with `environment: staging` resolve **Environment** `RAILWAY_TOKEN` (overrides repo). Conclusion: **the rotated value never landed where this workflow reads it** (or never landed in GitHub at all).

---

## Root-cause hypotheses (ranked)

1. **Rotate missed Environment `staging` secret (highest)** — Human rotated in Railway UI and/or updated the wrong GitHub surface; `updatedAt` for Environment `staging`/`RAILWAY_TOKEN` still **2026-08-09**. Workflow correctly prefers Environment secret → still Unauthorized.
2. **Wrong token type / env scope** — Railway **Project Token** bound to **production** only (or Account token without project access) cannot `railway up` to `--environment staging`. Repo token works for **production** deploy; that does **not** prove staging scope.
3. **Bad paste on Aug 9 Environment token** — truncated / whitespace / wrong clipboard; gate only checks non-empty.
4. **Wrong project ID in Environment `staging`** — token valid for another project → Unauthorized for `RAILWAY_PROJECT_ID` used in `railway up` (cannot verify value without reading secret).
5. **Workflow flag / UUID mismatch (ruled out for this failure class)** — Gate passed; error is Unauthorized, not “Environment not found”. Name `staging` is intentional (CLI 5.x field fix). No workflow-only patch without a valid token.
6. **Obsolete CLI flag (ruled out)** — Same `railway up --ci -y --project/--environment/--service` pattern as production; prod SUCCESS with same CLI install path.

**Not fixable in workflow without a new/correct token.** Agent will not invent or paste token values.

---

## Human checklist (exact)

### A. Create the right Railway token

1. Open Railway → project **`responsible-comfort`** (`96032c9a-38cf-4792-8168-b78d5353e26b`).
2. Create a **Project Token** with access to environment **`staging`** (`5ce7864a-27c5-43c7-847d-667aecfbf773`).
   - Prefer Project Token scoped to **staging** (not production-only).
   - Account/workspace tokens only if they can deploy this project’s staging env (verify in Railway UI).
3. Copy the **full** token once (no truncate, no leading/trailing space/newline).

### B. Put it where this workflow reads it (critical)

4. GitHub → `ragheeda-boop/SalesOS` → **Settings → Environments → `staging` → Environment secrets**.
5. **Update** secret name exactly: `RAILWAY_TOKEN` (overwrite).  
   - Confirm `updatedAt` moves to **now** via `gh secret list --env staging` (names/timestamps only).
6. Optional but recommended: also set Repository secret `RAILWAY_TOKEN` only if you intentionally want a shared account token — **this workflow will still prefer Environment `staging`/`RAILWAY_TOKEN` while that env secret exists.**

### C. Confirm inventory secrets (Environment `staging`)

| Secret | Expected |
|--------|----------|
| `RAILWAY_TOKEN` | New staging-scoped token (just set) |
| `RAILWAY_PROJECT_ID` | `96032c9a-38cf-4792-8168-b78d5353e26b` |
| `RAILWAY_STAGING_SERVICE_ID` | `668122aa-523b-4ec3-a7d8-c3b579c90f66` |
| `RAILWAY_STAGING_ENVIRONMENT_ID` | `5ce7864a-27c5-43c7-847d-667aecfbf773` (gate inventory; deploy uses name `staging`) |

Var: `RAILWAY_STAGING_HEALTH_URL` = `https://salesos-staging.up.railway.app/health` (already set).

### D. Re-prove

7. Actions → **Deploy Staging** → branch `staging` → `confirm_staging=CONFIRM-STAGING-DEPLOY`.
8. Expect: Gate SUCCESS → Deploy Backend SUCCESS → Staging Health Gate HTTP 200.
9. Proof of paste: Environment `staging` `RAILWAY_TOKEN` `updatedAt` **after** rotate and **before** the new run.

Do **not** paste token values into chat, issues, or commits.

### Fast diagnostic (optional)

If you believe the **repo** token already has staging access: temporarily **delete** Environment `staging` secret `RAILWAY_TOKEN` (so the job falls back to repo secret) and re-dispatch once.  
- SUCCESS → Environment token was the bad override; recreate a staging Project Token into Environment `staging`.  
- Still Unauthorized → need a staging-scoped Project Token (repo token is likely production-scoped).

---

*A-09 steps 1–2 remain Human-Gate. Workflow SHA on failing run: `df5028cc`. No production GO.*
