# QA Engineer — SalesOS

> SalesOS Engineering Team · Saudi Arabia (Remote OK)

---

## About SalesOS

SalesOS is an AI-native enterprise intelligence platform with 93% unit test coverage, 41 E2E tests across 7 critical paths, and 2054 total tests. We enforce 85% minimum coverage per domain via automated checks. Our test pyramid spans unit tests (pytest + Jest), integration tests, E2E tests (Playwright), and performance tests.

## Role

You will own quality assurance across the full stack — design test strategies, build automated test suites, perform performance testing, and ensure our GA release meets production standards. You will work across backend (Python/FastAPI) and frontend (React/Next.js) testing.

## Requirements

### Must-Have

- **Playwright** — E2E testing, page object model, cross-browser testing, visual regression
- **Jest** — React component testing, mocking, snapshot testing, code coverage
- **pytest** — Python unit/integration testing, fixtures, parametrize, coverage reporting
- **API testing** — REST API testing, contract testing, schema validation
- **Performance testing** — load testing, stress testing, latency measurement
- **Test strategy** — test pyramid design, risk-based testing, regression suites

### Nice-to-Have

- **Security testing** — OWASP Top 10, vulnerability scanning, penetration testing basics
- **Accessibility testing** — WCAG AA audit, screen reader testing, keyboard navigation
- **Arabic/RTL testing** — bidirectional layout validation, Arabic text rendering
- **Database testing** — PostgreSQL data integrity, migration testing
- **CI/CD integration** — test automation in pipelines, flaky test management

## Architecture Context

| Test Layer | Tool | Current | Target |
|-----------|------|---------|--------|
| Unit Tests | pytest (backend), Jest (frontend) | 93% coverage | 93%+ maintained |
| Integration Tests | pytest + testcontainers | 70% coverage | 80% |
| E2E Tests | Playwright | 41 tests, 7 paths | 100+ tests, all paths |
| Performance | load-test.py | Script exists | CI-integrated |
| Contract Tests | describeWidgetContract | Widget SDK only | All API contracts |
| Security | Trivy, Bandit, Semgrep | CI workflow | + runtime scanning |

## Test Infrastructure

| Component | Tool | Notes |
|-----------|------|-------|
| Backend Unit | pytest + coverage | InMemory repositories for isolation |
| Backend Integration | pytest + PostgreSQL/Neo4j | Real database tests |
| Frontend Unit | Jest + React Testing Library | Component + hook tests |
| E2E | Playwright | Chromium, Firefox, WebKit |
| Performance | Custom load-test.py | p50/p95/p99 measurement |
| Contract | Widget SDK testing utils | `describeWidgetContract()` |
| CI | GitHub Actions | Tests run on every PR |

## Responsibilities

1. Design and maintain test strategy across all layers
2. Build and extend E2E test suites with Playwright
3. Create performance test scenarios and baseline measurements
4. Ensure test coverage stays above 85% per domain
5. Investigate and resolve flaky tests
6. Integrate tests into CI/CD pipeline (gate on failure)
7. Perform regression testing before releases
8. Validate Arabic/RTL functionality across the platform
9. Conduct accessibility audits (WCAG AA)
10. Track and report quality metrics to engineering leadership

## Key Projects

| Project | Description | Priority |
|---------|-------------|----------|
| E2E Expansion | 41 → 100+ tests covering all critical paths | P0 |
| Performance Baseline | Automated p95/p99 tracking per endpoint | P0 |
| Arabic QA | Full bilingual testing across all interfaces | P1 |
| Security Testing | OWASP Top 10 validation, auth testing | P1 |
| Accessibility Audit | WCAG AA compliance across all pages | P1 |
| Contract Testing | API contract tests for all 17 routers | P2 |

## What We Offer

- Own quality for a platform with high test culture (93% coverage enforced)
- Modern testing stack: Playwright, Jest, pytest, load testing
- Clear quality gates — automated coverage enforcement in CI
- Impact: your work directly protects production reliability
- Competitive compensation aligned with Saudi market

## Interview Process

1. **Technical Screening** — Testing concepts, test pyramid, automation approaches (1 hour)
2. **Hands-On Challenge** — Write Playwright E2E test + pytest unit test (take-home, 2 hours max)
3. **Architecture Discussion** — Test strategy, flaky tests, performance testing (45 min)
4. **Team Fit** — Meet the engineering team (30 min)
5. **Offer** — Within 48 hours of final interview

---

*SalesOS is an equal opportunity employer. We value diversity and inclusion.*
