# A-09 — Discard invalid user UUIDs; restore live staging env ID (2026-08-13)

**Validation:** **light validated** (`gh secret set` + `gh secret list` timestamps; no token values)  
**Claims:** `staging_parity_complete=false` · `production_go=false`  
**Follow-up to:** [`A09-USER-UUID-SET-2026-08-13.md`](./A09-USER-UUID-SET-2026-08-13.md) (`f7bd8bf`)

---

## Verdict

User UUIDs `1ef5b31a-…` / `29252eae-…` are **discarded** — not valid in `responsible-comfort`.  
Live staging env ID restored in GitHub so a future successful token cannot target a nonexistent environment.

| ID | Role | Status |
|----|------|--------|
| `5ce7864a-27c5-43c7-847d-667aecfbf773` | Live staging (CLI-OK) | **Restored** → repo + Environment `staging` `RAILWAY_STAGING_ENVIRONMENT_ID` |
| `652c450a-1473-4445-98e4-15aceefd49c3` | Live production (CLI-OK) | **Confirmed** → repo `RAILWAY_ENVIRONMENT_ID` re-set to this value |
| `1ef5b31a-6869-483b-9b23-9cfc6b2a6686` | User staging paste | **Discarded** (CLI: Environment not found) |
| `29252eae-7eb7-472e-83c0-271a34ee0bfc` | User production paste | **Discarded** (CLI: Environment not found; already restored in `f7bd8bf`) |

---

## Secrets after restore (`gh secret list` — names + `updatedAt` only)

| Scope | Secret | `updatedAt` (UTC) | Note |
|-------|--------|-------------------|------|
| Repository | `RAILWAY_STAGING_ENVIRONMENT_ID` | **2026-08-12T23:03:34Z** | set to `5ce7864a-…` |
| Environment `staging` | `RAILWAY_STAGING_ENVIRONMENT_ID` | **2026-08-12T23:03:35Z** | set to `5ce7864a-…` |
| Repository | `RAILWAY_ENVIRONMENT_ID` | **2026-08-12T23:04:22Z** (re-confirm set) | `652c450a-…` |
| Environment `staging` | `RAILWAY_TOKEN` | **2026-08-09T18:13:07Z** | **unchanged** — rotate never landed here |

No invented tokens. No secret value dumps beyond public env UUIDs.

---

## Human residual (token — one screen)

Environment `staging` `RAILWAY_TOKEN` still shows `updatedAt` **2026-08-09**. Pasting only at account/repo level will **not** fix Deploy Staging.

1. Railway → project **responsible-comfort** → create **Project Token** scoped to env **staging** (`5ce7864a-…`).
2. GitHub → repo **Settings → Environments → `staging` → Secrets** → edit **`RAILWAY_TOKEN`** → paste token → Save.
3. Confirm Environment `staging` `RAILWAY_TOKEN` `updatedAt` is **today** (not 2026-08-09).
4. Re-dispatch **Deploy Staging** workflow.

---

*No `feature_ai_copilot` flip. No alembic. No token values printed.*
