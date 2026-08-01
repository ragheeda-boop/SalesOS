# Swarm Validation — 2026-08-01 (QA Team Alpha)

**Product:** SalesOS  
**Scope:** Narrow validation only (not full suite)  
**Git:** `master` @ `800753f` (includes `9577c98` and later)  
**Classification:** light validated (targeted pytest + Jest only)

## Environment

- Docker Compose backend: **up / healthy** (`salesos-backend-1`)
- Postgres, Redis, Neo4j: healthy at check time
- Host: Windows; tests via `docker compose exec` (backend) and local `npx jest` (frontend; `node_modules` present)

## Backend (Docker)

**Command:**

```text
cd salesos
docker compose exec -T backend pytest tests/integration/test_adversarial_write_protection.py tests/unit/test_jwt_audience_split.py -q
```

**Note:** bare `pytest` was not on PATH (`exec: pytest: not found`). Equivalent used:

```text
docker compose exec -T backend python -m pytest tests/integration/test_adversarial_write_protection.py tests/unit/test_jwt_audience_split.py -q
```

**Result:** **15 passed**, 0 failed, 2 warnings — ~77s of test time (wall clock higher due to container load / concurrent `poetry install` in same container).

| File | Outcome |
|------|---------|
| `tests/integration/test_adversarial_write_protection.py` | included in 15 pass |
| `tests/unit/test_jwt_audience_split.py` | included in 15 pass |

## Frontend (optional narrow Jest)

**Command:**

```text
cd salesos/frontend
npx jest --testPathPattern="middleware-auth|packages/ui/__tests__/card|components/foundation/__tests__/card" --passWithNoTests
```

**Result:** **3 suites passed**, **24 tests passed**, 0 failed (~35s).

| Suite | Outcome |
|-------|---------|
| `src/lib/auth/__tests__/middleware-auth.test.ts` | PASS |
| `packages/ui/__tests__/card.test.tsx` | PASS |
| `src/components/foundation/__tests__/card.test.tsx` | PASS |

## Summary counts

| Layer | Passed | Failed |
|-------|--------|--------|
| Backend pytest (narrow) | 15 | 0 |
| Frontend Jest (narrow) | 24 | 0 |
| **Total** | **39** | **0** |

## Limits (honesty)

- Not a full pytest or npm test suite.
- No claim of production GO, browser pass, or CI green beyond these commands.
- Concurrent container activity (`poetry install --with dev`, extra pytest) may have inflated wall time; pass/fail counts above are from the completed primary backend run and the Jest run recorded here.

---

## Addendum — STORY-02-02 QA verify (2026-08-01, tip `f2c7587`)

**DEC:** [`DEC-088-STORY-02-02-BROWSER-VERIFY.md`](../../../../docs/program/decisions/DEC-088-STORY-02-02-BROWSER-VERIFY.md)  
**Label:** **light validated** (units only) — browser **not validated**

**Command:**

```text
cd salesos/frontend
node node_modules/jest/bin/jest.js --config jest.config.js --testPathPattern="middleware-auth|auth/__tests__/session" --no-coverage
```

**Result:** **2 suites / 14 tests PASS** (`middleware-auth.test.ts`, `session.test.ts`).

**Browser/E2E:** harness present (`playwright.smoke.config.ts`, `e2e/smoke-auth-ui.spec.ts`, `scripts/smoke-ui.ps1`) — **not run**. Blockers: FE `node_modules` incomplete (no `.bin`, broken `next`); `:3000`/`:8000` down; Docker compose FE build/API failures. **No browser-pass claim.** STORY-02-02 remains **PARTIAL**.
