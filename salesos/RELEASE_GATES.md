# Release Gates

> Automated release gate specification for SalesOS.
> All gates **must** pass before any deployment to production.

---

## Gate 1: Security Review

| # | Check | Status |
|---|-------|--------|
| 1.1 | All critical security issues resolved = 0 | ❌ / ✅ |
| 1.2 | No hardcoded secrets (checked via automated scan) | ❌ / ✅ |
| 1.3 | Auth required on all routes (`Depends(get_current_tenant_id)` or `Depends(get_current_user_id)` on every `@router.*` / `@app.*` decorator) | ❌ / ✅ |
| 1.4 | Token blacklist + rotation tested | ❌ / ✅ |
| 1.5 | CSRF protection active | ❌ / ✅ |
| 1.6 | Rate limiting active | ❌ / ✅ |

**Failure**: Block release. Assign to Security Team.

---

## Gate 2: Architecture Review

| # | Check | Status |
|---|-------|--------|
| 2.1 | No cross-domain imports (`domains/` does not import from `app/` or `runtime/`) | ❌ / ✅ |
| 2.2 | No runtime imports from `app/` (`runtime/` does not import from `app/`) | ❌ / ✅ |
| 2.3 | Repository pattern used (no raw SQLAlchemy in domain layer) | ❌ / ✅ |
| 2.4 | Architecture score >= 95% (computed by architecture scoring tool) | ❌ / ✅ |

**Failure**: Block release. Assign to Architecture Team.

---

## Gate 3: Performance Review

| # | Check | Status |
|---|-------|--------|
| 3.1 | API p50 <= 200ms | ❌ / ✅ |
| 3.2 | API p95 <= 500ms | ❌ / ✅ |
| 3.3 | API p99 <= 1000ms | ❌ / ✅ |
| 3.4 | Database query time <= 100ms | ❌ / ✅ |
| 3.5 | No endpoint exceeds performance budget | ❌ / ✅ |
| 3.6 | Performance regression detected and blocked | ❌ / ✅ |

**Failure**: Block release. Assign to Performance Team.

---

## Gate 4: Testing & Coverage

| # | Check | Status |
|---|-------|--------|
| 4.1 | Unit test coverage >= 85% | ❌ / ✅ |
| 4.2 | Integration test coverage >= 70% | ❌ / ✅ |
| 4.3 | Security regression tests all pass | ❌ / ✅ |
| 4.4 | No flaky tests | ❌ / ✅ |
| 4.5 | Test suite completes within 10 minutes | ❌ / ✅ |

**Failure**: Block release. Assign to QA Team.

---

## Gate 5: CI/CD

| # | Check | Status |
|---|-------|--------|
| 5.1 | All CI checks pass (ruff, mypy, pytest) | ❌ / ✅ |
| 5.2 | Docker build succeeds | ❌ / ✅ |
| 5.3 | Migration runs without errors | ❌ / ✅ |
| 5.4 | No dependency vulnerabilities (pip audit) | ❌ / ✅ |

**Failure**: Block release. Assign to DevOps Team.

---

## Gate 6: Infrastructure

| # | Check | Status |
|---|-------|--------|
| 6.1 | All services healthy (health endpoint check) | ❌ / ✅ |
| 6.2 | Database connection pool adequate | ❌ / ✅ |
| 6.3 | No port conflicts | ❌ / ✅ |
| 6.4 | Resource limits defined | ❌ / ✅ |

**Failure**: Block release. Assign to Infrastructure Team.

---

## Gate 7: Documentation

| # | Check | Status |
|---|-------|--------|
| 7.1 | API docs generated | ❌ / ✅ |
| 7.2 | ADRs updated for any architecture changes | ❌ / ✅ |
| 7.3 | Changelog updated | ❌ / ✅ |
| 7.4 | README updated if interfaces changed | ❌ / ✅ |

**Failure**: Block release. Assign to Documentation Team.

---

## Gate 8: Release Decision

**ALL gates must pass for release to proceed.**

If any gate fails:

