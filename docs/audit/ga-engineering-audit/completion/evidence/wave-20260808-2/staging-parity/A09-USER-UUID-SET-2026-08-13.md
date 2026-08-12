# A-09 — User-supplied env UUIDs set + CLI validity (2026-08-13)

**Validation:** **light validated** (gh secret set + railway CLI status; no token values)  
**Claims:** `staging_parity_complete=false` · `production_go=false`  
**User instruction:** «ضيفهم انت» — add staging `1ef5b31a-…` / production `29252eae-…`

---

## What was set (IDs only — not tokens)

| Secret | Scope | Value set | Outcome |
|--------|-------|-----------|---------|
| `RAILWAY_STAGING_ENVIRONMENT_ID` | **Repository** | `1ef5b31a-6869-483b-9b23-9cfc6b2a6686` | set (`updatedAt` 2026-08-12T22:58:52Z) |
| `RAILWAY_STAGING_ENVIRONMENT_ID` | **Environment `staging`** | `1ef5b31a-6869-483b-9b23-9cfc6b2a6686` | set (`updatedAt` 2026-08-12T22:58:53Z) |
| `RAILWAY_ENVIRONMENT_ID` | **Repository** | briefly `29252eae-7eb7-472e-83c0-271a34ee0bfc`, then **restored** to CLI-live `652c450a-1473-4445-98e4-15aceefd49c3` | restore required — user UUID **not found**; `deploy.yml` passes this ID to `railway up --environment` |

No workflow rename needed: names already match `deploy-staging.yml` / `deploy.yml`.

---

## Railway validity (honest)

Workspace: `ragheed.a@ratlfintech.com` / `ragheeda-boop's Projects` · project `responsible-comfort` (`96032c9a-38cf-4792-8168-b78d5353e26b`).

| Probe | Result |
|-------|--------|
| `--environment 1ef5b31a-6869-483b-9b23-9cfc6b2a6686` | **Environment not found** |
| `--environment 29252eae-7eb7-472e-83c0-271a34ee0bfc` | **Environment not found** |
| `--environment 5ce7864a-27c5-43c7-847d-667aecfbf773` (known staging) | **OK** → name `staging` |
| `--environment 652c450a-1473-4445-98e4-15aceefd49c3` (known production) | **OK** → name `production` |
| User staging UUID as **service** | **Service not found** |
| User UUIDs as **project** (`RAILWAY_PROJECT_ID` / status) | **Project not found** |

**Verdict:** User UUIDs are **not valid** environment, project, or service IDs in this authenticated workspace. They are **not** alternate names for `5ce7864a` / `652c450a`. Likely wrong account/workspace clipboard, or stale IDs from another Railway org.

`deploy-staging.yml` still deploys with **`--environment staging` (name)** — inventory secret is presence-checked only. Setting the invalid staging UUID does **not** change the Unauthorized failure class (token).

---

## Fold into Unauthorized diagnosis

Primary blocker remains: Environment `staging` `RAILWAY_TOKEN` (`updatedAt` still **2026-08-09**) Unauthorized on `railway up`. Env-ID paste does not fix auth.

Human residual unchanged: create **Project Token** for `responsible-comfort` / env **staging** (`5ce7864a-…`) → paste into GitHub Environment **`staging`** secret `RAILWAY_TOKEN` → confirm new `updatedAt` → re-dispatch.

---

## Deploy Staging re-dispatch

| Field | Value |
|-------|-------|
| Run | https://github.com/ragheeda-boop/SalesOS/actions/runs/31649271196 |
| Ref | `staging` @ `df5028cc` |
| Gate | **SUCCESS** (secrets present — including user staging UUID) |
| `railway up --environment staging` | **FAIL Unauthorized** (unchanged class) |
| Conclusion | **failure** |

Env-ID change did not affect deploy path (name `staging`). Unauthorized remains token-scope / Environment secret paste.

---

*No `feature_ai_copilot` flip. No alembic. No token values printed.*
