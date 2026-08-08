# Stream A — SEC-02 remainder + SEC-03 (+ SEC-04 note)

**Date:** 2026-08-06  
**Run:** EAB-2026-08-06-001  
**Validation:** **light validated** (Read/Grep spot-check; no pytest / Docker boot)  
**Commit:** none

## Status

| Finding | Status |
|---------|--------|
| **EAB-001-P0-SEC-02** (lifetime sessions) | **code-fixed** — Wave 1 password refuse unchanged; five lifetime `AsyncSession`s replaced |
| **EAB-001-P1-SEC-03** | **code-fixed** — `TenantContextMiddleware` reset via ContextVar Token |
| **EAB-001-P2-SEC-04** | **mitigated** — prod compose pins empty `SALESOS_TESTING`; startup + CSRF log ERROR if ENV prod/staging + flag truthy; bypass retained for tests |

## Pattern (SEC-02)

Repos that only accept `AsyncSession` are wrapped with `FactoryBoundRepository` (`app/database.py`):

1. Each public async method opens `tenant_scoped_session(async_session)`
2. Applies DEC-085 `set_config('app.tenant_id', …, true)` from ContextVar (same as `get_db`)
3. Commits on success; rolls back on error
4. No `app.state._*_session` lifetime handles; shutdown loop removed

Background paths (timeline recorder, workflow subscriber) pin tenant ContextVar from the event before repo calls.

## Residual risks

- Per-method sessions: multi-step workflow engine updates are no longer one DB transaction (each repo call commits). Prefer eventual native `session_factory` on those repos if atomic execute is required.
- Legacy `app/startup.py` still constructs lifetime sessions if used (main path is `boot/startup.py`).
- Runtime not exercised (no Docker boot / pytest this stream).

*Stream A — light validated — production no-go unchanged — no commit*
