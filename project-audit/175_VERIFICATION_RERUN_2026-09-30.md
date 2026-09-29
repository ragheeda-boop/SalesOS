# Verification re-run — 2026-09-30

Re-ran the Decision/Agents, frontend, and CI checks on `fix/login-and-keys` after commits `7cf147e7`, `40835ccc`, `79792cb1`, and `d1bbe8fd`. No code change. No production database write, migration, deploy, Apollo call, or push.

## Results

| Check | Result |
|---|---|
| Decision lab Jest | 3 suites, 120 passed |
| Agents lab Jest | 6 suites, 38 passed |
| Decision and Agents `tsc --noEmit` | both exit 0, using a type root outside the repository |
| Frontend `docker build --target build` | image `fe-verify:20260930` created (`d9fcd92796d0`) |
| `next lint` inside that image | PASS, no ESLint warnings or errors |
| Parallel `npm run test` | 335 suites passed; 2,691 passed; 1 skipped; exit 0. One worker force-exited after the suites passed (non-failing) |
| Prettier on `src` with the root `.gitignore` | PASS (`All matched files use Prettier code style!`) |
| CI YAML | `build-frontend`: no `if`, `contents: read` only, `push: false`. `packages: write` and `push: true` only on `build-backend`, which stays `if: false` |
| `git diff --check` | exit 0 (CRLF warning on the unstaged Wave 13 probe script only) |

Route manifests inside the local image: 117 prerender routes, 118 `staticRoutes`, 17 `dynamicRoutes`, 137 app-path routes. The compiler's static-page banner from this build was not retained. The image context also contained five gitignored pages, so this count is not a clean checkout count.

## Prettier residual, not committed

`prettier --check` on `src` inside the image, without the root ignore file, reported five files:

- `src/app/v3/data/companies/page.tsx`
- `src/app/v3/data/er/page.tsx`
- `src/app/v3/data/imports/page.tsx`
- `src/app/v3/data/people/page.tsx`
- `src/app/v3/data/review-queue/page.tsx`

Root `.gitignore` pattern `data/` ignores them. They are not in the index. `COPY . .` still sends them into the local image. Applying that ignore file makes the `src` check pass. They were left unstaged.

## Left unstaged on purpose

- `salesos/scripts/probe-wave13-api-residuals.ps1`
- `salesos/docker-compose.windows.yml`
- `salesos/docs/architecture/`
- `salesos/docs/discovery/`
- `salesos/docs/ops/`
- `salesos/docs/roadmap/PRODUCTIZATION_ROADMAP.md`
- `scripts/` (root `discover_*.py`)

## Gates

G2–G16 and G8 stay closed. Production remains NOT APPROVED. The header statements in AGENTS.md §214 that `decisionHttp` is missing, that Prettier fails on 243 committed `src` files, and that CI Stage 6 is `if: false` are superseded by this re-run.