1. **Generate** a detailed failure report with failing checks and evidence.
2. **Assign** to the responsible team (as indicated per gate above).
3. **Block** merge until the issue is resolved.
4. **Re-run** all gates after the fix — a previous pass does not carry over.

| Gate | Result |
|------|--------|
| Gate 1 — Security Review | ❌ / ✅ |
| Gate 2 — Architecture Review | ❌ / ✅ |
| Gate 3 — Performance Review | ❌ / ✅ |
| Gate 4 — Testing & Coverage | ❌ / ✅ |
| Gate 5 — CI/CD | ❌ / ✅ |
| Gate 6 — Infrastructure | ❌ / ✅ |
| Gate 7 — Documentation | ❌ / ✅ |
| **Gate 8 — Final Decision** | **❌ / ✅** |

---

## Automation Implementation

The release gates are enforced via a **GitHub Actions workflow** (`.github/workflows/release-gates.yml`).

```yaml
name: Release Gates

on:
  pull_request:
    types: [opened, synchronize, reopened]
  push:
    branches: [main, release/*]

jobs:
  gate-1-security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check critical security issues
        run: ...
      - name: Scan for hardcoded secrets
        run: ...
      - name: Verify auth on all routes
        run: ...
      - name: Check token blacklist + rotation
        run: ...
      - name: Verify CSRF protection
        run: ...
      - name: Verify rate limiting
        run: ...

  gate-2-architecture:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check cross-domain imports
        run: ...
      - name: Check runtime imports from app/
        run: ...
      - name: Check repository pattern compliance
        run: ...
      - name: Compute architecture score
        run: ...

  gate-3-performance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Benchmark API endpoints
        run: ...
      - name: Check database query times
        run: ...
      - name: Detect performance regression
        run: ...

  gate-4-testing:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run unit tests with coverage
        run: ...
      - name: Run integration tests with coverage
        run: ...
      - name: Run security regression tests
        run: ...
      - name: Detect flaky tests
        run: ...
      - name: Check test suite duration
        run: ...

  gate-5-cicd:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run ruff
        run: ...
      - name: Run mypy
        run: ...
      - name: Run pytest
        run: ...
      - name: Build Docker image
        run: ...
      - name: Run migrations
        run: ...
      - name: pip audit
        run: ...

  gate-6-infrastructure:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check health endpoints
        run: ...
      - name: Verify database connection pool
        run: ...
      - name: Check for port conflicts
        run: ...
      - name: Verify resource limits
        run: ...

  gate-7-documentation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Verify API docs generated
        run: ...
      - name: Check ADR updates
        run: ...
      - name: Verify Changelog updated
        run: ...
      - name: Check README updates
        run: ...

  gate-8-decision:
    needs:
      - gate-1-security
      - gate-2-architecture
      - gate-3-performance
      - gate-4-testing
      - gate-5-cicd
      - gate-6-infrastructure
      - gate-7-documentation
    if: ${{ always() }}
    runs-on: ubuntu-latest
    steps:
      - name: Check all gate results
        run: |
          echo "Gate 1: ${{ needs.gate-1-security.result }}"
          echo "Gate 2: ${{ needs.gate-2-architecture.result }}"
          echo "Gate 3: ${{ needs.gate-3-performance.result }}"
          echo "Gate 4: ${{ needs.gate-4-testing.result }}"
          echo "Gate 5: ${{ needs.gate-5-cicd.result }}"
          echo "Gate 6: ${{ needs.gate-6-infrastructure.result }}"
          echo "Gate 7: ${{ needs.gate-7-documentation.result }}"
      - name: Fail if any gate failed
        if: >
          needs.gate-1-security.result != 'success' ||
          needs.gate-2-architecture.result != 'success' ||
          needs.gate-3-performance.result != 'success' ||
          needs.gate-4-testing.result != 'success' ||
          needs.gate-5-cicd.result != 'success' ||
          needs.gate-6-infrastructure.result != 'success' ||
          needs.gate-7-documentation.result != 'success'
        run: exit 1
```

Each step outputs **pass** or **fail**. If any step fails, the workflow fails and **no deployment occurs**.
