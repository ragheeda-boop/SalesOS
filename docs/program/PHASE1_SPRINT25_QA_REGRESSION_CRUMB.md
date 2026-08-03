# Sprint 25 — Full regression suite (final) — inventory crumb

> **Honesty:** **NOT VALIDATED** — inventory + **candidate** RC pin only. Does **not** claim 100% pass, Board-declared RC / soak start, or Production GO.  
> **Sprint:** 25 · Owner: QA-Lead · Priority: P0 · Risk: High  
> **Story AC (plan text):** “100% pass against the RC candidate build”  
> **This land:** Suite matrix from **existing** CI / workflow definitions + candidate `RC_SHA` pin + empty results tables. **No suite execution** in this crumb (low-load; requires explicit approval).

## Status

| Claim | Label |
|-------|--------|
| Suite inventory documented from workflows | **present** (this crumb) |
| Candidate RC SHA pinned | **present** — `fe84441` (re-pinned from `26f2ab5`; see below) |
| Evidence / QA-Lead **declares** RC (feature freeze + soak clock) | **not validated** — procedure documented; Board must freeze |
| Full regression executed on pinned SHA | **not validated** |
| 100% pass against RC candidate | **not validated** — **forbidden to claim** until Evidence records green runs on the pinned SHA for adopted matrix rows |
| Production GO / Companion acceptance | **Forbidden** |
| Stage 6 GHCR as regression gate | **SKIPPED** (DEC-150 B) — not required |

## Candidate RC SHA (pinned)

