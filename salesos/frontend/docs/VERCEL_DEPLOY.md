# Vercel — SalesOS frontend deploy

**Project:** `sales-os` (`prj_xWwDXwTodsosOJXMJUzdTzA9L9RA`) on team **Muhide**  
**Production URLs:** `sales-os-muhide.vercel.app`, `sales-os-jet.vercel.app`  
**App path in monorepo:** `salesos/frontend`

## Root Directory (avoid double path)

Wave 19 saw CLI builds resolve to `salesos/frontend/salesos/frontend` when **both**:

1. Vercel project **Root Directory** is set to `salesos/frontend`, **and**
2. `vercel deploy` is run from the local `salesos/frontend` directory.

That stacks the path twice and breaks CLI deploys.

### GitHub (recommended production path)

- Connect repo **`ragheeda-boop/SalesOS`** to project **`sales-os`**
- Set **Root Directory** = `salesos/frontend` (relative to repo root)
- Push to `master` → Vercel builds from Git (latest prod deploys **READY** via GitHub integration)

### Local CLI from Muhide workspace

Choose **one** (not both):

| Approach | Vercel dashboard Root Directory | Where to run CLI |
|----------|--------------------------------|------------------|
| A — deploy from frontend folder | **Empty** / `.` | `cd salesos/frontend` then deploy |
| B — deploy from monorepo root | `salesos/frontend` | repo / Muhide root, not `salesos/frontend` |

Linked project metadata lives in `salesos/frontend/.vercel/project.json` (gitignored). Do not commit secrets.

## Build settings

Repo ships `salesos/frontend/vercel.json` (Next.js, security headers). Local validation (when approved): `npm run lint`, `npx tsc --noEmit`, `npm run build`.

## GitHub Actions (DEC-149)

Canonical FE production path remains **Vercel Git integration** (push `master` → project `sales-os`).

Optional CLI trigger from `.github/workflows/deploy.yml` / `deploy-staging.yml` when these secret **names** are set (values out-of-band — do not invent):

| Secret | Purpose |
|--------|---------|
| `VERCEL_TOKEN` | Vercel CLI auth |
| `VERCEL_ORG_ID` | Team / org id (CLI env) |
| `VERCEL_PROJECT_ID` | Project id for `sales-os` |

If those secrets are absent, Actions skip CLI and rely on Git integration. Backend deploy is Railway (see DEC-149 §6) — not Vercel.
