# SalesOS vNext — Engineering Strategy

> **Author**: Engineering Director
> **Status**: Approved
> **Version**: v1.0
> **Last Updated**: 2026-07-16
> **Supersedes**: All prior development workflows

---

## Table of Contents

1. [Branch Strategy](#1-branch-strategy)
2. [Code Review Process](#2-code-review-process)
3. [Testing Strategy](#3-testing-strategy)
4. [CI/CD Pipeline](#4-cicd-pipeline)
5. [Release Process](#5-release-process)
6. [Quality Gates](#6-quality-gates)
7. [Definition of Ready](#7-definition-of-ready)
8. [Definition of Done](#8-definition-of-done)
9. [Developer Experience](#9-developer-experience)
10. [Documentation Requirements](#10-documentation-requirements)
11. [Architecture Governance](#11-architecture-governance)
12. [Technical Debt Policy](#12-technical-debt-policy)

---

## 1. Branch Strategy

### Current State

Branches follow the format `feat/`, `fix/`, `chore/`, `hotfix/` with ticket number (e.g. `feat/SALES-42-company-ingestion`). PRs use squash merge to `main`. This pattern works but lacks a formal branching model for multi-developer coordination, hotfix traceability, and release isolation.

### Target State: GitHub Flow with Release Branches

```
main
  │
  ├── feat/SALES-123-feature-name    (feature branches from main)
  ├── fix/SALES-456-bug-name         (bugfix branches from main)
  ├── hotfix/SALES-789-critical      (hotfix branches from main, merge to main + latest release)
  │
  └── release/v2.1.0                 (release branches from main, merge back after go-live)
```

| Branch | Source | Merge Target | Lifespan | Purpose |
|--------|--------|-------------|----------|---------|
| `main` | — | — | Permanent | Integration branch. Always deployable. Protected. |
| `feat/*` | `main` | `main` via squash | Days | Single feature. One per developer. |
| `fix/*` | `main` | `main` via squash | Days | Bug fix not blocking release. |
| `hotfix/*` | `main` | `main` + `release/*` via merge commit | Hours | Critical production bug. Requires CTO override. |
| `release/v*` | `main` | `main` via merge commit | Sprint | Release stabilization. Only bugfixes merged. |

### Branch Naming Rules

| Element | Convention | Example |
|---------|-----------|---------|
| Features | `feat/SALES-NNN-kebab-description` | `feat/SALES-142-bulk-company-import` |
| Bugfixes | `fix/SALES-NNN-kebab-description` | `fix/SALES-158-search-timeout` |
| Hotfixes | `hotfix/SALES-NNN-kebab-description` | `hotfix/SALES-201-auth-bypass` |
| Chores | `chore/SALES-NNN-kebab-description` | `chore/SALES-89-upgrade-tailwind` |
| Releases | `release/v{major}.{minor}.{patch}` | `release/v2.1.0` |

### Rules

1. **`main` is protected** — no direct pushes. All changes via PR.
2. **Feature branches are short-lived** — max 3 days. Longer branches need justification.
3. **Release branches freeze `main`** — once `release/v*` is cut, only bugfixes and release-specific changes are merged to the release branch.
4. **Release branches merge back** — after release, the release branch is merged into `main` with a merge commit.
5. **Hotfix branches bypass quality gates** — only with documented CTO override. Technical debt created within 24 hours.

### Migration

1. Add branch protection rules to `main` in GitHub (required status checks, no direct push).
2. Document the branching model in `CONTRIBUTING.md`.
3. Enforce naming convention with a GitHub Action that validates branch names on push.

---

## 2. Code Review Process

### Current State

Code review follows the Engineering Constitution (Article 1): every PR needs a Code Reviewer and a Domain Expert. Reviews check architecture compliance, code quality, testing, events, observability, AI quality, documentation, and UX. A formal checklist exists in `docs/QUALITY_GATE.md`.

### Target State: Structured Review with Automated Pre-checks

#### Review Requirements

| Role | Required For | Responsibilities |
|------|-------------|-----------------|
| **Author** | Every PR | Self-review before requesting. Run lint, type check, tests locally. |
| **Code Reviewer** | Every PR | Code quality, patterns, test coverage, adherence to conventions. |
| **Domain Expert** | Changes with domain logic | Business correctness, event semantics, data model accuracy. |
| **Security Reviewer** | Auth, data, or infra changes | Vulnerability assessment, secret exposure, auth correctness. |
| **CTO** | Hotfixes, PR overrides, ADR changes | Final approval on exceptions. |

#### PR Checklist (Automated + Manual)

Every PR must pass these checks before review begins:

```
[ ] All CI gates pass (lint, type check, tests, security, architecture)
[ ] Branch is up to date with main (no conflicts)
[ ] Self-review completed (author checked their own diff)
[ ] At least 1 review from Code Reviewer
[ ] At least 1 review from Domain Expert (if domain logic changes)
[ ] Quality Gate checklist attached as PR description template
[ ] ADR referenced (if architectural change)
[ ] Technical debt register updated (if debt introduced)
[ ] CHANGELOG updated
```

#### Review Workflow

```
Author creates PR → CI runs all gates → Author requests review
  → Code Reviewer approves + Domain Expert approves → Author merges
```

| State | Action | Who |
|-------|--------|-----|
| Draft | Author is still working | Author |
| Ready for Review | Author marks as "Ready" + requests reviewers | Author |
| Changes Requested | Reviewer flags blocking issues | Reviewer |
| Approved | All reviewers approve | Reviewer |
| Merged | Squash merge to main | Author |

#### Review SLA

| Type | First Response | Approval |
|------|---------------|----------|
| Normal PR | Within 4 business hours | Within 24 hours |
| Hotfix | Within 1 hour | Within 2 hours |
| Release PR | Within 2 business hours | Within 8 hours |

#### Migration

1. Create a PR template with the Quality Gate checklist as default body.
2. Configure GitHub branch protection to require status checks and reviews.
3. Add CODEOWNERS file for automatic reviewer assignment per domain.
4. Document review SLA in `CONTRIBUTING.md`.

---

## 3. Testing Strategy

### Current State

- **93% unit test coverage** — exceeding the 85% target.
- **70% integration coverage** — meeting the target.
- **60% E2E coverage** — meeting the target.
- **2,110+ total tests** (269 E2E).
- **15+ testpaths** in pytest config — coverage reporting is fragmented.
- **Backend AI tests: 0** — critical governance violation (Constitution Article 2.2).
- **Agent Runtime tests: 0** — placeholder runtime with no tests.
- **RAG pipeline tests: 0** — empty test directory.
- **No load testing in CI** — performance regressions go undetected.
- **No performance regression tracking** — no baseline comparison.

### Target State: Consolidated Test Pyramid

```
           ╱╲
          ╱  ╲         E2E (60% coverage, 300+ tests)
         ╱    ╲
        ╱──────╲       Integration (75% coverage, 400+ tests)
       ╱        ╲
      ╱──────────╲     Contract (100% of endpoints, 150+ tests)
     ╱            ╲
    ╱──────────────╲   Unit (90%+ coverage, 2,500+ tests)
   ╱────────────────╲
  ╱──────────────────╲ Load & Performance (CI-gated, 20+ scenarios)
 ──────────────────────
```

#### Test Categories

| Category | Scope | Tools | Target | Current | CI Stage |
|----------|-------|-------|--------|---------|----------|
| **Unit** | Single function/class, all dependencies mocked | pytest, pytest-asyncio, InMemoryRepository | 90%+ | 93% | Stage 3 |
| **Integration** | Service + real DB, cross-domain via contracts | pytest, testcontainers, PostgreSQL | 75%+ | 70% | Stage 4 |
| **Contract** | API schema compliance (provider + consumer) | pytest (backend), Vitest (frontend), OpenAPI | 100% | Partial | Stage 2 |
| **E2E** | Full user journey, all services running | Playwright, pytest | 300+ tests | 269 | Stage 7 |
| **Load & Performance** | Throughput, latency, resource usage under load | k6, locust, custom benchmark | CI-gated | 0 | Stage 6 |
| **AI** | AIService, agents, RAG pipeline, PromptRegistry | pytest with mocked LLM, eval harness | 85%+ | 0% | Stage 3 |
| **Architecture** | Domain isolation, layer rules, circular imports | pytest-arch, custom import scanner | 100% | 95%+ | Stage 2 |

#### Test Consolidation Plan

**Problem**: 15+ testpaths in `pytest.ini` fragment coverage reporting and confuse developers.

**Target**: Single pytest configuration with one `tests/` directory mirroring `src/`:

```
tests/
  unit/                          # Mirrors src/ structure
    domains/
      identity/
      company/
      search/
      crm/
      timeline/
      scoring/
      ai/
      workflow/
      employee/
      customer-success/
      enrichment/
      entity-resolution/
      pipeline/
      decision-platform/
      data-fabric/
      feature-store/
    bootstrap/
    middleware/
  integration/                   # Cross-domain + external dependencies
  e2e/                           # End-to-end (Playwright)
  contract/                      # API contract tests
    provider/                    # Backend verifies its API matches schema
    consumer/                    # Frontend verifies its client matches schema
  performance/                   # Load tests (k6, locust)
  ai/                            # AI-specific: eval, model contract, regression
  conftest.py                    # Shared fixtures
  pytest.ini                     # Single config with one testpaths entry
```

**Migration**:
1. Create the consolidated `tests/` directory structure.
2. Move unit tests from scattered paths into `tests/unit/domains/*/`.
3. Merge all `conftest.py` files into `tests/conftest.py` with shared fixtures.
4. Update `pytest.ini` to have a single `testpaths = tests/unit tests/integration tests/contract tests/ai`.
5. Update CI to use consolidated configuration.
6. Add `tests/performance/` with k6 scenarios for critical paths.
7. Add AI test suite: mock LLM provider, test all AIService paths, test agent lifecycle, test RAG pipeline.

---

## 4. CI/CD Pipeline

### Current State

- **6 GitHub Actions workflows** — lint, test, security, docker, e2e, deploy.
- **7-stage pipeline** — lint → type check → unit tests → integration → security → docker → e2e.
- **Ruff + MyPy enforced** in CI.
- **85% coverage gate** via pytest-cov.
- **Security scanning**: Bandit SAST, Trivy, Semgrep, pip-audit, npm audit.
- **No load testing** in CI.
- **No performance regression tracking**.
- **Docker Compose** with 15+ services but healthcheck inconsistencies (Kafka).

### Target Pipeline Architecture

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ Stage 1   │   │ Stage 2   │   │ Stage 3   │   │ Stage 4   │   │ Stage 5   │   │ Stage 6   │   │ Stage 7   │
│           │   │           │   │           │   │           │   │           │   │           │   │           │
│  Lint     │──▶│  Type     │──▶│  Unit +   │──▶│  Integ-   │──▶│  Security │──▶│  Load +   │──▶│  E2E      │
│  & Format │   │  Check    │   │  Arch +   │   │  ration   │   │  Scan     │   │  Perf     │   │  Tests    │
│           │   │           │   │  AI Tests │   │  Tests    │   │           │   │  Tests    │   │           │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
     │               │               │               │               │               │               │
     ▼               ▼               ▼               ▼               ▼               ▼               ▼
  ruff check    mypy --strict   pytest tests/   pytest tests/   bandit -r src/   k6 run tests/   Playwright
  black --check  ruff check     unit/ + tests/  integration/    trivy scan .     performance/     e2e
                                                ai/             semgrep                          (Docker
  ESLint         tsc --noEmit   85% cov gate                     pip-audit                        Compose)
  prettier                                                     npm audit
```

#### Stage Details

| Stage | Name | Duration Target | Fail Action | Artifacts |
|-------|------|----------------|-------------|-----------|
| 1 | Lint & Format | < 2 min | Block PR | — |
| 2 | Type Check | < 3 min | Block PR | — |
| 3 | Unit + Arch + AI Tests | < 5 min | Block PR | Coverage report |
| 4 | Integration Tests | < 10 min | Block PR | Test report |
| 5 | Security Scan | < 10 min | Block PR | SARIF report |
| 6 | Load & Performance | < 15 min | Warn → Block if regression > 10% | Perf report |
| 7 | E2E Tests | < 20 min | Block PR | Video + trace |

#### CI/CD Workflow Consolidation

**Current**: 6 separate workflows (lint.yml, test.yml, security.yml, docker.yml, e2e.yml, deploy.yml).

**Target**: 3 consolidated workflows:

```
1. pull_request.yml      — Stages 1-6 (every PR)
2. merge_to_main.yml     — Stages 1-7 + Docker build + deploy to staging
3. release.yml           — Stages 1-7 + Docker build + deploy to production + tag
```

#### Performance Regression Tracking

**Current**: No performance baselines. Regressions go unnoticed.

**Target**: 
1. k6 tests run in Stage 6 with baseline comparison.
2. Baseline stored as JSON in `artifacts/perf-baseline.json`.
3. CI compares current run to baseline. Regression > 10% blocks the PR.
4. Baseline updated on `main` merges (approved by reviewer).
5. Dashboard at `docs/vnext/PERFORMANCE_BASELINE.md` auto-updated from CI.

#### Docker Compose Healthcheck Fixes

**Current**: Kafka healthcheck is inconsistent — sometimes reports healthy before broker is ready.

**Target**: Standardized healthcheck pattern across all 15+ services:

```yaml
services:
  kafka:
    healthcheck:
      test: ["CMD-SHELL", "kafka-broker-api-versions.sh --bootstrap-server localhost:9092"]
      interval: 10s
      timeout: 5s
      retries: 10
      start_period: 30s
  postgres:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U salesos"]
      interval: 5s
      timeout: 5s
      retries: 5
  neo4j:
    healthcheck:
      test: ["CMD-SHELL", "cypher-shell -u neo4j -p $NEO4J_PASSWORD 'RETURN 1'"]
      interval: 10s
      timeout: 5s
      retries: 5
```

Add Celery worker service with healthcheck:

```yaml
  celery-worker:
    build: .
    command: celery -A salesos.tasks worker --loglevel=info
    depends_on:
      redis:
        condition: service_healthy
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "celery -A salesos.tasks inspect ping"]
      interval: 30s
      timeout: 10s
      retries: 3
```

#### Migration

1. Consolidate 6 workflows into 3 as defined above.
2. Add k6 to CI (Stage 6) with baseline comparison.
3. Create `tests/performance/` with initial k6 scenarios for critical endpoints.
4. Fix all Docker Compose healthchecks to use the standardized pattern.
5. Add Celery worker to Docker Compose.
6. Add performance baseline artifact upload on main merges.
7. Update GitHub branch protection to require all 7 stages.

---

## 5. Release Process

### Current State

Releases follow a monthly cadence. Quality gates are documented but the release process lacks formal phases, versioning rules, rollback procedures, and changelog automation.

### Target State: Phased Release with Gates

#### Versioning: Semantic Versioning

| Component | Versioned | Scheme | Independently? |
|-----------|-----------|--------|---------------|
| Platform API | ✅ | `v{major}` in URL path | Yes (URL path) |
| Python packages | ✅ | Semver | Yes |
| NPM packages | ✅ | Semver | Yes |
| Docker images | ✅ | `{version}-{sha}` | Yes |
| **Overall Release** | ✅ | `v{major}.{minor}.{patch}` | — |

Version bump rules:

| Change Type | Bump | Example |
|-------------|------|---------|
| Breaking API change | Major | `v2.0.0` → `v3.0.0` |
| New feature (backward-compatible) | Minor | `v2.0.0` → `v2.1.0` |
| Bug fix (backward-compatible) | Patch | `v2.0.0` → `v2.0.1` |
| Security hotfix | Patch + hotfix suffix | `v2.0.1-hotfix.1` |

#### Release Phases

Each release follows 4 phases:

| Phase | Duration | Activities | Gates |
|-------|----------|------------|-------|
| **Planning** | 1 week | Scope definition, sprint planning, capacity allocation | PRD approved, ADRs drafted |
| **Development** | 3 weeks | Implementation, testing, code review | All PRs merged to `main`, all tests passing |
| **Stabilization** | 1 week | Release branch cut, regression testing, staging deploy, load testing | All 7 CI stages pass, perf regression < 10%, security scan clean |
| **Release** | 1 day | Production deploy, smoke tests, monitoring, rollback on-call | Health checks pass, error rate < 0.1%, p99 within budget |

#### Release Checklist

```markdown
## Release vX.Y.Z Checklist

### Pre-Release
[ ] All PRs for this release merged to main
[ ] Release branch `release/vX.Y.Z` cut from main
[ ] CHANGELOG.md updated with all changes
[ ] Version bumped in all relevant files (pyproject.toml, package.json, Docker tags)
[ ] Load tests pass with no regression > 10%
[ ] Security scan clean (all tools)
[ ] Migration scripts tested on staging DB
[ ] Rollback plan documented
[ ] Monitoring dashboards reviewed (all metrics OK)

### Release
[ ] Docker images built and tagged: salesos/api:vX.Y.Z, salesos/frontend:vX.Y.Z
[ ] Production deploy (gradual rollout: 10% → 50% → 100%)
[ ] Smoke tests pass on production
[ ] Error rate < 0.1% at 5 min post-deploy
[ ] P99 latency within budget at 15 min post-deploy
[ ] Release branch merged back to main

### Post-Release
[ ] Technical debt from this release registered
[ ] Feature flags for new features set to 100%
[ ] Feature flag removal tickets created (2 sprints from now)
[ ] Release announced in #engineering channel
```

#### Changelog

Changelog follows Keep a Changelog format with sections:

- **Added** — new features
- **Changed** — changes in existing functionality
- **Deprecated** — soon-to-be removed features
- **Removed** — removed features
- **Fixed** — bug fixes
- **Security** — security fixes
- **Technical Debt** — debt introduced/resolved

#### Rollback

Every release must have a documented rollback plan:

1. **Application rollback**: Revert Docker image to previous version tag.
2. **Database rollback**: Alembic `downgrade` to previous revision.
3. **Feature flag rollback**: Disable feature flag at runtime (no deploy needed).
4. **Full rollback**: Revert git merge, rebuild, redeploy.

Rollback decision criteria:
- Error rate > 1% for more than 5 minutes
- P99 latency exceeds budget by 2x for more than 15 minutes
- Critical security vulnerability discovered post-deploy
- Data integrity issue confirmed

#### Migration

1. Create `RELEASE_CHECKLIST.md` template.
2. Automate version bumping with a script (`scripts/bump_version.py`).
3. Add release workflow to CI (`release.yml`).
4. Document rollback procedures in `ops/RUNBOOK.md`.
5. Add CHANGELOG validation to PR checks (must be updated for user-facing changes).

---

## 6. Quality Gates

### Current State

8 gates defined in `docs/QUALITY_GATE.md` with 40+ checks (34 automated, 36 manual). All gates are blocking. CTO override process exists.

### Target State: Strengthened Gates with New Checks

#### All Gates (from QUALITY_GATE.md) Remain + Additions

| Gate | Current Checks | vNext Additions | Automation Target |
|------|---------------|-----------------|-------------------|
| 1: Architecture | 6 auto + 4 manual | Import boundary enforcement, file size < 600 lines | 8 auto + 3 manual |
| 2: Code Quality | 7 auto + 2 manual | mypy strict (remove `ignore_missing_imports = true`), no Any | 9 auto + 1 manual |
| 3: Testing | 5 auto + 3 manual | AI test coverage ≥ 85%, load test no regression | 8 auto + 1 manual |
| 4: Events & Telemetry | 5 auto + 3 manual | — | 5 auto + 3 manual |
| 5: Observability | 3 auto + 4 manual | Performance baseline check | 5 auto + 3 manual |
| 6: AI Quality | 3 auto + 5 manual | Model evaluation results in CI | 5 auto + 3 manual |
| 7: Documentation | 2 auto + 9 manual | ADR directory check, README accuracy check | 4 auto + 7 manual |
| 8: UX & Accessibility | 3 auto + 6 manual | — | 3 auto + 6 manual |

#### New Quality Gates for vNext

| Gate | Checks | Automation | Blocking |
|------|--------|------------|----------|
| **9: Performance** | Load test regression < 10%, p99 within budget, k6 scenarios pass | Full | ✅ |
| **10: Infrastructure** | Docker healthchecks valid, Terraform remote state configured, backup verified | Partial | ✅ |

#### MyPy Configuration Fix

**Current**: `ignore_missing_imports = true` in mypy config — masks real type errors.

**Target**: Remove `ignore_missing_imports = true`. Add stub packages or `type: ignore` comments with justification for _real_ missing imports.

Migration:
1. Remove `ignore_missing_imports = true` from `pyproject.toml` mypy config.
2. Run mypy and categorize all new errors:
   - Missing stubs → add `types-*` package or create inline stub.
   - Genuine type errors → fix the code.
   - Vendor library without stubs → add `# type: ignore[import]` with justification.
3. Add CI check that new code does not introduce new `type: ignore` without ticket reference.

#### Terraform State Configuration

**Current**: No remote state configured — state stored locally, risk of loss or conflict.

**Target**: Remote state with locking:

```hcl
terraform {
  backend "s3" {
    bucket         = "salesos-terraform-state"
    key            = "production/terraform.tfstate"
    region         = "eu-west-1"
    encrypt        = true
    dynamodb_table = "salesos-terraform-locks"
  }
}
```

**Migration**:
1. Create S3 bucket and DynamoDB table for state locking.
2. Configure backend in all Terraform configurations.
3. Migrate existing local state to remote (`terraform init -migrate-state`).
4. Add CI check that Terraform is always run with remote state configured.

#### Backup Restore Verification

**Current**: No automated backup restore verification in CI.

**Target**: Weekly CI job that:
1. Restores the latest production backup to a staging environment.
2. Runs data integrity checks (row counts, checksums, referential integrity).
3. Runs a smoke test suite against the restored data.
4. Reports pass/fail. Failure triggers an incident.

**Migration**:
1. Create `scripts/verify_backup.py` script.
2. Add weekly CI workflow `backup-verify.yml`.
3. Document in `ops/RUNBOOK.md`.

#### Migration

1. Add new gates to `docs/QUALITY_GATE.md` and update the gate summary table.
2. Fix mypy configuration and enforce in CI.
3. Configure Terraform remote state.
4. Add backup verification workflow.
5. Add performance gate to CI Stage 6.

---

## 7. Definition of Ready

### Current State

No formal Definition of Ready exists. Stories are pulled into sprints based on backlog grooming, but there is no checklist to ensure a story is truly ready for implementation.

### Target State

A story is **Ready** for implementation only when all of the following are true:

```
[ ] User story or requirement clearly stated
[ ] Acceptance criteria defined (3-5 concrete, testable conditions)
[ ] Technical approach reviewed with Tech Lead (for stories > 3 story points)
[ ] Dependencies identified and resolved or explicitly accepted
[ ] API contracts drafted (if adding/modifying endpoints)
[ ] ADR drafted (if architectural change)
[ ] Test strategy defined (unit, integration, contract, e2e)
[ ] Feature flag identified (name, default state, removal sprint)
[ ] UX mockups or wireframes approved (if UI change)
[ ] Security implications reviewed (if auth, data, or external input)
[ ] Performance implications identified (if new endpoint or data pipeline)
[ ] Estimation completed (story points)
[ ] All "Unknowns" resolved — no black-box work items
```

#### Ready Checklist by Story Type

| Criteria | Feature | Bugfix | Technical Debt | Hotfix |
|----------|---------|--------|----------------|--------|
| User story clearly stated | ✅ | ✅ | ✅ | ✅ |
| Acceptance criteria defined | ✅ | ✅ | ✅ | — |
| Tech Lead review | ✅ (if > 3 pts) | — | ✅ | — |
| Dependencies resolved | ✅ | — | — | — |
| API contracts drafted | ✅ | — | — | — |
| ADR drafted | ✅ (if architectural) | — | — | — |
| Test strategy defined | ✅ | ✅ | ✅ | — |
| Feature flag identified | ✅ | — | — | — |
| UX mockups approved | ✅ (if UI) | — | — | — |
| Security reviewed | ✅ | ✅ (if security) | — | — |
| Performance reviewed | ✅ (if new endpoint) | — | — | — |
| Estimated | ✅ | ✅ | ✅ | — |

#### Story Point Guidelines

| Points | Effort | Complexity | Risk |
|--------|--------|------------|------|
| 1 | < 4 hours | Trivial | None |
| 2 | 4-8 hours | Low | Low |
| 3 | 1-2 days | Medium | Low |
| 5 | 2-3 days | Medium-High | Medium |
| 8 | 3-5 days | High | Medium-High |
| 13 | 1-2 weeks | Very High | High |

Any story > 8 points must be decomposed into smaller stories.

#### Migration

1. Add DoR checklist to sprint planning template.
2. Enforce DoR via sprint planning — no story enters a sprint without DoR checks.
3. Document DoR in `CONTRIBUTING.md`.

---

## 8. Definition of Done

### Current State

Code acceptance criteria are defined in `docs/PROJECT_MANIFEST.md` Part VII with 5 gates. The quality gate system provides the closest equivalent to a DoD.

### Target State

A story is **Done** only when all of the following are true:

```
[ ] Code merged to main (PR approved + passing all CI gates)
[ ] All acceptance criteria met (verified by tests or manual QA)
[ ] Unit tests written and passing (coverage ≥ 85% for new code)
[ ] Integration tests written and passing (if cross-domain or external dependency)
[ ] Contract tests written and passing (if new/modified endpoint)
[ ] E2E tests written and passing (if new user journey)
[ ] Architecture compliance verified (no cross-domain imports, no violations)
[ ] Feature flag created (if new feature) — default OFF
[ ] Events registered in Event Catalog (if new events)
[ ] Capability registered in Capability Catalog (if new capability)
[ ] OpenAPI schema updated (auto from Pydantic, verified by contract tests)
[ ] ADR written (if architectural change)
[ ] CHANGELOG updated
[ ] Documentation updated (README, API docs, user guide as applicable)
[ ] Technical debt registered (if any debt introduced)
[ ] Performance impact measured and within budget (if applicable)
[ ] Security review completed (if applicable)
[ ] Accessibility verified (if UI change)
[ ] Monitoring dashboard reviewed (metrics, logs, traces working)
[ ] Product owner acceptance (demo or sign-off)
```

#### Done Checklist by Story Type

| Criteria | Feature | Bugfix | Technical Debt | Hotfix |
|----------|---------|--------|----------------|--------|
| Code merged | ✅ | ✅ | ✅ | ✅ |
| Acceptance criteria met | ✅ | ✅ | ✅ | ✅ |
| Unit tests | ✅ | ✅ | ✅ | — |
| Integration tests | ✅ | ✅ (if applicable) | — | — |
| Contract tests | ✅ | — | — | — |
| E2E tests | ✅ | ✅ | — | — |
| Architecture compliance | ✅ | ✅ | ✅ | ✅ |
| Feature flag | ✅ | — | — | — |
| Events catalog updated | ✅ | — | — | — |
| Capability catalog updated | ✅ | — | — | — |
| OpenAPI schema updated | ✅ | ✅ | — | ✅ |
| ADR written | ✅ (if architectural) | — | — | — |
| CHANGELOG updated | ✅ | ✅ | ✅ | ✅ |
| Documentation updated | ✅ | ✅ | ✅ | — |
| Technical debt registered | ✅ (if incurred) | — | — | ✅ |
| Performance measured | ✅ | ✅ | — | — |
| Security reviewed | ✅ | ✅ (if security) | — | ✅ |
| Accessibility verified | ✅ (if UI) | — | — | — |
| Monitoring reviewed | ✅ | ✅ | — | ✅ |
| PO acceptance | ✅ | ✅ | — | — |

#### Migration

1. Add DoD checklist to PR template (as part of PR body).
2. Enforce DoD via code review — reviewer checks DoD items.
3. Automated checks cover as many DoD items as possible.
4. Document DoD in `CONTRIBUTING.md`.

---

## 9. Developer Experience

### Current State

- **Python 3.12, FastAPI, SQLAlchemy async, Alembic** — modern stack with good DX.
- **Next.js 15, React 19, TypeScript 5.7, Tailwind 3.4** — but README incorrectly says Tailwind v4.
- **Ruff + MyPy enforced** in CI with pre-commit hooks.
- **Docker Compose** with 15+ services — but takes long to start and has healthcheck inconsistencies.
- **15+ testpaths** — confusing to navigate.
- **No ADR directory** — ADRs are scattered across `docs/` and `PROJECT_MANIFEST.md`.
- **Frontend packages** — 13 packages with no import boundary enforcement.
- **Celery workers not in Docker Compose** — have to run manually.
- **Terraform no remote state** — risk of state loss.
- **No backup restore verification** — recovery untested.

### Target State

#### README Accuracy

**Problem**: README says Tailwind v4, package.json shows v3.4.

**Fix**: Audit README for accuracy against `package.json`, `pyproject.toml`, and other source-of-truth files. Add a CI check that validates README version claims match package.json:

```yaml
# In lint.yml
- name: Validate README versions
  run: python scripts/validate_readme_versions.py
```

#### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.9.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.13.0
    hooks:
      - id: mypy
        args: [--strict, src/]
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-json
      - id: check-yaml
      - id: detect-private-key
      - id: no-commit-to-branch
        args: [--branch, main]
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets
```

#### Developer Tooling Improvements

| Improvement | Current State | Target State | Effort |
|-------------|--------------|--------------|--------|
| Pre-commit hooks | Ruff only | Ruff + MyPy + secrets + format + branch check | 1 day |
| Docker Compose startup | 15+ services, slow | Optimized with profiles (dev/prod/test); Celery added | 2 days |
| Local dev script | None | `make dev` or `scripts/dev.sh` — one command | 1 day |
| Test execution | Multiple testpaths, confusing | `pytest tests/unit` — one command, clear structure | Part of test consolidation |
| Coverage reporting | Fragmented across 15+ paths | Single report with per-domain breakdown | Part of test consolidation |
| API docs | OpenAPI at /docs | OpenAPI + dedicated dev portal page | 1 week |
| Environment setup | Manual, error-prone | `make setup` — installs deps, creates DB, runs migrations, seeds data | 2 days |
| Code generation | None | `make domain NAME=xxx` — creates domain scaffold from template | 3 days |
| README accuracy | Contains stale info (Tailwind v4) | CI-verified against package manifest | 1 day |

#### Migration

1. Set up pre-commit hooks (file: `.pre-commit-config.yaml`).
2. Create `Makefile` with common targets: `dev`, `setup`, `test`, `lint`, `typecheck`, `domain`.
3. Add Docker Compose profiles: `docker compose --profile dev up`.
4. Add Celery worker to Docker Compose.
5. Fix README inaccuracies and add CI validation.
6. Create domain scaffold generator script.

---

## 10. Documentation Requirements

### Current State

Documentation is comprehensive but has gaps:
- **ADRs are scattered** — some in `PROJECT_MANIFEST.md`, some in `docs/`, no dedicated ADR directory.
- **README version inaccuracies** — Tailwind v4 claim contradicts package.json.
- **Runbook content gaps** — noted in GA launch plan.
- **No contribution guide** — developers have to infer conventions from code and manifests.

### Target State

#### ADR Directory

**Target**: `docs/adr/` directory with sequentially numbered records:

```
docs/adr/
  README.md                    # Index of all ADRs
  0001-modular-monolith.md     # ADR-001: Modular Monolith
  0002-postgresql-primary.md   # ADR-002: PostgreSQL as Primary OLTP
  0003-neo4j-knowledge-graph.md
  ...
  0029-llm-provider-abstraction.md
```

**Migration**:
1. Create `docs/adr/` directory.
2. Extract existing ADRs from `PROJECT_MANIFEST.md` (Part II) into individual files.
3. Create index (`docs/adr/README.md`) with table of contents.
4. Update `PROJECT_MANIFEST.md` to reference ADR directory.
5. Enforce that all new ADRs are created as files in `docs/adr/` — not inline in manifests.

#### Required Documentation Per Artifact

| Artifact | Required Docs | Owner | Review Cadence |
|----------|--------------|-------|----------------|
| **Capability** | Capability Catalog entry, API docs, user guide | Domain Engineer | Per release |
| **API Endpoint** | OpenAPI schema (auto), provider contract test, consumer contract test | Backend Engineer | Per PR |
| **Domain Event** | Event Catalog entry, schema, consumer map | Domain Engineer | Per PR |
| **AI Asset** | AI Catalog entry, prompt registration, eval results | AI Engineer | Per sprint |
| **Infrastructure** | Deployment guide, runbook, SLA targets | DevOps Engineer | Per release |
| **Architecture Decision** | ADR in `docs/adr/` | Decision author | Per decision |
| **UI Component** | Storybook story, accessibility statement, design token usage | Frontend Engineer | Per PR |
| **Migration** | Migration guide, rollback plan, data verification script | Database Engineer | Per migration |
| **Release** | Changelog entry, release notes, deployment checklist | Release Manager | Per release |

#### README Requirements

Every package and project must have a README with:

```markdown
# Project/Package Name

## Description
<!-- What does this do? -->

## Quick Start
<!-- How to use it in 30 seconds -->

## Prerequisites
<!-- Python version, Node version, services needed -->

## Installation
<!-- How to install and set up -->

## Usage
<!-- Basic usage examples -->

## Testing
<!-- How to run tests -->

## API
<!-- Key API surfaces (if applicable) -->

## Configuration
<!-- Environment variables, config files -->

## Contributing
<!-- Link to CONTRIBUTING.md -->

## License
```

#### Migration

1. Create `docs/adr/` directory and migrate existing ADRs.
2. Create `CONTRIBUTING.md` with all conventions (branching, commit messages, PR process, coding standards).
3. Add CI check for README accuracy (version claims vs source of truth).
4. Audit all package READMEs for completeness against the template above.
5. Add documentation check to PR quality gates.

---

## 11. Architecture Governance

### Current State

- **ADRs scattered** — some in `PROJECT_MANIFEST.md` Part II, some in `docs/` files, no dedicated directory.
- **Architecture Review Board** — exists in constitution but no formal operating procedures.
- **Frozen Interfaces** — protected by constitution but no automated enforcement.
- **Cross-domain imports** — blocked by PR review but no automated scanner in CI for frontend.
- **Frontend import boundaries** — 13 packages with no enforcement.
- **Architecture compliance** — verified by automated script (`arch-compliance.ps1`) at 95%+.

### Target State

#### ADR Process

Every architectural decision follows this flow:

```
1. Identify need  →  2. Draft ADR  →  3. ARB review  →  4. Approve/Reject  →  5. Record
```

ADR template (placed in `docs/adr/README.md`):

```markdown
# ADR-NNN: Title

**Status**: [Proposed | Accepted | Deprecated | Superseded]
**Date**: YYYY-MM-DD
**Author**: Name
**Supersedes**: ADR-MMM (if applicable)

## Context
<!-- Why is this decision needed? What problem does it solve? -->

## Decision
<!-- What is the decision? -->

## Consequences
<!-- What are the trade-offs, risks, and benefits? -->

## Compliance
<!-- How will compliance be enforced (CI check, manual review)? -->
```

#### Architecture Review Board (ARB)

| Role | Member | Responsibilities |
|------|--------|-----------------|
| Chief Architect | Ragheed | ARB chair, final decision authority |
| Domain Architects | Per domain | Domain-specific expertise |
| Engineering Director | Ragheed | Process enforcement, resource allocation |
| CTO | — | Final appeal authority |

#### ARB Operating Procedures

| Activity | Cadence | Quorum |
|----------|---------|--------|
| ADR review | Asynchronous (within 48h of submission) | Chief Architect + 1 Domain Architect |
| Architecture sync | Bi-weekly | Chief Architect + 2 Domain Architects |
| Emergency review | Within 4 hours of request | Chief Architect + CTO |
| Quarterly retrospective | Quarterly | Full ARB |

#### Automated Architecture Enforcement

| Rule | Tool | Enforcement |
|------|------|-------------|
| No cross-domain Python imports | `pytest-arch` + custom scanner | CI gate 1 |
| No infrastructure imports in domain | Layer scanner | CI gate 1 |
| No circular dependencies | `pytest-arch` | CI gate 1 |
| No Frozen Interface modification | Interface scanner | CI gate 1 |
| File size < 600 lines | `ruff` rule or custom check | CI gate 2 |
| Frontend import boundaries | `eslint-plugin-import` + custom rule | CI gate 2 |
| ADR exists for architectural changes | PR label + check script | CI gate 7 |
| No cross-domain API client imports (frontend) | Custom eslint rule | CI gate 2 |

#### Frontend Import Boundary Enforcement

**Current**: 13 frontend packages with no import boundary enforcement — Company widgets can import Timeline internals.

**Target**: ESLint rule enforcing package-level import boundaries:

```jsonc
// .eslintrc.json (per package)
{
  "rules": {
    "@salesos/import-boundaries": [
      "error",
      {
        "boundaries": [
          { "from": ["@salesos/widget-*"], "allow": ["@salesos/widget-sdk", "@salesos/api-client"] },
          { "from": ["@salesos/api-*"], "allow": ["@salesos/api-client"] },
          { "from": ["@salesos/widget-sdk"], "allow": ["@salesos/design-language", "@salesos/ui"] },
          { "from": ["@salesos/ui"], "allow": ["@salesos/design-language"] },
          { "from": ["@salesos/design-language"], "allow": [] }
        ]
      }
    ]
  }
}
```

#### Migration

1. Create `docs/adr/` directory and migrate all existing ADRs.
2. Implement frontend import boundary enforcement with ESLint plugin.
3. Add ADR presence check to CI (PRs with architectural changes require ADR).
4. Formalize ARB membership and operating procedures.
5. Add file size check to CI.
6. Create ADR template in `docs/adr/template.md`.

---

## 12. Technical Debt Policy

### Current State

- **Technical Debt Register** exists in `memory/technical-debt.md` with 1 tracked item (low).
- **Pattern Scan**: 80 violations resolved, architecture compliance 95%+.
- **Constitution Article 2.3** requires debt registration and resolution.
- **No automated debt tracking** — relies on manual registration.
- **No debt budget** — no limit on accumulated debt per sprint.

### Target State

#### Technical Debt Register

Maintained at `memory/technical-debt.md` with this schema:

```markdown
## TD-NNN: Description

| Field | Value |
|-------|-------|
| **ID** | TD-NNN |
| **Area** | Domain / Infra / Frontend / AI / Testing / Docs |
| **Severity** | Critical / High / Medium / Low |
| **Effort** | X hours / Y days / Z sprints |
| **Age** | Created: YYYY-MM-DD |
| **Owner** | @github-username |
| **Status** | Open / In Progress / Resolved / Accepted |
| **Resolution Sprint** | Sprint N (if resolved) |

### Description
<!-- What is the debt? -->

### Impact
<!-- Why is this debt harmful? -->

### Remediation Plan
<!-- How will it be fixed? -->

### Created By
<!-- What introduced this debt? PR #, hotfix, design shortcut -->
```

#### Debt Classification

| Severity | Definition | Resolution SLA |
|----------|------------|---------------|
| **Critical** | Blocks production reliability, security, or data integrity | Resolve within current sprint |
| **High** | Significantly impacts development velocity, test reliability, or performance | Resolve within 1 sprint |
| **Medium** | Impacts code quality, developer experience, or documentation accuracy | Resolve within 3 sprints |
| **Low** | Cosmetic, non-blocking, nice-to-have improvements | Resolve within 6 sprints |

#### Debt Budget

| Metric | Limit | Current | Status |
|--------|-------|---------|--------|
| Critical debt items | 0 | 0 | 🟢 |
| High debt items | ≤ 2 | 0 | 🟢 |
| Medium debt items | ≤ 5 | ~2 | 🟢 |
| Low debt items | ≤ 10 | ~1 | 🟢 |
| Total debt items | ≤ 10 | ~3 | 🟢 |
| Maximum debt age (Critical) | 1 sprint | — | 🟢 |
| Maximum debt age (High) | 2 sprints | — | 🟢 |
| Debt added per sprint | ≤ 3 items | — | 🟡 Needs monitoring |

#### Debt Automation

| Automation | Description | Timeline |
|------------|-------------|----------|
| **PR debt check** | PR template prompts "Does this introduce debt? If yes, register." | Sprint 1 |
| **Debt dashboard** | Auto-generated from `memory/technical-debt.md` | Sprint 2 |
| **Aging alerts** | Slack notification when debt exceeds SLA | Sprint 2 |
| **Debt budget enforcement** | CI warning if debt budget exceeded | Sprint 3 |
| **Feature freeze on debt overflow** | Block new features if debt exceeds budget | Sprint 4 |

#### Debt Prevention

| Practice | Description |
|----------|-------------|
| **Review-first** | Code review catches shortcuts before merge |
| **Test-first** | Writing tests first reduces "I'll add tests later" debt |
| **ADR-first** | Architectural decisions are documented before implementation |
| **Sprint debt cap** | Max 3 debt items per sprint (added or resolved) |
| **Debt repayment sprint** | Every 4th sprint is a "debt sprint" — resolve existing debt, no new features |

#### Migration

1. Update `memory/technical-debt.md` with the standardized schema.
2. Add PR template prompt for debt registration.
3. Create debt dashboard script.
4. Add Slack notifications for aging debt.
5. Enforce debt budget in CI (warning at first, blocking later).

---

## Appendix A: Audit Issue Resolution Map

| # | Audit Finding | Section | Resolution | Priority |
|---|---------------|---------|------------|----------|
| 1 | `ignore_missing_imports = true` in mypy | §6 Quality Gates | Remove config, fix all new type errors, add stubs | P1 |
| 2 | 15+ testpaths fragments coverage reporting | §3 Testing Strategy | Consolidate to single `tests/` directory | P1 |
| 3 | README says Tailwind v4, package.json v3.4 | §9 Developer Experience | Fix README, add CI version validation | P0 |
| 4 | No ADR directory, decisions scattered | §11 Architecture Governance | Create `docs/adr/`, migrate existing ADRs | P1 |
| 5 | Frontend packages without import boundaries | §11 Architecture Governance | ESLint import boundary rules | P1 |
| 6 | No load testing in CI | §4 CI/CD Pipeline | Add k6 stage with baseline comparison | P1 |
| 7 | No performance regression tracking | §4 CI/CD Pipeline | Baseline comparison in CI Stage 6 | P1 |
| 8 | Docker Compose healthcheck inconsistencies (Kafka) | §4 CI/CD Pipeline | Standardize healthcheck pattern across all services | P1 |
| 9 | Terraform no remote state | §6 Quality Gates | Configure S3 backend + DynamoDB locking | P1 |
| 10 | Celery workers not in Docker Compose | §4 CI/CD Pipeline | Add celery-worker service with healthcheck | P1 |
| 11 | No backup restore verification in CI | §6 Quality Gates | Weekly backup verify workflow | P2 |

## Appendix B: Key Metrics and Targets

| Metric | Current | vNext Target | Measurement |
|--------|---------|-------------|-------------|
| Unit test coverage | 93% | ≥ 90% | pytest-cov |
| Integration coverage | 70% | ≥ 75% | pytest-cov (integration paths) |
| E2E tests | 269 | ≥ 300 | Playwright test count |
| Total tests | 2,110+ | ≥ 3,000 | pytest + Playwright |
| Backend AI test coverage | 0% | ≥ 85% | pytest-cov (ai domain) |
| Agent runtime tests | 0 | ≥ 100 | pytest |
| Architecture compliance | 95% | ≥ 98% | `arch-compliance.ps1` |
| Performance regression | Untracked | < 10% from baseline | k6 baseline comparison |
| Security posture | 10/10 | 10/10 | External pentest |
| Technical debt (critical) | 0 | 0 | TDR audit |
| Technical debt (total) | 1 | ≤ 10 | TDR audit |
| ADR coverage | Scattered | 100% in `docs/adr/` | File existence check |
| Frontend import boundary compliance | 0% | 100% | ESLint rule |
| MyPy strict compliance | Partial (ignore_missing_imports) | 100% strict | mypy exit code |
| Docker healthcheck compliance | Inconsistent | 100% standardized | Compose validation |
| Terraform remote state | Not configured | 100% | `terraform init` check |
| Backup restore verification | None | Weekly passing | CI workflow |
| CI pipeline stages | 6 workflows, 7 stages | 3 workflows, 7 stages | Workflow file count |
| Pre-commit hooks | Ruff only | Full suite | `.pre-commit-config.yaml` |
| README accuracy | Untracked | CI-validated per commit | `validate_readme_versions.py` |

---

*This Engineering Strategy is binding on all SalesOS vNext development. All teams must align their workflows to this strategy by Sprint 2 of vNext.*