| Field | Value |
|-------|--------|
| **Candidate `RC_SHA` (short)** | `fe84441` |
| **Candidate `RC_SHA` (full)** | `fe844410415a284382671d406bef3e4c2e62dce8` |
| **Subject** | `docs(security): firm handoff READY for STORY-14-04 residual-external` |
| **Prior candidate** | `26f2ab5` (`26f2ab57372970b761a495eaf3949ed558830247`) — superseded; Board freeze may still choose another later full tip-line green tip |
| **Why this tip** | Evidence #1 absolute tip — full tip-line GREEN (Watchdog). Re-pinned so candidate RC tracks latest green tip before Board freezes. |
| **Tip-line context (≠ regression AC)** | CI [30846452123](https://github.com/ragheeda-boop/SalesOS/actions/runs/30846452123) SUCCESS (S1–5) · Docker Smoke [30846452103](https://github.com/ragheeda-boop/SalesOS/actions/runs/30846452103) SUCCESS · Security Scan [30846452081](https://github.com/ragheeda-boop/SalesOS/actions/runs/30846452081) SUCCESS · Deploy+Health Gate [30846452115](https://github.com/ragheeda-boop/SalesOS/actions/runs/30846452115) SUCCESS · Stage 6 **SKIPPED** |
| **Regression suite status on this SHA** | **NOT VALIDATED** (all suite rows below stay **NOT VALIDATED**; tip-line ≠ suite pass) |
| **RC soak clock** | **Not started** — candidate pin ≠ Board RC declare |

Advance / re-pin rule: if a **later** absolute tip earns full tip-line green before Board freezes, Evidence/QA-Lead **re-pins** this section to that SHA and clears any filled result rows back to **NOT VALIDATED** until re-run evidence exists for the new SHA. Re-pin `26f2ab5` → `fe84441` applied; prior tip-line URLs for `26f2ab5` are **context only**, not AC evidence on this SHA.

## How Evidence / QA-Lead declares RC

Board owns freeze; Evidence #1 + QA-Lead own the SHA pin and evidence pack. Declare only with all steps below.

1. **Confirm tip-line eligibility** (Evidence #1): absolute tip is full tip-line green (S1–5 + Deploy Health Gate when run; +S7 if path-triggered). Stage 6 SKIPPED OK. Do **not** use a nearby green tip.
2. **Propose candidate** in this crumb (and Board hub): short + full SHA, subject, date/UTC, tip-line run URLs.
3. **Board freezes** `RC_SHA` = feature freeze tip. Until Board says “RC declared,” status stays **candidate** — soak clock **does not** start from QA alone.
4. **QA-Lead records declaration block** (fill when Board freezes — leave blank until then):

   | Field | Value |
   |-------|--------|
   | Declared `RC_SHA` | _pending Board freeze_ |
   | Declared by (Board) | _pending_ |
   | Declared at (UTC) | _pending_ |
   | QA-Lead ack | _pending_ |
   | Soak clock start | _pending_ — **not started** |

5. **Pin CI evidence to that exact SHA** (not “latest master”):
   ```text
   git rev-parse HEAD
   git log -1 --oneline
   gh run list --workflow=CI --commit <RC_SHA> --limit 5
   gh run list --workflow="Stage 7 E2E" --commit <RC_SHA> --limit 5
   gh run list --workflow="Security Scan" --commit <RC_SHA> --limit 5
   gh run list --workflow="Docker Smoke Test" --commit <RC_SHA> --limit 5
   ```
6. **Fill results tables** below with run IDs/URLs/conclusions **only** after Board-approved suite evidence on the pinned SHA. Until then every row stays **NOT VALIDATED**.
7. **Do not** equate tip-line green, “green on nearby tip,” or partial suite green with “100% pass on RC.”

Optional tag (Board only): `git tag -a rc-<YYYYMMDD> <RC_SHA>` after declaration — not required for this inventory.

## Results tables (empty — NOT VALIDATED)

> Fill only after Board-approved runs on the pinned `RC_SHA`. Tip-line SUCCESS links above are **context**, not suite-row pass claims.

### A. Primary CI — workflow `CI` (`.github/workflows/ci.yml`)

| ID | Stage / job | Result | Run ID / URL | Notes |
|----|-------------|--------|--------------|-------|
| A1 | `lint-backend` | **NOT VALIDATED** | — | |
| A2 | `lint-frontend` | **NOT VALIDATED** | — | |
| A3 | `typecheck-backend` | **NOT VALIDATED** | — | |
| A4 | `typecheck-frontend` | **NOT VALIDATED** | — | |
| A5 | `test-backend` | **NOT VALIDATED** | — | pytest `-m "not e2e"` |
| A6 | `test-frontend` | **NOT VALIDATED** | — | Jest |
| A7 | `integration-backend` | **NOT VALIDATED** | — | |
| A8 | `security-pip-audit` | **NOT VALIDATED** | — | |
| A9 | `security-npm-audit` | **NOT VALIDATED** | — | |
| A10 | `security-bandit` | **NOT VALIDATED** | — | |
| A11 | `security-secrets-scan` | **NOT VALIDATED** | — | |
| A12 | `test-architecture` | **NOT VALIDATED** | — | |
| A13 | `arch-compliance` | **NOT VALIDATED** | — | |
| A14 | Stage 6 `build-*` | **SKIPPED** | — | DEC-150 B — not a pass criterion |
| A15 | Stage 7 `e2e` (in ci.yml) | **SKIPPED** | — | use workflow B |
| A16 | `ci-summary` | **NOT VALIDATED** | — | aggregate only |

### B. Stage 7 E2E — workflow `Stage 7 E2E`

| ID | Job | Result | Run ID / URL | Notes |
|----|-----|--------|--------------|-------|
| B1 | `e2e` (`smoke-auth-ui.spec.ts`) | **NOT VALIDATED** | — | Not full Playwright 01–27 |

### C. Docker Smoke Test

| ID | Job | Result | Run ID / URL | Notes |
|----|-----|--------|--------------|-------|
| C1 | `smoke` | **NOT VALIDATED** | — | |

### D. Security Scan

| ID | Job | Result | Run ID / URL | Notes |
|----|-----|--------|--------------|-------|
| D1 | `secret-scan` / Gitleaks / Trivy | **NOT VALIDATED** | — | ≠ pentest substitute |
| D2 | Remaining security-scan jobs | **NOT VALIDATED** | — | |

### E. Deploy / field (optional Board gate)

| ID | Workflow | Result | Run ID / URL | Notes |
|----|----------|--------|--------------|-------|
| E1 | Deploy Staging | **NOT VALIDATED** | — | if Board includes |
| E2 | Deploy Production (health gate) | **NOT VALIDATED** | — | tip-line context ≠ AC |
| E3 | Deploy to Production (K8s) | **OUT OF SCOPE** | — | Production GO forbidden |

### Contract (in A5/A7)

| ID | Slice | Result | Run ID / URL | Notes |
|----|-------|--------|--------------|-------|
| K1 | `tests/contract/ -m contract` | **NOT VALIDATED** | — | no separate workflow |

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

## Exact `gh` / workflow commands (list only — do not run full suites)

Set once:

```text
set RC_SHA=fe844410415a284382671d406bef3e4c2e62dce8
```

**List / inspect (read-only — preferred under low-load):**

```text
gh run list --workflow=CI --commit %RC_SHA% --limit 5
gh run list --workflow="Stage 7 E2E" --commit %RC_SHA% --limit 5
gh run list --workflow="Docker Smoke Test" --commit %RC_SHA% --limit 5
gh run list --workflow="Security Scan" --commit %RC_SHA% --limit 5
gh run list --workflow="Deploy Staging" --commit %RC_SHA% --limit 5
gh run list --workflow="Deploy Production" --commit %RC_SHA% --limit 5

gh run view <RUN_ID> --json conclusion,status,headSha,url,jobs
gh run view <RUN_ID> --log-failed
```

**Re-dispatch (requires explicit approval — heavy; do not run from this crumb):**

```text
gh workflow run CI --ref %RC_SHA%
gh workflow run "Stage 7 E2E" --ref %RC_SHA%
gh workflow run "Docker Smoke Test" --ref %RC_SHA%
gh workflow run "Security Scan" --ref %RC_SHA%
gh workflow run "Deploy Staging" --ref %RC_SHA%
```

Job-level drill-down after a CI run exists: Actions UI → run → jobs A1–A13, or `gh api repos/{owner}/{repo}/actions/runs/<RUN_ID>/jobs`.

## Dispatch checklist (approval-gated — do not run from this crumb)

> **Honesty:** Pre-execution gate only. Does **not** authorize suite runs, claim 100% pass, Board-declared RC / soak start, or Production GO. Tip-line green ≠ suite-row pass. All results tables remain **NOT VALIDATED** until Board-approved evidence on the pinned SHA.

### Pre-flight

- [ ] Board has **frozen** `RC_SHA` (candidate alone does not start soak)
- [ ] Confirm pin: `git rev-parse` / `git log -1` match short + full SHA in this crumb (`fe84441` / `fe844410415a284382671d406bef3e4c2e62dce8` unless Board re-pins again)
- [ ] Evidence #1 tip-line eligibility reviewed for that exact SHA (S1–5 + Deploy Health Gate when run; +S7 if path-triggered). Stage 6 **SKIPPED** OK
- [ ] On any further re-pin: update Candidate RC block, clear A–E/K rows to **NOT VALIDATED**, re-dispatch only against the new SHA
- [ ] Read-only `gh run list … --commit %RC_SHA%` first (low-load); **no** `gh workflow run` without explicit approval

### Workflows to dispatch (Board-approved only)

| Order | Workflow | Matrix | Notes |
|-------|----------|--------|-------|
| 1 | `CI` | A1–A13, A16 | A14 Stage 6 SKIPPED; A15 use B |
| 2 | `Stage 7 E2E` | B1 | smoke-auth only — not Playwright 01–27 |
| 3 | `Docker Smoke Test` | C1 | if Release Plan still requires |
| 4 | `Security Scan` | D1–D2 | ≠ pentest substitute |
| 5 | `Deploy Staging` *(optional)* | E1 | Board gate only |
| — | Contract | K1 | via A5/A7 (no separate workflow) |

### Post-dispatch (fill tables only with SHA-matched proof)

- [ ] A1–A13 green on pinned `RC_SHA` — A14 SKIPPED OK  
- [ ] B1 / C1 (if adopted) / D\* green on pinned `RC_SHA`  
- [ ] K1 contract coverage acknowledged  
- [ ] Optional E1 if Board requires  
- [ ] Run IDs/URLs recorded — only then may status leave **not validated** toward an **earned** label  

**Hard stops:** no suite runs without approval; no 100% pass / Production GO / soak-started invent; tip-line SUCCESS ≠ filled AC.

## Suggested RC “full regression” checklist (execution deferred)

When Board freezes `RC_SHA` and approves runs, Evidence should tick the dispatch checklist above. Until then: **inventory + candidate pin only** (`fe84441` · **NOT VALIDATED**).

## Explicit non-claims

- **Not** 100% pass  
- **Not** Board-declared RC / feature freeze complete  
- **Not** RC soak clock started  
- **Not** Production GO / GA GO  
- **Not** full Playwright 01–27 suite (CI gate is `smoke-auth-ui` only)  
- **Not** Stage 6 GHCR required  
- **Not** live LLM / `feature_ai_copilot=True`  
- Tip-line green on candidate SHA ≠ filled regression results tables

## Board close criteria

1. This inventory crumb is linked from Sprint-25.  
2. Candidate `RC_SHA` pinned here (done: `fe84441`; was `26f2ab5`).  
3. Board declares / freezes `RC_SHA` (pending).  
4. QA attaches Evidence pack of green runs **on that SHA** for the matrix rows Board adopts.  
5. Sprint-25 AC line updated only with an earned validation label — never invented 100% pass.

## Non-goals

- Running full suites without approval (low-load)  
- Inventing pass rates  
- Closing Phase 6 solely from this docs land  
- Weakening auth / CSRF / RBAC / evidence gates to “make green”
