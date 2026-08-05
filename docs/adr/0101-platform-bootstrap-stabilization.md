# ADR-101: Platform Bootstrap & Stabilization

**Status**: Accepted
**Date**: 2026-08-05
**Author**: Principal Platform Engineer (Cowork session)
**Related**: ADR-100 (Repository Canonicalization — complete, this ADR does not reopen it), `docs/audit/SANDBOX_VALIDATION_LIMITATIONS.md`
**Supersedes**: nothing. **Does not continue under ADR-100** — this is a new program with a different scope.

---

## Context

ADR-100's four phases (Safe Cleanup, Repository Documentation, Legacy Isolation, Pending Migration Completion) are complete. Repository topology is canonical and internally consistent. That program is closed.

An attempt to begin Docker/Bootstrap validation inside the Cowork sandbox surfaced an environment limitation, not a project defect: the sandbox has no Docker daemon, and its npm workspace symlinks are corrupted at the filesystem/mount layer (`readlink` on `node_modules/@salesos/*` returns `Input/output error`, confirmed in `docs/audit/SANDBOX_VALIDATION_LIMITATIONS.md`). Every `TS2307 Cannot find module '@salesos/*'` error produced by `npm run typecheck` in that sandbox is explained by this alone and must not be treated as evidence of a real code defect. Decision, confirmed by the user: **stop attempting to reproduce or fix errors inside the sandbox. Move execution to a local machine or other trusted environment; this session analyzes real output rather than generating unverifiable diagnoses.**

This is a distinct program from ADR-100, per explicit direction:

```
Repository Engineering   ✅ Complete
        ↓
Platform Stabilization   ← this ADR
        ↓
Production Readiness
        ↓
UX/UI Modernization
        ↓
Feature Development
```

## Decision

### Scope

**In scope:**
- Install (npm, Poetry)
- Build (frontend build, backend package build)
- Startup (frontend dev/prod server, backend Uvicorn process)
- Docker (image builds, `docker compose up`, container health)
- Healthchecks (the `/health` and equivalent endpoints already defined in `docker-compose.yml`)
- Tests (Jest, pytest — as verification that a fix actually resolved the failure, not as a general QA pass)

**Out of scope (governed elsewhere, not reopened here):**
- Architecture — governed by ADR-100 and the ADR-036 four-layer model
- Repository structure — governed by ADR-100
- Refactoring — no code redesign, only minimal fixes to unblock boot
- Documentation reorganization — governed by ADR-100 Phase 2 (already complete)

### Operating model: Bootstrap Engineer

This ADR's execution follows a fixed cycle, one failure at a time:

```
Run → First Failure → Root Cause → Minimal Fix → Run Again → Repeat
```

Rules:
1. **One failure per cycle.** Do not attempt to fix a second issue spotted while investigating the first — log it, keep going on the first.
2. **Minimal fix only.** The smallest change that resolves the specific reproduced failure. Not a refactor, not a "while I'm here" improvement.
3. **No fix without reproduction.** An error is only actioned if it reproduced on a local machine or another trusted execution environment — never from sandbox output alone (per `docs/audit/SANDBOX_VALIDATION_LIMITATIONS.md`).
4. **Re-run after every fix.** Confirm the specific failure is gone before moving to the next one.

### Execution waves

| Wave | Scope | Commands |
|---|---|---|
| **Wave 1 — Frontend** | Install → typecheck → build | `npm install` → `npm run typecheck` → `npm run build` |
| **Wave 2 — Backend** | Install → migrate → test | `poetry install` → `alembic upgrade head` → `pytest` |
| **Wave 3 — Docker** | Build → boot → verify | `docker compose up --build` → healthcheck status → log review |
| **Wave 4 — Integration** | Cross-service verification | Frontend ↔ Backend, Database, Redis, Search, AI, Workers |

Waves are sequential — do not start Wave *N+1* until Wave *N* is either clean or its open failures are explicitly deferred by the user. Diagnostics (`node -v`, `npm ls @salesos/*`, etc. — per the command list already issued) run before Wave 1's install step, not after.

### Tooling division (context, not an action owned by this ADR)

Per user direction, three parallel tracks now run without conflict, since none of them depend on repository restructuring anymore:
1. **Platform Stabilization** (this ADR) — bootstrap/build/Docker fixes, driven by real local execution output.
2. **UX/UI Modernization** — design system work, independent of this ADR's scope.
3. **Feature Backlog Preparation** — queued for after platform stabilization, not started here.

## Consequences

- Every fix under this ADR must cite the reproducing command and its exact output — no fix is accepted on the basis of sandbox-only errors.
- `@salesos/config`'s dependency specifier (`"*"` vs. `"workspace:*"`) remains **unchanged and unresolved** — flagged in `docs/audit/SANDBOX_VALIDATION_LIMITATIONS.md` as a historical question (`git log`/`git blame`), not a confirmed defect, and out of this ADR's "minimal fix" mandate unless it actually reproduces as a real install/build failure.
- This ADR closes only when Wave 4 completes with a documented Green Bootstrap — a full local `docker compose up --build` with all services passing healthchecks.

## Next step

Waiting on the user to run Wave 1's diagnostic + install/typecheck/build sequence locally and paste the first real, full error output (if any). Nothing is fixed until then.
