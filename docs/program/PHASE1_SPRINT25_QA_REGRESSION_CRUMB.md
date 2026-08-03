# Sprint 25 — Full regression suite (final) — inventory crumb

> **Honesty:** **NOT VALIDATED** — inventory only. Does **not** claim 100% pass, RC soak start, or Production GO.  
> **Sprint:** 25 · Owner: QA-Lead · Priority: P0 · Risk: High  
> **Story AC (plan text):** “100% pass against the RC candidate build”  
> **This land:** Suite matrix invented from **existing** CI / workflow definitions + how to pin an RC SHA. **No suite execution** in this crumb (low-load; requires explicit approval).

## Status

| Claim | Label |
|-------|--------|
| Suite inventory documented from workflows | **present** (this crumb) |
| Full regression executed on an RC candidate | **not validated** |
| 100% pass against RC candidate | **not validated** — **forbidden to claim** until Evidence records green runs on a pinned SHA |
| Production GO / Companion acceptance | **Forbidden** |
| Stage 6 GHCR as regression gate | **SKIPPED** (DEC-150 B) — not required |

## How to pin the RC candidate SHA

Board / Release must declare the RC tip before QA can claim pass/fail against it.

1. **Declare** `RC_SHA` = the git commit Board freezes as Release Candidate (feature freeze). Prefer a full 40-char SHA.  
2. **Verify tip identity:**
   ```text
   git rev-parse HEAD
   git log -1 --oneline
   ```
3. **Pin CI evidence to that SHA** (not “latest master”):
   ```text
   gh run list --workflow=CI --commit <RC_SHA> --limit 5
   gh run list --workflow="Stage 7 E2E" --commit <RC_SHA> --limit 5
   gh run list --workflow="Security Scan" --commit <RC_SHA> --limit 5
   gh run list --workflow="Docker Smoke Test" --commit <RC_SHA> --limit 5
   ```
4. **Record** in Evidence: `RC_SHA`, workflow run IDs/URLs, job conclusions, and date. Until that pack exists, status stays **not validated**.  
5. **Do not** equate “green on some nearby tip” with “100% pass on RC” — SHA must match.

Optional tag (Board only): `git tag -a rc-<YYYYMMDD> <RC_SHA>` after declaration — not required for this inventory.

## Suite matrix (from existing workflows)

Sources under `.github/workflows/` (repo root). Commands are what CI runs; local re-runs need explicit approval (low-load).

### A. Primary CI — `.github/workflows/ci.yml` (`name: CI`)

| ID | Stage / job | What it runs | Role in “full regression” |
|----|-------------|--------------|---------------------------|
| A1 | Stage 1 `lint-backend` | `poetry run ruff check` + `ruff format --check` on `app/ tests/ sdk/ modules/` | Gate |
| A2 | Stage 1 `lint-frontend` | `npm run lint` + Prettier check on `src/**` | Gate |
| A3 | Stage 2 `typecheck-backend` | `poetry run mypy app/ sdk/ modules/` | Gate |
| A4 | Stage 2 `typecheck-frontend` | `npx tsc --noEmit` | Gate |
| A5 | Stage 3 `test-backend` | Alembic upgrade + head check + **pytest** (`-m "not e2e"`, cov-fail-under=55); PR-only diff-coverage ≥80 | **BE unit/integration-ish pytest** (includes unmarked + `contract`-marked tests when selected by `-m "not e2e"`) |
| A6 | Stage 3 `test-frontend` | `npm run test -- --coverage --forceExit` → **Jest** (`jest.config.js`) | **FE unit** |
| A7 | Stage 4 `integration-backend` | **pytest** `-m "not e2e" -n auto` with Postgres + Redis | **BE integration** |
| A8 | Stage 5 `security-pip-audit` | `pip-audit --strict` (named ignore PYSEC-2026-1325 only) | Security gate |
| A9 | Stage 5 `security-npm-audit` | `npm audit --audit-level=high` | Security gate |
| A10 | Stage 5 `security-bandit` | Bandit high/high fail | Security gate |
| A11 | Stage 5 `security-secrets-scan` | Forbidden-file check + Trivy fs CRITICAL,HIGH | Security gate |
| A12 | Stage 5 `test-architecture` | `pytest tests/test_architecture.py` | Arch fitness |
| A13 | Stage 5 `arch-compliance` | `salesos/scripts/arch-compliance.ps1` | Arch compliance % |
| A14 | Stage 6 `build-*` | GHCR docker build/push | **QUARANTINED** (`if: false`, DEC-150 B) — **SKIPPED**, not a pass criterion |
| A15 | Stage 7 `e2e` (inside ci.yml) | Playwright smoke | **SKIPPED** in ci.yml (`if: false`) — use workflow B |
| A16 | `ci-summary` | Aggregates Stages 1–5; fails on critical job failures | Summary only |

