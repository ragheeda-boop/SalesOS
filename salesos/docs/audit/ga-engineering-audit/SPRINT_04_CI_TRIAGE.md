# Sprint 04 — CI Failure Triage

**Date:** 2026-07-31
**Trigger commit:** `354e13c` — "chore: Sprint 04 CI field-verification trigger (2026-07-31 18:59)"
**Branch:** `master` (push event)
**Scope note:** Analysis only. No code modified, no workflows rerun, no fixes implemented — per the explicit mandate for this pass. Every finding below is backed by direct evidence pulled from the actual GitHub Actions run logs (`gh run view --log-failed` / `gh run view --job <id> --log`), not inferred or assumed.

## Result

5 workflows triggered on this push. **All 5 failed.** 17 failed jobs total.

| Workflow | Run ID | Result |
|---|---|---|
| CI | [30645254785](https://github.com/ragheeda-boop/SalesOS/actions/runs/30645254785) | ❌ failure |
| Docker Smoke Test | [30645252933](https://github.com/ragheeda-boop/SalesOS/actions/runs/30645252933) | ❌ failure |
| Security Scan | [30645252925](https://github.com/ragheeda-boop/SalesOS/actions/runs/30645252925) | ❌ failure |
| Deploy Production | [30645252795](https://github.com/ragheeda-boop/SalesOS/actions/runs/30645252795) | ❌ failure |
| Deploy Staging | [30645252769](https://github.com/ragheeda-boop/SalesOS/actions/runs/30645252769) | ❌ failure |

---

## CI workflow

### 1. Stage 2: Backend Types (MyPy)
- **Root Cause:** `poetry run mypy app/ sdk/ modules/ cli/` — `salesos/backend/cli/` does not exist.
- **Evidence:** `mypy: error: cannot read file 'cli': No such file or directory`. Confirmed via `ls salesos/backend/cli` → No such file or directory (`salesos/backend/modules/` does exist).
- **Classification:** Configuration | **Severity:** Medium | **Blocking:** YES
- **Est. Fix Time:** 2 min
- **Recommended Story:** Bundle with #2, #9 (CI path cleanup)
- **Acceptance Criteria:** `mypy` invocation only references directories that exist; job passes or fails only on real type errors.

### 2. Stage 1: Backend Lint (Ruff)
- **Root Cause:** Two distinct issues: (a) same non-existent `cli/` path; (b) 3,611 real Ruff violations across nearly the entire backend, including auto-generated `app/alembic/versions/*.py` files apparently never intended to be style-checked.
- **Evidence:** `##[error]cli:1:1: E902 No such file or directory`; `grep -c "##\[error\]"` on the captured log → 3611, spanning 60+ directories (`app/alembic/versions` alone: 54).
- **Classification:** Tooling (never previously enforced against this codebase) + Configuration (missing exclude for generated files) | **Severity:** HIGH | **Blocking:** YES
- **Est. Fix Time:** Large — 1–2 days. `ruff check --fix` auto-resolves a meaningful fraction; the rest needs real review across ~150+ files.
- **Recommended Story:** Dedicated Sprint story, not a CI-config patch.
- **Acceptance Criteria:** `ruff check` exits 0; `app/alembic/versions/` excluded from style enforcement; `cli/` path resolved.

### 3. Stage 5: Secrets Scan (Trivy filesystem scan)
- **Root Cause:** **Insufficient evidence.** Log shows `[npm] Detecting vulnerabilities...` → `[poetry] Detecting vulnerabilities...` → exit code 1, with no vulnerability table or error message printed between them.
- **Evidence:** Full captured step log has zero content between "Detecting vulnerabilities" and the exit.
- **Classification:** Tooling (tentative) | **Severity:** Medium | **Blocking:** YES
- **Est. Fix Time:** Unknown — requires local reproduction with verbose Trivy output before scoping.
- **Recommended Story:** Investigation spike.
- **Acceptance Criteria:** Root cause identified with verbose/debug output before any fix is attempted.

### 4. Stage 5: pip-audit
- **Root Cause:** `poetry: command not found` — job never installs Poetry (sibling `lint-backend`/`typecheck-backend` jobs in the same file do).
- **Evidence:** `poetry: command not found` — exit 127.
- **Classification:** Configuration | **Severity:** Low | **Blocking:** YES
- **Est. Fix Time:** 2 min
- **Recommended Story:** Bundle with #1, #9.
- **Acceptance Criteria:** Job installs Poetry before invoking it; pip-audit runs to actual completion.

### 5. Stage 5: Bandit SAST (Upload bandit results)
- **Root Cause:** `bandit -f sarif` — installed Bandit version does not support `-f sarif`. `Run bandit` is masked by `|| true` (shows green) but produces no file; the upload step then fails on the missing file.
- **Evidence:** `bandit: error: argument -f/--format: invalid choice: 'sarif' (choose from csv, custom, html, json, screen, txt, xml, yaml)`; `##[error]Path does not exist: salesos/backend/bandit-results.sarif`.
- **Classification:** Configuration | **Severity:** Medium | **Blocking:** YES
- **Est. Fix Time:** 15–30 min (install `bandit-sarif-formatter`, or emit JSON + convert).
- **Recommended Story:** Bundle with #10 (identical root cause, second occurrence).
- **Acceptance Criteria:** Bandit produces a valid SARIF file; findings actually visible in GitHub code scanning (currently silently absent).

### 6. Stage 5: npm audit
- **Root Cause:** 31 real high-severity vulnerabilities in frontend deps (Next.js — 5 advisories incl. SSRF and DoS; `postcss`; `sharp`). Fixes available per `npm audit`'s own output. No severity threshold/allowlist configured.
- **Evidence:** Full advisory list captured in run logs, ending `31 high severity vulnerabilities` / `fix available via npm audit fix`.
- **Classification:** Dependency | **Severity:** HIGH | **Blocking:** YES
- **Est. Fix Time:** 1–4 hours (`npm audit fix` + regression test; Next.js bump may not be purely mechanical).
- **Recommended Story:** Dedicated dependency-remediation story.
- **Acceptance Criteria:** `npm audit` clean, or documented accepted-risk allowlist; frontend suite still green after the bump.

### 7. Stage 3: Frontend Unit Tests
- **Root Cause:** 33/194 suites fail — exactly matches the already-documented Sprint 01 gap (missing `Card`/`CardHeader`/`CardContent` component + scattered stale UI-text assertions). Not a regression.
- **Evidence:** `Test Suites: 33 failed, 161 passed, 194 total` / `Tests: 163 failed, 1 skipped, 2092 passed, 2256 total` — identical to Sprint 01's own closing numbers.
- **Classification:** Test Failure (pre-existing, already scoped) | **Severity:** Medium | **Blocking:** YES
- **Est. Fix Time:** 1–2 days (matches the Sprint 01 estimate).
- **Recommended Story:** The Jest-debt story already flagged as needed in Sprint 01's closing report — still open.
- **Acceptance Criteria:** `Card` component implemented to spec; 194/194 passing or each remaining failure individually triaged and accepted.

*(CI Summary's "Fail if any critical job failed" is the aggregate gate working correctly — not an independent failure.)*

---

## Docker Smoke Test workflow

### 8. Validate Compose File
- **Root Cause:** `docker compose config` fails before anything runs — `required variable GF_SECURITY_ADMIN_PASSWORD is missing a value`. The smoke-test workflow provides env vars for postgres/neo4j/JWT/secret but not for the `grafana` service.
- **Evidence:** `error while interpolating services.grafana.environment.[]: required variable GF_SECURITY_ADMIN_PASSWORD is missing a value`.
- **Classification:** Configuration | **Severity:** Medium | **Blocking:** YES (blocks the entire job; "Collect Docker Logs"/"Stop Services" failures are downstream consequences, not independent issues)
- **Est. Fix Time:** 5 min
- **Acceptance Criteria:** `docker compose config --quiet` succeeds in the smoke-test workflow's env.

---

## Security Scan workflow

### 9. pip-audit (distinct from #4)
- **Root Cause:** `pip-audit: error: argument -f/--format: expected one argument` — malformed CLI invocation, different bug from CI's missing-Poetry issue.
- **Evidence:** Exit 2, argument parsing error.
- **Classification:** Configuration | **Severity:** Low | **Blocking:** YES
- **Est. Fix Time:** 10 min

### 10. sast-scan (same root cause as #5) → cascades to semgrep
- **Root Cause:** Same Bandit `-f sarif` bug. "Upload bandit results" failing stops the job before "Install semgrep"/"Run semgrep" run (both skipped), so "Upload semgrep results" fails on a file that was never generated.
- **Evidence:** `##[error]Path does not exist: semgrep-results.sarif`; job step list shows semgrep steps skipped.
- **Classification:** Configuration (cascading) | **Severity:** Medium | **Blocking:** YES
- **Est. Fix Time:** Resolved once #5 is fixed, assuming step conditions let semgrep run regardless of Bandit's outcome.

### 11. secret-scan (Upload Trivy config results)
- **Root Cause:** SARIF category collision — this job already uploaded one Trivy SARIF earlier in the same job (secrets+vulns); the second upload (IaC config scan) collides on tool/category.
- **Evidence:** `Aborting upload: only one run of the codeql/analyze or codeql/upload-sarif actions is allowed per job per tool/category ... Tool: (Trivy)`.
- **Classification:** Configuration | **Severity:** Low-Medium (first upload succeeded; only the second is lost) | **Blocking:** YES
- **Est. Fix Time:** 10 min (distinct `category:` per `upload-sarif` step).

---

## Deploy Production workflow

### 12. Pre-deploy Validation — "Verify CI passed on this commit" ⚠️ CRITICAL
- **Root Cause:** Misleadingly named — the step body never checks CI status. It only checks `if [[ "refs/heads/master" != "refs/heads/main" ]]; then exit 1; fi`. This repo's real branch is `master`, not `main` — **fails unconditionally, on every push, regardless of CI outcome.**
- **Evidence:** `##[error]Deploy only allowed from main branch`, despite running on `master`.
- **Classification:** Configuration | **Severity:** CRITICAL | **Blocking:** YES — production deploy is completely non-functional, independent of every other finding in this report.
- **Est. Fix Time:** 2 min to correct the literal — but the step still wouldn't verify real CI status even after that; a genuine implementation (Checks API) is a separate, deeper fix.
- **Recommended Story:** Highest-priority standalone fix.
- **Acceptance Criteria:** Step correctly identifies `master` AND genuinely queries this commit's CI conclusion before allowing deploy.

### 13. Automatic Rollback — "Rollback to previous slot"
- **Root Cause:** Missing SSH host configuration for the rollback action.
- **Evidence:** `Error: missing server host`.
- **Classification:** Infrastructure | **Severity:** HIGH (safety net non-functional) | **Blocking:** YES for this job; only matters in practice once #12 is fixed.
- **Est. Fix Time:** Cannot estimate without knowing ops-side secret provisioning state.

### 14. Deploy Notification — "GitHub commit comment"
- **Root Cause:** `HttpError: Resource not accessible by integration` (403) — `GITHUB_TOKEN` lacks write permission for commit comments (missing `permissions:` block).
- **Evidence:** `status: 403`.
- **Classification:** Configuration | **Severity:** Low (cosmetic) | **Blocking:** YES for this job
- **Est. Fix Time:** 5 min (`permissions: contents: write`).

---

## Deploy Staging workflow

### 15–16. Build & Push Frontend / Build & Push Backend
- **Root Cause:** Both images build successfully (incl. SBOM generation); failure is specifically pushing to GHCR — `403 Forbidden` on blob HEAD request.
- **Evidence:** `ERROR: failed to push ghcr.io/ragheeda-boop/salesos/{frontend,backend}:staging: ... 403 Forbidden` (identical pattern, both jobs).
- **Classification:** Infrastructure | **Severity:** HIGH (blocks all staging deploys) | **Blocking:** YES
- **Est. Fix Time:** Uncertain — 15–30 min if it's a missing `permissions: packages: write`; could require manual GHCR package visibility/linking or an org-level policy change. Flagging uncertainty rather than guessing.

---

## Execution Order (highest ROI → lowest)

1. **#12** — Deploy Production branch check. 2 min, unblocks all of production deploy.
2. **#4, #9** — pip-audit in both workflows. Trivial, mirrors an already-working pattern elsewhere.
3. **#8** — Docker Smoke Test env var. 5 min, unblocks the whole job.
4. **#5/#10** — Bandit SARIF format. One fix resolves 3 job failures.
5. **#11** — Trivy SARIF category collision. 10 min.
6. **#14** — Deploy Production permissions. 5 min, cosmetic but easy.
7. **#1/#2 partial** — remove `cli/` from mypy/ruff invocations.
8. **#15/#16** — GHCR 403. Moderate/uncertain effort, high impact.
9. **#13** — Deploy Production rollback SSH host. Gated on ops access.
10. **#3** — Trivy filesystem scan silent failure. Needs local reproduction first.
11. **#6** — npm audit remediation. Real work, own story.
12. **#2 (main body)** — Ruff, 3,611 violations. Biggest line item, own story.
13. **#7** — Frontend Jest debt (33 suites). Already scoped from Sprint 01.

**Rationale:** items 1–9 are 2-to-30-minute configuration corrections (workflow YAML, env vars, tool flags — zero application-code risk) that would flip most red jobs green almost immediately. Items 10–13 are either genuinely unscoped investigations or large, already-identified bodies of real engineering work that deserve their own stories rather than being rushed into a CI-config pass.

---

## S04-02 Status

**FIELD VERIFICATION COMPLETE.** Real GitHub Actions execution triggered and observed on `master`; full evidence collected above. **CI GREEN is explicitly not met.**

## Decision

See `docs/program/DECISION_LOG.md` D-S4-002.

**Can Sprint 04 continue? YES WITH CI STORIES.**

None of the 17 failures originate in Sprint 04 feature code — STORY-04-01/04-02/02-03 are not yet implemented, and every failure is pre-existing CI/pipeline configuration or tooling debt first surfaced by this being the program's first real CI run. Sprint 04's actual feature work (tenant extension, provisioning workflow) does not depend on Deploy Production or Deploy Staging succeeding, and can proceed locally. However, CI currently provides **zero working merge-gate protection** — every stage is red — so dedicated CI-remediation stories must be opened per the Execution Order above, starting with the Deploy Production branch-name fix, rather than silently treating "CI is red" as acceptable background noise going forward.
