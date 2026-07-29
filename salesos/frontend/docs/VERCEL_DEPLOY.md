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