**Contract note:** OpenAPI/HTTP contract tests live under `salesos/backend/tests/contract/` (`@pytest.mark.contract`, DEC-094/106/131). There is **no** separate contract workflow; they are part of the BE pytest path exercised by A5/A7 when not deselected. Narrow local slice historically: `poetry run pytest tests/contract/ -m contract` (requires approval).

### B. Stage 7 E2E — `.github/workflows/e2e-stage7.yml` (`name: Stage 7 E2E`)

| ID | Job | What it runs | Role |
|----|-----|--------------|------|
| B1 | `e2e` | Real Postgres/Redis + uvicorn + disposable register + **Playwright** `e2e/smoke-auth-ui.spec.ts` (chromium) | Authenticated UI smoke (criterion 3.7 path). **Not** the full numbered 01–27 Playwright suite |

Path filters / schedule per workflow file — confirm a run exists **for `RC_SHA`** before citing.

### C. Docker compose smoke — `.github/workflows/docker-smoke.yml` (`name: Docker Smoke Test`)

| ID | Job | What it runs | Role |
|----|-----|--------------|------|
| C1 | `smoke` | `docker compose config` + build + up + `salesos/scripts/docker-smoke.ps1` | Compose E2E smoke |

### D. Standalone Security Scan — `.github/workflows/security-scan.yml` (`name: Security Scan`)

| ID | Jobs (representative) | What it runs | Role |
|----|----------------------|--------------|------|
| D1 | `secret-scan` | Forbidden files + **Gitleaks** + Trivy SARIF | Secrets / vulns |
| D2 | Remaining jobs in file | Bandit / npm-audit / related scans as defined in workflow | Parallel security surface |

Tip-line Security Scan SUCCESS is **build validated for CI only** — not a pentest substitute (see STORY-14-04 crumb).

### E. Deploy / field smokes (adjacent — not “unit regression”)

| ID | Workflow | What | Role for RC regression |
|----|----------|------|------------------------|
| E1 | `deploy-staging.yml` | Staging deploy + HTTP smoke retries | Staging field smoke — record if Board includes in RC gate |
| E2 | `deploy.yml` | Railway deploy path + health checks | Deploy evidence — not a substitute for A–D |
| E3 | `deploy-production.yml` | Production path + `smoke-test.ps1` | **Out of scope** for RC inventory claim; Production GO forbidden here |

### F. Related Phase-6 suites (separate stories — do not conflate)

| Story | Crumb | Relation |
|-------|-------|----------|
| STORY-14-07 LLM regression | [`PHASE1_STORY_14_07_LLM_REGRESSION_CRUMB.md`](./PHASE1_STORY_14_07_LLM_REGRESSION_CRUMB.md) | Non-prod golden LLM harness — **not** the “Full regression suite (final)” AC |
| STORY-14-01 load / soak | harness under `salesos/scripts/` | Perf/soak — Board-scoped residual; not claimed here |

## Suggested RC “full regression” checklist (execution deferred)

When Board pins `RC_SHA` and approves runs, Evidence should tick:

- [ ] A1–A13 green on `RC_SHA` (`CI` workflow) — Stage 6 SKIPPED OK  
- [ ] B1 green on `RC_SHA` (`Stage 7 E2E`) — smoke-auth only unless Board expands scope  
- [ ] C1 green on `RC_SHA` (`Docker Smoke Test`) if still required by Release Plan  
- [ ] D\* green on `RC_SHA` (`Security Scan`)  
- [ ] Contract coverage acknowledged as part of A5/A7 (or explicit `tests/contract/ -m contract` evidence)  
- [ ] Optional E1 staging smoke if Board requires field confirmation  
- [ ] Pass matrix + run URLs attached — only then may QA move status off **not validated** toward an earned label  

Until then: **inventory only**.

## Explicit non-claims

- **Not** 100% pass  
- **Not** RC soak clock started  
- **Not** Production GO / GA GO  
- **Not** full Playwright 01–27 suite (CI gate is `smoke-auth-ui` only)  
- **Not** Stage 6 GHCR required  
- **Not** live LLM / `feature_ai_copilot=True`

## Board close criteria

1. This inventory crumb is linked from Sprint-25.  
2. Board declares `RC_SHA`.  
3. QA attaches Evidence pack of green runs **on that SHA** for the matrix rows Board adopts.  
4. Sprint-25 AC line updated only with an earned validation label — never invented 100% pass.

## Non-goals

- Running full suites without approval (low-load)  
- Inventing pass rates  
- Closing Phase 6 solely from this docs land  
- Weakening auth / CSRF / RBAC / evidence gates to “make green”
