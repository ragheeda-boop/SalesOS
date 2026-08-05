# Sandbox Validation Limitations — 2026-08-05

**Purpose:** Record what was and was not validated during the Docker/Bootstrap stabilization attempt, and why. This document exists so no `@salesos/*` or `TS7006` error observed in the Cowork sandbox is later mistaken for a confirmed project defect.

**Status: sandbox debugging halted per explicit decision.** Execution moves to the user's local machine; this session continues in Execution Support Mode (analyze real output, do not attempt to reproduce or fix inside this sandbox).

---

## 1. Docker — static review only, no execution

**No Docker daemon is available in this sandbox.** `docker compose up` could not be run. Findings below are from reading configuration files only:

- `salesos/backend/Dockerfile` — multi-stage build, `python:3.12-slim` base (matches `pyproject.toml`'s `python = "^3.12"`), Poetry-based dependency install, non-root runtime user, `HEALTHCHECK` against `/health`. No issues found on read.
- `salesos/frontend/Dockerfile` — multi-stage build, `node:22-alpine` base, npm workspace install with `--include-workspace-root`, Next.js standalone output, non-root runtime user, `HEALTHCHECK`. No issues found on read.
- `salesos/docker-compose.yml` — `backend`/`frontend` service definitions have correct build contexts, `depends_on` with `service_healthy` conditions, sensible env var defaults with fallbacks.

**Conclusion: no obvious problems on static read. This is not equivalent to a passing build — it has never actually been executed in this session.**

## 2. TypeScript validation — result is unreliable, not a project defect

`npm run typecheck` was run against `salesos/frontend` (existing `node_modules`, Node 22 matching the Dockerfile base) and produced many `TS2307: Cannot find module '@salesos/ui'` (and `@salesos/search`, `@salesos/hooks`, etc.) errors, plus scattered `TS7006` implicit-`any` errors.

**Root cause identified — filesystem layer, not code:**
```
$ readlink node_modules/@salesos/ui
readlink: node_modules/@salesos/ui: Input/output error

$ stat node_modules/@salesos/ui
  File: node_modules/@salesos/ui
  Size: 0          Blocks: 0
  ... symbolic link, unreadable target
```
The npm workspace symlink itself is corrupted at the mount layer this Cowork sandbox uses to bridge the Windows filesystem — the link's target cannot be read at all (not "points to the wrong place," but genuinely unreadable). The actual target exists and is intact: `packages/ui/src/index.ts` is present and readable directly.

**Implication:** every `TS2307 Cannot find module '@salesos/*'` error is expected and explained by this broken symlink layer alone. **These errors are not evidence of a real project defect** and must not be treated as a punch list. The `TS7006` implicit-`any` errors are a separate category (unrelated to module resolution) and *may* be real, but cannot be distinguished from cascading noise caused by the unresolved imports in the same files without a clean re-run in a working environment.

**No code was changed in response to these errors. No fix was attempted.**

## 3. `@salesos/config` version specifier — observation, not a confirmed bug

While comparing the working tree to git `HEAD`, one semantic difference was found in `salesos/frontend/package.json`: `dependencies["@salesos/config"]` is `"*"` in the working tree vs. `"workspace:*"` in the last commit.

**Re-examined per your instruction, before concluding anything:**
- Package manager confirmed: **npm** — `salesos/frontend/package-lock.json` exists; no `pnpm-lock.yaml` or `yarn.lock` anywhere in the tree; `package.json` has no `packageManager` field forcing a different tool.
- `packages/config` **does exist** in the monorepo (`salesos/frontend/packages/config/package.json`, `name: "@salesos/config"`, `version: "5.0.0"`) — the package itself is real, not missing.
- Checked all other `@salesos/*` entries in the same `package.json`: **11 other workspace packages** (`charts`, `design-language`, `forms`, `hooks`, `icons`, `renderer`, `runtime`, `ui`, `workspace`, `workspace-generator`) are *already* declared with a bare `"*"` in committed `HEAD` — `"workspace:*"` was not the established pattern for any of them.
- `"workspace:"` as a literal protocol prefix is pnpm/Yarn Berry syntax; plain npm workspaces resolve local packages via ordinary semver ranges (including `"*"`) matching a package present in the workspace, without needing that prefix.

**This raises the possibility that `@salesos/config`'s `"workspace:*"` in `HEAD` was the outlier, and the uncommitted local change to `"*"` brings it in line with the other 11 — i.e., this may be a correction already in progress, not a regression.** This is inference, not confirmation — it has **not** been changed, reverted, or otherwise acted on. Recommend confirming intent with whoever made the local edit (or checking `git log -p` / `git blame` history beyond just `HEAD`) before treating it as either a bug or a fix.

---

## Local validation command list (Execution Support Mode)

Run in this exact order. **Diagnose before installing** — this determines whether a fresh `npm install` is even the right first move, or whether the problem is workspace configuration rather than corrupted `node_modules`.

### Step 0 — Diagnostics (run first, before touching `node_modules`)
```bash
cd salesos/frontend
node -v
npm -v
npm config get install-links
npm config get workspaces
npm config get link-workspace-packages
npm ls @salesos/ui
npm ls @salesos/config
ls -la node_modules/@salesos        # macOS/Linux
# dir node_modules\@salesos         # Windows cmd, if applicable
```

### Step 1 — Frontend
```bash
npm install --workspaces --include-workspace-root
npm run typecheck
npm run build
```

### Step 2 — Backend
```bash
cd ../backend
poetry install
poetry run alembic upgrade head
poetry run pytest -x
```

### Step 3 — Full stack (only after Steps 1–2 are clean or understood)
```bash
cd ..
docker compose up --build
```

**When something fails: send the full, unedited output of the first error — not a summary, not just the last line.** We fix sequentially, one confirmed real error at a time, until the first successful boot (Green Bootstrap).
